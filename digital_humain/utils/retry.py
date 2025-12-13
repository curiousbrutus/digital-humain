"""Retry utilities with exponential backoff for transient errors."""

import time
import functools
from typing import Callable, Optional, Tuple, Type, Any
from loguru import logger


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for retry with exponential backoff.
    
    Implements automatic retries with exponentially increasing wait times
    for transient errors. Critical for improving application resilience
    without overwhelming network resources.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation (default 2.0)
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @exponential_backoff(max_retries=3, base_delay=1.0)
        def fetch_data():
            # Function that may fail transiently
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Attempt the operation
                    result = func(*args, **kwargs)
                    
                    # Log successful retry
                    if attempt > 0:
                        logger.info(
                            f"Operation '{func.__name__}' succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                
                except exceptions as e:
                    last_exception = e
                    
                    # If this was the last attempt, raise the exception
                    if attempt == max_retries:
                        logger.error(
                            f"Operation '{func.__name__}' failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    logger.warning(
                        f"Operation '{func.__name__}' failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    
                    time.sleep(delay)
            
            # Should not reach here, but raise last exception if it does
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class RetryManager:
    """
    Manager for retry operations with state tracking.
    
    Useful for non-decorator scenarios and when retry state needs to be tracked.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.attempt_count = 0
        
    def reset(self) -> None:
        """Reset attempt counter."""
        self.attempt_count = 0
        
    def should_retry(self) -> bool:
        """
        Check if should retry.
        
        Returns:
            True if should retry, False otherwise
        """
        return self.attempt_count < self.max_retries
    
    def get_delay(self) -> float:
        """
        Get delay for current attempt.
        
        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.exponential_base ** self.attempt_count),
            self.max_delay
        )
        return delay
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            exceptions: Tuple of exception types to catch and retry
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        self.reset()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.attempt_count = attempt
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1}"
                    )
                
                return result
            
            except exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(
                        f"Operation failed after {self.max_retries} retries: {e}"
                    )
                    raise
                
                delay = self.get_delay()
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {delay:.2f}s: {e}"
                )
                
                time.sleep(delay)
        
        if last_exception:
            raise last_exception


def is_transient_error(exception: Exception) -> bool:
    """
    Determine if an error is transient and can be retried.
    
    Args:
        exception: Exception to check
        
    Returns:
        True if error is transient, False otherwise
    """
    # Check for common transient error patterns
    error_str = str(exception).lower()
    
    transient_patterns = [
        'timeout',
        'connection',
        'network',
        'temporary',
        'unavailable',
        'retry',
        'busy',
        'rate limit'
    ]
    
    return any(pattern in error_str for pattern in transient_patterns)
