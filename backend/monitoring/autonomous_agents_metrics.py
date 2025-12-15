"""
Metrics and logging infrastructure for autonomous agents.

This module provides Prometheus metrics collection and structured logging
for monitoring the performance and behavior of autonomous agents.
"""

import time
import functools
import inspect
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge, Info
import structlog


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class Metrics:
    """
    Prometheus metrics for autonomous agents system.

    Tracks performance, quality, and resource usage of all components.
    """

    # ===== Question Validator Metrics =====
    validation_success = Counter(
        'question_validation_success_total',
        'Number of questions validated successfully'
    )

    validation_failure = Counter(
        'question_validation_failure_total',
        'Number of questions that failed validation'
    )

    clarification_requests = Counter(
        'clarification_requests_total',
        'Number of clarification requests generated',
        ['question_type']
    )

    validation_duration = Histogram(
        'validation_duration_seconds',
        'Time taken to validate a question',
        buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    )

    entity_extraction_success = Counter(
        'entity_extraction_success_total',
        'Number of successful entity extractions'
    )

    entity_extraction_failure = Counter(
        'entity_extraction_failure_total',
        'Number of failed entity extractions'
    )

    # ===== Endpoint Planner Metrics =====
    plans_generated = Counter(
        'endpoint_plans_generated_total',
        'Number of execution plans generated'
    )

    plans_failed = Counter(
        'endpoint_plans_failed_total',
        'Number of failed plan generations',
        ['failure_reason']
    )

    api_calls_in_plan = Histogram(
        'api_calls_per_plan',
        'Number of API calls in generated plans',
        buckets=[1, 2, 3, 4, 5, 7, 10, 15]
    )

    plan_optimization_savings = Counter(
        'plan_optimization_api_calls_saved_total',
        'Number of API calls saved through optimization (enriched endpoints)'
    )

    enriched_endpoints_used = Counter(
        'enriched_endpoints_used_total',
        'Number of times enriched endpoints were used',
        ['endpoint_name']
    )

    plan_generation_duration = Histogram(
        'plan_generation_duration_seconds',
        'Time taken to generate execution plan',
        buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    )

    # ===== Cache Metrics =====
    cache_hits = Counter(
        'cache_hits_total',
        'Number of cache hits',
        ['endpoint_name']
    )

    cache_misses = Counter(
        'cache_misses_total',
        'Number of cache misses',
        ['endpoint_name']
    )

    cache_sets = Counter(
        'cache_sets_total',
        'Number of cache set operations',
        ['endpoint_name']
    )

    cache_hit_rate = Gauge(
        'cache_hit_rate',
        'Current cache hit rate (0-1)',
        ['endpoint_name']
    )

    cache_size_bytes = Gauge(
        'cache_size_bytes',
        'Current cache size in bytes'
    )

    cache_ttl_seconds = Histogram(
        'cache_ttl_seconds',
        'TTL assigned to cached items',
        ['cache_strategy'],
        buckets=[30, 60, 300, 600, 1800, 3600, 86400]
    )

    multi_user_cache_shares = Counter(
        'multi_user_cache_shares_total',
        'Number of times cache was shared between users',
        ['endpoint_name']
    )

    # ===== API Orchestrator Metrics =====
    api_calls_executed = Counter(
        'api_calls_executed_total',
        'Number of API calls executed',
        ['endpoint_name', 'status']
    )

    api_call_duration = Histogram(
        'api_call_duration_seconds',
        'Duration of API calls',
        ['endpoint_name'],
        buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
    )

    api_call_retries = Counter(
        'api_call_retries_total',
        'Number of API call retries',
        ['endpoint_name']
    )

    api_call_failures = Counter(
        'api_call_failures_total',
        'Number of API call failures',
        ['endpoint_name', 'error_type']
    )

    parallel_execution_count = Counter(
        'parallel_execution_count_total',
        'Number of times parallel execution was used'
    )

    sequential_execution_levels = Histogram(
        'sequential_execution_levels',
        'Number of sequential execution levels in plans',
        buckets=[1, 2, 3, 4, 5]
    )

    # ===== End-to-End Pipeline Metrics =====
    pipeline_requests = Counter(
        'pipeline_requests_total',
        'Total number of pipeline requests',
        ['question_type']
    )

    pipeline_success = Counter(
        'pipeline_success_total',
        'Number of successful pipeline executions',
        ['question_type']
    )

    pipeline_failure = Counter(
        'pipeline_failure_total',
        'Number of failed pipeline executions',
        ['question_type', 'failure_stage']
    )

    pipeline_duration = Histogram(
        'pipeline_duration_seconds',
        'Total pipeline execution time',
        ['question_type'],
        buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0]
    )

    # ===== Component Performance Metrics =====
    component_duration = Histogram(
        'component_duration_seconds',
        'Duration of individual component execution',
        ['component'],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    )

    # ===== LLM Usage Metrics =====
    llm_calls = Counter(
        'llm_calls_total',
        'Number of LLM API calls',
        ['component', 'model']
    )

    llm_tokens_used = Counter(
        'llm_tokens_used_total',
        'Number of LLM tokens used',
        ['component', 'model', 'token_type']
    )

    llm_call_duration = Histogram(
        'llm_call_duration_seconds',
        'Duration of LLM calls',
        ['component'],
        buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0]
    )

    # ===== System Health Metrics =====
    active_sessions = Gauge(
        'active_sessions',
        'Number of active user sessions'
    )

    system_info = Info(
        'autonomous_agents_system',
        'Information about the autonomous agents system'
    )

    # ===== Quality Metrics =====
    user_satisfaction = Counter(
        'user_satisfaction_total',
        'User satisfaction ratings',
        ['rating']
    )

    incorrect_responses = Counter(
        'incorrect_responses_total',
        'Number of incorrect responses (user corrections)',
        ['question_type']
    )


def measure_duration(component_name: str):
    """
    Decorator to measure the duration of a function execution.

    Args:
        component_name: Name of the component being measured

    Returns:
        Decorator function

    Example:
        @measure_duration('question_validator')
        async def validate(self, question):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                Metrics.component_duration.labels(
                    component=component_name
                ).observe(duration)
                logger.info(
                    "component_execution_completed",
                    component=component_name,
                    duration=duration
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                Metrics.component_duration.labels(
                    component=component_name
                ).observe(duration)
                logger.info(
                    "component_execution_completed",
                    component=component_name,
                    duration=duration
                )

        # Return appropriate wrapper based on whether function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_cache_hit_rate(endpoint_name: str, is_hit: bool):
    """
    Track cache hit rate for an endpoint.

    Args:
        endpoint_name: Name of the endpoint
        is_hit: Whether it was a cache hit
    """
    if is_hit:
        Metrics.cache_hits.labels(endpoint_name=endpoint_name).inc()
    else:
        Metrics.cache_misses.labels(endpoint_name=endpoint_name).inc()

    # Calculate and update hit rate
    hits = Metrics.cache_hits.labels(endpoint_name=endpoint_name)._value.get()
    misses = Metrics.cache_misses.labels(endpoint_name=endpoint_name)._value.get()
    total = hits + misses

    if total > 0:
        hit_rate = hits / total
        Metrics.cache_hit_rate.labels(endpoint_name=endpoint_name).set(hit_rate)


def track_llm_usage(component: str, model: str, prompt_tokens: int, completion_tokens: int, duration: float):
    """
    Track LLM usage metrics.

    Args:
        component: Name of the component using the LLM
        model: Model name
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        duration: Duration of the LLM call in seconds
    """
    Metrics.llm_calls.labels(component=component, model=model).inc()
    Metrics.llm_tokens_used.labels(component=component, model=model, token_type='prompt').inc(prompt_tokens)
    Metrics.llm_tokens_used.labels(component=component, model=model, token_type='completion').inc(completion_tokens)
    Metrics.llm_call_duration.labels(component=component).observe(duration)

    logger.info(
        "llm_usage",
        component=component,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        duration=duration
    )


def track_plan_optimization(api_calls_saved: int, enriched_endpoint: str):
    """
    Track API call savings from plan optimization.

    Args:
        api_calls_saved: Number of API calls saved
        enriched_endpoint: Name of the enriched endpoint used
    """
    Metrics.plan_optimization_savings.inc(api_calls_saved)
    Metrics.enriched_endpoints_used.labels(endpoint_name=enriched_endpoint).inc()

    logger.info(
        "plan_optimization",
        api_calls_saved=api_calls_saved,
        enriched_endpoint=enriched_endpoint
    )


def initialize_system_info(version: str, environment: str):
    """
    Initialize system information metrics.

    Args:
        version: System version
        environment: Environment name (dev, staging, prod)
    """
    Metrics.system_info.info({
        'version': version,
        'environment': environment,
        'component': 'autonomous_agents'
    })

    logger.info(
        "system_initialized",
        version=version,
        environment=environment
    )


# Export all metrics and utilities
__all__ = [
    'Metrics',
    'measure_duration',
    'track_cache_hit_rate',
    'track_llm_usage',
    'track_plan_optimization',
    'initialize_system_info',
    'logger'
]
