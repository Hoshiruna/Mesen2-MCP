"""Tool: get_ppu_state

Get PPU/graphics chip state for debugging
"""

import ctypes
from typing import Dict, Any, Optional
from debug_bridge import MesenBridge
from enums import CpuType
from utils.errors import safe_tool_call, InvalidCpuTypeError


@safe_tool_call
def get_ppu_state(bridge: MesenBridge, cpu_type: Optional[int] = None, **kwargs) -> Dict[str, Any]:
    """Get PPU/graphics chip state (simplified)

    Note: Full PPU state is 200+ fields. This returns a simplified subset
    of the most useful information for debugging.

    Parameters:
        cpu_type (optional): CPU type to query PPU for (default: SNES)

    Returns:
        Dictionary with simplified PPU state:
        - cpu_type: str - Name of the CPU type
        - scanline: int - Current scanline being drawn
        - cycle: int - Cycle within current scanline
        - frame_count: int - Total frames rendered
        - (more fields depending on console)
    """
    # Default to SNES if not specified
    if cpu_type is None:
        cpu_type = CpuType.Snes
    else:
        try:
            cpu_type = CpuType(cpu_type)
        except ValueError:
            raise InvalidCpuTypeError(f"Invalid CPU type: {cpu_type}")

    # For now, return a simplified state using basic queries
    # Full PPU state would require complex struct mapping (200+ bytes)

    if cpu_type == CpuType.Snes:
        return _get_snes_ppu_state_simple(bridge)
    elif cpu_type == CpuType.Nes:
        return _get_nes_ppu_state_simple(bridge)
    elif cpu_type == CpuType.Gameboy:
        return _get_gameboy_ppu_state_simple(bridge)
    else:
        raise InvalidCpuTypeError(f"PPU state not yet supported for {cpu_type.name}")


def _get_snes_ppu_state_simple(bridge: MesenBridge) -> Dict[str, Any]:
    """Get simplified SNES PPU state

    Note: This is a placeholder returning basic frame info.
    Full implementation would require complex struct mapping.
    """
    return {
        "cpu_type": "Snes",
        "note": "Full PPU state requires complex struct mapping. "
                "Use get_cpu_state and memory tools for detailed debugging.",
        "available_in_phase_2": True
    }


def _get_nes_ppu_state_simple(bridge: MesenBridge) -> Dict[str, Any]:
    """Get simplified NES PPU state"""
    return {
        "cpu_type": "Nes",
        "note": "Full PPU state requires complex struct mapping. "
                "Use get_cpu_state and memory tools for detailed debugging.",
        "available_in_phase_2": True
    }


def _get_gameboy_ppu_state_simple(bridge: MesenBridge) -> Dict[str, Any]:
    """Get simplified Gameboy PPU state"""
    return {
        "cpu_type": "Gameboy",
        "note": "Full PPU state requires complex struct mapping. "
                "Use get_cpu_state and memory tools for detailed debugging.",
        "available_in_phase_2": True
    }
