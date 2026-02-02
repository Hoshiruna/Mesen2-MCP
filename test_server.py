"""Simple test script for MCP server"""

import json
from mcp_server import MCPServer

# Create server
print("Creating MCP server...")
server = MCPServer()

print(f"\nAvailable tools: {', '.join(server.tools.keys())}\n")

# Test 1: debugger_status
print("=" * 60)
print("Test 1: debugger_status")
print("=" * 60)
request = {"method": "debugger_status", "params": {}}
response = server.handle_request(request)
print(json.dumps(response, indent=2))

# Test 2: get_cpu_state (will fail if ROM not loaded, but that's okay)
print("\n" + "=" * 60)
print("Test 2: get_cpu_state")
print("=" * 60)
request = {"method": "get_cpu_state", "params": {}}
response = server.handle_request(request)
print(json.dumps(response, indent=2))

# Test 3: get_memory_range (will fail if ROM not loaded)
print("\n" + "=" * 60)
print("Test 3: get_memory_range")
print("=" * 60)
request = {
    "method": "get_memory_range",
    "params": {
        "memory_type": "SnesWorkRam",
        "start_address": 0,
        "length": 16
    }
}
response = server.handle_request(request)
print(json.dumps(response, indent=2))

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
