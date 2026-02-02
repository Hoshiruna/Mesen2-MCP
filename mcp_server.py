"""Mesen2 MCP (Model Context Protocol) Server

This server exposes Mesen2's debugger functionality via the MCP protocol,
allowing LLMs to query and control the emulator for debugging assistance.
"""

import json
import sys
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from debug_bridge import MesenBridge
from utils.errors import MesenMCPError


class MCPServer:
    """MCP server for Mesen2 debugger"""

    def __init__(self, dll_path: Optional[str] = None):
        """Initialize MCP server

        Args:
            dll_path: Optional path to MesenCore.dll
        """
        self.bridge = MesenBridge(dll_path)
        self.tools = {}
        self._register_tools()

    def _register_tools(self):
        """Register all available MCP tools"""
        # Import tools here to avoid circular dependencies
        from tools.debugger_status import debugger_status
        from tools.cpu_state import get_cpu_state
        from tools.ppu_state import get_ppu_state
        from tools.memory import get_memory_range, set_memory
        from tools.disassembly import get_disassembly
        from tools.trace import get_trace_tail
        from tools.events import get_debug_events
        from tools.breakpoints import set_breakpoints
        from tools.execution import step, resume, pause
        from tools.streaming_tools import (
            start_streaming, stop_streaming,
            subscribe_trace, subscribe_events, subscribe_memory, unsubscribe_memory,
            get_changes, get_streaming_status
        )

        self.tools = {
            # Phase 1: Polling Tools
            "debugger_status": debugger_status,
            "get_cpu_state": get_cpu_state,
            "get_ppu_state": get_ppu_state,
            "get_memory_range": get_memory_range,
            "set_memory": set_memory,
            "get_disassembly": get_disassembly,
            "get_trace_tail": get_trace_tail,
            "get_debug_events": get_debug_events,
            "set_breakpoints": set_breakpoints,
            "step": step,
            "resume": resume,
            "pause": pause,

            # Phase 2: Streaming Tools
            "start_streaming": start_streaming,
            "stop_streaming": stop_streaming,
            "subscribe_trace": subscribe_trace,
            "subscribe_events": subscribe_events,
            "subscribe_memory": subscribe_memory,
            "unsubscribe_memory": unsubscribe_memory,
            "get_changes": get_changes,
            "get_streaming_status": get_streaming_status,
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a single MCP tool request

        Args:
            request: MCP request dict with 'method' and 'params'

        Returns:
            MCP response dict with 'success', 'data', and optional 'error'
        """
        method = request.get("method")
        params = request.get("params", {})

        # Validate method
        if not method:
            return self._error_response("Missing 'method' field")

        if method not in self.tools:
            return self._error_response(f"Unknown tool: {method}")

        # Execute tool
        try:
            result = self.tools[method](self.bridge, **params)
            return self._success_response(result)

        except MesenMCPError as e:
            return self._error_response(str(e))

        except Exception as e:
            return self._error_response(f"Unexpected error: {e}")

    def _success_response(self, data: Any) -> Dict[str, Any]:
        """Create a success response

        Args:
            data: Tool result data

        Returns:
            Success response dict
        """
        return {
            "success": True,
            "data": data,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

    def _error_response(self, error: str) -> Dict[str, Any]:
        """Create an error response

        Args:
            error: Error message

        Returns:
            Error response dict
        """
        return {
            "success": False,
            "error": error,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }

    def run(self):
        """Run the MCP server (stdio mode)

        Reads JSON requests from stdin, processes them, and writes JSON responses to stdout.
        """
        print("[MCP Server] Starting Mesen2 MCP Debugger Server", file=sys.stderr)
        print(f"[MCP Server] Bridge initialized successfully", file=sys.stderr)
        print(f"[MCP Server] {len(self.tools)} tools available", file=sys.stderr)
        print(f"[MCP Server] Waiting for requests on stdin...", file=sys.stderr)

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                # Parse request
                request = json.loads(line)

                # Handle request
                response = self.handle_request(request)

                # Send response
                print(json.dumps(response), flush=True)

            except json.JSONDecodeError as e:
                # Invalid JSON
                error_response = self._error_response(f"Invalid JSON: {e}")
                print(json.dumps(error_response), flush=True)

            except Exception as e:
                # Unexpected error
                error_response = self._error_response(f"Server error: {e}")
                print(json.dumps(error_response), flush=True)

    def run_interactive(self):
        """Run in interactive mode for testing

        Allows manual testing by typing JSON requests
        """
        print("=" * 60)
        print("Mesen2 MCP Server - Interactive Mode")
        print("=" * 60)
        print(f"Bridge connected: Mesen version {self.bridge.dll.GetMesenVersion()}")
        print(f"Available tools: {', '.join(self.tools.keys())}")
        print("\nEnter JSON requests (one per line), or 'quit' to exit")
        print("Example: {\"method\": \"debugger_status\", \"params\": {}}")
        print("=" * 60)

        while True:
            try:
                line = input("\n> ").strip()

                if line.lower() in ('quit', 'exit', 'q'):
                    print("Goodbye!")
                    break

                if not line:
                    continue

                # Parse and handle request
                request = json.loads(line)
                response = self.handle_request(request)

                # Pretty print response
                print(json.dumps(response, indent=2))

            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

            except Exception as e:
                print(f"Error: {e}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Mesen2 MCP Debugger Server")
    parser.add_argument(
        "--dll-path",
        type=str,
        help="Path to MesenCore.dll (optional, will search automatically)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode for testing"
    )

    args = parser.parse_args()

    try:
        server = MCPServer(dll_path=args.dll_path)

        if args.interactive:
            server.run_interactive()
        else:
            server.run()

    except Exception as e:
        print(f"[FAIL] Failed to start server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
