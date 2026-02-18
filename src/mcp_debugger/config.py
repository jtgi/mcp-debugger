"""Configuration management for MCP Toolbelt."""

import json
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("mcp_toolbelt_config.json")

DEFAULT_CONFIG = {
    "proxy_target": None,
    "tools": [
        {
            "name": "echo",
            "description": "Echo back the input message",
            "input_schema": {
                "type": "object",
                "properties": {"message": {"type": "string", "description": "Message to echo"}},
                "required": ["message"],
            },
            "mock_response": "{{message}}",
        }
    ],
}


def load_config(path: Path | None = None) -> dict:
    """Load config from file, return defaults if not found."""
    config_path = path or DEFAULT_CONFIG_PATH
    if config_path.exists():
        try:
            return {**DEFAULT_CONFIG, **json.loads(config_path.read_text())}
        except json.JSONDecodeError:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict, path: Path | None = None):
    """Save config to file with pretty printing."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.write_text(json.dumps(config, indent=2) + "\n")


def get_config_path() -> Path:
    return DEFAULT_CONFIG_PATH
