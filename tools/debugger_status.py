"""Tool: debugger_status

Check if debugger is running and get basic emulator state
"""

from typing import Dict, Any
from debug_bridge import MesenBridge


def debugger_status(bridge: MesenBridge, **kwargs) -> Dict[str, Any]:
    """Get current debugger and emulator status

    Parameters:
        None

    Returns:
        Dictionary with status information:
        - debugger_running: bool - Is debugger initialized
        - emulation_running: bool - Is emulator running
        - execution_stopped: bool - Is execution paused at breakpoint
        - emulation_paused: bool - Is emulation manually paused
        - dll_responsive: bool - Is DLL responding to calls
        - mesen_version: int - Mesen version number
    """
    return {
        "debugger_running": bridge.is_debugger_running(),
        "emulation_running": bridge.is_emulation_running(),
        "execution_stopped": bridge.is_execution_stopped(),
        "emulation_paused": bridge.is_emulation_paused(),
        "dll_responsive": bridge.check_dll_loaded(),
        "mesen_version": bridge.dll.GetMesenVersion()
    }
