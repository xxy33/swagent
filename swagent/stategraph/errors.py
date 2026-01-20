"""
Error handling and retry mechanisms for StateGraph workflow engine.
"""
from dataclasses import dataclass, field
from typing import (
    Dict, Any, Optional, Callable, Awaitable, Union, List, Type,
    TypeVar, Generic
)
from enum import Enum
import asyncio
import functools
import traceback
from datetime import datetime


class StateGraphError(Exception):
    """Base exception for all StateGraph errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class NodeExecutionError(StateGraphError):
    """Error during node execution."""

    def __init__(
        self,
        message: str,
        node_name: str,
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.node_name = node_name
        self.original_error = original_error
        self.traceback = traceback.format_exc() if original_error else None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "node_name": self.node_name,
            "original_error": str(self.original_error) if self.original_error else None,
            "traceback": self.traceback
        })
        return data


class RetryExhaustedError(StateGraphError):
    """All retry attempts have been exhausted."""

    def __init__(
        self,
        message: str,
        node_name: str,
        attempts: int,
        last_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.node_name = node_name
        self.attempts = attempts
        self.last_error = last_error

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "node_name": self.node_name,
            "attempts": self.attempts,
            "last_error": str(self.last_error) if self.last_error else None
        })
        return data


class GraphValidationError(StateGraphError):
    """Error during graph validation."""

    def __init__(
        self,
        message: str,
        validation_errors: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.validation_errors = validation_errors

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["validation_errors"] = self.validation_errors
        return data


class GraphExecutionError(StateGraphError):
    """Error during graph execution."""

    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        current_node: Optional[str] = None,
        iteration: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.execution_id = execution_id
        self.current_node = current_node
        self.iteration = iteration

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "execution_id": self.execution_id,
            "current_node": self.current_node,
            "iteration": self.iteration
        })
        return data


class TimeoutError(StateGraphError):
    """Execution timed out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        node_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.timeout_seconds = timeout_seconds
        self.node_name = node_name


class MaxIterationsError(StateGraphError):
    """Maximum iterations exceeded."""

    def __init__(
        self,
        message: str,
        max_iterations: int,
        actual_iterations: int,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.max_iterations = max_iterations
        self.actual_iterations = actual_iterations


class BackoffStrategy(Enum):
    """Backoff strategies for retry delays."""
    CONSTANT = "constant"      # Same delay each retry
    LINEAR = "linear"          # Delay increases linearly
    EXPONENTIAL = "exponential"  # Delay doubles each retry
    FIBONACCI = "fibonacci"    # Delay follows fibonacci sequence


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (0 = no retry)
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        backoff_strategy: Strategy for increasing delay
        backoff_multiplier: Multiplier for backoff calculation
        retry_on: Exception types to retry on (None = all)
        ignore_on: Exception types to not retry on
        jitter: Add randomness to delay (0.0 to 1.0)
    """
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    retry_on: Optional[List[Type[Exception]]] = None
    ignore_on: Optional[List[Type[Exception]]] = None
    jitter: float = 0.0

    def should_retry(self, error: Exception) -> bool:
        """Check if the error should trigger a retry."""
        # Check ignore list first
        if self.ignore_on:
            for exc_type in self.ignore_on:
                if isinstance(error, exc_type):
                    return False

        # Check retry list
        if self.retry_on:
            for exc_type in self.retry_on:
                if isinstance(error, exc_type):
                    return True
            return False

        # Default: retry all
        return True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        import random

        if attempt <= 0:
            return 0

        if self.backoff_strategy == BackoffStrategy.CONSTANT:
            delay = self.initial_delay

        elif self.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.initial_delay * attempt

        elif self.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))

        elif self.backoff_strategy == BackoffStrategy.FIBONACCI:
            # Calculate fibonacci-like sequence
            a, b = self.initial_delay, self.initial_delay
            for _ in range(attempt - 1):
                a, b = b, a + b
            delay = a

        else:
            delay = self.initial_delay

        # Apply jitter
        if self.jitter > 0:
            jitter_range = delay * self.jitter
            delay += random.uniform(-jitter_range, jitter_range)

        # Clamp to max
        return min(delay, self.max_delay)


@dataclass
class RetryState:
    """Tracks retry state for a single operation."""
    attempt: int = 0
    errors: List[Exception] = field(default_factory=list)
    start_time: Optional[datetime] = None
    last_attempt_time: Optional[datetime] = None

    def record_attempt(self, error: Optional[Exception] = None):
        """Record an attempt."""
        self.attempt += 1
        self.last_attempt_time = datetime.now()
        if self.start_time is None:
            self.start_time = self.last_attempt_time
        if error:
            self.errors.append(error)


class RetryHandler:
    """
    Handles retry logic for operations.

    Usage:
        handler = RetryHandler(config)
        result = await handler.execute(my_async_func, arg1, arg2)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    async def execute(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retries fail
        """
        state = RetryState()
        last_error: Optional[Exception] = None

        while state.attempt < self.config.max_attempts + 1:
            state.attempt += 1
            if state.start_time is None:
                state.start_time = datetime.now()
            state.last_attempt_time = datetime.now()

            try:
                return await func(*args, **kwargs)

            except Exception as e:
                last_error = e
                state.errors.append(e)

                # Check if we should retry
                if not self.config.should_retry(e):
                    raise

                # Check if more attempts available
                if state.attempt >= self.config.max_attempts + 1:
                    raise RetryExhaustedError(
                        message=f"All {self.config.max_attempts} retry attempts exhausted",
                        node_name=getattr(func, '__name__', 'unknown'),
                        attempts=state.attempt,
                        last_error=e
                    )

                # Wait before retry
                delay = self.config.get_delay(state.attempt)
                await asyncio.sleep(delay)

        # Should not reach here, but just in case
        raise RetryExhaustedError(
            message="Retry loop ended unexpectedly",
            node_name=getattr(func, '__name__', 'unknown'),
            attempts=state.attempt,
            last_error=last_error
        )


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    retry_on: Optional[List[Type[Exception]]] = None
) -> Callable:
    """
    Decorator to add retry logic to an async function.

    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        backoff_strategy: Backoff strategy
        retry_on: Exception types to retry on

    Returns:
        Decorated function

    Example:
        @with_retry(max_attempts=3, initial_delay=1.0)
        async def unreliable_operation():
            # ... may fail
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        backoff_strategy=backoff_strategy,
        retry_on=retry_on
    )
    handler = RetryHandler(config)

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await handler.execute(func, *args, **kwargs)
        return wrapper

    return decorator


@dataclass
class ErrorContext:
    """Context information for error handling."""
    node_name: Optional[str] = None
    execution_id: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    iteration: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorHandler:
    """
    Global error handler for workflow execution.

    Allows registering custom handlers for different error types.
    """

    def __init__(self):
        self._handlers: Dict[Type[Exception], Callable] = {}
        self._fallback_handler: Optional[Callable] = None
        self._error_log: List[Dict[str, Any]] = []

    def register(
        self,
        error_type: Type[Exception],
        handler: Callable[[Exception, ErrorContext], Awaitable[None]]
    ) -> None:
        """
        Register a handler for a specific error type.

        Args:
            error_type: Exception class to handle
            handler: Async function to call on error
        """
        self._handlers[error_type] = handler

    def set_fallback(
        self,
        handler: Callable[[Exception, ErrorContext], Awaitable[None]]
    ) -> None:
        """
        Set fallback handler for unregistered error types.

        Args:
            handler: Async function to call
        """
        self._fallback_handler = handler

    async def handle(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None
    ) -> bool:
        """
        Handle an error.

        Args:
            error: The exception
            context: Error context

        Returns:
            True if error was handled, False otherwise
        """
        ctx = context or ErrorContext()

        # Log the error
        self._error_log.append({
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "message": str(error),
            "node_name": ctx.node_name,
            "execution_id": ctx.execution_id
        })

        # Find appropriate handler
        for error_type, handler in self._handlers.items():
            if isinstance(error, error_type):
                await handler(error, ctx)
                return True

        # Use fallback handler
        if self._fallback_handler:
            await self._fallback_handler(error, ctx)
            return True

        return False

    def get_error_log(self) -> List[Dict[str, Any]]:
        """Get the error log."""
        return list(self._error_log)

    def clear_error_log(self) -> None:
        """Clear the error log."""
        self._error_log.clear()


# Convenience function for creating retry configs
def retry_config(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff: str = "exponential",
    jitter: float = 0.0
) -> RetryConfig:
    """
    Create a retry configuration with sensible defaults.

    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff: Backoff strategy ("constant", "linear", "exponential", "fibonacci")
        jitter: Jitter factor (0.0 to 1.0)

    Returns:
        RetryConfig instance
    """
    strategy_map = {
        "constant": BackoffStrategy.CONSTANT,
        "linear": BackoffStrategy.LINEAR,
        "exponential": BackoffStrategy.EXPONENTIAL,
        "fibonacci": BackoffStrategy.FIBONACCI
    }

    return RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_strategy=strategy_map.get(backoff, BackoffStrategy.EXPONENTIAL),
        jitter=jitter
    )
