# Troubleshooting Guide

Common issues and solutions for the Mesen2 MCP Debugger Server.

## Common Issues

### Issue: "DLL not found" or "Failed to load MesenCore DLL"

**Cause**: MesenCore.dll not in PATH or wrong platform architecture.

**Solutions**:

1. **Check DLL exists**:

   ```bash
   # Windows
   dir ..\bin\win-x64\Release\MesenCore.dll

   # Linux
   ls ../bin/linux-x64/Release/libMesen.so

   # macOS
   ls ../bin/macos-x64/Release/libMesen.dylib
   ```

2. **Specify DLL path manually**:

   ```python
   from debug_bridge import MesenBridge
   bridge = MesenBridge(dll_path="C:/path/to/MesenCore.dll")
   ```

   Or via config file:

   ```json
   {
       "dll_path": "C:/absolute/path/to/MesenCore.dll"
   }
   ```

3. **Verify platform architecture matches**:
   - 64-bit DLL requires 64-bit Python
   - Check Python architecture: `python -c "import platform; print(platform.architecture())"`
   - Rebuild Mesen2 for your platform if needed

4. **Check DLL dependencies**:
   - Windows: Ensure Visual C++ Redistributable installed
   - Linux: Ensure SDL2 installed (`sudo apt-get install libsdl2-dev`)
   - macOS: Install SDL2 via Homebrew (`brew install sdl2`)

### Issue: "Debugger not initialized" or "IsDebuggerRunning() returns false"

**Cause**: Debugger not started or ROM not loaded.

**Solutions**:

1. **Load a ROM in Mesen first**:
   - Open Mesen2 emulator
   - Load a ROM file (File > Open)
   - Verify ROM is running

2. **Enable Debug Mode in Mesen settings**:
   - Tools > Preferences > Advanced
   - Check "Enable Debugger"

3. **Auto-initialize debugger** (in config):

   ```json
   {
       "auto_initialize_debugger": true
   }
   ```

4. **Manual initialization**:

   ```python
   bridge = MesenBridge()
   bridge.initialize_debugger()
   ```

### Issue: "Struct size mismatch" or "Access violation"

**Cause**: ctypes struct packing doesn't match C++ struct layout.

**Solutions**:

1. **Run struct validation tests**:

   ```bash
   cd mcp_server
   python tests/test_struct_sizes.py
   ```

2. **Check struct packing**:
   - All structs use `_pack_ = 1` for tight packing
   - Field order must match C++ exactly

3. **Reference implementation**:
   - C++ structs: `../Core/Debugger/DebugTypes.h`
   - C# marshaling: `../UI/Interop/DebugApi.cs` (rosetta stone)

4. **Update struct if needed**:
   - Edit `mcp_server/struct_defs.py`
   - Run validation tests to verify

### Issue: "Callback not firing" or "Notification not received"

**Cause**: Callback garbage collected or not registered correctly.

**Solutions**:

1. **Verify callback is registered**:

   ```python
   bridge = MesenBridge()
   def my_callback(event_type, data):
       print(f"Event: {event_type}")

   listener_id = bridge.register_notification_callback(my_callback)
   # Listener reference is now kept alive
   ```

2. **Check callback refs**:

   ```python
   # Should have entries
   print(f"Callback refs: {len(bridge._callback_refs)}")
   ```

3. **Don't let bridge go out of scope**:
   - Keep bridge instance alive for duration of callback usage

4. **Cleanup properly**:

   ```python
   # When done
   bridge.unregister_notification_callback()
   ```

### Issue: "Sampler consuming too much CPU"

**Cause**: Polling rate too high or no rate limiting.

**Solutions**:

1. **Reduce polling rate** (in config):

   ```json
   {
       "streaming": {
           "polling_rate_hz": 5
       }
   }
   ```

2. **Adjust rate limits**:

   ```json
   {
       "streaming": {
           "rate_limits": {
               "max_trace_lines_per_second": 500,
               "max_events_per_second": 50,
               "max_memory_changes_per_second": 25
           }
       }
   }
   ```

3. **Subscribe only to needed feeds**:
   - Don't subscribe to trace if you only need events
   - Unsubscribe from memory watches when done

4. **Check sampler stats**:

   ```python
   stats = sampler.get_stats()
   print(f"Total samples: {stats['total_samples']}")
   print(f"Queue size: {stats['queue_size']}")
   ```

### Issue: "Changes queue overflowing" or "Missing events"

**Cause**: LLM not consuming changes fast enough.

**Solutions**:

1. **Increase queue size** (in config):

   ```json
   {
       "streaming": {
           "max_queue_size": 5000
       }
   }
   ```

2. **Call `get_changes` more frequently**:

   ```json
   {"method": "get_changes", "params": {"max_count": 100}}
   ```

3. **Reduce subscription count**:
   - Only subscribe to feeds you actively need
   - Unsubscribe when analysis is done

4. **Check for backpressure**:

   ```python
   status = get_streaming_status(bridge)
   print(f"Queue size: {status['stats']['queue_size']}")
   ```

### Issue: "Memory reads returning garbage" or "Invalid data"

**Cause**: Reading invalid memory type or address.

**Solutions**:

1. **Check valid memory types**:

   ```json
   {"method": "debugger_status", "params": {}}
   ```

2. **Verify address is within bounds**:

   ```python
   from enums import MemoryType
   bridge = MesenBridge()

   # Get memory region size
   size = bridge.get_memory_size(MemoryType.SnesWorkRam)
   print(f"SNES Work RAM size: {size} bytes")

   # Ensure address < size
   ```

3. **Pause emulation for volatile memory**:
   - Some memory regions change rapidly
   - Pause emulation for consistent reads

   ```json
   {"method": "pause", "params": {}}
   {"method": "get_memory_range", "params": {...}}
   {"method": "resume", "params": {}}
   ```

4. **Respect max read size**:
   - Default limit: 4096 bytes
   - Adjust in config if needed:

   ```json
   {
       "tools": {
           "max_memory_read_size": 8192
       }
   }
   ```

### Issue: "Thread safety violations" or "Concurrent access errors"

**Cause**: Multiple threads accessing DLL without proper locking.

**Solutions**:

1. **Enable thread safety** (in config):

   ```json
   {
       "thread_safety": {
           "use_locks": true,
           "lock_timeout_seconds": 5.0
       }
   }
   ```

2. **Use safe_call wrapper**:

   ```python
   bridge = MesenBridge()
   result = bridge.safe_call(bridge.dll.IsDebuggerRunning)
   ```

3. **Limit concurrent calls**:

   ```json
   {
       "thread_safety": {
           "max_concurrent_calls": 5
       }
   }
   ```

4. **Run thread safety tests**:

   ```bash
   python tests/test_stability.py
   ```

### Issue: "Execution trace missing lines" or "Gaps in trace"

**Cause**: Trace buffer overflow or cursor tracking issue.

**Solutions**:

1. **Increase trace limit**:

   ```json
   {
       "tools": {
           "max_trace_lines": 5000
       }
   }
   ```

2. **Check cursor position**:

   ```python
   sampler = get_sampler(bridge)
   cursor_pos = sampler.cursor.get("trace", 0)
   print(f"Trace cursor: {cursor_pos}")
   ```

3. **Reset cursor if needed**:

   ```python
   sampler.cursor.reset()
   ```

4. **Use smaller poll windows**:

   ```json
   {"method": "subscribe_trace", "params": {"max_lines_per_poll": 50}}
   ```

## Platform-Specific Issues

### Windows

**Issue**: "DLL is blocked by Windows"

**Solution**:

1. Right-click on `MesenCore.dll`
2. Properties > General tab
3. Check "Unblock" at bottom
4. Click Apply

**Issue**: "Visual C++ Redistributable not installed"

**Solution**:

1. Download from Microsoft:
   - [VC++ 2015-2022 x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)
2. Install and restart

### Linux

**Issue**: "libSDL2.so not found"

**Solution**:

```bash
# Ubuntu/Debian
sudo apt-get install libsdl2-dev

# Fedora
sudo dnf install SDL2-devel

# Arch
sudo pacman -S sdl2
```

**Issue**: "Permission denied loading .so"

**Solution**:

```bash
chmod +x libMesen.so
```

### macOS

**Issue**: "Library not loaded: @rpath/libMesen.dylib"

**Solution**:

1. Install SDL2:

   ```bash
   brew install sdl2
   ```

2. Set library path:

   ```bash
   export DYLD_LIBRARY_PATH=/path/to/mesen/bin:$DYLD_LIBRARY_PATH
   ```

**Issue**: "Unsigned DLL blocked by security"

**Solution**:

1. System Preferences > Security & Privacy
2. Allow app to run (appears after first blocked attempt)

## Debugging Tips

### Enable Debug Logging

In config:

```json
{
    "logging": {
        "level": "DEBUG",
        "console": true,
        "file": "mcp_server_debug.log"
    }
}
```

### Run Health Check

```python
from debug_bridge import MesenBridge

bridge = MesenBridge()
health = bridge.health_check()

for key, value in health.items():
    status = "[OK]" if value else "[FAIL]"
    print(f"{status} {key}: {value}")
```

### Test Individual Components

```bash
# Test DLL loading
python debug_bridge.py

# Test struct sizes
python tests/test_struct_sizes.py

# Test all tools
python tests/test_all_tools.py

# Test streaming
python tests/test_streaming.py

# Test stability
python tests/test_stability.py
```

### Verify Configuration

```python
from utils.config import Config

config = Config()
print(config.config)  # Print entire config
```

### Check Sampler Stats

```python
from tools.streaming_tools import get_streaming_status

status = get_streaming_status(bridge)
print(f"Streaming: {status['streaming']}")
print(f"Stats: {status['stats']}")
```

## Getting Help

If you've tried the solutions above and still have issues:

1. **Check logs**: Set log level to DEBUG and review output
2. **Run all tests**: `pytest tests/` or run individual test files
3. **Verify versions**:
   - Python version: `python --version` (requires 3.8+)
   - Mesen version: Check in bridge output
   - Platform: Windows/Linux/macOS
4. **Open an issue** on GitHub with:
   - Full error message and stack trace
   - Platform and versions
   - Steps to reproduce
   - Relevant config settings
   - Output of health check and test runs

## Performance Tuning

### For High-Frequency Trace Capture

```json
{
    "streaming": {
        "polling_rate_hz": 20,
        "max_queue_size": 5000,
        "rate_limits": {
            "max_trace_lines_per_second": 5000
        }
    },
    "performance": {
        "prefetch_trace_lines": true
    }
}
```

### For Low-Latency Memory Watches

```json
{
    "streaming": {
        "polling_rate_hz": 30,
        "rate_limits": {
            "max_memory_changes_per_second": 100
        }
    }
}
```

### For Minimal CPU Usage

```json
{
    "streaming": {
        "polling_rate_hz": 2,
        "rate_limits": {
            "max_trace_lines_per_second": 100,
            "max_events_per_second": 20
        }
    }
}
```

## Known Limitations

1. **Debugger requires ROM loaded**: Most debugging functions require an active ROM
2. **Memory reads limited to 4KB**: Default safety limit (configurable)
3. **Streaming requires debugger initialized**: Background sampler needs debugger running
4. **Single emulator instance**: One MCP server per Mesen instance
5. **Platform-specific DLL names**: Must match platform (dll/so/dylib)

## Best Practices

1. **Always load ROM before debugging**
2. **Pause emulation for consistent memory reads**
3. **Unsubscribe from feeds when done**
4. **Use health checks before critical operations**
5. **Configure rate limits appropriate for your use case**
6. **Run tests after making configuration changes**
7. **Keep bridge instance alive while streaming**
8. **Clean up callbacks when done**
9. **Monitor queue size to avoid overflow**
10. **Use appropriate logging level for production**
