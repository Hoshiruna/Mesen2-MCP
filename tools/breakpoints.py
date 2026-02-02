"""Tool: set_breakpoints

Manage breakpoints for debugging
"""

import ctypes
from typing import Dict, Any, List
from debug_bridge import MesenBridge
from struct_defs import Breakpoint
from enums import CpuType, MemoryType, BreakpointType
from utils.errors import safe_tool_call, MesenMCPError


@safe_tool_call
def set_breakpoints(
    bridge: MesenBridge,
    breakpoints: List[Dict[str, Any]],
    **kwargs
) -> Dict[str, Any]:
    """Configure execution/read/write breakpoints

    Parameters:
        breakpoints: List of breakpoint definitions
          Each breakpoint dict should have:
            - type: str - "Execute", "Read", "Write", or "Forbid"
            - address: int - Memory address
            - cpu_type: int or str - CPU type (optional, default: Snes)
            - memory_type: int or str - Memory type (optional, default: SnesMemory)
            - enabled: bool - Enable breakpoint (optional, default: True)
            - condition: str - Condition expression (optional, default: "")
            - end_address: int - End address for range (optional)

    Returns:
        Dictionary with:
        - breakpoints_set: int - Number of breakpoints configured
        - success: bool - True if all breakpoints set successfully
    """
    if not isinstance(breakpoints, list):
        raise MesenMCPError("breakpoints must be a list")

    # Setup SetBreakpoints function signature
    if not hasattr(bridge.dll, '_set_breakpoints_setup'):
        bridge.dll.SetBreakpoints.argtypes = [
            ctypes.POINTER(Breakpoint),  # Breakpoint array
            ctypes.c_uint32,             # Count
        ]
        bridge.dll.SetBreakpoints.restype = None
        bridge.dll._set_breakpoints_setup = True

    # Convert breakpoint dicts to Breakpoint structs
    bp_structs = []
    for i, bp_dict in enumerate(breakpoints):
        try:
            bp_struct = _create_breakpoint_struct(bp_dict, i)
            bp_structs.append(bp_struct)
        except Exception as e:
            raise MesenMCPError(f"Error creating breakpoint {i}: {e}")

    # Create array
    bp_array = (Breakpoint * len(bp_structs))(*bp_structs)

    # Set breakpoints
    bridge.dll.SetBreakpoints(bp_array, len(bp_structs))

    return {
        "breakpoints_set": len(bp_structs),
        "success": True,
    }


def _create_breakpoint_struct(bp_dict: Dict[str, Any], bp_id: int) -> Breakpoint:
    """Create a Breakpoint struct from a dict"""

    # Parse breakpoint type
    bp_type_str = bp_dict.get("type", "Execute")
    try:
        bp_type = BreakpointType[bp_type_str]
    except KeyError:
        raise MesenMCPError(
            f"Invalid breakpoint type: {bp_type_str}. "
            "Valid types: Execute, Read, Write, Forbid"
        )

    # Parse CPU type
    cpu_type = bp_dict.get("cpu_type", CpuType.Snes)
    if isinstance(cpu_type, str):
        try:
            cpu_type = CpuType[cpu_type]
        except KeyError:
            raise MesenMCPError(f"Invalid CPU type: {cpu_type}")
    else:
        cpu_type = CpuType(cpu_type)

    # Parse memory type
    memory_type = bp_dict.get("memory_type", MemoryType.SnesMemory)
    if isinstance(memory_type, str):
        try:
            memory_type = MemoryType[memory_type]
        except KeyError:
            raise MesenMCPError(f"Invalid memory type: {memory_type}")
    else:
        memory_type = MemoryType(memory_type)

    # Get address
    address = bp_dict.get("address")
    if address is None:
        raise MesenMCPError("Breakpoint must have 'address' field")

    if not isinstance(address, int):
        raise MesenMCPError(f"Address must be integer, got {type(address)}")

    # Get end address (for range breakpoints)
    end_address = bp_dict.get("end_address", address)

    # Get enabled flag
    enabled = bp_dict.get("enabled", True)

    # Get condition expression
    condition = bp_dict.get("condition", "")
    if len(condition) > 999:
        condition = condition[:999]  # Truncate to fit in struct

    # Create struct
    bp = Breakpoint()
    bp.Id = bp_id
    bp.CpuType = cpu_type
    bp.MemoryType = memory_type
    bp.Type = bp_type
    bp.StartAddr = address
    bp.EndAddr = end_address
    bp.Enabled = enabled
    bp.MarkEvent = bp_dict.get("mark_event", False)
    bp.IgnoreDummyOperations = bp_dict.get("ignore_dummy", True)

    # Set condition string
    if condition:
        condition_bytes = condition.encode('utf-8')
        ctypes.memmove(
            ctypes.addressof(bp.Condition),
            condition_bytes,
            min(len(condition_bytes), 999)
        )

    return bp
