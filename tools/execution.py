"""Tools: step, resume, pause

Control emulator execution for debugging
"""

import ctypes
from typing import Dict, Any, Optional
from debug_bridge import MesenBridge
from enums import CpuType, StepType, get_cpu_type_name
from utils.errors import safe_tool_call, InvalidCpuTypeError, MesenMCPError


@safe_tool_call
def step(
    bridge: MesenBridge,
    cpu_type: Optional[int] = None,
    count: int = 1,
    step_type: str = "Step",
    **kwargs
) -> Dict[str, Any]:
    """Step execution by instruction/scanline/frame

    Parameters:
        cpu_type (optional): Which CPU to step (default: current/main CPU)
        count: Number of steps to execute (default: 1)
        step_type: Type of step (default: "Step")
                  Options: "Step", "StepOver", "StepOut",
                          "PpuStep", "PpuScanline", "PpuFrame",
                          "CpuCycleStep"

    Returns:
        Dictionary with:
        - stepped: bool - True if step executed
        - step_type: str - Type of step performed
        - count: int - Number of steps executed
    """
    # Default to SNES if not specified
    if cpu_type is None:
        cpu_type = CpuType.Snes
    else:
        try:
            cpu_type = CpuType(cpu_type)
        except ValueError:
            raise InvalidCpuTypeError(f"Invalid CPU type: {cpu_type}")

    # Convert step type string to enum
    try:
        step_type_enum = StepType[step_type]
    except KeyError:
        valid_types = ", ".join(t.name for t in StepType)
        raise MesenMCPError(
            f"Invalid step type: {step_type}. "
            f"Valid types: {valid_types}"
        )

    # Setup Step function signature
    if not hasattr(bridge.dll, '_step_setup'):
        bridge.dll.Step.argtypes = [
            ctypes.c_uint32,  # CpuType
            ctypes.c_int32,   # Step count
            ctypes.c_uint32,  # StepType
        ]
        bridge.dll.Step.restype = None
        bridge.dll._step_setup = True

    # Execute step
    bridge.dll.Step(cpu_type, count, step_type_enum)

    return {
        "stepped": True,
        "cpu_type": get_cpu_type_name(cpu_type),
        "step_type": step_type,
        "count": count,
    }


@safe_tool_call
def resume(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Resume execution (from breakpoint or pause)

    Parameters:
        None

    Returns:
        Dictionary with:
        - resumed: bool - True if execution resumed
        - execution_stopped: bool - Current execution state
    """
    # Resume execution
    bridge.resume_execution()

    # Check if still stopped (might hit another breakpoint immediately)
    is_stopped = bridge.is_execution_stopped()

    return {
        "resumed": True,
        "execution_stopped": is_stopped,
    }


def pause(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Pause emulation

    Parameters:
        None

    Returns:
        Dictionary with:
        - paused: bool - True if emulation paused
        - emulation_paused: bool - Current pause state
    """
    # Pause emulation
    bridge.pause_emulation()

    # Confirm pause state
    is_paused = bridge.is_emulation_paused()

    return {
        "paused": True,
        "emulation_paused": is_paused,
    }
