import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager
import os

import asyncio


class Database:
    def __init__(self, db_url: str, pool_size: int = 10):
        self.db_url = db_url
        self.pool_size = pool_size
        os.makedirs(os.path.dirname(db_url.replace("sqlite:///", "")), exist_ok=True)

    def get_connection(self):
        conn = sqlite3.connect(self.db_url)
        conn.row_factory = sqlite3.Row
        return conn

    async def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_query_sync, query, params)

    def _execute_query_sync(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    async def execute_write(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._execute_write_sync, query, params)

    def _execute_write_sync(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor

    async def initialize(self):
        await self._initialize_sync()

    async def _initialize_sync(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._init_sync)

    def _init_sync(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    markdown_report TEXT,
                    confidence REAL,
                    sources TEXT,
                    created_at TEXT NOT NULL,
                    delivered_at TEXT,
                    delivered BOOLEAN DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS research_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    ttl_seconds INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cot_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_date TEXT UNIQUE NOT NULL,
                    asset TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT UNIQUE NOT NULL,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.commit()

    async def save_report(
        self,
        date: str,
        report_type: str,
        title: str,
        content: str,
        markdown_report: str,
        confidence: float,
        sources: List[str],
    ):
        now = datetime.now().isoformat()
        sources_json = ",".join(sources)

        cursor = await self.execute_write(
            """
            INSERT OR REPLACE INTO reports 
            (date, type, title, content, markdown_report, confidence, sources, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                date,
                report_type,
                title,
                content,
                markdown_report,
                confidence,
                sources_json,
                now,
            ),
        )

        return cursor.lastrowid if cursor.lastrowid is not None else 0

    async def get_report(self, date: str, report_type: str) -> Optional[Dict]:
        rows = await self.execute_query(
            "SELECT * FROM reports WHERE date = ? AND type = ?", (date, report_type)
        )
        if rows:
            row = rows[0]
            return {
                "id": row["id"],
                "date": row["date"],
                "type": row["type"],
                "title": row["title"],
                "content": row["content"],
                "markdown_report": row["markdown_report"],
                "confidence": row["confidence"],
                "sources": row["sources"].split(",") if row["sources"] else [],
                "created_at": row["created_at"],
                "delivered_at": row["delivered_at"],
                "delivered": bool(row["delivered"]),
            }
        return None

    async def mark_delivered(self, report_id: int):
        now = datetime.now().isoformat()
        await self.execute_write(
            "UPDATE reports SET delivered_at = ?, delivered = 1 WHERE id = ?",
            (now, report_id),
        )

    async def cache_get(self, key: str) -> Optional[Dict]:
        rows = await self.execute_query(
            """
            SELECT value FROM research_cache 
            WHERE key = ? AND expires_at > datetime('now')
            """,
            (key,),
        )

        if rows:
            import json

            return json.loads(rows[0]["value"])

        await self._cleanup_cache()
        return None

    async def cache_set(self, key: str, value: Dict, ttl_seconds: int):
        import json

        now = datetime.now()
        expires = now.isoformat()

        value_json = json.dumps(value)

        await self.execute_write(
            """
            INSERT OR REPLACE INTO research_cache (key, value, ttl_seconds, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, value_json, ttl_seconds, now.isoformat(), expires),
        )

    async def _cleanup_cache(self):
        await self.execute_write(
            "DELETE FROM research_cache WHERE expires_at < datetime('now')"
        )

    async def save_agent_state(self, thread_id: str, state: Dict):
        import json

        now = datetime.now().isoformat()
        state_json = json.dumps(state)

        await self.execute_write(
            """
            INSERT OR REPLACE INTO agent_state (thread_id, state, updated_at)
            VALUES (?, ?, ?)
            """,
            (thread_id, state_json, now),
        )

    async def get_agent_state(self, thread_id: str) -> Optional[Dict]:
        rows = await self.execute_query(
            "SELECT state FROM agent_state WHERE thread_id = ?", (thread_id,)
        )

        if rows:
            import json

            return json.loads(rows[0]["state"])

        return None

    async def get_recent_reports(
        self, limit: int = 10, report_type: Optional[str] = None
    ) -> List[Dict]:
        query = "SELECT * FROM reports"
        params = []

        if report_type:
            query += " WHERE type = ?"
            params.append(report_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = await self.execute_query(query, tuple(params))

        return [
            {
                "id": row["id"],
                "date": row["date"],
                "type": row["type"],
                "title": row["title"],
                "content": row["content"],
                "markdown_report": row["markdown_report"],
                "confidence": row["confidence"],
                "sources": row["sources"].split(",") if row["sources"] else [],
                "created_at": row["created_at"],
                "delivered_at": row["delivered_at"],
                "delivered": bool(row["delivered"]),
            }
            for row in rows
        ]
