"""Error handling for MCP server

Custom exception classes for specific error conditions
"""

import ctypes
import functools


class MesenMCPError(Exception):
    """Base exception for all MCP server errors"""
    pass


class DebuggerNotInitializedError(MesenMCPError):
    """Debugger is not running or initialized"""
    pass


class EmulatorNotRunningError(MesenMCPError):
    """Emulator is not running"""
    pass


class InvalidMemoryTypeError(MesenMCPError):
    """Invalid memory type specified"""
    pass


class InvalidAddressError(MesenMCPError):
    """Address out of range for memory type"""
    pass


class DllNotLoadedError(MesenMCPError):
    """MesenCore.dll could not be loaded"""
    pass


class InvalidCpuTypeError(MesenMCPError):
    """Invalid CPU type specified"""
    pass


class StructSizeMismatchError(MesenMCPError):
    """ctypes struct size doesn't match C++ struct"""
    pass


# Decorator for safe tool calls

def safe_tool_call(func):
    """Decorator for tool functions that ensures debugger is initialized

    Usage:
        @safe_tool_call
        def my_tool(bridge, **kwargs):
            # Tool implementation
            pass
    """
    @functools.wraps(func)
    def wrapper(bridge, **kwargs):
        try:
            # Check debugger is initialized
            if not bridge.is_debugger_running():
                raise DebuggerNotInitializedError(
                    "Debugger not initialized. Load a ROM and enable debugging first."
                )

            # Call the actual function
            return func(bridge, **kwargs)

        except ctypes.ArgumentError as e:
            raise MesenMCPError(f"Invalid argument to DLL function: {e}")

        except OSError as e:
            raise DllNotLoadedError(f"DLL error: {e}")

        except Exception as e:
            # Re-raise MesenMCPError exceptions as-is
            if isinstance(e, MesenMCPError):
                raise
            # Wrap other exceptions
            raise MesenMCPError(f"Unexpected error: {e}")

    return wrapper


def require_emulation_running(func):
    """Decorator that requires emulation to be running

    Usage:
        @require_emulation_running
        def my_tool(bridge, **kwargs):
            # Tool implementation
            pass
    """
    @functools.wraps(func)
    def wrapper(bridge, **kwargs):
        if not bridge.is_emulation_running():
            raise EmulatorNotRunningError(
                "Emulator not running. Start emulation first."
            )
        return func(bridge, **kwargs)

    return wrapper


def validate_memory_type(memory_type, valid_types=None):
    """Validate a memory type value

    Args:
        memory_type: The memory type to validate
        valid_types: Optional list of valid memory types

    Raises:
        InvalidMemoryTypeError: If memory type is invalid
    """
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from enums import MemoryType

    try:
        # Try to convert to MemoryType enum
        mem_type = MemoryType(memory_type)

        # Check against valid types if provided
        if valid_types is not None and mem_type not in valid_types:
            raise InvalidMemoryTypeError(
                f"Memory type {mem_type.name} not valid for this operation"
            )

        return mem_type

    except ValueError:
        raise InvalidMemoryTypeError(
            f"Invalid memory type: {memory_type}"
        )


def validate_address(address, memory_size):
    """Validate an address is within bounds

    Args:
        address: The address to validate
        memory_size: The size of the memory region

    Raises:
        InvalidAddressError: If address is out of bounds
    """
    if not isinstance(address, int):
        raise InvalidAddressError(
            f"Address must be an integer, got {type(address)}"
        )

    if address < 0:
        raise InvalidAddressError(
            f"Address cannot be negative: {address}"
        )

    if address >= memory_size:
        raise InvalidAddressError(
            f"Address {hex(address)} out of range (size: {hex(memory_size)})"
        )


def validate_cpu_type(cpu_type):
    """Validate a CPU type value

    Args:
        cpu_type: The CPU type to validate

    Returns:
        CpuType enum value

    Raises:
        InvalidCpuTypeError: If CPU type is invalid
    """
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from enums import CpuType

    try:
        return CpuType(cpu_type)
    except ValueError:
        raise InvalidCpuTypeError(
            f"Invalid CPU type: {cpu_type}"
        )


# Test function

if __name__ == "__main__":
    print("Testing error handling...")

    # Test custom exceptions
    try:
        raise DebuggerNotInitializedError("Test error")
    except MesenMCPError as e:
        print(f"[OK] Caught MesenMCPError: {e}")

    # Test validation functions
    try:
        validate_memory_type(999999)
    except InvalidMemoryTypeError as e:
        print(f"[OK] Caught InvalidMemoryTypeError: {e}")

    try:
        validate_address(-1, 1000)
    except InvalidAddressError as e:
        print(f"[OK] Caught InvalidAddressError: {e}")

    try:
        validate_cpu_type(999)
    except InvalidCpuTypeError as e:
        print(f"[OK] Caught InvalidCpuTypeError: {e}")

    print("\n[PASS] Error handling tests passed!")
