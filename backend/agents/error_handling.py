"""
Unified error handling strategies for all agents.

This module provides a consistent approach to error handling,
retries, fallbacks, and degraded mode across the pipeline.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Awaitable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Minor issue, can continue normally
    MEDIUM = "medium"     # Issue that affects quality but not functionality
    HIGH = "high"         # Critical issue, need fallback
    FATAL = "fatal"       # Unrecoverable, must stop


@dataclass
class ErrorContext:
    """Context information about an error."""
    component: str
    operation: str
    error: Exception
    severity: ErrorSeverity
    attempt: int = 1
    max_attempts: int = 3
    metadata: Dict[str, Any] = None


class ErrorHandlingStrategy:
    """
    Base class for error handling strategies.

    Implements Chain of Responsibility pattern:
    1. Retry with exponential backoff
    2. Fallback to alternative method
    3. Degraded mode (partial results)
    4. Error message to user
    """

    def __init__(
        self,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        enable_fallback: bool = True,
        enable_degraded_mode: bool = True,
    ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.enable_fallback = enable_fallback
        self.enable_degraded_mode = enable_degraded_mode

    async def handle_error(
        self,
        context: ErrorContext,
        operation: Callable[[], Awaitable[T]],
        fallback: Optional[Callable[[], Awaitable[T]]] = None,
    ) -> T:
        """
        Handle an error using the strategy chain.

        Args:
            context: Error context information
            operation: The operation to retry
            fallback: Optional fallback operation

        Returns:
            Result from operation, fallback, or degraded mode
        """
        # Step 1: Retry with backoff
        if context.attempt <= self.max_retries:
            logger.info(
                f"Retrying {context.component}.{context.operation} "
                f"(attempt {context.attempt}/{self.max_retries})"
            )
            delay = self._calculate_delay(context.attempt)
            await asyncio.sleep(delay)

            try:
                return await operation()
            except Exception as retry_error:
                logger.warning(
                    f"Retry {context.attempt} failed for {context.component}.{context.operation}: {retry_error}"
                )
                context.error = retry_error
                context.attempt += 1

                # Retry again if we haven't exceeded max_retries
                if context.attempt <= self.max_retries:
                    return await self.handle_error(context, operation, fallback)

        # Step 2: Try fallback
        if self.enable_fallback and fallback:
            logger.info(f"Attempting fallback for {context.component}.{context.operation}")
            try:
                return await fallback()
            except Exception as fallback_error:
                logger.warning(f"Fallback failed: {fallback_error}")
                context.error = fallback_error

        # Step 3: Degraded mode
        if self.enable_degraded_mode:
            logger.info(f"Entering degraded mode for {context.component}.{context.operation}")
            return self._degraded_mode_response(context)

        # Step 4: Raise error (no recovery possible)
        logger.error(
            f"All recovery attempts failed for {context.component}.{context.operation}",
            exc_info=context.error
        )
        raise context.error

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with optional exponential backoff."""
        if self.exponential_backoff:
            return self.retry_delay * (2 ** (attempt - 1))
        return self.retry_delay

    def _degraded_mode_response(self, context: ErrorContext) -> Any:
        """
        Provide degraded mode response.
        Override in subclasses for component-specific behavior.
        """
        raise NotImplementedError("Subclasses must implement degraded mode")


class IntentErrorStrategy(ErrorHandlingStrategy):
    """Error handling strategy for Intent Agent."""

    def __init__(self, **kwargs):
        super().__init__(
            max_retries=1,  # Intent detection is fast, only retry once
            retry_delay=0.5,
            **kwargs
        )

    def _degraded_mode_response(self, context: ErrorContext):
        """Return generic info intent as fallback."""
        from backend.agents.types import IntentResult

        logger.warning(f"Intent detection failed, falling back to info_generale")
        return IntentResult(
            intent="info_generale",
            entities={},
            needs_data=False,
            confidence=0.0,
            reasoning="Fallback due to error in intent detection"
        )


class ToolErrorStrategy(ErrorHandlingStrategy):
    """Error handling strategy for Tool Agent."""

    def __init__(self, **kwargs):
        super().__init__(
            max_retries=2,  # API calls can be flaky
            retry_delay=1.0,
            exponential_backoff=True,
            **kwargs
        )

    def _degraded_mode_response(self, context: ErrorContext):
        """Return error payload for tool execution."""
        from backend.agents.types import ToolCallResult

        return ToolCallResult(
            name=context.metadata.get("tool_name", "unknown"),
            arguments=context.metadata.get("arguments", {}),
            output={"error": str(context.error)},
            error=str(context.error)
        )


class AnalysisErrorStrategy(ErrorHandlingStrategy):
    """Error handling strategy for Analysis Agent."""

    def __init__(self, **kwargs):
        super().__init__(
            max_retries=1,  # Analysis is expensive, only retry once
            retry_delay=1.0,
            **kwargs
        )

    def _degraded_mode_response(self, context: ErrorContext):
        """Return minimal analysis result."""
        from backend.agents.types import AnalysisResult

        logger.warning("Analysis failed, returning minimal result")
        return AnalysisResult(
            brief="Analyse limitée en raison d'une erreur technique.",
            data_points=[
                "Les données ont été collectées mais l'analyse complète n'a pas pu être générée.",
                f"Erreur: {str(context.error)}"
            ],
            gaps=["analyse_complete"],
            safety_notes=["Résultat partiel - certaines informations peuvent manquer"]
        )


class ResponseErrorStrategy(ErrorHandlingStrategy):
    """Error handling strategy for Response Agent."""

    def __init__(self, **kwargs):
        super().__init__(
            max_retries=1,
            retry_delay=1.0,
            enable_degraded_mode=True,
            **kwargs
        )

    def _degraded_mode_response(self, context: ErrorContext):
        """Return error message in appropriate language."""
        language = context.metadata.get("language", "fr")

        if language == "fr":
            return (
                "❌ Une erreur technique est survenue lors de la génération de la réponse. "
                "Les données ont été collectées mais je n'ai pas pu les synthétiser correctement. "
                "Merci de réessayer ou de reformuler votre question."
            )
        else:
            return (
                "❌ A technical error occurred while generating the response. "
                "Data was collected but I couldn't synthesize it properly. "
                "Please try again or rephrase your question."
            )


class CausalErrorStrategy(ErrorHandlingStrategy):
    """Error handling strategy for Causal Agent."""

    def __init__(self, **kwargs):
        super().__init__(
            max_retries=0,  # Causal is optional, don't retry
            enable_fallback=False,
            enable_degraded_mode=True,
            **kwargs
        )

    def _degraded_mode_response(self, context: ErrorContext):
        """Return None to skip causal analysis."""
        logger.info("Causal analysis failed, skipping (optional component)")
        return None


# Factory function to get appropriate strategy
def get_error_strategy(component: str) -> ErrorHandlingStrategy:
    """
    Get the appropriate error handling strategy for a component.

    Args:
        component: Component name ('intent', 'tool', 'analysis', 'response', 'causal')

    Returns:
        Error handling strategy instance
    """
    strategies = {
        "intent": IntentErrorStrategy,
        "tool": ToolErrorStrategy,
        "analysis": AnalysisErrorStrategy,
        "response": ResponseErrorStrategy,
        "causal": CausalErrorStrategy,
    }

    strategy_class = strategies.get(component, ErrorHandlingStrategy)
    return strategy_class()


# Decorator for automatic error handling
def with_error_handling(component: str):
    """
    Decorator to automatically apply error handling to async functions.

    Usage:
        @with_error_handling("intent")
        async def detect_intent(self, message):
            # Implementation
            pass
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs) -> T:
            strategy = get_error_strategy(component)
            operation_name = func.__name__

            async def operation():
                return await func(*args, **kwargs)

            try:
                return await operation()
            except Exception as error:
                context = ErrorContext(
                    component=component,
                    operation=operation_name,
                    error=error,
                    severity=ErrorSeverity.HIGH,
                    metadata=kwargs
                )
                return await strategy.handle_error(context, operation)

        return wrapper
    return decorator
