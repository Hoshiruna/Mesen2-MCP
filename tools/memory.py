"""Tools: get_memory_range, set_memory

Read and write memory for debugging
"""

import ctypes
from typing import Dict, Any, List, Union
from debug_bridge import MesenBridge
from enums import MemoryType, get_memory_type_name
from utils.errors import (
    safe_tool_call,
    InvalidMemoryTypeError,
    InvalidAddressError,
    MesenMCPError
)


@safe_tool_call
def get_memory_range(
    bridge: MesenBridge,
    memory_type: Union[int, str],
    start_address: int,
    length: int,
    **kwargs
) -> Dict[str, Any]:
    """Read a range of memory

    Parameters:
        memory_type: Memory region to read from (int or string name)
                    Examples: 2 or "SnesWorkRam", 50 or "NesMemory"
        start_address: Starting address (decimal or hex)
        length: Number of bytes to read (max 4096 for safety)

    Returns:
        Dictionary with:
        - memory_type: str - Name of memory type
        - start_address: int - Starting address
        - length: int - Number of bytes read
        - data: str - Hex string of bytes (e.g., "01 02 FF FE")
        - data_bytes: list[int] - List of byte values [1, 2, 255, 254]
    """
    # Validate and convert memory type
    if isinstance(memory_type, str):
        # Try to convert string name to enum
        try:
            memory_type = MemoryType[memory_type]
        except KeyError:
            raise InvalidMemoryTypeError(f"Unknown memory type name: {memory_type}")
    else:
        try:
            memory_type = MemoryType(memory_type)
        except ValueError:
            raise InvalidMemoryTypeError(f"Invalid memory type value: {memory_type}")

    # Validate parameters
    if not isinstance(start_address, int) or start_address < 0:
        raise InvalidAddressError(f"Invalid start address: {start_address}")

    if not isinstance(length, int) or length <= 0:
        raise InvalidAddressError(f"Invalid length: {length}")

    # Enforce max length for safety
    MAX_LENGTH = 4096
    if length > MAX_LENGTH:
        raise InvalidAddressError(
            f"Length {length} exceeds maximum of {MAX_LENGTH} bytes. "
            "Use multiple requests for larger regions."
        )

    # Get memory size to validate address range
    mem_size = bridge.get_memory_size(memory_type)
    if mem_size == 0:
        raise InvalidMemoryTypeError(
            f"Memory type {memory_type.name} has size 0. "
            "This may mean no ROM is loaded or this memory type is not available."
        )

    if start_address >= mem_size:
        raise InvalidAddressError(
            f"Start address {hex(start_address)} is beyond memory size {hex(mem_size)}"
        )

    # Adjust length if it would go past end of memory
    if start_address + length > mem_size:
        length = mem_size - start_address

    # Setup GetMemoryValues function signature
    if not hasattr(bridge.dll, '_get_memory_values_setup'):
        bridge.dll.GetMemoryValues.argtypes = [
            ctypes.c_int32,                    # MemoryType
            ctypes.c_uint32,                   # Start address
            ctypes.c_uint32,                   # End address (inclusive)
            ctypes.POINTER(ctypes.c_uint8),   # Output buffer
        ]
        bridge.dll.GetMemoryValues.restype = None
        bridge.dll._get_memory_values_setup = True

    # Allocate buffer
    buffer = (ctypes.c_uint8 * length)()

    # Read memory
    bridge.dll.GetMemoryValues(
        memory_type,
        start_address,
        start_address + length - 1,  # End address is inclusive
        buffer
    )

    # Convert to list and hex string
    data_bytes = list(buffer)
    data_hex = " ".join(f"{b:02X}" for b in data_bytes)

    return {
        "memory_type": memory_type.name,
        "start_address": start_address,
        "length": length,
        "data": data_hex,
        "data_bytes": data_bytes,
    }


@safe_tool_call
def set_memory(
    bridge: MesenBridge,
    memory_type: Union[int, str],
    address: int,
    data: Union[str, List[int]],
    **kwargs
) -> Dict[str, Any]:
    """Write bytes to memory

    Parameters:
        memory_type: Memory region to write to (int or string name)
        address: Target address
        data: Bytes to write, either:
              - Hex string: "01 FF 42" or "01FF42"
              - List of ints: [1, 255, 66]

    Returns:
        Dictionary with:
        - memory_type: str - Name of memory type
        - address: int - Address written to
        - bytes_written: int - Number of bytes written
    """
    # Validate and convert memory type
    if isinstance(memory_type, str):
        try:
            memory_type = MemoryType[memory_type]
        except KeyError:
            raise InvalidMemoryTypeError(f"Unknown memory type name: {memory_type}")
    else:
        try:
            memory_type = MemoryType(memory_type)
        except ValueError:
            raise InvalidMemoryTypeError(f"Invalid memory type value: {memory_type}")

    # Validate address
    if not isinstance(address, int) or address < 0:
        raise InvalidAddressError(f"Invalid address: {address}")

    # Parse data
    if isinstance(data, str):
        # Remove spaces and convert hex string to bytes
        data = data.replace(" ", "").replace("0x", "")
        if len(data) % 2 != 0:
            raise MesenMCPError(f"Hex string must have even length: {data}")

        try:
            data_bytes = [int(data[i:i+2], 16) for i in range(0, len(data), 2)]
        except ValueError as e:
            raise MesenMCPError(f"Invalid hex string: {e}")

    elif isinstance(data, list):
        # Validate list of integers
        if not all(isinstance(b, int) and 0 <= b <= 255 for b in data):
            raise MesenMCPError("Data list must contain integers 0-255")
        data_bytes = data

    else:
        raise MesenMCPError(f"Data must be hex string or list of ints, got {type(data)}")

    # Check memory size
    mem_size = bridge.get_memory_size(memory_type)
    if address + len(data_bytes) > mem_size:
        raise InvalidAddressError(
            f"Write would exceed memory bounds (size: {hex(mem_size)})"
        )

    # Setup SetMemoryValues function signature
    if not hasattr(bridge.dll, '_set_memory_values_setup'):
        bridge.dll.SetMemoryValues.argtypes = [
            ctypes.c_int32,                    # MemoryType
            ctypes.c_uint32,                   # Address
            ctypes.POINTER(ctypes.c_uint8),   # Data buffer
            ctypes.c_int32,                    # Length
        ]
        bridge.dll.SetMemoryValues.restype = None
        bridge.dll._set_memory_values_setup = True

    # Create buffer
    buffer = (ctypes.c_uint8 * len(data_bytes))(*data_bytes)

    # Write memory
    bridge.dll.SetMemoryValues(
        memory_type,
        address,
        buffer,
        len(data_bytes)
    )

    return {
        "memory_type": memory_type.name,
        "address": address,
        "bytes_written": len(data_bytes),
    }
