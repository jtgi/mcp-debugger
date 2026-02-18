"""Main FastAPI application with MCP server integration."""

import json
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Any
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from mcp_debugger import db
from mcp_debugger import config as config_module

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def pretty_json(value):
    """Jinja filter to pretty-print JSON."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    return json.dumps(value, indent=2)


templates.env.filters["pretty_json"] = pretty_json


def log_to_console(direction: str, method: str, data: dict | None):
    """Log request/response to stdout."""
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    colors = {
        "incoming": "\033[94m",  # blue
        "outgoing": "\033[93m",  # yellow
        "proxy_out": "\033[95m",  # purple
        "proxy_in": "\033[96m",  # cyan
    }
    reset = "\033[0m"
    color = colors.get(direction, "")

    prefix = f"{color}[{timestamp}] {direction.upper():10}{reset} {method}"
    if data:
        print(f"{prefix}\n{json.dumps(data, indent=2)}", file=sys.stderr)
    else:
        print(prefix, file=sys.stderr)

# In-memory state
sessions: dict[str, dict] = {}
proxy_target: str | None = None
proxy_session_id: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(title="MCP Toolbelt", lifespan=lifespan)


# ============ Web UI ============


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, proxy: str | None = None):
    global proxy_target, proxy_session_id
    if proxy is not None:
        proxy_target = proxy if proxy else None
        proxy_session_id = None
    logs = await db.get_logs(100)
    mock_tools = await db.get_mock_tools()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "logs": logs,
            "mock_tools": mock_tools,
            "proxy_target": proxy_target,
        },
    )


@app.post("/api/logs/clear")
async def clear_logs():
    await db.clear_logs()
    return {"status": "ok"}


@app.get("/api/logs")
async def get_logs():
    logs = await db.get_logs(100)
    return logs


@app.post("/api/proxy/set")
async def set_proxy(request: Request):
    global proxy_target, proxy_session_id
    data = await request.json()
    proxy_target = data.get("url")
    proxy_session_id = None  # Reset session when target changes
    # Save to config
    cfg = config_module.load_config()
    cfg["proxy_target"] = proxy_target
    config_module.save_config(cfg)
    return {"status": "ok", "proxy_target": proxy_target}


@app.post("/api/mock-tools")
async def create_mock_tool(request: Request):
    data = await request.json()
    await db.save_mock_tool(
        name=data["name"],
        description=data.get("description", ""),
        input_schema=data.get("input_schema", {"type": "object", "properties": {}}),
        mock_response=data.get("mock_response", {"text": "mock response"}),
    )
    return {"status": "ok"}


@app.delete("/api/mock-tools/{name}")
async def delete_mock_tool(name: str):
    await db.delete_mock_tool(name)
    return {"status": "ok"}


# ============ MCP Server ============


def get_config_tools():
    """Get tools from config file."""
    cfg = config_module.load_config()
    tools = []
    for t in cfg.get("tools", []):
        tools.append({
            "name": t["name"],
            "description": t.get("description", ""),
            "inputSchema": t.get("input_schema", {"type": "object", "properties": {}}),
            "_mock_response": t.get("mock_response"),
        })
    return tools


async def get_all_tools():
    """Get all tools (config + db mock tools)."""
    tools = get_config_tools()
    mock_tools = await db.get_mock_tools()
    for mt in mock_tools:
        tools.append({
            "name": mt["name"],
            "description": mt["description"],
            "inputSchema": mt["input_schema"],
            "_mock_response": mt["mock_response"],
        })
    # Return without internal _mock_response field
    return [{k: v for k, v in t.items() if not k.startswith("_")} for t in tools]


def substitute_template(template: str, arguments: dict) -> str:
    """Simple template substitution: {{key}} -> arguments[key]."""
    result = template
    for key, value in arguments.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


async def handle_tool_call(name: str, arguments: dict) -> dict:
    # Check config tools first
    cfg = config_module.load_config()
    for t in cfg.get("tools", []):
        if t["name"] == name:
            response = t.get("mock_response", "")
            if isinstance(response, str):
                return {"content": [{"type": "text", "text": substitute_template(response, arguments)}]}
            return {"content": [{"type": "text", "text": json.dumps(response)}]}

    # Check db mock tools
    mock_tools = await db.get_mock_tools()
    for mt in mock_tools:
        if mt["name"] == name:
            response = mt["mock_response"]
            if isinstance(response, str):
                return {"content": [{"type": "text", "text": substitute_template(response, arguments)}]}
            return {"content": [{"type": "text", "text": json.dumps(response)}]}

    raise ValueError(f"Unknown tool: {name}")


def make_response(req_id: Any, result: dict | None = None, error: dict | None = None) -> dict:
    if error:
        return {"jsonrpc": "2.0", "id": req_id, "error": error}
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


async def ensure_proxy_session(client: httpx.AsyncClient) -> str | None:
    """Initialize a session with the upstream server if needed."""
    global proxy_session_id
    if proxy_session_id:
        return proxy_session_id

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    init_payload = {
        "jsonrpc": "2.0",
        "id": "init",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-toolbelt-proxy", "version": "0.1.0"},
        },
    }
    resp = await client.post(proxy_target, json=init_payload, headers=headers)
    proxy_session_id = resp.headers.get("mcp-session-id")
    return proxy_session_id


async def proxy_request(method: str, params: dict, req_id: Any, session_id: str) -> dict:
    """Proxy a request to the upstream MCP server."""
    global proxy_session_id
    if not proxy_target:
        return make_response(req_id, error={"code": -32600, "message": "No proxy target configured"})

    async with httpx.AsyncClient(timeout=30.0) as client:
        upstream_session = await ensure_proxy_session(client)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if upstream_session:
            headers["mcp-session-id"] = upstream_session

        payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}

        await db.log_request(session_id, "proxy_out", method, params)
        log_to_console("proxy_out", method, params)

        resp = await client.post(proxy_target, json=payload, headers=headers)
        text = resp.text

        # Parse SSE or JSON response
        if text.startswith("event:") or text.startswith("data:"):
            for line in text.split("\n"):
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    await db.log_request(session_id, "proxy_in", method, result=data.get("result"), error=data.get("error"))
                    log_to_console("proxy_in", method, data.get("result") or data.get("error"))
                    return data
        else:
            data = resp.json()
            await db.log_request(session_id, "proxy_in", method, result=data.get("result"), error=data.get("error"))
            log_to_console("proxy_in", method, data.get("result") or data.get("error"))
            return data

    return make_response(req_id, error={"code": -32600, "message": "Proxy failed"})


async def handle_mcp_request(request_data: dict, session_id: str) -> dict | None:
    method = request_data.get("method", "")
    params = request_data.get("params", {})
    req_id = request_data.get("id")

    await db.log_request(session_id, "incoming", method, params)
    log_to_console("incoming", method, params)

    # Notifications have no id
    if req_id is None:
        return None

    # If proxy mode and not a local-only method, proxy it
    if proxy_target and method not in ("initialize",):
        return await proxy_request(method, params, req_id, session_id)

    result = None
    error = None

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mcp-toolbelt", "version": "0.1.0"},
        }
    elif method == "tools/list":
        tools = await get_all_tools()
        result = {"tools": tools}
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        try:
            result = await handle_tool_call(tool_name, arguments)
        except ValueError as e:
            error = {"code": -32601, "message": str(e)}
    elif method == "ping":
        result = {}
    else:
        error = {"code": -32601, "message": f"Unknown method: {method}"}

    response = make_response(req_id, result, error)
    await db.log_request(session_id, "outgoing", method, result=result, error=error)
    log_to_console("outgoing", method, result or error)
    return response


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    accept = request.headers.get("accept", "")
    session_id = request.headers.get("mcp-session-id", "default")

    body = await request.body()
    if not body:
        return JSONResponse({"error": "Empty body"}, status_code=400)

    try:
        request_data = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    response = await handle_mcp_request(request_data, session_id)

    if response is None:
        return JSONResponse(content=None, status_code=202)

    # Return as SSE if client accepts it
    if "text/event-stream" in accept:
        async def generate():
            yield f"event: message\ndata: {json.dumps(response)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "mcp-session-id": session_id,
            },
        )

    return JSONResponse(response, headers={"mcp-session-id": session_id})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
