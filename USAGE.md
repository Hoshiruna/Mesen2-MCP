# Mesen2 MCP Debugger Server - Usage Guide

A practical guide to using the Mesen2 MCP Debugger Server for AI-assisted debugging and analysis.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Common Workflows](#common-workflows)
- [Tool Reference](#tool-reference)
- [Configuration](#configuration)
- [Examples](#examples)

## Quick Start

### Prerequisites

1. **Mesen2 emulator** installed and compiled
2. **Python 3.8+** installed
3. **MesenCore.dll** accessible in one of these locations:
   - `../bin/win-x64/Release/MesenCore.dll`
   - Current directory
   - System PATH

### Installation

```bash
cd mcp_server
pip install -r requirements.txt
```

### Starting the Server

**Interactive mode** (for testing):

```bash
python mcp_server.py --interactive
```

**MCP mode** (for AI assistants):

```bash
python mcp_server.py
```

### First Test

In interactive mode, try:

```json
{"method": "debugger_status", "params": {}}
```

Expected response:

```json
{
  "success": true,
  "data": {
    "debugger_running": false,
    "emulation_running": false,
    "execution_stopped": false,
    "cpu_type": "Snes"
  },
  "timestamp": "2026-02-02T12:34:56Z"
}
```

## Basic Usage

### Loading a ROM

1. **Open Mesen2 emulator**
2. **Load a ROM** (File > Open)
3. **Enable debugger** (Tools > Debugger or press F7)
4. **Start MCP server** in another terminal

### Checking Status

Always start by checking the debugger status:

```json
{"method": "debugger_status", "params": {}}
```

This returns:
- Is debugger running?
- Is emulation running?
- Is execution stopped (at breakpoint)?
- Current console type (SNES/NES/Gameboy)

### Reading CPU State

Get current CPU registers and flags:

```json
{"method": "get_cpu_state", "params": {}}
```

Returns:

```json
{
  "cycle_count": 12345678,
  "pc": 32768,
  "registers": {
    "a": 66,
    "x": 16,
    "y": 32,
    "sp": 511
  },
  "flags": {
    "carry": false,
    "zero": true,
    "negative": false
  }
}
```

### Reading Memory

Read a range of memory (up to 4KB):

```json
{
  "method": "get_memory_range",
  "params": {
    "memory_type": "SnesWorkRam",
    "start_address": 32768,
    "length": 256
  }
}
```

Returns hex bytes: `00 FF 42 00 ...`

## Common Workflows

### Workflow 1: Analyzing a Bug

**Scenario**: Game crashes when entering a specific room.

1. **Load the ROM and navigate to just before the crash**

2. **Set a breakpoint** at the suspected function:

   ```json
   {
     "method": "set_breakpoints",
     "params": {
       "breakpoints": [
         {
           "type": "Execute",
           "address": 32768,
           "enabled": true
         }
       ]
     }
   }
   ```

3. **Resume execution**:

   ```json
   {"method": "resume", "params": {}}
   ```

4. **When breakpoint hits, check CPU state**:

   ```json
   {"method": "get_cpu_state", "params": {}}
   ```

5. **Get execution trace** (last 100 instructions):

   ```json
   {
     "method": "get_trace_tail",
     "params": {
       "count": 100,
       "offset": 0
     }
   }
   ```

6. **Step through instructions** to find the bug:

   ```json
   {"method": "step", "params": {"count": 1}}
   ```

7. **Check memory at each step**:

   ```json
   {
     "method": "get_memory_range",
     "params": {
       "memory_type": "SnesWorkRam",
       "start_address": 32768,
       "length": 16
     }
   }
   ```

### Workflow 2: Monitoring Real-Time Behavior

**Scenario**: Watch how variables change during gameplay.

1. **Start streaming**:

   ```json
   {"method": "start_streaming", "params": {}}
   ```

2. **Subscribe to memory changes** (e.g., player health at $7E0100):

   ```json
   {
     "method": "subscribe_memory",
     "params": {
       "memory_type": "SnesWorkRam",
       "address": 256,
       "length": 16
     }
   }
   ```

3. **Subscribe to debug events**:

   ```json
   {"method": "subscribe_events", "params": {}}
   ```

4. **Resume emulation**:

   ```json
   {"method": "resume", "params": {}}
   ```

5. **Let the game run for a few seconds**

6. **Retrieve accumulated changes**:

   ```json
   {
     "method": "get_changes",
     "params": {
       "max_count": 100
     }
   }
   ```

   Returns changes like:

   ```json
   {
     "change_count": 42,
     "changes": [
       {
         "type": "memory_delta",
         "memory_type": "SnesWorkRam",
         "address": 256,
         "old_data": [100, 0, 0, 0],
         "new_data": [95, 0, 0, 0],
         "timestamp": 1738502096.123
       }
     ]
   }
   ```

7. **Stop streaming when done**:

   ```json
   {"method": "stop_streaming", "params": {}}
   ```

### Workflow 3: Performance Analysis

**Scenario**: Find CPU hotspots in game logic.

1. **Start streaming with trace enabled**:

   ```json
   {"method": "start_streaming", "params": {}}
   {"method": "subscribe_trace", "params": {"max_lines_per_poll": 1000}}
   ```

2. **Resume emulation for analysis period**:

   ```json
   {"method": "resume", "params": {}}
   ```

3. **Wait 5-10 seconds** to collect trace data

4. **Pause emulation**:

   ```json
   {"method": "pause", "params": {}}
   ```

5. **Retrieve all trace changes**:

   ```json
   {
     "method": "get_changes",
     "params": {
       "max_count": 1000
     }
   }
   ```

6. **Analyze trace** (in your AI assistant):
   - Count instruction frequency
   - Identify loops (repeated PC values)
   - Find longest instruction sequences

7. **Set breakpoints on hot functions**:

   ```json
   {
     "method": "set_breakpoints",
     "params": {
       "breakpoints": [
         {"type": "Execute", "address": 32800, "enabled": true},
         {"type": "Execute", "address": 33024, "enabled": true}
       ]
     }
   }
   ```

### Workflow 4: Memory Corruption Hunt

**Scenario**: Something is overwriting important data.

1. **Find the memory address being corrupted** (e.g., 0x7E1000)

2. **Set a write breakpoint**:

   ```json
   {
     "method": "set_breakpoints",
     "params": {
       "breakpoints": [
         {
           "type": "Write",
           "address": 4096,
           "memory_type": "SnesWorkRam",
           "enabled": true
         }
       ]
     }
   }
   ```

3. **Resume until breakpoint**:

   ```json
   {"method": "resume", "params": {}}
   ```

4. **When breakpoint hits, get the callstack** (via debug events):

   ```json
   {"method": "get_debug_events", "params": {"max_count": 100}}
   ```

5. **Inspect the instruction that wrote**:

   ```json
   {"method": "get_cpu_state", "params": {}}
   {"method": "get_disassembly", "params": {"line_count": 20}}
   ```

6. **Check surrounding memory**:

   ```json
   {
     "method": "get_memory_range",
     "params": {
       "memory_type": "SnesWorkRam",
       "start_address": 4080,
       "length": 32
     }
   }
   ```

## Tool Reference

### Status & Query Tools

#### `debugger_status`

Check debugger and emulator state.

```json
{"method": "debugger_status", "params": {}}
```

**Returns**: debugger_running, emulation_running, execution_stopped, cpu_type, rom_name

#### `get_cpu_state`

Get CPU registers and flags.

```json
{
  "method": "get_cpu_state",
  "params": {
    "cpu_type": "Snes"  // Optional: Snes, Nes, Gameboy
  }
}
```

**Returns**: cycle_count, pc, registers (a/x/y/sp), flags (carry/zero/negative/etc)

#### `get_ppu_state`

Get graphics chip state.

```json
{"method": "get_ppu_state", "params": {}}
```

**Returns**: scanline, cycle, frame_count, vblank, brightness

### Memory Tools

#### `get_memory_range`

Read memory with validation (max 4KB).

```json
{
  "method": "get_memory_range",
  "params": {
    "memory_type": "SnesWorkRam",  // See memory types below
    "start_address": 0,
    "length": 256
  }
}
```

**Memory types**: `SnesMemory`, `SnesWorkRam`, `SnesSaveRam`, `SnesPrgRom`, `SnesVideoRam`, etc.

#### `set_memory`

Write bytes to memory.

```json
{
  "method": "set_memory",
  "params": {
    "memory_type": "SnesWorkRam",
    "address": 256,
    "data": "FF 00 42"  // Hex string
  }
}
```

### Analysis Tools

#### `get_disassembly`

Disassemble code around an address.

```json
{
  "method": "get_disassembly",
  "params": {
    "address": 32768,     // Optional: defaults to current PC
    "line_count": 20,     // Optional: default 20
    "line_offset": -10    // Optional: default -10 (10 lines before)
  }
}
```

#### `get_trace_tail`

Get recent execution trace.

```json
{
  "method": "get_trace_tail",
  "params": {
    "count": 100,  // Default 100, max 1000
    "offset": 0    // Default 0 (most recent)
  }
}
```

**Returns**: List of executed instructions with PC, bytes, and disassembly.

#### `get_debug_events`

Get debug events (breakpoints, IRQs, NMIs).

```json
{
  "method": "get_debug_events",
  "params": {
    "max_count": 100  // Default 100, max 1000
  }
}
```

**Returns**: List of events with type, PC, scanline, cycle.

### Control Tools

#### `set_breakpoints`

Configure breakpoints.

```json
{
  "method": "set_breakpoints",
  "params": {
    "breakpoints": [
      {
        "type": "Execute",  // Execute, Read, Write, Forbid
        "address": 32768,
        "enabled": true,
        "condition": "",           // Optional expression
        "end_address": 32768      // Optional for range
      }
    ]
  }
}
```

#### `step`

Step execution by instruction/scanline/frame.

```json
{
  "method": "step",
  "params": {
    "count": 1,           // Default 1
    "step_type": "Step"   // Step, StepOver, StepOut, PpuStep, PpuScanline, PpuFrame
  }
}
```

#### `resume`

Resume from breakpoint.

```json
{"method": "resume", "params": {}}
```

#### `pause`

Pause emulation.

```json
{"method": "pause", "params": {}}
```

### Streaming Tools

#### `start_streaming`

Start background sampler (10 Hz polling).

```json
{"method": "start_streaming", "params": {}}
```

#### `subscribe_trace`

Subscribe to execution trace changes.

```json
{
  "method": "subscribe_trace",
  "params": {
    "max_lines_per_poll": 100  // Optional: default 100
  }
}
```

#### `subscribe_events`

Subscribe to debug event changes.

```json
{"method": "subscribe_events", "params": {}}
```

#### `subscribe_memory`

Subscribe to memory range changes (max 256 bytes).

```json
{
  "method": "subscribe_memory",
  "params": {
    "memory_type": "SnesWorkRam",
    "address": 256,
    "length": 16
  }
}
```

#### `unsubscribe_memory`

Unsubscribe from memory watch.

```json
{
  "method": "unsubscribe_memory",
  "params": {
    "address": 256
  }
}
```

#### `get_changes`

Get accumulated changes from queue.

```json
{
  "method": "get_changes",
  "params": {
    "max_count": 100  // Default 100, max 1000
  }
}
```

**Returns**: List of change deltas (trace_delta, events_delta, memory_delta).

#### `get_streaming_status`

Get sampler status and statistics.

```json
{"method": "get_streaming_status", "params": {}}
```

#### `stop_streaming`

Stop background sampler.

```json
{"method": "stop_streaming", "params": {}}
```

## Configuration

### Custom Configuration

Create `my_config.json`:

```json
{
    "streaming": {
        "polling_rate_hz": 20,
        "max_queue_size": 5000,
        "rate_limits": {
            "max_trace_lines_per_second": 2000
        }
    },
    "tools": {
        "max_memory_read_size": 8192
    },
    "logging": {
        "level": "DEBUG",
        "file": "debug.log"
    }
}
```

Start server with custom config:

```bash
python mcp_server.py --config my_config.json
```

### Important Settings

**Increase streaming performance**:

```json
{
    "streaming": {
        "polling_rate_hz": 30,
        "rate_limits": {
            "max_trace_lines_per_second": 5000
        }
    }
}
```

**Reduce CPU usage**:

```json
{
    "streaming": {
        "polling_rate_hz": 5,
        "rate_limits": {
            "max_trace_lines_per_second": 500
        }
    }
}
```

**Increase memory read limit**:

```json
{
    "tools": {
        "max_memory_read_size": 16384
    }
}
```

## Examples

### Example 1: Find Player Health Address

```json
// 1. Pause game when health is full
{"method": "pause", "params": {}}

// 2. Search Work RAM for value 100 (full health)
{"method": "get_memory_range", "params": {
  "memory_type": "SnesWorkRam",
  "start_address": 0,
  "length": 4096
}}

// Look for pattern "64" (100 in hex) in results

// 3. Take damage in game

// 4. Search again for new value (e.g., 95)
{"method": "get_memory_range", "params": {
  "memory_type": "SnesWorkRam",
  "start_address": 0,
  "length": 4096
}}

// 5. Compare results to find address that changed from 100 to 95
// Found at address 0x7E0100!

// 6. Set write breakpoint to find who modifies it
{"method": "set_breakpoints", "params": {
  "breakpoints": [{
    "type": "Write",
    "address": 256
  }]
}}

// 7. Resume and take damage
{"method": "resume", "params": {}}

// 8. When breakpoint hits, check the writer
{"method": "get_cpu_state", "params": {}}
{"method": "get_disassembly", "params": {"line_count": 10}}
```

### Example 2: Monitor Frame Rate

```json
// 1. Start streaming with events
{"method": "start_streaming", "params": {}}
{"method": "subscribe_events", "params": {}}

// 2. Resume emulation
{"method": "resume", "params": {}}

// 3. Wait 5 seconds

// 4. Get events
{"method": "get_changes", "params": {"max_count": 1000}}

// 5. Count NMI events (one per frame)
// Analyze: events.filter(e => e.type === "Nmi").length / 5 seconds = FPS

// 6. Stop streaming
{"method": "stop_streaming", "params": {}}
```

### Example 3: Dump Sprite Table

```json
// SNES sprite table is at $0000-$021F in PPU OAM

// 1. Pause emulation
{"method": "pause", "params": {}}

// 2. Read sprite table (544 bytes)
{"method": "get_memory_range", "params": {
  "memory_type": "SnesSpriteRam",
  "start_address": 0,
  "length": 544
}}

// 3. Parse sprite data (4 bytes per sprite)
// Byte 0: X position
// Byte 1: Y position
// Byte 2: Tile number
// Byte 3: Attributes (palette, priority, flip)
```

## Tips and Best Practices

### Performance Tips

1. **Pause emulation** before reading large memory regions
2. **Unsubscribe** from streams when analysis is done
3. **Limit trace collection** to specific time windows
4. **Use breakpoints** instead of polling for one-time events

### Debugging Tips

1. **Start with debugger_status** to verify connection
2. **Use interactive mode** for experimenting
3. **Check TROUBLESHOOTING.md** for common issues
4. **Enable debug logging** when diagnosing problems

### Safety Tips

1. **Don't write to ROM** - use `SnesWorkRam` or `SnesSaveRam` only
2. **Respect memory limits** - max 4KB per read (default)
3. **Avoid infinite loops** - set breakpoints with conditions
4. **Save state first** - before making memory modifications

## Integration with AI Assistants

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mesen-debugger": {
      "command": "python",
      "args": ["d:/Mesen2-MCP/mcp_server/mcp_server.py"],
      "cwd": "d:/Mesen2-MCP/mcp_server"
    }
  }
}
```

### Example AI Prompts

**For bug analysis**:
> "The game crashes when I press the jump button. Can you help me debug it? Set breakpoints on button handling code and analyze what happens."

**For performance**:
> "This level runs slowly. Can you profile the code and find the bottleneck?"

**For reverse engineering**:
> "I want to understand how the physics system works. Can you trace the player movement code and explain it?"

**For memory hunting**:
> "Find where the player's position is stored in RAM and monitor how it changes."

## Getting Help

- **Documentation**: See [README.md](README.md) for technical details
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for solutions
- **Issues**: Report bugs at GitHub issues
- **Tests**: Run `python tests/test_all_tools.py` to verify setup

## Next Steps

1. **Try interactive mode**: Get familiar with tools
2. **Load your ROM**: Test with real games
3. **Run examples**: Try the workflows above
4. **Customize config**: Tune for your use case
5. **Integrate with AI**: Add to Claude Desktop or other assistants

Happy debugging! 🎮
