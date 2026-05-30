#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DB_PATH = Path(os.environ.get("AI_PEERS_DB", "~/.local/state/ai-peers/peers.db")).expanduser()
ACTIVE_WINDOW_SECONDS = int(os.environ.get("AI_PEERS_ACTIVE_WINDOW", "75"))
SKIP_PID_CHECK = os.environ.get("AI_PEERS_SKIP_PID_CHECK", "0") == "1"
DEFAULT_SUMMARY = "available"
ROLE_EASY = "easy-programmer"
ROLE_HARD = "hard-programmer"
ROLE_ORCH = "orchestrator-reviewer"
ROLE_WORKER = "worker"


def stable_peer_id() -> str:
    session_key = os.environ.get("AI_PEERS_SESSION_KEY", "").strip()
    if session_key:
        return session_key
    return uuid.uuid4().hex[:12]


def now_ts() -> float:
    return time.time()


def ensure_parent_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def connect() -> sqlite3.Connection:
    ensure_parent_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS peers (
                peer_id TEXT PRIMARY KEY,
                client TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'worker',
                hostname TEXT NOT NULL,
                pid INTEGER NOT NULL,
                cwd TEXT,
                repo_root TEXT,
                summary TEXT NOT NULL DEFAULT '',
                active_files_json TEXT NOT NULL DEFAULT '[]',
                started_at REAL NOT NULL,
                last_seen REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_peer_id TEXT NOT NULL,
                to_peer_id TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at REAL NOT NULL,
                read_at REAL,
                FOREIGN KEY (from_peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_peers_last_seen ON peers(last_seen);
            CREATE INDEX IF NOT EXISTS idx_messages_to_peer_read ON messages(to_peer_id, read_at, created_at);
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(peers)").fetchall()}
        if "role" not in columns:
            conn.execute("ALTER TABLE peers ADD COLUMN role TEXT NOT NULL DEFAULT 'worker'")
        conn.commit()


def run_git(args: list[str], cwd: str | None) -> str | None:
    if not cwd:
        return None
    try:
        completed = subprocess.run(
            ["git", "-C", cwd, *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        value = completed.stdout.strip()
        return value or None
    except Exception:
        return None


def infer_repo_root(cwd: str | None) -> str | None:
    return run_git(["rev-parse", "--show-toplevel"], cwd)


def infer_client() -> str:
    explicit = os.environ.get("AI_PEERS_CLIENT")
    if explicit:
        return explicit
    try:
        parent_cmd = subprocess.run(
            ["ps", "-o", "command=", "-p", str(os.getppid())],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ).stdout.lower()
    except Exception:
        parent_cmd = ""
    if "opencode" in parent_cmd:
        return "opencode"
    if "codex" in parent_cmd:
        return "codex"
    if "claude" in parent_cmd:
        return "claude-code"
    if "agent" in parent_cmd or "cursor" in parent_cmd:
        return "cursor-agent"
    return "unknown"


def infer_role(client: str) -> str:
    explicit = os.environ.get("AI_PEERS_ROLE")
    if explicit:
        return explicit
    if client == "opencode":
        return ROLE_EASY
    if client == "cursor-agent":
        return ROLE_HARD
    if client == "claude-code":
        return ROLE_HARD
    if client == "codex":
        return ROLE_ORCH
    return ROLE_WORKER


def infer_cwd() -> str:
    return (
        os.environ.get("AI_PEERS_LAUNCH_CWD")
        or os.environ.get("PWD")
        or os.getcwd()
    )


def make_registration() -> dict[str, Any]:
    cwd = infer_cwd()
    client = infer_client()
    return {
        "peer_id": stable_peer_id(),
        "client": client,
        "role": infer_role(client),
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "cwd": cwd,
        "repo_root": infer_repo_root(cwd),
        "summary": os.environ.get("AI_PEERS_SUMMARY", DEFAULT_SUMMARY),
        "active_files_json": json.dumps([]),
        "started_at": now_ts(),
        "last_seen": now_ts(),
    }


def pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def cleanup_stale_peers() -> int:
    cutoff = now_ts() - ACTIVE_WINDOW_SECONDS
    removed = 0
    with connect() as conn:
        rows = conn.execute("SELECT peer_id, pid, last_seen FROM peers").fetchall()
        for row in rows:
            is_stale = row["last_seen"] < cutoff
            pid_dead = (not SKIP_PID_CHECK) and (not pid_is_alive(int(row["pid"])))
            if is_stale or pid_dead:
                conn.execute("DELETE FROM peers WHERE peer_id = ?", (row["peer_id"],))
                removed += 1
        conn.commit()
    return removed


def get_peer(peer_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM peers WHERE peer_id = ?", (peer_id,)).fetchone()
    return normalize_peer_row(row) if row is not None else None


def set_summary_for_peer(peer_id: str, summary: str, active_files: list[str] | None = None) -> dict[str, Any] | None:
    files = [str(path) for path in (active_files or [])]
    with connect() as conn:
        conn.execute(
            """
            UPDATE peers
            SET summary = ?, active_files_json = ?, last_seen = ?
            WHERE peer_id = ?
            """,
            (summary.strip(), json.dumps(files), now_ts(), peer_id),
        )
        conn.commit()
    return get_peer(peer_id)


def check_messages_for_peer(peer_id: str, limit: int = 20, mark_read: bool = True) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 100))
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                messages.id,
                messages.from_peer_id,
                messages.to_peer_id,
                messages.body,
                messages.created_at,
                messages.read_at,
                peers.client AS from_client,
                peers.role AS from_role,
                peers.cwd AS from_cwd,
                peers.repo_root AS from_repo_root,
                peers.summary AS from_summary
            FROM messages
            LEFT JOIN peers ON peers.peer_id = messages.from_peer_id
            WHERE messages.to_peer_id = ? AND messages.read_at IS NULL
            ORDER BY messages.created_at ASC
            LIMIT ?
            """,
            (peer_id, limit),
        ).fetchall()
        if mark_read and rows:
            ids = [row["id"] for row in rows]
            placeholders = ", ".join("?" for _ in ids)
            conn.execute(
                f"UPDATE messages SET read_at = ? WHERE id IN ({placeholders})",
                [now_ts(), *ids],
            )
            conn.commit()
    return [normalize_message_row(row) for row in rows]


class PeerStore:
    def __init__(self, registration: dict[str, Any] | None = None) -> None:
        init_db()
        cleanup_stale_peers()
        self.registration = registration or make_registration()
        self.peer_id = self.registration["peer_id"]
        self.register()

    def register(self) -> None:
        with connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO peers (
                    peer_id, client, role, hostname, pid, cwd, repo_root, summary, active_files_json, started_at, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.registration["peer_id"],
                    self.registration["client"],
                    self.registration["role"],
                    self.registration["hostname"],
                    self.registration["pid"],
                    self.registration["cwd"],
                    self.registration["repo_root"],
                    self.registration["summary"],
                    self.registration["active_files_json"],
                    self.registration["started_at"],
                    now_ts(),
                ),
            )
            conn.commit()

    def heartbeat(self) -> None:
        with connect() as conn:
            conn.execute(
                "UPDATE peers SET last_seen = ? WHERE peer_id = ?",
                (now_ts(), self.peer_id),
            )
            conn.commit()

    def remove_self(self) -> None:
        with connect() as conn:
            conn.execute("DELETE FROM peers WHERE peer_id = ?", (self.peer_id,))
            conn.commit()

    def set_summary(self, summary: str, active_files: list[str] | None = None) -> dict[str, Any]:
        files = [str(path) for path in (active_files or [])]
        with connect() as conn:
            conn.execute(
                """
                UPDATE peers
                SET summary = ?, active_files_json = ?, last_seen = ?
                WHERE peer_id = ?
                """,
                (summary.strip(), json.dumps(files), now_ts(), self.peer_id),
            )
            conn.commit()
        return self.get_self()

    def get_self(self) -> dict[str, Any]:
        with connect() as conn:
            row = conn.execute("SELECT * FROM peers WHERE peer_id = ?", (self.peer_id,)).fetchone()
        if row is None:
            return {}
        return normalize_peer_row(row)

    def list_peers(
        self,
        scope: str = "machine",
        include_self: bool = False,
        only_active: bool = True,
        role: str | None = None,
    ) -> list[dict[str, Any]]:
        cleanup_stale_peers()
        current = self.get_self()
        where = []
        params: list[Any] = []
        if not include_self:
            where.append("peer_id != ?")
            params.append(self.peer_id)
        if only_active:
            where.append("last_seen >= ?")
            params.append(now_ts() - ACTIVE_WINDOW_SECONDS)
        if scope == "repo" and current.get("repo_root"):
            where.append("repo_root = ?")
            params.append(current["repo_root"])
        if scope == "directory" and current.get("cwd"):
            where.append("cwd = ?")
            params.append(current["cwd"])
        if role:
            where.append("role = ?")
            params.append(role)
        query = "SELECT * FROM peers"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY last_seen DESC, started_at DESC"
        with connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [normalize_peer_row(row) for row in rows]

    def send_message(self, to_peer_id: str, body: str) -> dict[str, Any]:
        body = body.strip()
        if not body:
            raise ValueError("Message body cannot be empty.")
        with connect() as conn:
            target = conn.execute(
                "SELECT peer_id FROM peers WHERE peer_id = ?",
                (to_peer_id,),
            ).fetchone()
            if target is None:
                raise ValueError(f"Peer '{to_peer_id}' was not found.")
            cursor = conn.execute(
                """
                INSERT INTO messages (from_peer_id, to_peer_id, body, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (self.peer_id, to_peer_id, body, now_ts()),
            )
            conn.commit()
            message_id = int(cursor.lastrowid)
        return {
            "message_id": message_id,
            "from_peer_id": self.peer_id,
            "to_peer_id": to_peer_id,
            "body": body,
        }

    def recommend_peer(self, task_kind: str, difficulty: str = "easy") -> dict[str, Any]:
        current = self.get_self()
        if task_kind == "review" and current.get("role") == ROLE_ORCH:
            return {
                "task_kind": task_kind,
                "difficulty": difficulty,
                "role_order": [ROLE_ORCH],
                "recommended": current,
                "fallbacks": [],
            }
        peers = self.list_peers(include_self=False, only_active=True)
        by_role: dict[str, list[dict[str, Any]]] = {}
        for peer in peers:
            by_role.setdefault(str(peer["role"]), []).append(peer)
        if task_kind == "review":
            order = [ROLE_ORCH]
        elif difficulty == "hard":
            order = [ROLE_HARD, ROLE_ORCH]
        else:
            order = [ROLE_EASY, ROLE_HARD, ROLE_ORCH]
        candidates: list[dict[str, Any]] = []
        for role in order:
            candidates.extend(by_role.get(role, []))
        return {
            "task_kind": task_kind,
            "difficulty": difficulty,
            "role_order": order,
            "recommended": candidates[0] if candidates else None,
            "fallbacks": candidates[1:],
        }

    def check_messages(self, limit: int = 20, mark_read: bool = True) -> list[dict[str, Any]]:
        return check_messages_for_peer(self.peer_id, limit=limit, mark_read=mark_read)


def normalize_peer_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "peer_id": row["peer_id"],
        "client": row["client"],
        "role": row["role"],
        "hostname": row["hostname"],
        "pid": row["pid"],
        "cwd": row["cwd"],
        "repo_root": row["repo_root"],
        "summary": row["summary"],
        "active_files": json.loads(row["active_files_json"] or "[]"),
        "started_at": row["started_at"],
        "last_seen": row["last_seen"],
        "age_seconds": round(now_ts() - float(row["started_at"]), 1),
        "idle_seconds": round(now_ts() - float(row["last_seen"]), 1),
    }


def normalize_message_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "from_peer_id": row["from_peer_id"],
        "to_peer_id": row["to_peer_id"],
        "body": row["body"],
        "created_at": row["created_at"],
        "read_at": row["read_at"],
        "from_client": row["from_client"],
        "from_role": row["from_role"] if "from_role" in row.keys() else None,
        "from_cwd": row["from_cwd"],
        "from_repo_root": row["from_repo_root"],
        "from_summary": row["from_summary"],
    }
