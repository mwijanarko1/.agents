#!/Users/mikhail/.agents/vendor/ai-peers/.venv/bin/python
from __future__ import annotations

import atexit
import os
import signal
import threading
import time

from mcp.server.fastmcp import FastMCP

from store import ACTIVE_WINDOW_SECONDS, PeerStore, cleanup_stale_peers

HEARTBEAT_SECONDS = max(5, ACTIVE_WINDOW_SECONDS // 3)
_PARENT_PID = os.getppid()
STORE = PeerStore()
MCP = FastMCP(
    "ai-peers",
    instructions=(
        "Use native subagents as the default specialist layer. Use this peer bridge only when "
        "the user explicitly asks for cross-tool delegation and names the target coding tool. "
        "Codex remains the orchestrator and final reviewer for bridged work."
    ),
    json_response=True,
)


def _cleanup(*_args: object) -> None:
    STORE.remove_self()
    raise SystemExit(0)


def _parent_watchdog() -> None:
    """Exit if the parent process dies (ppid becomes 1 / launchd on macOS)."""
    while True:
        try:
            if os.getppid() != _PARENT_PID:
                STORE.remove_self()
                raise SystemExit(0)
        except SystemExit:
            raise
        except Exception:
            pass
        time.sleep(HEARTBEAT_SECONDS)


def _heartbeat_loop() -> None:
    while True:
        try:
            STORE.heartbeat()
            cleanup_stale_peers()
        except Exception:
            pass
        time.sleep(HEARTBEAT_SECONDS)


@MCP.tool(description="Show this session's peer identity and current metadata.")
def whoami() -> dict:
    return STORE.get_self()


@MCP.tool(
    description="List other active AI sessions on this machine, optionally scoped to the current repo or directory."
)
def list_peers(
    scope: str = "machine",
    include_self: bool = False,
    only_active: bool = True,
    role: str | None = None,
) -> dict:
    return {
        "peers": STORE.list_peers(
            scope=scope,
            include_self=include_self,
            only_active=only_active,
            role=role,
        )
    }


@MCP.tool(
    description="Compatibility helper for explicit bridge requests only: recommend which peer should take a task."
)
def recommend_peer(task_kind: str = "implement", difficulty: str = "easy") -> dict:
    return STORE.recommend_peer(task_kind=task_kind, difficulty=difficulty)


@MCP.tool(
    description="Update what this session is working on and optionally list active files so peers can avoid collisions."
)
def set_summary(summary: str, active_files: list[str] | None = None) -> dict:
    return {"peer": STORE.set_summary(summary=summary, active_files=active_files or [])}


@MCP.tool(description="Send a short coordination message to another peer session by its peer_id.")
def send_message(peer_id: str, message: str) -> dict:
    return {"sent": STORE.send_message(to_peer_id=peer_id, body=message)}


@MCP.tool(description="Read unread coordination messages sent to this session.")
def check_messages(limit: int = 20, mark_read: bool = True) -> dict:
    return {"messages": STORE.check_messages(limit=limit, mark_read=mark_read)}


def main() -> None:
    atexit.register(STORE.remove_self)
    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)
    threading.Thread(target=_parent_watchdog, daemon=True).start()
    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    MCP.run(transport="stdio")


if __name__ == "__main__":
    main()
