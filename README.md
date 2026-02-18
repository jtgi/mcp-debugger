# MCP Debugger

Debug, inspect, and mock MCP servers. Like webhook.site but for MCP.

<img width="1430" height="1098" alt="CleanShot 2026-02-17 at 17 52 46@2x" src="https://github.com/user-attachments/assets/1209b66d-cacd-4db1-9421-e140686b51de" />

## Quick Start

```bash
# Run from git (no install needed)
uvx --from git+https://github.com/jtgi/mcp-debugger mcp-debugger

# Or clone and run
git clone https://github.com/jtgi/mcp-debugger
cd mcp-debugger
uv run mcp-debugger
```

## Usage

```bash
mcp-debugger                                    # Run on localhost:8765
mcp-debugger --port 9000                        # Custom port
mcp-debugger --proxy https://your-mcp-server/mcp # Proxy to upstream server
mcp-debugger --ngrok                            # Expose via ngrok tunnel
mcp-debugger --ngrok-domain your.ngrok-free.app # Use a custom ngrok domain
NGROK_DOMAIN=your.ngrok-free.app mcp-debugger   # Or via env var
```

### Example

```
$ export NGROK_DOMAIN="slightly-divine-dove.ngrok-free.app"
$ uvx --from git+https://github.com/jtgi/mcp-debugger mcp-debugger

  MCP Toolbelt
  ────────────────────────────────────
  Local:    http://127.0.0.1:8765
  MCP:      http://127.0.0.1:8765/mcp
  Public:   https://slightly-divine-dove.ngrok-free.app
  MCP:      https://slightly-divine-dove.ngrok-free.app/mcp
  ────────────────────────────────────

[15:24:01] INCOMING   initialize
{
  "protocolVersion": "2025-03-26",
  "capabilities": {},
  "clientInfo": {
    "name": "mcp",
    "version": "0.1.0"
  }
}
[15:24:01] OUTGOING   initialize
{
  "protocolVersion": "2024-11-05",
  "capabilities": {
    "tools": {}
  },
  "serverInfo": {
    "name": "mcp-toolbelt",
    "version": "0.1.0"
  }
}
[15:24:02] INCOMING   notifications/initialized
[15:24:02] INCOMING   tools/list
[15:24:02] OUTGOING   tools/list
{
  "tools": [
    {
      "name": "echo",
      "description": "Echo back the input message",
      "inputSchema": {
        "type": "object",
        "properties": {
          "message": {
            "type": "string",
            "description": "Message to echo"
          }
        },
        "required": [
          "message"
        ]
      }
    }
  ]
}
```

## Features

### 1. Request Logging
All MCP requests and responses are logged and visible in the web UI.

### 2. Proxy Mode
Forward requests to an upstream MCP server while tracing all traffic.

Set dynamically via query param:
```
http://localhost:8765/?proxy=https://your-mcp-server.com/mcp
```
Or configure in the web UI.

### 3. Mock Tools
Define custom tools with mocked responses via the web UI. Useful for testing MCP clients.

## Endpoints

- **Web UI**: http://localhost:8765/
- **MCP**: http://localhost:8765/mcp

