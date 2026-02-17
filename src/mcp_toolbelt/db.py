"""SQLite database for request logging and tool configurations."""

import aiosqlite
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("mcp_toolbelt.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                direction TEXT,  -- 'incoming' or 'outgoing'
                method TEXT,
                params TEXT,
                result TEXT,
                error TEXT,
                timestamp TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mock_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                input_schema TEXT,
                mock_response TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await db.commit()


async def log_request(
    session_id: str,
    direction: str,
    method: str,
    params: dict | None = None,
    result: dict | None = None,
    error: dict | None = None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO request_logs (session_id, direction, method, params, result, error, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                direction,
                method,
                json.dumps(params) if params else None,
                json.dumps(result) if result else None,
                json.dumps(error) if error else None,
                datetime.utcnow().isoformat(),
            ),
        )
        await db.commit()


async def get_logs(limit: int = 100):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM request_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def clear_logs():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM request_logs")
        await db.commit()


async def save_mock_tool(name: str, description: str, input_schema: dict, mock_response: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            INSERT INTO mock_tools (name, description, input_schema, mock_response, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                input_schema = excluded.input_schema,
                mock_response = excluded.mock_response,
                updated_at = excluded.updated_at
            """,
            (name, description, json.dumps(input_schema), json.dumps(mock_response), now, now),
        )
        await db.commit()


async def get_mock_tools():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM mock_tools ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_mock_tool(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM mock_tools WHERE name = ?", (name,))
        await db.commit()
