# MCP Toolbelt

Debug, inspect, and mock MCP servers. Like webhook.site but for MCP.

## Quick Start

```bash
# Run with uvx (no install needed)
uvx mcp-toolbelt

# Or with pipx
pipx run mcp-toolbelt

# Or install and run
pip install -e .
mcp-toolbelt
```

## Usage

```bash
mcp-toolbelt                              # Run on localhost:8765
mcp-toolbelt --port 9000                  # Custom port
mcp-toolbelt --ngrok                      # Expose via ngrok tunnel
mcp-toolbelt --proxy https://remote/mcp   # Proxy to another MCP server
```

## Features

### 1. Request Logging
All MCP requests and responses are logged and visible in the web UI.

### 2. Proxy Mode
Forward requests to an upstream MCP server while tracing all traffic:
```bash
mcp-toolbelt --proxy https://your-mcp-server.com/mcp
```
Or set dynamically via query param: `http://localhost:8765/?proxy=URL`

### 3. Mock Tools
Define custom tools with mocked responses via the web UI. Useful for testing MCP clients.

## Endpoints

- **Web UI**: http://localhost:8765/
- **MCP**: http://localhost:8765/mcp

## Requirements

- Python 3.11+
- ngrok (optional, for `--ngrok` flag)
