#!/usr/bin/env python3
from __future__ import annotations

import importlib
import os
import tempfile
import unittest


class PeerStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ["AI_PEERS_DB"] = os.path.join(self.tempdir.name, "peers.db")
        os.environ["AI_PEERS_SKIP_PID_CHECK"] = "1"
        global store_module
        import store as store_module  # type: ignore

        store_module = importlib.reload(store_module)

    def tearDown(self) -> None:
        self.tempdir.cleanup()
        os.environ.pop("AI_PEERS_DB", None)
        os.environ.pop("AI_PEERS_SKIP_PID_CHECK", None)

    def test_message_round_trip(self) -> None:
        first = store_module.PeerStore(
            {
                "peer_id": "peer-a",
                "client": "cursor-agent",
                "role": "hard-programmer",
                "hostname": "host",
                "pid": 10001,
                "cwd": "/tmp/project-a",
                "repo_root": "/tmp/project-a",
                "summary": "editing api",
                "active_files_json": "[]",
                "started_at": 1.0,
                "last_seen": 1.0,
            }
        )
        second = store_module.PeerStore(
            {
                "peer_id": "peer-b",
                "client": "opencode",
                "role": "easy-programmer",
                "hostname": "host",
                "pid": 10002,
                "cwd": "/tmp/project-b",
                "repo_root": "/tmp/project-b",
                "summary": "editing ui",
                "active_files_json": "[]",
                "started_at": 1.0,
                "last_seen": 1.0,
            }
        )

        sent = first.send_message("peer-b", "avoid auth.ts, I am in there")
        self.assertEqual(sent["to_peer_id"], "peer-b")

        unread = second.check_messages()
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread[0]["body"], "avoid auth.ts, I am in there")

        after_read = second.check_messages()
        self.assertEqual(after_read, [])

    def test_set_summary_updates_files(self) -> None:
        store = store_module.PeerStore(
            {
                "peer_id": "peer-c",
                "client": "cursor-agent",
                "role": "hard-programmer",
                "hostname": "host",
                "pid": 10003,
                "cwd": "/tmp/project-c",
                "repo_root": "/tmp/project-c",
                "summary": "starting",
                "active_files_json": "[]",
                "started_at": 1.0,
                "last_seen": 1.0,
            }
        )

        peer = store.set_summary("touching auth flow", ["src/auth.ts", "src/ui.tsx"])
        self.assertEqual(peer["summary"], "touching auth flow")
        self.assertEqual(peer["active_files"], ["src/auth.ts", "src/ui.tsx"])

    def test_recommend_peer_prefers_requested_lane(self) -> None:
        codex = store_module.PeerStore(
            {
                "peer_id": "peer-orch",
                "client": "codex",
                "role": "orchestrator-reviewer",
                "hostname": "host",
                "pid": 10004,
                "cwd": "/tmp/project-orch",
                "repo_root": "/tmp/project-orch",
                "summary": "reviewing",
                "active_files_json": "[]",
                "started_at": 1.0,
                "last_seen": 1.0,
            }
        )
        store_module.PeerStore(
            {
                "peer_id": "peer-easy",
                "client": "opencode",
                "role": "easy-programmer",
                "hostname": "host",
                "pid": 10005,
                "cwd": "/tmp/project-easy",
                "repo_root": "/tmp/project-easy",
                "summary": "easy",
                "active_files_json": "[]",
                "started_at": 1.0,
                "last_seen": 1.0,
            }
        )
        store_module.PeerStore(
            {
                "peer_id": "peer-hard",
                "client": "cursor-agent",
                "role": "hard-programmer",
                "hostname": "host",
                "pid": 10006,
                "cwd": "/tmp/project-hard",
                "repo_root": "/tmp/project-hard",
                "summary": "hard",
                "active_files_json": "[]",
                "started_at": 1.0,
                "last_seen": 1.0,
            }
        )

        easy = codex.recommend_peer(task_kind="implement", difficulty="easy")
        self.assertEqual(easy["recommended"]["peer_id"], "peer-easy")

        hard = codex.recommend_peer(task_kind="implement", difficulty="hard")
        self.assertEqual(hard["recommended"]["peer_id"], "peer-hard")

        review = codex.recommend_peer(task_kind="review", difficulty="hard")
        self.assertEqual(review["recommended"]["peer_id"], "peer-orch")


if __name__ == "__main__":
    unittest.main()
