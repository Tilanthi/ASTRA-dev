# astra_core/tests/test_thread_safe_timeout.py
import pytest
import time
from astra_core.core.thread_safe_timeout import call_with_timeout

def test_timeout_protection():
    """Test that timeout protection works correctly"""
    def slow_function():
        time.sleep(5)
        return "should not complete"

    with pytest.raises(TimeoutError):
        call_with_timeout(slow_function, timeout_seconds=1)

def test_successful_call():
    """Test that successful calls work correctly"""
    def fast_function():
        return "success"

    result = call_with_timeout(fast_function, timeout_seconds=5)
    assert result == "success"

def test_thread_safety():
    """Test that timeout works from worker threads"""
    import threading

    results = []
    def worker():
        try:
            result = call_with_timeout(lambda: time.sleep(10), timeout_seconds=1)
            results.append("no_timeout")
        except TimeoutError:
            results.append("timeout")

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    assert results == ["timeout"], "Timeout should work from worker thread"
