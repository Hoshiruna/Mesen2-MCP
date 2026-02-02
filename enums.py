"""Enum mappings for Mesen2 debugger types

These enums map to the C++ enum values in Core/Shared/
"""

from enum import IntEnum


class CpuType(IntEnum):
    """CPU type identifiers"""
    Snes = 0
    Spc = 1
    NecDsp = 2
    Sa1 = 3
    Gsu = 4
    Cx4 = 5
    St018 = 6
    Gameboy = 7
    Nes = 8
    Pce = 9
    Sms = 10
    Gba = 11
    Ws = 12


class ConsoleType(IntEnum):
    """Console type identifiers"""
    Snes = 0
    Gameboy = 1
    Nes = 2
    PcEngine = 3
    Sms = 4
    Gba = 5
    Ws = 6


class MemoryType(IntEnum):
    """Memory region type identifiers

    Note: This is a large enum with 60+ values covering all systems.
    Only the most common ones are included here for now.
    """
    # SNES Memory types
    SnesMemory = 0
    SnesPrgRom = 1
    SnesWorkRam = 2
    SnesSaveRam = 3
    SnesVideoRam = 4
    SnesSpriteRam = 5
    SnesCgRam = 6
    SnesRegister = 7

    # SPC Memory types
    SpcMemory = 8
    SpcRam = 9
    SpcRom = 10
    SpcDspRegisters = 11

    # SA1 Memory types
    Sa1Memory = 12
    Sa1InternalRam = 13

    # NES Memory types
    NesMemory = 50
    NesPrgRom = 51
    NesInternalRam = 52
    NesWorkRam = 53
    NesSaveRam = 54
    NesChrRom = 55
    NesChrRam = 56
    NesNametableRam = 57
    NesSpriteRam = 58
    NesSecondarySpriteRam = 59
    NesPaletteRam = 60

    # Gameboy Memory types
    GbMemory = 70
    GbPrgRom = 71
    GbWorkRam = 72
    GbCartRam = 73
    GbVideoRam = 74
    GbSpriteRam = 75
    GbBootRom = 76

    # GBA Memory types
    GbaMemory = 90
    GbaPrgRom = 91
    GbaIntWorkRam = 92
    GbaExtWorkRam = 93
    GbaSaveRam = 94

    # Generic
    None_ = 255


class MemoryOperationType(IntEnum):
    """Memory operation type identifiers"""
    Read = 0
    Write = 1
    ExecOpCode = 2
    ExecOperand = 3
    DmaRead = 4
    DmaWrite = 5
    DummyRead = 6
    DummyWrite = 7
    PpuRenderingRead = 8
    Idle = 9


class BreakpointType(IntEnum):
    """Breakpoint type identifiers"""
    Execute = 0
    Read = 1
    Write = 2
    Forbid = 3


class StepType(IntEnum):
    """Step execution type identifiers"""
    Step = 0
    StepOut = 1
    StepOver = 2
    CpuCycleStep = 3
    PpuStep = 4
    PpuScanline = 5
    PpuFrame = 6
    SpecificScanline = 7
    RunToNmi = 8
    RunToIrq = 9
    StepBack = 10


class DebugEventType(IntEnum):
    """Debug event type identifiers"""
    Register = 0
    Nmi = 1
    Irq = 2
    Breakpoint = 3
    BgColorChange = 4
    SpriteZeroHit = 5
    DmcDmaRead = 6
    DmaRead = 7


# Helper function to get enum name
def get_cpu_type_name(cpu_type: int) -> str:
    """Get human-readable name for CPU type"""
    try:
        return CpuType(cpu_type).name
    except ValueError:
        return f"Unknown({cpu_type})"


def get_memory_type_name(memory_type: int) -> str:
    """Get human-readable name for memory type"""
    try:
        return MemoryType(memory_type).name
    except ValueError:
        return f"Unknown({memory_type})"


def get_console_type_name(console_type: int) -> str:
    """Get human-readable name for console type"""
    try:
        return ConsoleType(console_type).name
    except ValueError:
        return f"Unknown({console_type})"
