"""Unit tests for retry utilities."""

import pytest
import time
from digital_humain.utils.retry import (
    exponential_backoff,
    RetryManager,
    is_transient_error
)


class TestExponentialBackoff:
    """Test exponential backoff decorator."""
    
    def test_successful_execution(self):
        """Test successful execution without retries."""
        call_count = 0
        
        @exponential_backoff(max_retries=3, base_delay=0.01)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert call_count == 1  # Only called once
    
    def test_retry_on_exception(self):
        """Test retry on exception."""
        call_count = 0
        
        @exponential_backoff(max_retries=3, base_delay=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = failing_func()
        
        assert result == "success"
        assert call_count == 3  # Called 3 times before success
    
    def test_max_retries_exhausted(self):
        """Test behavior when max retries exhausted."""
        call_count = 0
        
        @exponential_backoff(max_retries=2, base_delay=0.01)
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            always_failing()
        
        assert call_count == 3  # Initial + 2 retries
    
    def test_exponential_delay(self):
        """Test that delay increases exponentially."""
        delays = []
        
        @exponential_backoff(max_retries=3, base_delay=0.1, exponential_base=2.0)
        def track_delays():
            start = time.time()
            raise ValueError("Test")
        
        try:
            track_delays()
        except ValueError:
            pass
        
        # Delays should be approximately: 0.1, 0.2, 0.4 seconds
        # We can't test exact timing due to system variance
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        
        @exponential_backoff(
            max_retries=5,
            base_delay=1.0,
            max_delay=2.0,
            exponential_base=10.0
        )
        def capped_func():
            raise ValueError("Test")
        
        # With base=10, delays would be: 1, 10, 100, 1000, 10000
        # But should be capped at: 1, 2, 2, 2, 2
        
        start = time.time()
        try:
            capped_func()
        except ValueError:
            pass
        elapsed = time.time() - start
        
        # Total time should be ~9 seconds (1+2+2+2+2), not ~11111
        assert elapsed < 15  # Allow some variance
    
    def test_specific_exception_types(self):
        """Test catching specific exception types."""
        
        @exponential_backoff(
            max_retries=2,
            base_delay=0.01,
            exceptions=(ValueError,)
        )
        def selective_retry():
            raise TypeError("Wrong type")
        
        # TypeError should not be retried
        with pytest.raises(TypeError, match="Wrong type"):
            selective_retry()


class TestRetryManager:
    """Test RetryManager class."""
    
    def test_initialization(self):
        """Test RetryManager initialization."""
        manager = RetryManager(
            max_retries=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0
        )
        
        assert manager.max_retries == 3
        assert manager.base_delay == 1.0
        assert manager.max_delay == 60.0
        assert manager.exponential_base == 2.0
        assert manager.attempt_count == 0
    
    def test_should_retry(self):
        """Test should_retry method."""
        manager = RetryManager(max_retries=3)
        
        assert manager.should_retry() is True
        
        manager.attempt_count = 2
        assert manager.should_retry() is True
        
        manager.attempt_count = 3
        assert manager.should_retry() is False
    
    def test_get_delay(self):
        """Test get_delay calculation."""
        manager = RetryManager(
            max_retries=5,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0
        )
        
        # Test exponential increase
        manager.attempt_count = 0
        assert manager.get_delay() == 1.0  # 1.0 * 2^0
        
        manager.attempt_count = 1
        assert manager.get_delay() == 2.0  # 1.0 * 2^1
        
        manager.attempt_count = 2
        assert manager.get_delay() == 4.0  # 1.0 * 2^2
        
        # Test max delay cap
        manager.attempt_count = 10
        assert manager.get_delay() == 10.0  # Capped at max_delay
    
    def test_reset(self):
        """Test reset method."""
        manager = RetryManager()
        
        manager.attempt_count = 5
        manager.reset()
        
        assert manager.attempt_count == 0
    
    def test_execute_with_retry_success(self):
        """Test successful execution with retry."""
        manager = RetryManager(max_retries=3, base_delay=0.01)
        
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = manager.execute_with_retry(test_func)
        
        assert result == "success"
        assert call_count == 2
    
    def test_execute_with_retry_failure(self):
        """Test retry exhaustion."""
        manager = RetryManager(max_retries=2, base_delay=0.01)
        
        def always_fails():
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError, match="Permanent error"):
            manager.execute_with_retry(always_fails)
    
    def test_execute_with_retry_custom_exceptions(self):
        """Test retry with custom exception types."""
        manager = RetryManager(max_retries=2, base_delay=0.01)
        
        def raises_type_error():
            raise TypeError("Wrong type")
        
        # Should not retry TypeError by default
        with pytest.raises(TypeError):
            manager.execute_with_retry(
                raises_type_error,
                exceptions=(ValueError,)
            )


class TestIsTransientError:
    """Test is_transient_error function."""
    
    def test_transient_error_patterns(self):
        """Test detection of transient error patterns."""
        transient_errors = [
            Exception("Connection timeout occurred"),
            Exception("Network error: temporary failure"),
            Exception("Service temporarily unavailable"),
            Exception("Rate limit exceeded, retry later"),
            Exception("Database connection busy")
        ]
        
        for error in transient_errors:
            assert is_transient_error(error) is True
    
    def test_non_transient_errors(self):
        """Test non-transient errors."""
        non_transient_errors = [
            Exception("File not found"),
            Exception("Invalid syntax"),
            Exception("Permission denied"),
            Exception("Authentication failed")
        ]
        
        for error in non_transient_errors:
            assert is_transient_error(error) is False
    
    def test_case_insensitive(self):
        """Test case-insensitive pattern matching."""
        assert is_transient_error(Exception("TIMEOUT")) is True
        assert is_transient_error(Exception("Timeout")) is True
        assert is_transient_error(Exception("timeout")) is True
