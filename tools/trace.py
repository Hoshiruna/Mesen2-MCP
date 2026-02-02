"""Tool: get_trace_tail

Get recent execution trace for debugging
"""

import ctypes
from typing import Dict, Any, List
from debug_bridge import MesenBridge
from struct_defs import TraceRow
from utils.errors import safe_tool_call, MesenMCPError


@safe_tool_call
def get_trace_tail(
    bridge: MesenBridge,
    count: int = 100,
    offset: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """Get recent execution trace lines

    Parameters:
        count: Number of lines to retrieve (default: 100, max: 1000)
        offset: Offset from end, 0 = most recent (default: 0)

    Returns:
        Dictionary with:
        - total_trace_lines: int - Total lines in trace buffer
        - returned_count: int - Number of lines returned
        - offset: int - Offset used
        - trace_lines: list - List of trace line dicts
          Each trace line has:
            - pc: int - Program counter
            - bytes: str - Instruction bytes
            - text: str - Formatted trace text
    """
    # Validate parameters
    if not isinstance(count, int) or count <= 0:
        raise MesenMCPError(f"count must be positive integer, got {count}")

    if not isinstance(offset, int) or offset < 0:
        raise MesenMCPError(f"offset must be non-negative integer, got {offset}")

    # Cap count at 1000 for safety
    if count > 1000:
        count = 1000

    # Setup GetExecutionTrace function signature
    if not hasattr(bridge.dll, '_get_trace_setup'):
        bridge.dll.GetExecutionTrace.argtypes = [
            ctypes.POINTER(TraceRow),  # Output array
            ctypes.c_uint32,            # Start offset
            ctypes.c_uint32,            # Line count
        ]
        bridge.dll.GetExecutionTrace.restype = ctypes.c_uint32  # Returns actual count
        bridge.dll._get_trace_setup = True

    # Allocate array for trace rows
    trace_array = (TraceRow * count)()

    # Get trace data
    actual_count = bridge.dll.GetExecutionTrace(trace_array, offset, count)

    # Parse trace rows
    trace_lines = []
    for i in range(min(actual_count, count)):
        row = trace_array[i]

        # Extract byte code as hex string
        byte_code_list = [row.ByteCode[j] for j in range(row.ByteCodeSize)]
        byte_code_hex = " ".join(f"{b:02X}" for b in byte_code_list)

        # Extract log output (may be null-terminated)
        try:
            log_text = row.LogOutput.decode('utf-8', errors='ignore').rstrip('\x00')
        except:
            log_text = "[decode error]"

        trace_lines.append({
            "pc": row.ProgramCounter,
            "bytes": byte_code_hex,
            "text": log_text,
            "byte_count": row.ByteCodeSize,
        })

    return {
        "total_trace_lines": actual_count,
        "returned_count": len(trace_lines),
        "offset": offset,
        "trace_lines": trace_lines,
    }
