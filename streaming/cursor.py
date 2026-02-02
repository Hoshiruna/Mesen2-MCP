"""Cursor tracking for delta computation

Maintains cursor positions to track what data has already been sent,
enabling efficient delta/change detection.
"""

from typing import Any, Optional, Dict
import threading


class CursorTracker:
    """Maintains cursor positions for delta computation

    Tracks the last known position in various data streams (trace, events, etc.)
    to compute deltas efficiently.
    """

    def __init__(self):
        """Initialize cursor tracker"""
        self.cursors: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get cursor position for a key

        Args:
            key: Cursor key (e.g., "trace", "events_hash")
            default: Default value if key not found

        Returns:
            Cursor value or default
        """
        with self._lock:
            return self.cursors.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Update cursor position for a key

        Args:
            key: Cursor key
            value: New cursor value
        """
        with self._lock:
            self.cursors[key] = value

    def reset(self, key: Optional[str] = None) -> None:
        """Reset cursor(s)

        Args:
            key: Specific key to reset, or None to reset all
        """
        with self._lock:
            if key is None:
                self.cursors.clear()
            else:
                self.cursors.pop(key, None)

    def get_all(self) -> Dict[str, Any]:
        """Get all cursor positions

        Returns:
            Dictionary of all cursors
        """
        with self._lock:
            return self.cursors.copy()

    def __repr__(self) -> str:
        """String representation"""
        with self._lock:
            return f"CursorTracker({len(self.cursors)} cursors)"


# Test function
if __name__ == "__main__":
    print("Testing CursorTracker...")

    tracker = CursorTracker()

    # Test set and get
    tracker.set("trace", 1000)
    tracker.set("events_hash", 12345)

    assert tracker.get("trace") == 1000
    assert tracker.get("events_hash") == 12345
    assert tracker.get("nonexistent", "default") == "default"

    print(f"[OK] Set and get working")
    print(f"[OK] Tracker state: {tracker}")

    # Test get_all
    all_cursors = tracker.get_all()
    assert len(all_cursors) == 2
    print(f"[OK] get_all working: {all_cursors}")

    # Test reset
    tracker.reset("trace")
    assert tracker.get("trace") is None
    assert tracker.get("events_hash") == 12345
    print(f"[OK] Reset single key working")

    # Test reset all
    tracker.reset()
    assert len(tracker.get_all()) == 0
    print(f"[OK] Reset all working")

    print("\n[PASS] CursorTracker tests passed!")
