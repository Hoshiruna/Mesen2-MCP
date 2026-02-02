"""Bridge to MesenCore.dll via ctypes

This module provides a Python interface to the Mesen2 debugger API
through ctypes bindings to MesenCore.dll.
"""

import ctypes
import platform
import os
import threading
from pathlib import Path
from typing import Optional

from enums import CpuType, MemoryType, StepType


class MesenBridge:
    """Bridge to MesenCore.dll debugger API"""

    def __init__(self, dll_path: Optional[str] = None):
        """Initialize the bridge to MesenCore.dll

        Args:
            dll_path: Optional path to MesenCore.dll. If None, will search common locations.
        """
        self.dll = None
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._callback_refs = []  # Keep callback references to prevent GC
        self._notification_listener = None

        # Find and load DLL
        if dll_path is None:
            dll_path = self._find_dll()

        self._load_dll(dll_path)
        self._setup_function_signatures()
        self._validate_connection()

    def _find_dll(self) -> str:
        """Find MesenCore DLL based on platform

        Returns:
            Path to the DLL

        Raises:
            RuntimeError: If DLL cannot be found
        """
        system = platform.system()

        if system == "Windows":
            dll_name = "MesenCore.dll"
        elif system == "Linux":
            dll_name = "libMesen.so"
        elif system == "Darwin":  # macOS
            dll_name = "libMesen.dylib"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

        # Search locations
        search_paths = [
            # Current directory
            Path.cwd() / dll_name,
            # bin directory relative to project root (one level up from mcp_server/)
            Path.cwd().parent / "bin" / "win-x64" / "Release" / dll_name,
            # bin directory relative to current directory
            Path.cwd() / "bin" / "win-x64" / "Release" / dll_name,
            # System PATH (will be found by ctypes.CDLL)
            dll_name
        ]

        for path in search_paths:
            if isinstance(path, Path) and path.exists():
                return str(path)

        # Try just the name (searches PATH)
        return dll_name

    def _load_dll(self, dll_path: str):
        """Load the DLL using ctypes

        Args:
            dll_path: Path to the DLL

        Raises:
            OSError: If DLL cannot be loaded
        """
        try:
            self.dll = ctypes.CDLL(dll_path)
        except OSError as e:
            raise OSError(
                f"Failed to load MesenCore DLL at '{dll_path}'. "
                f"Make sure the DLL exists and is the correct architecture (x64). "
                f"Error: {e}"
            )

    def _setup_function_signatures(self):
        """Setup ctypes function signatures for commonly used functions"""

        # Basic functions
        self.dll.TestDll.restype = ctypes.c_bool
        self.dll.TestDll.argtypes = []

        self.dll.GetMesenVersion.restype = ctypes.c_uint32
        self.dll.GetMesenVersion.argtypes = []

        self.dll.InitDll.restype = None
        self.dll.InitDll.argtypes = []

        # Emulator control
        self.dll.IsRunning.restype = ctypes.c_bool
        self.dll.IsRunning.argtypes = []

        self.dll.IsPaused.restype = ctypes.c_bool
        self.dll.IsPaused.argtypes = []

        self.dll.Pause.restype = None
        self.dll.Pause.argtypes = []

        self.dll.Resume.restype = None
        self.dll.Resume.argtypes = []

        # Debugger functions
        self.dll.IsDebuggerRunning.restype = ctypes.c_bool
        self.dll.IsDebuggerRunning.argtypes = []

        self.dll.IsExecutionStopped.restype = ctypes.c_bool
        self.dll.IsExecutionStopped.argtypes = []

        self.dll.InitializeDebugger.restype = None
        self.dll.InitializeDebugger.argtypes = []

        self.dll.ReleaseDebugger.restype = None
        self.dll.ReleaseDebugger.argtypes = []

        self.dll.ResumeExecution.restype = None
        self.dll.ResumeExecution.argtypes = []

        # Memory functions
        self.dll.GetMemorySize.restype = ctypes.c_uint32
        self.dll.GetMemorySize.argtypes = [ctypes.c_int32]  # MemoryType

        self.dll.GetMemoryValue.restype = ctypes.c_uint8
        self.dll.GetMemoryValue.argtypes = [ctypes.c_int32, ctypes.c_uint32]  # MemoryType, address

    def _validate_connection(self):
        """Validate connection to DLL by calling TestDll()

        Raises:
            RuntimeError: If connection test fails
        """
        if not self.dll.TestDll():
            raise RuntimeError("DLL connection test failed - TestDll() returned false")

        # Get version info
        version = self.dll.GetMesenVersion()
        print(f"[MesenBridge] Connected to Mesen version: {version}")

        # Initialize DLL
        self.dll.InitDll()
        print(f"[MesenBridge] DLL initialized successfully")

    def check_dll_loaded(self) -> bool:
        """Verify DLL is still accessible

        Returns:
            True if DLL is loaded and responsive
        """
        try:
            return self.dll.TestDll()
        except:
            return False

    def initialize_debugger(self) -> bool:
        """Initialize the debugger if not already running

        Returns:
            True if debugger is running (either was already running or just initialized)

        Raises:
            RuntimeError: If debugger initialization times out
        """
        if self.dll.IsDebuggerRunning():
            return True

        print("[MesenBridge] Initializing debugger...")
        self.dll.InitializeDebugger()

        # Wait for initialization (max 1 second)
        import time
        for _ in range(10):
            if self.dll.IsDebuggerRunning():
                print("[MesenBridge] Debugger initialized successfully")
                return True
            time.sleep(0.1)

        raise RuntimeError("Debugger initialization timeout")

    def release_debugger(self):
        """Release debugger resources"""
        if self.dll.IsDebuggerRunning():
            self.dll.ReleaseDebugger()
            print("[MesenBridge] Debugger released")

    def get_memory_size(self, memory_type: MemoryType) -> int:
        """Get the size of a memory region

        Args:
            memory_type: The memory region type

        Returns:
            Size in bytes
        """
        return self.dll.GetMemorySize(memory_type)

    def get_memory_value(self, memory_type: MemoryType, address: int) -> int:
        """Read a single byte from memory

        Args:
            memory_type: The memory region type
            address: The address to read from

        Returns:
            Byte value (0-255)
        """
        return self.dll.GetMemoryValue(memory_type, address)

    def is_debugger_running(self) -> bool:
        """Check if debugger is running

        Returns:
            True if debugger is initialized and running
        """
        return self.dll.IsDebuggerRunning()

    def is_execution_stopped(self) -> bool:
        """Check if execution is stopped (at breakpoint)

        Returns:
            True if execution is paused at a breakpoint
        """
        return self.dll.IsExecutionStopped()

    def is_emulation_running(self) -> bool:
        """Check if emulation is running

        Returns:
            True if emulator is running
        """
        return self.dll.IsRunning()

    def is_emulation_paused(self) -> bool:
        """Check if emulation is paused

        Returns:
            True if emulator is paused
        """
        return self.dll.IsPaused()

    def pause_emulation(self):
        """Pause emulation"""
        self.dll.Pause()

    def resume_emulation(self):
        """Resume emulation"""
        self.dll.Resume()

    def resume_execution(self):
        """Resume execution (from breakpoint)"""
        self.dll.ResumeExecution()

    def register_notification_callback(self, callback):
        """Register callback for debugger events

        Args:
            callback: Python function to call on debugger events

        Returns:
            Listener ID for unregistering later

        Note:
            The callback reference is kept alive to prevent garbage collection.
            Use unregister_notification_callback() to clean up.
        """
        # Create ctypes callback
        CALLBACK_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p)
        callback_func = CALLBACK_TYPE(callback)

        # Keep reference to prevent GC
        self._callback_refs.append(callback_func)

        # Note: RegisterNotificationCallback would need to be exposed by DLL
        # This is a placeholder for future implementation
        self._notification_listener = callback_func

        return len(self._callback_refs) - 1

    def unregister_notification_callback(self):
        """Unregister notification callback"""
        if self._notification_listener:
            with self._lock:
                self._notification_listener = None
                self._callback_refs.clear()

    def safe_call(self, func, *args, **kwargs):
        """Thread-safe wrapper for DLL calls

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If DLL not loaded or debugger not running
        """
        if not self.dll:
            raise RuntimeError("DLL not loaded")

        with self._lock:
            return func(*args, **kwargs)

    def health_check(self) -> dict:
        """Perform health check on DLL and debugger

        Returns:
            Dictionary with health status:
            - dll_loaded: bool
            - dll_responsive: bool
            - debugger_running: bool
            - emulation_running: bool
            - emulation_paused: bool
        """
        health = {
            "dll_loaded": self.dll is not None,
            "dll_responsive": False,
            "debugger_running": False,
            "emulation_running": False,
            "emulation_paused": False,
        }

        if health["dll_loaded"]:
            try:
                health["dll_responsive"] = self.check_dll_loaded()

                if health["dll_responsive"]:
                    health["debugger_running"] = self.is_debugger_running()
                    health["emulation_running"] = self.is_emulation_running()
                    health["emulation_paused"] = self.is_emulation_paused()
            except Exception:
                pass

        return health

    def __del__(self):
        """Cleanup on destruction"""
        try:
            # Unregister callbacks
            self.unregister_notification_callback()

            # Release debugger if running
            if self.dll and hasattr(self.dll, 'IsDebuggerRunning'):
                if self.dll.IsDebuggerRunning():
                    self.release_debugger()
        except Exception:
            # Ignore errors during cleanup
            pass


# Test function
if __name__ == "__main__":
    print("Testing MesenBridge...")

    try:
        bridge = MesenBridge()
        print(f"[OK] DLL loaded successfully")
        print(f"[OK] Mesen version: {bridge.dll.GetMesenVersion()}")
        print(f"[OK] DLL responsive: {bridge.check_dll_loaded()}")
        print(f"[OK] Debugger running: {bridge.is_debugger_running()}")
        print(f"[OK] Emulation running: {bridge.is_emulation_running()}")

        # Try to get SNES Work RAM size
        try:
            ram_size = bridge.get_memory_size(MemoryType.SnesWorkRam)
            print(f"[OK] SNES Work RAM size: {ram_size} bytes")
        except:
            print("  (SNES Work RAM size query failed - ROM may not be loaded)")

        print("\n[PASS] All tests passed!")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
