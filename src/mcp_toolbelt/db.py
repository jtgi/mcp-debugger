"""JSON flat file storage for request logging and tool configurations."""

import json
from datetime import datetime
from pathlib import Path
import asyncio

DATA_FILE = Path("mcp_toolbelt_data.json")
_lock = asyncio.Lock()


def _load_data() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"logs": [], "mock_tools": []}


def _save_data(data: dict):
    DATA_FILE.write_text(json.dumps(data, indent=2))


async def init_db():
    if not DATA_FILE.exists():
        _save_data({"logs": [], "mock_tools": []})


async def log_request(
    session_id: str,
    direction: str,
    method: str,
    params: dict | None = None,
    result: dict | None = None,
    error: dict | None = None,
):
    async with _lock:
        data = _load_data()
        log_id = len(data["logs"]) + 1
        data["logs"].append({
            "id": log_id,
            "session_id": session_id,
            "direction": direction,
            "method": method,
            "params": params,
            "result": result,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep only last 500 logs
        data["logs"] = data["logs"][-500:]
        _save_data(data)


async def get_logs(limit: int = 100):
    async with _lock:
        data = _load_data()
        logs = data["logs"][-limit:]
        logs.reverse()
        return logs


async def clear_logs():
    async with _lock:
        data = _load_data()
        data["logs"] = []
        _save_data(data)


async def save_mock_tool(name: str, description: str, input_schema: dict, mock_response: dict):
    async with _lock:
        data = _load_data()
        now = datetime.utcnow().isoformat()
        # Update existing or add new
        for tool in data["mock_tools"]:
            if tool["name"] == name:
                tool["description"] = description
                tool["input_schema"] = input_schema
                tool["mock_response"] = mock_response
                tool["updated_at"] = now
                _save_data(data)
                return
        # Add new
        data["mock_tools"].append({
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "mock_response": mock_response,
            "created_at": now,
            "updated_at": now,
        })
        _save_data(data)


async def get_mock_tools():
    async with _lock:
        data = _load_data()
        return sorted(data["mock_tools"], key=lambda t: t["name"])


async def delete_mock_tool(name: str):
    async with _lock:
        data = _load_data()
        data["mock_tools"] = [t for t in data["mock_tools"] if t["name"] != name]
        _save_data(data)
