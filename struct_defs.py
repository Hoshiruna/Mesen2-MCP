"""ctypes Structure definitions for Mesen2 debugger types

These structures map to C++ structs in Core/Debugger/DebugTypes.h
Reference: UI/Interop/DebugApi.cs for correct field layouts
"""

import ctypes


# Simple structs (flat, no nesting)

class AddressInfo(ctypes.Structure):
    """Memory address with type information (8 bytes)"""
    _pack_ = 1
    _fields_ = [
        ("Address", ctypes.c_int32),
        ("Type", ctypes.c_int32),  # MemoryType enum
    ]


class MemoryOperationInfo(ctypes.Structure):
    """Memory operation details (16 bytes)"""
    _pack_ = 1
    _fields_ = [
        ("Address", ctypes.c_uint32),
        ("Value", ctypes.c_int32),
        ("Type", ctypes.c_int32),      # MemoryOperationType enum
        ("MemType", ctypes.c_int32),   # MemoryType enum
    ]


# SNES CPU State (simple, flat structure)

class SnesCpuState(ctypes.Structure):
    """SNES CPU register state

    Size should be approximately 40-50 bytes
    Reference: Core/SNES/SnesCpu.h and UI/Interop/SnesApi.cs
    """
    _pack_ = 1
    _fields_ = [
        ("CycleCount", ctypes.c_uint64),  # 8 bytes
        ("A", ctypes.c_uint16),            # Accumulator
        ("X", ctypes.c_uint16),            # X index register
        ("Y", ctypes.c_uint16),            # Y index register
        ("SP", ctypes.c_uint16),           # Stack pointer
        ("D", ctypes.c_uint16),            # Direct page register
        ("PC", ctypes.c_uint16),           # Program counter
        ("K", ctypes.c_uint8),             # Program bank register
        ("DBR", ctypes.c_uint8),           # Data bank register
        ("PS", ctypes.c_uint8),            # Processor status flags
        ("EmulationMode", ctypes.c_bool),  # 6502 emulation mode
        ("NmiFlagCounter", ctypes.c_uint8),
        ("IrqLock", ctypes.c_bool),
        ("NeedNmi", ctypes.c_bool),
        ("IrqSource", ctypes.c_uint8),
        ("PrevIrqSource", ctypes.c_uint8),
        ("StopState", ctypes.c_uint8),     # SnesCpuStopState enum
    ]


# Trace structures

class TraceRow(ctypes.Structure):
    """Execution trace line (approximately 516 bytes)

    Contains instruction info and formatted log output
    """
    _pack_ = 1
    _fields_ = [
        ("ProgramCounter", ctypes.c_uint32),
        ("Type", ctypes.c_uint8),          # CpuType enum
        ("ByteCode", ctypes.c_uint8 * 8),  # Instruction bytes
        ("ByteCodeSize", ctypes.c_uint8),
        ("LogSize", ctypes.c_uint32),
        ("LogOutput", ctypes.c_char * 500),  # Formatted trace line
    ]


# Debug event structures (nested)

class DebugEventInfo(ctypes.Structure):
    """Debug event information (nested structure)

    Size approximately 64+ bytes
    Reference: Core/Debugger/DebugTypes.h
    """
    _pack_ = 1
    _fields_ = [
        ("Operation", MemoryOperationInfo),  # Nested struct (16 bytes)
        ("Type", ctypes.c_int32),            # DebugEventType enum
        ("ProgramCounter", ctypes.c_uint32),
        ("Scanline", ctypes.c_int16),
        ("Cycle", ctypes.c_uint16),
        ("BreakpointId", ctypes.c_int16),
        ("DmaChannel", ctypes.c_int8),
        ("_padding1", ctypes.c_uint8 * 1),   # Alignment padding
        # Note: Full struct has more fields (DmaChannelInfo, TargetMemory, etc.)
        # but these are the most critical ones for basic functionality
    ]


# Stack frame and callstack structures

class StackFrameInfo(ctypes.Structure):
    """Call stack frame information

    Reference: Core/Debugger/CallstackManager.h
    """
    _pack_ = 1
    _fields_ = [
        ("Source", ctypes.c_uint32),
        ("AbsSource", AddressInfo),           # Nested (8 bytes)
        ("Target", ctypes.c_uint32),
        ("AbsTarget", AddressInfo),           # Nested (8 bytes)
        ("Return", ctypes.c_uint32),
        ("ReturnStackPointer", ctypes.c_uint32),
        ("AbsReturn", AddressInfo),           # Nested (8 bytes)
        ("Flags", ctypes.c_uint8),            # StackFrameFlags enum
    ]


# Controller state (simple)

class DebugControllerState(ctypes.Structure):
    """Debug controller input override state

    Simple structure with boolean flags for each button
    """
    _pack_ = 1
    _fields_ = [
        # SNES buttons
        ("A", ctypes.c_bool),
        ("B", ctypes.c_bool),
        ("X", ctypes.c_bool),
        ("Y", ctypes.c_bool),
        ("L", ctypes.c_bool),
        ("R", ctypes.c_bool),
        # D-pad (alternative names for same buttons)
        ("Up", ctypes.c_bool),
        ("Down", ctypes.c_bool),
        ("Left", ctypes.c_bool),
        ("Right", ctypes.c_bool),
        # System buttons
        ("Select", ctypes.c_bool),
        ("Start", ctypes.c_bool),
    ]


# Breakpoint structure (complex due to condition string)

class Breakpoint(ctypes.Structure):
    """Breakpoint configuration

    Reference: Core/Debugger/Breakpoint.h
    Note: Simplified version - full struct has private implementation details
    """
    _pack_ = 1
    _fields_ = [
        ("Id", ctypes.c_uint32),
        ("CpuType", ctypes.c_uint8),          # CpuType enum
        ("MemoryType", ctypes.c_int32),       # MemoryType enum
        ("Type", ctypes.c_uint8),             # BreakpointType enum
        ("StartAddr", ctypes.c_int32),
        ("EndAddr", ctypes.c_int32),
        ("Enabled", ctypes.c_bool),
        ("MarkEvent", ctypes.c_bool),
        ("IgnoreDummyOperations", ctypes.c_bool),
        ("_padding1", ctypes.c_uint8 * 1),    # Alignment
        ("Condition", ctypes.c_char * 1000),  # Expression string
    ]


# NES-specific structures (for multi-console support)

class NesCpuState(ctypes.Structure):
    """NES CPU register state

    Reference: Core/NES/NesCpu.h
    """
    _pack_ = 1
    _fields_ = [
        ("CycleCount", ctypes.c_uint64),
        ("PC", ctypes.c_uint16),          # Program counter
        ("SP", ctypes.c_uint8),           # Stack pointer
        ("A", ctypes.c_uint8),            # Accumulator
        ("X", ctypes.c_uint8),            # X register
        ("Y", ctypes.c_uint8),            # Y register
        ("PS", ctypes.c_uint8),           # Processor status
        ("IRQFlag", ctypes.c_uint8),
        ("NMIFlag", ctypes.c_bool),
        ("_padding1", ctypes.c_uint8 * 2),  # Alignment
    ]


# Gameboy-specific structures

class GameboyCpuState(ctypes.Structure):
    """Gameboy CPU register state

    Reference: Core/Gameboy/GbCpu.h
    """
    _pack_ = 1
    _fields_ = [
        ("CycleCount", ctypes.c_uint64),
        ("PC", ctypes.c_uint16),
        ("SP", ctypes.c_uint16),
        ("A", ctypes.c_uint8),
        ("Flags", ctypes.c_uint8),
        ("B", ctypes.c_uint8),
        ("C", ctypes.c_uint8),
        ("D", ctypes.c_uint8),
        ("E", ctypes.c_uint8),
        ("H", ctypes.c_uint8),
        ("L", ctypes.c_uint8),
        ("IME", ctypes.c_bool),           # Interrupt master enable
        ("Halted", ctypes.c_bool),
        ("_padding1", ctypes.c_uint8 * 2),
    ]


# Helper functions

def print_struct_sizes():
    """Print sizes of all defined structures for validation"""
    structs = [
        ("AddressInfo", AddressInfo),
        ("MemoryOperationInfo", MemoryOperationInfo),
        ("SnesCpuState", SnesCpuState),
        ("NesCpuState", NesCpuState),
        ("GameboyCpuState", GameboyCpuState),
        ("TraceRow", TraceRow),
        ("DebugEventInfo", DebugEventInfo),
        ("StackFrameInfo", StackFrameInfo),
        ("DebugControllerState", DebugControllerState),
        ("Breakpoint", Breakpoint),
    ]

    print("ctypes Structure Sizes:")
    print("-" * 40)
    for name, struct_class in structs:
        size = ctypes.sizeof(struct_class)
        print(f"{name:30s} {size:4d} bytes")


if __name__ == "__main__":
    print_struct_sizes()
