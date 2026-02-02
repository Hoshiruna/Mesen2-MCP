"""Background sampler for change detection

Runs in a background thread, polls the debugger state, and maintains
a queue of changes for the MCP client to consume.
"""

import threading
import time
import sys
from collections import deque
from typing import Dict, Any, Optional, List

from streaming.cursor import CursorTracker
from streaming.filters import ChangeFilter


class BackgroundSampler:
    """Background sampler with cursor-based delta tracking"""

    def __init__(self, bridge, max_queue_size: int = 1000):
        """Initialize background sampler

        Args:
            bridge: MesenBridge instance
            max_queue_size: Maximum items in change queue (ring buffer)
        """
        self.bridge = bridge
        self.queue = deque(maxlen=max_queue_size)  # Ring buffer
        self.cursor = CursorTracker()
        self.filter = ChangeFilter()

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Subscriptions
        self.subscriptions = {
            "trace": False,
            "events": False,
            "memory_watches": []  # List of {memory_type, address, length}
        }

        # Statistics
        self.stats = {
            "samples_taken": 0,
            "changes_detected": 0,
            "items_dropped": 0,  # Items dropped due to queue overflow
        }

    def start(self):
        """Start background sampling thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._sample_loop, daemon=True)
        self.thread.start()
        print("[Sampler] Background sampler started", file=sys.stderr)

    def stop(self):
        """Stop background sampling"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("[Sampler] Background sampler stopped", file=sys.stderr)

    def subscribe(self, subscription_type: str, **kwargs):
        """Subscribe to a change feed

        Args:
            subscription_type: "trace", "events", or "memory"
            **kwargs: Additional parameters for the subscription
        """
        with self.lock:
            if subscription_type == "trace":
                self.subscriptions["trace"] = True
            elif subscription_type == "events":
                self.subscriptions["events"] = True
            elif subscription_type == "memory":
                # Add memory watch
                watch = {
                    "memory_type": kwargs.get("memory_type"),
                    "address": kwargs.get("address"),
                    "length": kwargs.get("length", 1),
                }
                self.subscriptions["memory_watches"].append(watch)

    def unsubscribe(self, subscription_type: str, **kwargs):
        """Unsubscribe from a change feed

        Args:
            subscription_type: "trace", "events", or "memory"
            **kwargs: Parameters to match for removal (for memory watches)
        """
        with self.lock:
            if subscription_type == "trace":
                self.subscriptions["trace"] = False
            elif subscription_type == "events":
                self.subscriptions["events"] = False
            elif subscription_type == "memory":
                # Remove matching memory watch
                address = kwargs.get("address")
                self.subscriptions["memory_watches"] = [
                    w for w in self.subscriptions["memory_watches"]
                    if w["address"] != address
                ]

    def get_changes(self, max_count: int = 100) -> List[Dict[str, Any]]:
        """Get accumulated changes from queue

        Args:
            max_count: Maximum changes to return

        Returns:
            List of change dictionaries
        """
        with self.lock:
            changes = []
            while len(changes) < max_count and len(self.queue) > 0:
                changes.append(self.queue.popleft())
            return changes

    def get_stats(self) -> Dict[str, Any]:
        """Get sampler statistics

        Returns:
            Statistics dictionary
        """
        with self.lock:
            return {
                **self.stats,
                "queue_size": len(self.queue),
                "queue_max": self.queue.maxlen,
                "subscriptions": {
                    "trace": self.subscriptions["trace"],
                    "events": self.subscriptions["events"],
                    "memory_watches": len(self.subscriptions["memory_watches"]),
                },
                "filter_stats": self.filter.get_stats(),
            }

    def _sample_loop(self):
        """Background sampling loop (runs at ~10 Hz)"""
        print("[Sampler] Sample loop started", file=sys.stderr)

        while self.running:
            try:
                # Check if debugger is running
                if not self.bridge.is_debugger_running():
                    time.sleep(0.1)
                    continue

                # Update stats
                with self.lock:
                    self.stats["samples_taken"] += 1

                # Sample subscribed feeds
                if self.subscriptions["trace"]:
                    self._sample_trace()

                if self.subscriptions["events"]:
                    self._sample_events()

                for watch in self.subscriptions["memory_watches"]:
                    self._sample_memory(watch)

                # Apply backoff if needed
                backoff = self.filter.get_backoff_delay()
                if backoff > 0:
                    time.sleep(backoff)

                # Normal polling interval (10 Hz = 100ms)
                time.sleep(0.1)

            except Exception as e:
                # Log error but keep running
                print(f"[Sampler] Error: {e}", file=sys.stderr)
                time.sleep(0.1)

    def _sample_trace(self):
        """Sample trace tail and compute delta"""
        try:
            # Import here to avoid circular dependency
            from tools.trace import get_trace_tail

            # Get a small sample (last 50 lines)
            result = get_trace_tail(self.bridge, count=50, offset=0)

            if not result or result.get("returned_count", 0) == 0:
                return

            total_lines = result.get("total_trace_lines", 0)
            trace_lines = result.get("trace_lines", [])

            # Check cursor
            last_position = self.cursor.get("trace", 0)

            if total_lines > last_position:
                # New trace lines available
                new_line_count = total_lines - last_position

                # Only include if filter allows
                if self.filter.should_include_trace(trace_lines):
                    with self.lock:
                        # Check if queue would overflow
                        if len(self.queue) >= self.queue.maxlen - 1:
                            self.stats["items_dropped"] += 1

                        self.queue.append({
                            "type": "trace_delta",
                            "new_lines": new_line_count,
                            "sample": trace_lines[:10],  # Just first 10 lines
                            "total_trace_lines": total_lines,
                            "timestamp": time.time(),
                        })
                        self.stats["changes_detected"] += 1

                # Update cursor
                self.cursor.set("trace", total_lines)

        except Exception as e:
            print(f"[Sampler] Trace sampling error: {e}", file=sys.stderr)

    def _sample_events(self):
        """Sample debug events and compute delta"""
        try:
            # Import here to avoid circular dependency
            from tools.events import get_debug_events

            # Get recent events
            result = get_debug_events(self.bridge, max_count=20)

            if not result or result.get("event_count", 0) == 0:
                return

            events = result.get("events", [])

            # Compute hash of events to detect changes
            event_hash = hash(tuple(
                (e.get("type"), e.get("pc"), e.get("scanline"))
                for e in events
            ))

            last_hash = self.cursor.get("events_hash", 0)

            if event_hash != last_hash:
                # Events changed
                if self.filter.should_include_events(events):
                    with self.lock:
                        if len(self.queue) >= self.queue.maxlen - 1:
                            self.stats["items_dropped"] += 1

                        self.queue.append({
                            "type": "events_delta",
                            "event_count": len(events),
                            "events": events[:5],  # Just first 5 events
                            "timestamp": time.time(),
                        })
                        self.stats["changes_detected"] += 1

                self.cursor.set("events_hash", event_hash)

        except Exception as e:
            print(f"[Sampler] Events sampling error: {e}", file=sys.stderr)

    def _sample_memory(self, watch: Dict[str, Any]):
        """Sample memory watch and detect changes

        Args:
            watch: Memory watch dict with memory_type, address, length
        """
        try:
            # Import here to avoid circular dependency
            from tools.memory import get_memory_range

            mem_type = watch["memory_type"]
            address = watch["address"]
            length = watch["length"]

            # Read memory
            result = get_memory_range(
                self.bridge,
                memory_type=mem_type,
                start_address=address,
                length=length
            )

            if not result:
                return

            data = result.get("data")

            # Compare with last known value
            key = f"memory_{mem_type}_{address}"
            last_data = self.cursor.get(key)

            if data != last_data:
                # Memory changed
                if self.filter.should_include_memory(data):
                    with self.lock:
                        if len(self.queue) >= self.queue.maxlen - 1:
                            self.stats["items_dropped"] += 1

                        self.queue.append({
                            "type": "memory_delta",
                            "memory_type": str(mem_type),
                            "address": address,
                            "length": length,
                            "old_data": last_data,
                            "new_data": data,
                            "timestamp": time.time(),
                        })
                        self.stats["changes_detected"] += 1

                self.cursor.set(key, data)

        except Exception as e:
            print(f"[Sampler] Memory sampling error: {e}", file=sys.stderr)
