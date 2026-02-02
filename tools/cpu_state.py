"""Tool: get_cpu_state

Get CPU registers and flags for debugging
"""

import ctypes
from typing import Dict, Any, Optional
from debug_bridge import MesenBridge
from enums import CpuType, get_cpu_type_name
from struct_defs import SnesCpuState, NesCpuState, GameboyCpuState
from utils.errors import safe_tool_call, InvalidCpuTypeError


@safe_tool_call
def get_cpu_state(bridge: MesenBridge, cpu_type: Optional[int] = None, **kwargs) -> Dict[str, Any]:
    """Get CPU register state

    Parameters:
        cpu_type (optional): CPU type to query (0=SNES, 7=Gameboy, 8=NES, etc.)
                            If not provided, assumes SNES (most common)

    Returns:
        Dictionary with CPU state:
        - cpu_type: str - Name of the CPU type
        - cycle_count: int - Total CPU cycles executed
        - pc: int - Program counter
        - registers: dict - CPU-specific registers
        - flags: dict - CPU status flags
    """
    # Default to SNES if not specified
    if cpu_type is None:
        cpu_type = CpuType.Snes

    try:
        cpu_type = CpuType(cpu_type)
    except ValueError:
        raise InvalidCpuTypeError(f"Invalid CPU type: {cpu_type}")

    # Setup function signature for GetCpuState
    if not hasattr(bridge.dll, '_get_cpu_state_setup'):
        bridge.dll.GetCpuState.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),  # State buffer (BaseState*)
            ctypes.c_uint32,                  # CPU type
        ]
        bridge.dll.GetCpuState.restype = None
        bridge.dll._get_cpu_state_setup = True

    # Get state based on CPU type
    if cpu_type == CpuType.Snes:
        return _get_snes_cpu_state(bridge)
    elif cpu_type == CpuType.Nes:
        return _get_nes_cpu_state(bridge)
    elif cpu_type == CpuType.Gameboy:
        return _get_gameboy_cpu_state(bridge)
    else:
        raise InvalidCpuTypeError(
            f"CPU type {get_cpu_type_name(cpu_type)} not yet supported. "
            "Currently supported: SNES, NES, Gameboy"
        )


def _get_snes_cpu_state(bridge: MesenBridge) -> Dict[str, Any]:
    """Get SNES CPU state"""
    state = SnesCpuState()

    # Call DLL function
    bridge.dll.GetCpuState(
        ctypes.cast(ctypes.pointer(state), ctypes.POINTER(ctypes.c_uint8)),
        CpuType.Snes
    )

    # Parse status flags
    ps = state.PS
    flags = {
        "carry": bool(ps & 0x01),
        "zero": bool(ps & 0x02),
        "irq_disable": bool(ps & 0x04),
        "decimal": bool(ps & 0x08),
        "index_mode_8": bool(ps & 0x10),
        "memory_mode_8": bool(ps & 0x20),
        "overflow": bool(ps & 0x40),
        "negative": bool(ps & 0x80),
    }

    return {
        "cpu_type": "Snes",
        "cycle_count": state.CycleCount,
        "pc": state.PC,
        "registers": {
            "a": state.A,
            "x": state.X,
            "y": state.Y,
            "sp": state.SP,
            "d": state.D,
            "dbr": state.DBR,
            "k": state.K,
        },
        "flags": flags,
        "emulation_mode": state.EmulationMode,
        "stop_state": state.StopState,
    }


def _get_nes_cpu_state(bridge: MesenBridge) -> Dict[str, Any]:
    """Get NES CPU state"""
    state = NesCpuState()

    # Call DLL function
    bridge.dll.GetCpuState(
        ctypes.cast(ctypes.pointer(state), ctypes.POINTER(ctypes.c_uint8)),
        CpuType.Nes
    )

    # Parse status flags
    ps = state.PS
    flags = {
        "carry": bool(ps & 0x01),
        "zero": bool(ps & 0x02),
        "irq_disable": bool(ps & 0x04),
        "decimal": bool(ps & 0x08),
        "overflow": bool(ps & 0x40),
        "negative": bool(ps & 0x80),
    }

    return {
        "cpu_type": "Nes",
        "cycle_count": state.CycleCount,
        "pc": state.PC,
        "registers": {
            "a": state.A,
            "x": state.X,
            "y": state.Y,
            "sp": state.SP,
        },
        "flags": flags,
        "irq_flag": state.IRQFlag,
        "nmi_flag": state.NMIFlag,
    }


def _get_gameboy_cpu_state(bridge: MesenBridge) -> Dict[str, Any]:
    """Get Gameboy CPU state"""
    state = GameboyCpuState()

    # Call DLL function
    bridge.dll.GetCpuState(
        ctypes.cast(ctypes.pointer(state), ctypes.POINTER(ctypes.c_uint8)),
        CpuType.Gameboy
    )

    # Parse flags (stored in Flags register)
    flags_reg = state.Flags
    flags = {
        "zero": bool(flags_reg & 0x80),
        "subtract": bool(flags_reg & 0x40),
        "half_carry": bool(flags_reg & 0x20),
        "carry": bool(flags_reg & 0x10),
    }

    return {
        "cpu_type": "Gameboy",
        "cycle_count": state.CycleCount,
        "pc": state.PC,
        "registers": {
            "a": state.A,
            "b": state.B,
            "c": state.C,
            "d": state.D,
            "e": state.E,
            "h": state.H,
            "l": state.L,
            "sp": state.SP,
        },
        "flags": flags,
        "ime": state.IME,
        "halted": state.Halted,
    }
