#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os

from store import PeerStore, check_messages_for_peer, cleanup_stale_peers, get_peer, set_summary_for_peer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-peers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    peers = subparsers.add_parser("peers", help="list active peers")
    peers.add_argument("--scope", choices=["machine", "repo", "directory"], default="machine")
    peers.add_argument("--include-self", action="store_true")
    peers.add_argument("--role")

    route = subparsers.add_parser("route", help="recommend a peer for a task")
    route.add_argument("--task-kind", choices=["implement", "review"], default="implement")
    route.add_argument("--difficulty", choices=["easy", "hard"], default="easy")

    send = subparsers.add_parser("send", help="send a message to a peer")
    send.add_argument("peer_id")
    send.add_argument("message")

    inbox = subparsers.add_parser("inbox", help="show unread messages")
    inbox.add_argument("--limit", type=int, default=20)
    inbox.add_argument("--keep-unread", action="store_true")

    poll = subparsers.add_parser("poll", help="show unread messages for the current AI_PEERS_SESSION_KEY or explicit peer id")
    poll.add_argument("--peer-id")
    poll.add_argument("--limit", type=int, default=20)
    poll.add_argument("--keep-unread", action="store_true")

    update = subparsers.add_parser("set-summary-for", help="update summary for the current AI_PEERS_SESSION_KEY or explicit peer id")
    update.add_argument("summary")
    update.add_argument("--peer-id")
    update.add_argument("--active-file", action="append", default=[])

    subparsers.add_parser("whoami", help="show current peer identity")
    cleanup = subparsers.add_parser("cleanup", help="remove stale peers")
    cleanup.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    session_peer_id = args.peer_id if hasattr(args, "peer_id") and args.peer_id else None
    if args.command == "poll":
        session_peer_id = session_peer_id or os.environ.get("AI_PEERS_SESSION_KEY")
        if not session_peer_id:
            raise SystemExit("Missing peer id. Set AI_PEERS_SESSION_KEY or pass --peer-id.")
        print(
            json.dumps(
                {
                    "peer": get_peer(session_peer_id),
                    "messages": check_messages_for_peer(
                        session_peer_id,
                        limit=args.limit,
                        mark_read=not args.keep_unread,
                    ),
                },
                indent=2,
            )
        )
        return

    if args.command == "set-summary-for":
        session_peer_id = session_peer_id or os.environ.get("AI_PEERS_SESSION_KEY")
        if not session_peer_id:
            raise SystemExit("Missing peer id. Set AI_PEERS_SESSION_KEY or pass --peer-id.")
        print(
            json.dumps(
                {
                    "peer": set_summary_for_peer(
                        session_peer_id,
                        summary=args.summary,
                        active_files=args.active_file,
                    )
                },
                indent=2,
            )
        )
        return

    store = PeerStore()
    try:
        if args.command == "peers":
            print(
                json.dumps(
                    {
                        "peers": store.list_peers(
                            scope=args.scope,
                            include_self=args.include_self,
                            role=args.role,
                        )
                    },
                    indent=2,
                )
            )
            return

        if args.command == "route":
            print(
                json.dumps(
                    store.recommend_peer(
                        task_kind=args.task_kind,
                        difficulty=args.difficulty,
                    ),
                    indent=2,
                )
            )
            return

        if args.command == "send":
            print(json.dumps({"sent": store.send_message(args.peer_id, args.message)}, indent=2))
            return

        if args.command == "inbox":
            print(
                json.dumps(
                    {
                        "messages": store.check_messages(
                            limit=args.limit,
                            mark_read=not args.keep_unread,
                        )
                    },
                    indent=2,
                )
            )
            return

        if args.command == "whoami":
            print(json.dumps(store.get_self(), indent=2))
            return

        if args.command == "cleanup":
            removed = cleanup_stale_peers()
            payload = {"removed": removed}
            print(json.dumps(payload, indent=2) if args.json else removed)
    finally:
        store.remove_self()


if __name__ == "__main__":
    main()
