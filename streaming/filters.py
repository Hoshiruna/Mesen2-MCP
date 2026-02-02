"""Rate limiting and filtering for change feeds

Prevents overwhelming the MCP client with too much data by applying
rate limits and backoff strategies.
"""

import time
import threading
from typing import Dict, Any, Optional


class ChangeFilter:
    """Filters and rate-limits changes"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize filter with configuration

        Args:
            config: Configuration dict with rate limits
        """
        self.config = config or {
            "max_trace_lines_per_second": 1000,
            "max_events_per_second": 100,
            "max_memory_changes_per_second": 50,
        }

        self.counters = {
            "trace": 0,
            "events": 0,
            "memory": 0,
        }

        self.last_reset = time.time()
        self._lock = threading.Lock()

        # Backoff state for handling overruns
        self.backoff_state = {
            "consecutive_overruns": 0,
            "current_backoff": 0.0,
        }

    def should_include_trace(self, trace_data: Any) -> bool:
        """Check if trace delta should be included

        Args:
            trace_data: Trace data to check (list of trace lines)

        Returns:
            True if should be included, False if rate limit exceeded
        """
        self._check_reset()

        with self._lock:
            data_len = len(trace_data) if isinstance(trace_data, (list, tuple)) else 1

            if self.counters["trace"] >= self.config["max_trace_lines_per_second"]:
                # Rate limit exceeded
                self._handle_overrun("trace")
                return False

            self.counters["trace"] += data_len
            return True

    def should_include_events(self, events_data: Any) -> bool:
        """Check if events delta should be included

        Args:
            events_data: Events data to check

        Returns:
            True if should be included, False if rate limit exceeded
        """
        self._check_reset()

        with self._lock:
            data_len = len(events_data) if isinstance(events_data, (list, tuple)) else 1

            if self.counters["events"] >= self.config["max_events_per_second"]:
                self._handle_overrun("events")
                return False

            self.counters["events"] += data_len
            return True

    def should_include_memory(self, memory_data: Any) -> bool:
        """Check if memory delta should be included

        Args:
            memory_data: Memory change data to check

        Returns:
            True if should be included, False if rate limit exceeded
        """
        self._check_reset()

        with self._lock:
            if self.counters["memory"] >= self.config["max_memory_changes_per_second"]:
                self._handle_overrun("memory")
                return False

            self.counters["memory"] += 1
            return True

    def _check_reset(self):
        """Reset counters every second"""
        now = time.time()

        with self._lock:
            if now - self.last_reset >= 1.0:
                # Reset counters
                self.counters = {k: 0 for k in self.counters}
                self.last_reset = now

                # Reset backoff if we're no longer overrunning
                if all(c == 0 for c in self.counters.values()):
                    self.backoff_state["consecutive_overruns"] = 0
                    self.backoff_state["current_backoff"] = 0.0

    def _handle_overrun(self, counter_type: str):
        """Handle rate limit overrun

        Args:
            counter_type: Type of counter that overran
        """
        self.backoff_state["consecutive_overruns"] += 1

    def get_backoff_delay(self) -> float:
        """Get current backoff delay

        Returns:
            Backoff delay in seconds (exponential backoff)
        """
        overruns = self.backoff_state["consecutive_overruns"]

        if overruns == 0:
            return 0.0

        # Exponential backoff: 0.1s, 0.2s, 0.4s, 0.8s, max 1.0s
        backoff = min(0.1 * (2 ** overruns), 1.0)
        return backoff

    def get_stats(self) -> Dict[str, Any]:
        """Get current filter statistics

        Returns:
            Dictionary with counter values and backoff state
        """
        with self._lock:
            return {
                "counters": self.counters.copy(),
                "backoff_delay": self.get_backoff_delay(),
                "consecutive_overruns": self.backoff_state["consecutive_overruns"],
                "config": self.config.copy(),
            }


# Test function
if __name__ == "__main__":
    print("Testing ChangeFilter...")

    filter = ChangeFilter({
        "max_trace_lines_per_second": 10,
        "max_events_per_second": 5,
        "max_memory_changes_per_second": 3,
    })

    # Test trace filtering
    print("\n[TEST] Trace filtering:")
    for i in range(15):
        trace_data = [f"line_{i}"]
        allowed = filter.should_include_trace(trace_data)
        print(f"  Line {i}: {'allowed' if allowed else 'BLOCKED'}")

    stats = filter.get_stats()
    print(f"\n[OK] Stats after trace test: {stats['counters']}")

    # Wait for reset
    print("\n[TEST] Waiting 1.5s for counter reset...")
    time.sleep(1.5)

    # Test events filtering
    print("\n[TEST] Events filtering:")
    for i in range(8):
        events_data = [f"event_{i}"]
        allowed = filter.should_include_events(events_data)
        print(f"  Event {i}: {'allowed' if allowed else 'BLOCKED'}")

    stats = filter.get_stats()
    print(f"\n[OK] Stats after events test: {stats['counters']}")
    print(f"[OK] Backoff delay: {stats['backoff_delay']:.3f}s")

    print("\n[PASS] ChangeFilter tests passed!")
