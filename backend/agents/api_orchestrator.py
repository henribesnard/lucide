"""
API Orchestrator for autonomous agents.

This module executes endpoint plans with parallel/sequential handling,
retry logic, and error management.

Phase 5 implementation.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
import structlog

logger = structlog.get_logger()


@dataclass
class CallResult:
    """Result of a single API call."""
    call_id: str
    endpoint_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    from_cache: bool = False


@dataclass
class ExecutionResult:
    """Result of executing a plan."""
    success: bool
    call_results: List[CallResult] = field(default_factory=list)
    total_api_calls: int = 0
    total_cache_hits: int = 0
    total_execution_time: float = 0.0
    collected_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class SimpleCircuitBreaker:
    """
    Simple circuit breaker implementation.

    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject calls
    - HALF_OPEN: Test if service recovered
    """

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.state == "OPEN":
            # Check if timeout passed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("circuit_breaker_half_open", failures=self.failures)
                return False
            return True
        return False

    def record_success(self):
        """Record successful call."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failures = 0
            logger.info("circuit_breaker_closed")

    def record_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("circuit_breaker_opened", failures=self.failures)


class APIOrchestrator:
    """
    Executes endpoint plans with intelligent orchestration.

    Features:
    - Parallel execution with asyncio
    - Dynamic parameter resolution
    - Retry logic (3 attempts)
    - Circuit breaker
    - Partial failure handling
    - Cache integration
    """

    def __init__(
        self,
        cache_manager=None,
        api_client=None,
        circuit_breaker: Optional[SimpleCircuitBreaker] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        self.cache = cache_manager
        self.api = api_client
        self.circuit_breaker = circuit_breaker or SimpleCircuitBreaker()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def execute(self, plan) -> ExecutionResult:
        """
        Execute an endpoint plan with parallel execution.

        Args:
            plan: ExecutionPlan from EndpointPlanner

        Returns:
            ExecutionResult with collected data and metrics
        """
        start_time = time.time()

        collected_data = {}
        call_results = []
        total_api_calls = 0
        total_cache_hits = 0
        errors = []

        # Get sequential execution levels for parallel execution
        levels = plan.get_sequential_calls()

        logger.info(
            "execution_start",
            question=plan.question,
            total_calls=len(plan.endpoints),
            levels=len(levels)
        )

        # Execute each level (calls in same level run in parallel)
        for level_idx, level_calls in enumerate(levels):
            logger.info(
                "executing_level",
                level=level_idx,
                calls_count=len(level_calls)
            )

            # Execute all calls in this level in parallel
            level_tasks = [
                self._execute_call(call, collected_data)
                for call in level_calls
            ]

            level_results = await asyncio.gather(*level_tasks, return_exceptions=True)

            # Process results
            for call, result in zip(level_calls, level_results):
                if isinstance(result, Exception):
                    # Handle exception
                    error_msg = f"Failed to execute {call.endpoint_name}: {str(result)}"
                    errors.append(error_msg)
                    logger.error(
                        "call_failed",
                        call_id=call.call_id,
                        endpoint=call.endpoint_name,
                        error=str(result)
                    )

                    call_results.append(CallResult(
                        call_id=call.call_id,
                        endpoint_name=call.endpoint_name,
                        success=False,
                        error=str(result)
                    ))
                else:
                    # Got CallResult
                    call_result = result
                    call_results.append(call_result)

                    if call_result.success:
                        # Store data for dependency resolution
                        collected_data[call.call_id] = call_result.data
                        collected_data[call.endpoint_name] = call_result.data

                        if call_result.from_cache:
                            total_cache_hits += 1
                        else:
                            total_api_calls += 1
                    else:
                        # Call failed - add to errors
                        if call_result.error:
                            errors.append(call_result.error)

        total_time = time.time() - start_time

        success = len(errors) == 0 or not plan.endpoints  # Success if no errors or no calls

        logger.info(
            "execution_complete",
            success=success,
            api_calls=total_api_calls,
            cache_hits=total_cache_hits,
            errors_count=len(errors),
            duration_ms=int(total_time * 1000)
        )

        return ExecutionResult(
            success=success,
            call_results=call_results,
            total_api_calls=total_api_calls,
            total_cache_hits=total_cache_hits,
            total_execution_time=total_time,
            collected_data=collected_data,
            errors=errors
        )

    async def _execute_call(
        self,
        call,
        collected_data: Dict[str, Any]
    ) -> CallResult:
        """
        Execute a single API call with caching, retries, and circuit breaker.

        Args:
            call: EndpointCall to execute
            collected_data: Data collected so far (for param resolution)

        Returns:
            CallResult
        """
        start_time = time.time()

        # 1. Check circuit breaker
        if self.circuit_breaker.is_open():
            logger.warning(
                "circuit_breaker_open",
                call_id=call.call_id,
                endpoint=call.endpoint_name
            )
            return CallResult(
                call_id=call.call_id,
                endpoint_name=call.endpoint_name,
                success=False,
                error="Circuit breaker is open",
                execution_time=time.time() - start_time
            )

        # 2. Resolve dynamic parameters
        resolved_params = self._resolve_params(call.params, collected_data)

        # 3. Check cache if available
        if self.cache:
            try:
                cached_data = await self.cache.get(call.endpoint_name, resolved_params)

                if cached_data is not None:
                    logger.info(
                        "cache_hit",
                        call_id=call.call_id,
                        endpoint=call.endpoint_name
                    )

                    return CallResult(
                        call_id=call.call_id,
                        endpoint_name=call.endpoint_name,
                        success=True,
                        data=cached_data,
                        execution_time=time.time() - start_time,
                        from_cache=True
                    )
            except Exception as e:
                logger.warning(
                    "cache_check_failed",
                    call_id=call.call_id,
                    error=str(e)
                )

        # 4. Make API call with retries
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    # Wait before retry
                    await asyncio.sleep(self.retry_delay * attempt)
                    logger.info(
                        "retry_attempt",
                        call_id=call.call_id,
                        attempt=attempt + 1,
                        max_retries=self.max_retries
                    )

                # Make the API call
                data = await self._make_api_call(call.endpoint_name, resolved_params)

                # Success!
                self.circuit_breaker.record_success()

                # Store in cache if available
                if self.cache:
                    try:
                        await self.cache.set(call.endpoint_name, resolved_params, data)
                    except Exception as e:
                        logger.warning(
                            "cache_set_failed",
                            call_id=call.call_id,
                            error=str(e)
                        )

                execution_time = time.time() - start_time

                logger.info(
                    "call_success",
                    call_id=call.call_id,
                    endpoint=call.endpoint_name,
                    attempt=attempt + 1,
                    duration_ms=int(execution_time * 1000)
                )

                return CallResult(
                    call_id=call.call_id,
                    endpoint_name=call.endpoint_name,
                    success=True,
                    data=data,
                    execution_time=execution_time,
                    from_cache=False
                )

            except Exception as e:
                last_error = e
                self.circuit_breaker.record_failure()

                logger.warning(
                    "call_attempt_failed",
                    call_id=call.call_id,
                    endpoint=call.endpoint_name,
                    attempt=attempt + 1,
                    error=str(e)
                )

        # All retries failed
        execution_time = time.time() - start_time

        logger.error(
            "call_failed_all_retries",
            call_id=call.call_id,
            endpoint=call.endpoint_name,
            error=str(last_error)
        )

        return CallResult(
            call_id=call.call_id,
            endpoint_name=call.endpoint_name,
            success=False,
            error=f"Failed after {self.max_retries} retries: {str(last_error)}",
            execution_time=execution_time
        )

    def _resolve_params(
        self,
        params: Dict[str, Any],
        collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve dynamic parameters from collected data.

        Example:
            params = {'team': '<from_teams_search>'}
            collected_data = {'call_0': {'response': [{'team': {'id': 85}}]}}
            → {'team': 85}

        Args:
            params: Parameters with potential placeholders
            collected_data: Data collected from previous calls

        Returns:
            Resolved parameters
        """
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith('<from_'):
                # Dynamic parameter: <from_teams_search> or <from_call_0>
                source = value[6:-1]  # Extract 'teams_search' or 'call_0'

                # Try to extract the value
                extracted = self._extract_value(collected_data.get(source), key)

                if extracted is not None:
                    resolved[key] = extracted
                else:
                    logger.warning(
                        "param_resolution_failed",
                        param_key=key,
                        source=source,
                        available_keys=list(collected_data.keys())
                    )
                    # Keep the placeholder (will likely fail API call)
                    resolved[key] = value
            else:
                # Static parameter
                resolved[key] = value

        return resolved

    def _extract_value(
        self,
        data: Any,
        key: str
    ) -> Any:
        """
        Extract value from nested data structure.

        Tries common patterns:
        - data['id']
        - data['response'][0]['team']['id']
        - data['team']['id']

        Args:
            data: Source data
            key: Key to extract (e.g., 'team', 'id')

        Returns:
            Extracted value or None
        """
        if data is None:
            return None

        # Direct access
        if isinstance(data, dict):
            if key in data:
                return data[key]

            # Try common patterns
            if 'response' in data and isinstance(data['response'], list) and len(data['response']) > 0:
                first_item = data['response'][0]
                if isinstance(first_item, dict) and key in first_item:
                    return first_item[key]

                # Try nested (e.g., team.id)
                if 'team' in first_item and isinstance(first_item['team'], dict):
                    if key in first_item['team']:
                        return first_item['team'][key]

            # Try 'id' as fallback
            if key == 'id' or key.endswith('_id'):
                if 'id' in data:
                    return data['id']

        return None

    async def _make_api_call(
        self,
        endpoint_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make an API call.

        This is a placeholder that should call the actual API client.
        For now, it simulates a call.

        Args:
            endpoint_name: Name of the endpoint
            params: Resolved parameters

        Returns:
            API response data
        """
        if self.api is None:
            # Simulate API call for testing
            await asyncio.sleep(0.1)  # Simulate network latency
            return {
                "endpoint": endpoint_name,
                "params": params,
                "response": [{"id": 123, "name": "Test Data"}]
            }

        # Call actual API client
        return await self.api.call(endpoint_name, params)
