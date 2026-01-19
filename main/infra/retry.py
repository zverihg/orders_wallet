"""
Retry utilities with exponential backoff and jitter.
"""
import random
import time
from functools import wraps
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff and jitter.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delay
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Last attempt failed, raise exception
                        raise
                    
                    # Calculate delay with exponential backoff
                    if jitter:
                        # Add random jitter (0 to 25% of delay)
                        jitter_amount = delay * 0.25 * random.random()
                        actual_delay = delay + jitter_amount
                    else:
                        actual_delay = delay
                    
                    # Cap at max_delay
                    actual_delay = min(actual_delay, max_delay)
                    
                    # Wait before retry
                    time.sleep(actual_delay)
                    
                    # Increase delay for next attempt
                    delay *= exponential_base
            
            # Should not reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator

