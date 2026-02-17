# MCP Toolbelt

Debug, inspect, and mock MCP servers. Like webhook.site but for MCP.

## Quick Start

```bash
# Run from git (no install needed)
uvx --from git+https://github.com/YOURORG/mcp-toolbelt mcp-toolbelt

# Or clone and run
git clone https://github.com/YOURORG/mcp-toolbelt
cd mcp-toolbelt
uv run mcp-toolbelt
```

## Usage

```bash
mcp-toolbelt                # Run on localhost:8765
mcp-toolbelt --port 9000    # Custom port
mcp-toolbelt --ngrok        # Expose via ngrok tunnel
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

## Requirements

- Python 3.11+
- ngrok (optional, for `--ngrok` flag)
