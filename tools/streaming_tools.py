"""Streaming tools for MCP server

Tools for subscribing to real-time change feeds and retrieving changes.
"""

from typing import Dict, Any, Optional
from debug_bridge import MesenBridge
from streaming.sampler import BackgroundSampler

# Global sampler instance (one per server)
_sampler: Optional[BackgroundSampler] = None


def get_sampler(bridge: MesenBridge) -> BackgroundSampler:
    """Get or create the global sampler instance

    Args:
        bridge: MesenBridge instance

    Returns:
        BackgroundSampler instance
    """
    global _sampler
    if _sampler is None:
        _sampler = BackgroundSampler(bridge)
    return _sampler


def start_streaming(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Start background sampler

    Parameters:
        None

    Returns:
        Dictionary with:
        - streaming: bool - True if sampler started
        - status: str - Status message
    """
    sampler = get_sampler(bridge)
    sampler.start()

    return {
        "streaming": True,
        "status": "Background sampler started",
        "polling_rate_hz": 10,
    }


def stop_streaming(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Stop background sampler

    Parameters:
        None

    Returns:
        Dictionary with:
        - streaming: bool - False (stopped)
        - status: str - Status message
        - stats: dict - Final statistics
    """
    sampler = get_sampler(bridge)
    stats = sampler.get_stats()
    sampler.stop()

    return {
        "streaming": False,
        "status": "Background sampler stopped",
        "final_stats": stats,
    }


def subscribe_trace(
    bridge: MesenBridge,
    max_lines_per_poll: int = 100,
    **kwargs
) -> Dict[str, Any]:
    """Subscribe to execution trace changes

    Parameters:
        max_lines_per_poll: Max trace lines per update (default: 100)

    Returns:
        Dictionary with:
        - subscribed: bool - True if subscribed
        - subscription_id: str - Subscription identifier
        - max_lines_per_poll: int - Configured limit
    """
    sampler = get_sampler(bridge)
    sampler.subscribe("trace", max_lines=max_lines_per_poll)

    return {
        "subscribed": True,
        "subscription_id": "trace",
        "max_lines_per_poll": max_lines_per_poll,
    }


def subscribe_events(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Subscribe to debug event changes

    Parameters:
        None

    Returns:
        Dictionary with:
        - subscribed: bool - True if subscribed
        - subscription_id: str - Subscription identifier
    """
    sampler = get_sampler(bridge)
    sampler.subscribe("events")

    return {
        "subscribed": True,
        "subscription_id": "events",
    }


def subscribe_memory(
    bridge: MesenBridge,
    memory_type: str,
    address: int,
    length: int = 1,
    **kwargs
) -> Dict[str, Any]:
    """Subscribe to memory range changes

    Parameters:
        memory_type: Memory region to watch
        address: Start address
        length: Number of bytes to watch (default: 1, max: 256)

    Returns:
        Dictionary with:
        - subscribed: bool - True if subscribed
        - subscription_id: str - Unique subscription identifier
        - memory_type: str - Memory type
        - address: int - Address being watched
        - length: int - Number of bytes
    """
    # Limit length for safety
    if length > 256:
        length = 256

    sampler = get_sampler(bridge)
    sampler.subscribe(
        "memory",
        memory_type=memory_type,
        address=address,
        length=length
    )

    subscription_id = f"memory_{memory_type}_{address}_{length}"

    return {
        "subscribed": True,
        "subscription_id": subscription_id,
        "memory_type": memory_type,
        "address": address,
        "length": length,
    }


def unsubscribe_memory(
    bridge: MesenBridge,
    address: int,
    **kwargs
) -> Dict[str, Any]:
    """Unsubscribe from memory watch

    Parameters:
        address: Address to stop watching

    Returns:
        Dictionary with:
        - unsubscribed: bool - True if unsubscribed
        - address: int - Address that was removed
    """
    sampler = get_sampler(bridge)
    sampler.unsubscribe("memory", address=address)

    return {
        "unsubscribed": True,
        "address": address,
    }


def get_changes(
    bridge: MesenBridge,
    max_count: int = 100,
    **kwargs
) -> Dict[str, Any]:
    """Get accumulated changes from queue

    Parameters:
        max_count: Maximum changes to return (default: 100, max: 1000)

    Returns:
        Dictionary with:
        - change_count: int - Number of changes returned
        - changes: list - List of change dicts
          Each change has:
            - type: str - Change type (trace_delta, events_delta, memory_delta)
            - timestamp: float - Unix timestamp
            - (type-specific fields)
    """
    # Limit max_count
    if max_count > 1000:
        max_count = 1000

    sampler = get_sampler(bridge)
    changes = sampler.get_changes(max_count)

    return {
        "change_count": len(changes),
        "changes": changes,
    }


def get_streaming_status(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Get streaming sampler status and statistics

    Parameters:
        None

    Returns:
        Dictionary with:
        - streaming: bool - True if sampler is running
        - stats: dict - Sampler statistics
    """
    sampler = get_sampler(bridge)
    stats = sampler.get_stats()

    return {
        "streaming": sampler.running,
        "stats": stats,
    }
