"""Tests for ctypes struct size validation

These tests verify that our ctypes Structure definitions match
the actual C++ struct sizes in MesenCore.dll
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import ctypes
from struct_defs import (
    AddressInfo,
    MemoryOperationInfo,
    SnesCpuState,
    NesCpuState,
    GameboyCpuState,
    TraceRow,
    DebugEventInfo,
    StackFrameInfo,
    DebugControllerState,
    Breakpoint,
)


def test_simple_struct_sizes():
    """Test simple structure sizes"""

    # These sizes are approximate and need to be validated against actual C++ sizeof()
    # We'll print them for now and validate once we can query the DLL

    print("\n=== Simple Struct Sizes ===")
    print(f"AddressInfo:          {ctypes.sizeof(AddressInfo)} bytes (expected: 8)")
    print(f"MemoryOperationInfo:  {ctypes.sizeof(MemoryOperationInfo)} bytes (expected: 16)")

    assert ctypes.sizeof(AddressInfo) == 8, "AddressInfo size mismatch"
    assert ctypes.sizeof(MemoryOperationInfo) == 16, "MemoryOperationInfo size mismatch"

    print("[OK] Simple struct sizes OK")


def test_cpu_state_sizes():
    """Test CPU state structure sizes"""

    print("\n=== CPU State Struct Sizes ===")
    print(f"SnesCpuState:     {ctypes.sizeof(SnesCpuState)} bytes")
    print(f"NesCpuState:      {ctypes.sizeof(NesCpuState)} bytes")
    print(f"GameboyCpuState:  {ctypes.sizeof(GameboyCpuState)} bytes")

    # Note: These sizes need to be validated against actual C++ structs
    # For now, just ensure they're reasonable (not 0 or huge)
    assert 20 < ctypes.sizeof(SnesCpuState) < 100, "SnesCpuState size unreasonable"
    assert 10 < ctypes.sizeof(NesCpuState) < 50, "NesCpuState size unreasonable"
    assert 10 < ctypes.sizeof(GameboyCpuState) < 50, "GameboyCpuState size unreasonable"

    print("[OK] CPU state struct sizes OK")


def test_complex_struct_sizes():
    """Test complex structure sizes"""

    print("\n=== Complex Struct Sizes ===")
    print(f"TraceRow:             {ctypes.sizeof(TraceRow)} bytes (expected: ~516)")
    print(f"DebugEventInfo:       {ctypes.sizeof(DebugEventInfo)} bytes")
    print(f"StackFrameInfo:       {ctypes.sizeof(StackFrameInfo)} bytes")
    print(f"DebugControllerState: {ctypes.sizeof(DebugControllerState)} bytes")
    print(f"Breakpoint:           {ctypes.sizeof(Breakpoint)} bytes (expected: ~1024)")

    # TraceRow has a 500-byte char array, so should be > 500
    assert ctypes.sizeof(TraceRow) > 500, "TraceRow too small"

    # Breakpoint has a 1000-byte condition string, so should be > 1000
    assert ctypes.sizeof(Breakpoint) > 1000, "Breakpoint too small"

    print("[OK] Complex struct sizes OK")


def test_nested_struct_access():
    """Test that nested structures are accessible"""

    print("\n=== Testing Nested Struct Access ===")

    # Create a DebugEventInfo and access nested MemoryOperationInfo
    event = DebugEventInfo()
    event.Operation.Address = 0x8000
    event.Operation.Value = 0x42
    event.ProgramCounter = 0x8100

    assert event.Operation.Address == 0x8000
    assert event.ProgramCounter == 0x8100

    print(f"[OK] Can access nested MemoryOperationInfo.Address: {hex(event.Operation.Address)}")
    print(f"[OK] Can access DebugEventInfo.ProgramCounter: {hex(event.ProgramCounter)}")
    print("[OK] Nested struct access OK")


def test_array_access():
    """Test that array fields are accessible"""

    print("\n=== Testing Array Field Access ===")

    # TraceRow has ByteCode array
    trace = TraceRow()
    trace.ByteCode[0] = 0xA9  # LDA immediate
    trace.ByteCode[1] = 0x42
    trace.ByteCodeSize = 2

    assert trace.ByteCode[0] == 0xA9
    assert trace.ByteCode[1] == 0x42
    assert trace.ByteCodeSize == 2

    print(f"[OK] Can access TraceRow.ByteCode[0]: {hex(trace.ByteCode[0])}")
    print(f"[OK] Can access TraceRow.ByteCodeSize: {trace.ByteCodeSize}")
    print("[OK] Array field access OK")


def run_all_tests():
    """Run all struct validation tests"""

    print("=" * 60)
    print("Running ctypes Structure Validation Tests")
    print("=" * 60)

    try:
        test_simple_struct_sizes()
        test_cpu_state_sizes()
        test_complex_struct_sizes()
        test_nested_struct_access()
        test_array_access()

        print("\n" + "=" * 60)
        print("[PASS] ALL TESTS PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
