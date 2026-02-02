"""Tool: get_debug_events

Get recent debug events (breakpoints, IRQs, NMIs, etc.)
"""

import ctypes
from typing import Dict, Any, List
from debug_bridge import MesenBridge
from struct_defs import DebugEventInfo
from enums import CpuType, get_cpu_type_name
from utils.errors import safe_tool_call, MesenMCPError


@safe_tool_call
def get_debug_events(
    bridge: MesenBridge,
    cpu_type: int = None,
    max_count: int = 100,
    **kwargs
) -> Dict[str, Any]:
    """Get recent debug events

    Parameters:
        cpu_type (optional): CPU type to get events for (default: SNES)
        max_count: Maximum events to return (default: 100, max: 1000)

    Returns:
        Dictionary with:
        - cpu_type: str - CPU type name
        - event_count: int - Number of events returned
        - events: list - List of event dicts
          Each event has:
            - type: str - Event type name
            - pc: int - Program counter when event occurred
            - scanline: int - Scanline number
            - cycle: int - Cycle number
            - (additional fields depending on event type)
    """
    # Default to SNES
    if cpu_type is None:
        cpu_type = CpuType.Snes
    else:
        try:
            cpu_type = CpuType(cpu_type)
        except ValueError:
            raise MesenMCPError(f"Invalid CPU type: {cpu_type}")

    # Validate max_count
    if not isinstance(max_count, int) or max_count <= 0:
        raise MesenMCPError(f"max_count must be positive integer, got {max_count}")

    if max_count > 1000:
        max_count = 1000

    # Setup GetDebugEvents function signature
    if not hasattr(bridge.dll, '_get_debug_events_setup'):
        bridge.dll.GetDebugEvents.argtypes = [
            ctypes.c_uint32,                     # CpuType
            ctypes.POINTER(DebugEventInfo),      # Output array
            ctypes.POINTER(ctypes.c_uint32),     # In/out: max count / actual count
        ]
        bridge.dll.GetDebugEvents.restype = None
        bridge.dll._get_debug_events_setup = True

    # Allocate array for events
    events_array = (DebugEventInfo * max_count)()
    event_count = ctypes.c_uint32(max_count)

    # Get events
    bridge.dll.GetDebugEvents(cpu_type, events_array, ctypes.byref(event_count))

    actual_count = event_count.value

    # Parse events
    events = []
    for i in range(min(actual_count, max_count)):
        event = events_array[i]

        # Basic event info
        event_dict = {
            "type": _get_event_type_name(event.Type),
            "pc": event.ProgramCounter,
            "scanline": event.Scanline,
            "cycle": event.Cycle,
        }

        # Add breakpoint ID if present
        if event.BreakpointId >= 0:
            event_dict["breakpoint_id"] = event.BreakpointId

        # Add DMA channel if present
        if event.DmaChannel >= 0:
            event_dict["dma_channel"] = event.DmaChannel

        # Add memory operation info
        if event.Operation.Address != 0:
            event_dict["operation"] = {
                "address": event.Operation.Address,
                "value": event.Operation.Value,
                "type": event.Operation.Type,
            }

        events.append(event_dict)

    return {
        "cpu_type": get_cpu_type_name(cpu_type),
        "event_count": len(events),
        "events": events,
    }


def _get_event_type_name(event_type: int) -> str:
    """Get human-readable event type name"""
    event_names = {
        0: "Register",
        1: "Nmi",
        2: "Irq",
        3: "Breakpoint",
        4: "BgColorChange",
        5: "SpriteZeroHit",
        6: "DmcDmaRead",
        7: "DmaRead",
    }
    return event_names.get(event_type, f"Unknown({event_type})")
