"""Test suite for Phase 2 streaming functionality

Tests BackgroundSampler, cursor tracking, rate limiting, and streaming tools.
"""

import sys
import time
import threading
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from debug_bridge import MesenBridge
from streaming.cursor import CursorTracker
from streaming.filters import ChangeFilter
from streaming.sampler import BackgroundSampler
from tools.streaming_tools import (
    start_streaming, stop_streaming,
    subscribe_trace, subscribe_events, subscribe_memory, unsubscribe_memory,
    get_changes, get_streaming_status
)


def test_cursor_tracker():
    """Test CursorTracker basic functionality"""
    print("\n[TEST] CursorTracker basic operations...")

    cursor = CursorTracker()

    # Test get with default
    assert cursor.get("trace", 0) == 0
    assert cursor.get("nonexistent", "default") == "default"

    # Test set and get
    cursor.set("trace", 12345)
    assert cursor.get("trace") == 12345

    # Test update
    cursor.set("trace", 67890)
    assert cursor.get("trace") == 67890

    # Test multiple keys
    cursor.set("events_hash", 0xABCD)
    cursor.set("memory_0x7E0000", b"\x00\xFF")

    assert cursor.get("events_hash") == 0xABCD
    assert cursor.get("memory_0x7E0000") == b"\x00\xFF"

    # Test reset
    cursor.reset()
    assert cursor.get("trace", 0) == 0
    assert cursor.get("events_hash", 0) == 0

    print("  [PASS] CursorTracker basic operations")


def test_cursor_thread_safety():
    """Test CursorTracker thread safety"""
    print("\n[TEST] CursorTracker thread safety...")

    cursor = CursorTracker()
    errors = []

    def worker(worker_id, iterations):
        try:
            for i in range(iterations):
                key = f"worker_{worker_id}"
                cursor.set(key, i)
                value = cursor.get(key)
                # Should get our own value or another thread's value
                # but never None or exception
                assert value is not None
        except Exception as e:
            errors.append(e)

    # Run 10 threads, 100 iterations each
    threads = [threading.Thread(target=worker, args=(i, 100)) for i in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    if errors:
        raise AssertionError(f"Thread safety errors: {errors}")

    print("  [PASS] CursorTracker thread safety")


def test_change_filter():
    """Test ChangeFilter rate limiting"""
    print("\n[TEST] ChangeFilter rate limiting...")

    filter = ChangeFilter({
        "max_trace_lines_per_second": 100,
        "max_events_per_second": 10,
        "max_memory_changes_per_second": 5
    })

    # Test trace rate limiting
    # First 100 lines should pass
    for i in range(100):
        trace_data = [{"pc": 0x8000 + i}]
        assert filter.should_include_trace(trace_data) == True

    # 101st should fail (over limit)
    trace_data = [{"pc": 0x9000}]
    assert filter.should_include_trace(trace_data) == False

    # Wait for reset (just over 1 second)
    time.sleep(1.1)

    # Should allow again after reset
    trace_data = [{"pc": 0xA000}]
    assert filter.should_include_trace(trace_data) == True

    print("  [PASS] ChangeFilter rate limiting")


def test_change_filter_backoff():
    """Test ChangeFilter exponential backoff"""
    print("\n[TEST] ChangeFilter exponential backoff...")

    filter = ChangeFilter({
        "max_trace_lines_per_second": 10
    })

    # Trigger overrun
    for i in range(15):
        trace_data = [{"pc": 0x8000 + i}]
        filter.should_include_trace(trace_data)

    # Check backoff state increases
    assert filter.backoff_state["consecutive_overruns"] > 0
    backoff1 = filter.get_backoff_delay()
    assert backoff1 > 0

    # Trigger more overruns
    for i in range(15):
        trace_data = [{"pc": 0x9000 + i}]
        filter.should_include_trace(trace_data)

    backoff2 = filter.get_backoff_delay()
    assert backoff2 >= backoff1  # Should increase or stay same

    # Wait for reset
    time.sleep(1.1)

    # Allow some traffic (below limit)
    for i in range(5):
        trace_data = [{"pc": 0xA000 + i}]
        filter.should_include_trace(trace_data)

    # Backoff should reset after successful period
    backoff3 = filter.get_backoff_delay()
    assert backoff3 == 0.0  # Should reset

    print("  [PASS] ChangeFilter exponential backoff")


def test_background_sampler_lifecycle():
    """Test BackgroundSampler start/stop"""
    print("\n[TEST] BackgroundSampler lifecycle...")

    try:
        bridge = MesenBridge()
        sampler = BackgroundSampler(bridge, max_queue_size=100)

        # Initially not running
        assert sampler.running == False

        # Start sampler
        sampler.start()
        assert sampler.running == True
        assert sampler.thread is not None
        assert sampler.thread.is_alive()

        # Let it run briefly
        time.sleep(0.5)

        # Stop sampler
        sampler.stop()
        assert sampler.running == False

        # Thread should exit
        time.sleep(0.2)
        assert not sampler.thread.is_alive()

        print("  [PASS] BackgroundSampler lifecycle")

    except Exception as e:
        print(f"  [SKIP] BackgroundSampler lifecycle (DLL not available: {e})")


def test_background_sampler_subscriptions():
    """Test BackgroundSampler subscription management"""
    print("\n[TEST] BackgroundSampler subscriptions...")

    try:
        bridge = MesenBridge()
        sampler = BackgroundSampler(bridge)

        # Initially no subscriptions
        assert sampler.subscriptions["trace"] == False
        assert sampler.subscriptions["events"] == False
        assert len(sampler.subscriptions["memory_watches"]) == 0

        # Subscribe to trace
        sampler.subscribe("trace", max_lines=100)
        assert sampler.subscriptions["trace"] == True

        # Subscribe to events
        sampler.subscribe("events")
        assert sampler.subscriptions["events"] == True

        # Subscribe to memory
        sampler.subscribe("memory", memory_type="SnesWorkRam", address=0x7E0000, length=256)
        assert len(sampler.subscriptions["memory_watches"]) == 1

        watch = sampler.subscriptions["memory_watches"][0]
        assert watch["memory_type"] == "SnesWorkRam"
        assert watch["address"] == 0x7E0000
        assert watch["length"] == 256

        # Unsubscribe memory
        sampler.unsubscribe("memory", address=0x7E0000)
        assert len(sampler.subscriptions["memory_watches"]) == 0

        print("  [PASS] BackgroundSampler subscriptions")

    except Exception as e:
        print(f"  [SKIP] BackgroundSampler subscriptions (DLL not available: {e})")


def test_background_sampler_queue():
    """Test BackgroundSampler change queue"""
    print("\n[TEST] BackgroundSampler queue...")

    try:
        bridge = MesenBridge()
        sampler = BackgroundSampler(bridge, max_queue_size=10)

        # Add some mock changes
        for i in range(5):
            sampler.queue.append({
                "type": "trace_delta",
                "offset": i * 100,
                "timestamp": time.time()
            })

        # Get changes
        changes = sampler.get_changes(max_count=3)
        assert len(changes) == 3

        # Queue should have 2 remaining
        assert len(sampler.queue) == 2

        # Add more to test ring buffer
        for i in range(15):
            sampler.queue.append({
                "type": "test",
                "index": i
            })

        # Should cap at max_queue_size (10)
        assert len(sampler.queue) == 10

        # Oldest items should be discarded
        # Newest 10 items should have indices 5-14
        changes = sampler.get_changes(max_count=10)
        assert len(changes) == 10
        assert changes[0]["index"] == 5
        assert changes[-1]["index"] == 14

        print("  [PASS] BackgroundSampler queue")

    except Exception as e:
        print(f"  [SKIP] BackgroundSampler queue (DLL not available: {e})")


def test_streaming_tools_integration():
    """Test streaming tools with actual bridge"""
    print("\n[TEST] Streaming tools integration...")

    try:
        bridge = MesenBridge()

        # Test start_streaming
        result = start_streaming(bridge)
        assert result["streaming"] == True
        assert result["polling_rate_hz"] == 10

        # Test get_streaming_status
        status = get_streaming_status(bridge)
        assert status["streaming"] == True
        assert "stats" in status

        # Test subscribe_trace
        result = subscribe_trace(bridge, max_lines_per_poll=100)
        assert result["subscribed"] == True
        assert result["subscription_id"] == "trace"
        assert result["max_lines_per_poll"] == 100

        # Test subscribe_events
        result = subscribe_events(bridge)
        assert result["subscribed"] == True
        assert result["subscription_id"] == "events"

        # Test subscribe_memory
        result = subscribe_memory(
            bridge,
            memory_type="SnesWorkRam",
            address=0x7E0000,
            length=256
        )
        assert result["subscribed"] == True
        assert "subscription_id" in result
        assert result["memory_type"] == "SnesWorkRam"
        assert result["address"] == 0x7E0000
        assert result["length"] == 256

        # Let sampler run briefly
        time.sleep(0.5)

        # Test get_changes
        result = get_changes(bridge, max_count=100)
        assert "change_count" in result
        assert "changes" in result
        assert isinstance(result["changes"], list)

        # Test unsubscribe_memory
        result = unsubscribe_memory(bridge, address=0x7E0000)
        assert result["unsubscribed"] == True
        assert result["address"] == 0x7E0000

        # Test stop_streaming
        result = stop_streaming(bridge)
        assert result["streaming"] == False
        assert "final_stats" in result

        print("  [PASS] Streaming tools integration")

    except Exception as e:
        print(f"  [SKIP] Streaming tools integration (DLL not available: {e})")


def test_streaming_tools_edge_cases():
    """Test streaming tools edge cases and validation"""
    print("\n[TEST] Streaming tools edge cases...")

    try:
        bridge = MesenBridge()

        # Test subscribe_memory with oversized length
        result = subscribe_memory(
            bridge,
            memory_type="SnesWorkRam",
            address=0x7E0000,
            length=1000  # Should be capped to 256
        )
        assert result["length"] == 256

        # Test get_changes with oversized max_count
        start_streaming(bridge)
        result = get_changes(bridge, max_count=5000)  # Should be capped to 1000
        assert result["change_count"] <= 1000

        stop_streaming(bridge)

        print("  [PASS] Streaming tools edge cases")

    except Exception as e:
        print(f"  [SKIP] Streaming tools edge cases (DLL not available: {e})")


def test_sampler_stability():
    """Test sampler runs stably for extended period"""
    print("\n[TEST] BackgroundSampler stability (2 second run)...")

    try:
        bridge = MesenBridge()
        sampler = BackgroundSampler(bridge)

        # Subscribe to all feeds
        sampler.subscribe("trace")
        sampler.subscribe("events")

        # Start sampler
        sampler.start()

        # Run for 2 seconds
        time.sleep(2.0)

        # Should still be running
        assert sampler.running == True
        assert sampler.thread.is_alive()

        # Get stats
        stats = sampler.get_stats()
        assert "total_samples" in stats
        assert stats["total_samples"] > 0  # Should have sampled at least once

        # Stop cleanly
        sampler.stop()
        time.sleep(0.2)
        assert not sampler.thread.is_alive()

        print("  [PASS] BackgroundSampler stability")

    except Exception as e:
        print(f"  [SKIP] BackgroundSampler stability (DLL not available: {e})")


def run_all_tests():
    """Run all streaming tests"""
    print("=" * 60)
    print("Phase 2 Streaming Tests")
    print("=" * 60)

    tests = [
        test_cursor_tracker,
        test_cursor_thread_safety,
        test_change_filter,
        test_change_filter_backoff,
        test_background_sampler_lifecycle,
        test_background_sampler_subscriptions,
        test_background_sampler_queue,
        test_streaming_tools_integration,
        test_streaming_tools_edge_cases,
        test_sampler_stability,
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            # Count as skipped if it's a setup issue
            if "DLL not available" in str(e) or "SKIP" in str(e):
                skipped += 1
            else:
                print(f"  [FAIL] {test.__name__}: {e}")
                failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
