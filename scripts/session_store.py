#!/usr/bin/env python3
"""
Local SQLite session and memory store for ~/.agents learning.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{2,}")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    project_root TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'hook',
    started_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    observation_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    scope TEXT NOT NULL,
    project_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    event TEXT NOT NULL,
    tool_name TEXT,
    prompt TEXT,
    tool_input TEXT,
    tool_output TEXT,
    search_text TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semantic_memories (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    fact TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    strength REAL NOT NULL DEFAULT 0.5,
    source_observation_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS procedural_memories (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    trigger_condition TEXT NOT NULL,
    steps TEXT NOT NULL DEFAULT '[]',
    strength REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_observations_session ON observations(session_id);
CREATE INDEX IF NOT EXISTS idx_observations_project ON observations(project_id);
"""


MIGRATIONS = [
    ("observations", "kind", "TEXT NOT NULL DEFAULT 'tool_result'"),
]


FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
    search_text,
    content='observations',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS observations_fts_insert AFTER INSERT ON observations BEGIN
    INSERT INTO observations_fts(rowid, search_text) VALUES (new.id, new.search_text);
END;

CREATE TRIGGER IF NOT EXISTS observations_fts_delete AFTER DELETE ON observations BEGIN
    INSERT INTO observations_fts(observations_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
END;

CREATE TRIGGER IF NOT EXISTS observations_fts_update AFTER UPDATE ON observations BEGIN
    INSERT INTO observations_fts(observations_fts, rowid, search_text) VALUES('delete', old.id, old.search_text);
    INSERT INTO observations_fts(rowid, search_text) VALUES (new.id, new.search_text);
END;
"""


def state_db_path(state_root: Path) -> Path:
    return state_root / "state.db"


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sanitize_fts_query(query: str) -> str:
    terms = TOKEN_RE.findall(query)
    return " OR ".join(f'"{term}"' if "." in term or "-" in term else term for term in terms)


def compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def extract_files(*values: Any) -> list[str]:
    files: list[str] = []
    path_re = re.compile(r"\b[A-Za-z0-9_./-]+\.(?:py|js|ts|tsx|jsx|json|md|toml|yaml|yml|swift|go|rs|java|kt)\b")
    for value in values:
        text = value if isinstance(value, str) else compact_json(value)
        files.extend(path_re.findall(text))
    return files


def observation_rank(row: dict[str, Any] | sqlite3.Row) -> int:
    kind = row["kind"] if "kind" in row.keys() else ""
    ranks = {
        "user_prompt": 0,
        "session_summary": 1,
        "verification": 2,
        "code_change": 3,
        "tool_call": 4,
        "tool_result": 5,
    }
    return ranks.get(kind or "", 6)


def extract_terms(text: str) -> list[str]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "into", "then",
        "have", "using", "tool", "output", "input", "file", "path", "run",
    }
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.lower() not in stop and not token.isdigit()
    ]


class SessionStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), timeout=1.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(SCHEMA_SQL)
        self._apply_migrations()
        try:
            self._conn.executescript(FTS_SQL)
        except sqlite3.OperationalError:
            # Some SQLite builds omit FTS5. Search falls back to LIKE.
            pass
        row = self._conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if row is None:
            self._conn.execute("INSERT INTO schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
        self._conn.commit()

    def _apply_migrations(self) -> None:
        for table, column, definition in MIGRATIONS:
            existing = {
                row["name"]
                for row in self._conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            if column not in existing:
                self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def ensure_session(self, session_id: str, project_id: str, project_name: str, project_root: str, source: str = "hook") -> None:
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO sessions(id, project_id, project_name, project_root, source, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                project_id=excluded.project_id,
                project_name=excluded.project_name,
                project_root=excluded.project_root,
                updated_at=excluded.updated_at
            """,
            (session_id, project_id, project_name, project_root, source, now, now),
        )
        self._conn.commit()

    def add_observation(
        self,
        *,
        session_id: str,
        project_id: str,
        project_name: str,
        project_root: str,
        event: str,
        kind: str = "tool_result",
        tool_name: str = "",
        prompt: str = "",
        tool_input: Any = None,
        tool_output: Any = None,
        timestamp: str | None = None,
        scope: str = "project",
        raw: dict[str, Any] | None = None,
    ) -> int:
        self.ensure_session(session_id, project_id, project_name, project_root)
        timestamp = timestamp or utc_timestamp()
        tool_input = tool_input if tool_input is not None else {}
        tool_output = tool_output if tool_output is not None else ""
        search_text = self._build_search_text(
            kind=kind,
            event=event,
            tool_name=tool_name,
            prompt=prompt,
            tool_input=tool_input,
            tool_output=tool_output,
        )
        raw_json = compact_json(raw or {})
        cursor = self._conn.execute(
            """
            INSERT INTO observations(
                session_id, timestamp, scope, project_id, project_name, event,
                tool_name, prompt, tool_input, tool_output, search_text, raw_json, kind
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                timestamp,
                scope,
                project_id,
                project_name,
                event,
                tool_name,
                prompt,
                compact_json(tool_input),
                tool_output if isinstance(tool_output, str) else compact_json(tool_output),
                search_text,
                raw_json,
                kind,
            ),
        )
        self._conn.execute(
            "UPDATE sessions SET observation_count = observation_count + 1, updated_at = ? WHERE id = ?",
            (time.time(), session_id),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def _build_search_text(
        self,
        *,
        kind: str,
        event: str,
        tool_name: str,
        prompt: str,
        tool_input: Any,
        tool_output: Any,
    ) -> str:
        input_text = compact_json(tool_input)
        output_text = tool_output if isinstance(tool_output, str) else compact_json(tool_output)
        if tool_name == "Bash" and kind == "tool_result":
            return "\n".join(
                [
                    f"kind:{kind}",
                    tool_name or "",
                    event or "",
                    input_text,
                ]
            )
        return "\n".join(
            [
                f"kind:{kind}",
                prompt or "",
                tool_name or "",
                event or "",
                input_text,
                output_text,
            ]
        )

    def search(self, query: str, *, project_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        limit = max(1, min(limit, 100))
        fts_query = sanitize_fts_query(query)
        params: list[Any] = []
        project_clause = ""
        if project_id:
            project_clause = "AND o.project_id = ?"
            params.append(project_id)

        if fts_query:
            try:
                rows = self._conn.execute(
                    f"""
                    SELECT o.*, bm25(observations_fts) AS score
                    FROM observations_fts
                    JOIN observations o ON o.id = observations_fts.rowid
                    WHERE observations_fts MATCH ? {project_clause}
                    ORDER BY score
                    LIMIT ?
                    """,
                    [fts_query, *params, limit],
                ).fetchall()
                return sorted((dict(row) for row in rows), key=observation_rank)
            except sqlite3.OperationalError:
                pass

        like = f"%{query}%"
        rows = self._conn.execute(
            f"""
            SELECT *, 0.0 AS score
            FROM observations o
            WHERE search_text LIKE ? {project_clause}
            ORDER BY id DESC
            LIMIT ?
            """,
            [like, *params, limit],
        ).fetchall()
        return sorted((dict(row) for row in rows), key=observation_rank)

    def list_sessions(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT *
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (max(1, min(limit, 200)),),
        ).fetchall()
        return [dict(row) for row in rows]

    def project_profile(self, project_id: str) -> dict[str, Any]:
        rows = self._conn.execute(
            """
            SELECT *
            FROM observations
            WHERE project_id = ?
            ORDER BY id DESC
            LIMIT 500
            """,
            (project_id,),
        ).fetchall()
        file_counter: Counter[str] = Counter()
        term_counter: Counter[str] = Counter()
        recent: list[str] = []
        for row in rows:
            prompt = row["prompt"] or ""
            tool_input = json.loads(row["tool_input"] or "{}")
            kind = row["kind"] if "kind" in row.keys() else ""
            tool_output = "" if kind == "tool_result" and row["tool_name"] == "Bash" else row["tool_output"] or ""
            for file_path in extract_files(prompt, tool_input, tool_output):
                file_counter[file_path] += 1
            for term in extract_terms(f"{prompt} {tool_output}"):
                term_counter[term] += 1
            if prompt and len(recent) < 10:
                recent.append(prompt[:160])

        return {
            "project_id": project_id,
            "observation_count": len(rows),
            "top_files": [{"file": name, "count": count} for name, count in file_counter.most_common(15)],
            "top_terms": [{"term": name, "count": count} for name, count in term_counter.most_common(15)],
            "recent_activity": recent,
        }

    def build_context(self, query: str, *, project_id: str | None = None, budget_chars: int = 6000) -> str:
        rows = self.search(query, project_id=project_id, limit=20)
        lines: list[str] = []
        used = 0
        for row in rows:
            label = row["prompt"] or row["tool_name"]
            body = row["prompt"] if row["prompt"] else (row["tool_output"] or "")[:240]
            item = f"- [{row['project_name']}] {label}: {body}"
            if used + len(item) > budget_chars:
                break
            lines.append(item)
            used += len(item)
        if not lines:
            return ""
        return "\n".join(lines)
