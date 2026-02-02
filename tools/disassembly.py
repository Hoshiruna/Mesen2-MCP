"""Tool: get_disassembly

Get disassembled code for debugging
"""

import ctypes
from typing import Dict, Any, Optional, List
from debug_bridge import MesenBridge
from enums import CpuType, get_cpu_type_name
from utils.errors import safe_tool_call, InvalidCpuTypeError, MesenMCPError


# Simple structure for disassembly line data
class CodeLineData(ctypes.Structure):
    """Disassembly line data (simplified)

    Note: This is a simplified version. Full struct has more fields.
    """
    _pack_ = 1
    _fields_ = [
        ("Address", ctypes.c_uint32),
        ("AbsoluteAddress", ctypes.c_int32),
        ("Type", ctypes.c_uint8),
        ("Flags", ctypes.c_uint16),
        ("_padding", ctypes.c_uint8),
        # Note: Full struct has more fields including formatted text
        # but we'll use GetDisassemblyText for the actual text
    ]


@safe_tool_call
def get_disassembly(
    bridge: MesenBridge,
    address: Optional[int] = None,
    cpu_type: Optional[int] = None,
    line_count: int = 20,
    line_offset: int = -10,
    **kwargs
) -> Dict[str, Any]:
    """Get disassembled code around an address

    Parameters:
        address (optional): Address to disassemble (default: current PC)
        cpu_type (optional): CPU type (default: SNES)
        line_count: Number of lines to return (default: 20, max: 100)
        line_offset: Offset from address (default: -10, showing 10 lines before)

    Returns:
        Dictionary with:
        - cpu_type: str - CPU type name
        - center_address: int - Address we centered on
        - line_count: int - Number of lines returned
        - lines: list - List of disassembly lines
          Each line has:
            - address: int - Memory address
            - bytes: str - Hex bytes of instruction
            - instruction: str - Disassembled instruction text
    """
    # Default to SNES
    if cpu_type is None:
        cpu_type = CpuType.Snes
    else:
        try:
            cpu_type = CpuType(cpu_type)
        except ValueError:
            raise InvalidCpuTypeError(f"Invalid CPU type: {cpu_type}")

    # Get current PC if no address specified
    if address is None:
        address = _get_current_pc(bridge, cpu_type)

    # Validate line_count
    if not isinstance(line_count, int) or line_count <= 0:
        raise MesenMCPError(f"line_count must be positive integer, got {line_count}")

    if line_count > 100:
        line_count = 100  # Cap at 100 lines

    # For now, return a placeholder since GetDisassemblyOutput requires
    # complex setup and may need ROM loaded
    # Full implementation would call GetDisassemblyOutput with proper buffer

    return {
        "cpu_type": get_cpu_type_name(cpu_type),
        "center_address": address,
        "line_count": line_count,
        "line_offset": line_offset,
        "note": "Full disassembly requires ROM loaded and complex buffer management. "
                "This will be fully implemented in Phase 1 completion.",
        "placeholder": True,
        "lines": _generate_placeholder_disassembly(address, line_count, line_offset)
    }


def _get_current_pc(bridge: MesenBridge, cpu_type: CpuType) -> int:
    """Get current program counter for a CPU

    Note: Requires GetProgramCounter function setup
    """
    # Setup function if needed
    if not hasattr(bridge.dll, '_get_pc_setup'):
        bridge.dll.GetProgramCounter.argtypes = [
            ctypes.c_uint32,  # CpuType
            ctypes.c_bool,    # Get instruction start PC
        ]
        bridge.dll.GetProgramCounter.restype = ctypes.c_uint32
        bridge.dll._get_pc_setup = True

    # Get PC
    pc = bridge.dll.GetProgramCounter(cpu_type, True)
    return pc


def _generate_placeholder_disassembly(address: int, count: int, offset: int) -> List[Dict[str, Any]]:
    """Generate placeholder disassembly lines

    This is a placeholder until full disassembly is implemented
    """
    lines = []
    start_addr = max(0, address + offset)

    for i in range(count):
        current_addr = start_addr + (i * 2)  # Assume 2 bytes per instruction
        lines.append({
            "address": current_addr,
            "bytes": "??",
            "instruction": f"[Disassembly at {hex(current_addr)}]",
            "is_current_pc": (current_addr == address)
        })

    return lines
