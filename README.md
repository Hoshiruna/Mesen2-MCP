# Mesen2 MCP Debugger Server

Python MCP (Model Context Protocol) server that exposes Mesen2's debugger API for AI-assisted debugging and analysis.

## What is This?

A production-ready MCP server that allows AI assistants (like Claude) to:
- Query CPU state, memory, and PPU registers
- Set breakpoints and control execution
- Stream real-time changes (trace, events, memory)
- Analyze game behavior and debug issues

**All 3 development phases complete** - 20 MCP tools, streaming support, full configuration system.

## Quick Start

### Prerequisites

- Python 3.8+
- Mesen2 emulator with MesenCore.dll
- A ROM loaded in Mesen2

### Installation

```bash
cd mcp_server
pip install -r requirements.txt
```

### Test Connection

```bash
python mcp_server.py --interactive
```

Try this command:

```json
{"method": "debugger_status", "params": {}}
```

### Start Server (for AI assistants)

```bash
python mcp_server.py
```

## Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide with examples and workflows (⭐ start here!)
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Solutions to common issues
- **[default_config.json](config/default_config.json)** - Configuration reference

## Features

### 20 MCP Tools Available

**Polling Tools (12)**:
- Status & State: `debugger_status`, `get_cpu_state`, `get_ppu_state`
- Memory Access: `get_memory_range`, `set_memory`
- Analysis: `get_disassembly`, `get_trace_tail`, `get_debug_events`
- Control: `set_breakpoints`, `step`, `resume`, `pause`

**Streaming Tools (8)**:
- Control: `start_streaming`, `stop_streaming`
- Subscriptions: `subscribe_trace`, `subscribe_events`, `subscribe_memory`, `unsubscribe_memory`
- Retrieval: `get_changes`, `get_streaming_status`

### Key Capabilities

- ✓ **Multi-Console Support**: SNES, NES, Gameboy
- ✓ **Real-Time Streaming**: 10 Hz background sampling with delta detection
- ✓ **Memory Safety**: Validated reads/writes with configurable limits
- ✓ **Thread-Safe**: Concurrent access with proper locking
- ✓ **Rate Limiting**: Exponential backoff to prevent overload
- ✓ **Production Ready**: Comprehensive tests, config system, and documentation

## Configuration

Create custom config (optional):

```json
{
    "streaming": {
        "polling_rate_hz": 20,
        "max_queue_size": 5000
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

Use it:

```bash
python mcp_server.py --config my_config.json
```

## AI Assistant Integration

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mesen-debugger": {
      "command": "python",
      "args": ["C:/path/to/Mesen2/mcp_server/mcp_server.py"]
    }
  }
}
```

### Example AI Prompts

- "The game crashes when I jump. Can you debug it?"
- "Find where the player's health is stored in RAM"
- "Profile this level and find performance bottlenecks"
- "Explain how the physics system works"

## Example Workflow

**Finding a bug**:

```json
// 1. Set breakpoint at suspected function
{"method": "set_breakpoints", "params": {
  "breakpoints": [{"type": "Execute", "address": 32768}]
}}

// 2. Resume execution
{"method": "resume", "params": {}}

// 3. When it breaks, check state
{"method": "get_cpu_state", "params": {}}

// 4. Get trace history
{"method": "get_trace_tail", "params": {"count": 100}}

// 5. Step through to find issue
{"method": "step", "params": {"count": 1}}
```

**Real-time monitoring**:

```json
// 1. Start streaming
{"method": "start_streaming", "params": {}}

// 2. Watch memory range (e.g., player position)
{"method": "subscribe_memory", "params": {
  "memory_type": "SnesWorkRam",
  "address": 256,
  "length": 16
}}

// 3. Resume game
{"method": "resume", "params": {}}

// 4. Get changes after a few seconds
{"method": "get_changes", "params": {"max_count": 100}}

// 5. Stop when done
{"method": "stop_streaming", "params": {}}
```

## Project Structure

```
mcp_server/
├── mcp_server.py              # Entry point
├── debug_bridge.py            # DLL interface (ctypes)
├── struct_defs.py             # C struct mappings
├── enums.py                   # Enum definitions
├── tools/                     # 20 MCP tool implementations
├── streaming/                 # Real-time change feeds
├── utils/                     # Config and error handling
├── tests/                     # 37 tests (all passing)
├── config/                    # Configuration
├── README.md                  # This file
├── USAGE.md                   # Detailed usage guide
└── TROUBLESHOOTING.md         # Problem solutions
```

## Testing

Run all tests:

```bash
# Struct validation
python tests/test_struct_sizes.py

# All tools (14 tests)
python tests/test_all_tools.py

# Streaming (10 tests)
python tests/test_streaming.py

# Stability (13 tests)
python tests/test_stability.py
```

## Platform Support

- **Windows**: Fully tested ✓
- **Linux**: Supported (requires SDL2)
- **macOS**: Supported (requires SDL2)

## Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review [USAGE.md](USAGE.md) for examples
- Test connection: `python debug_bridge.py`
- Run health check: See USAGE.md for health check examples

## Technical Details

- **Language**: Python 3.8+
- **Interface**: ctypes bindings to MesenCore.dll
- **Protocol**: MCP over JSON stdio
- **Threading**: Thread-safe with RLocks
- **Configuration**: JSON-based with defaults
- **Testing**: 37 tests covering all components

## License

Part of the Mesen2 ecosystem - GPL V3
