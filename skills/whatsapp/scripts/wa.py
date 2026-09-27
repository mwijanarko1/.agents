#!/usr/bin/env python3
"""WhatsApp: read local desktop DB, send via PinchTab Web."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CONFIG_PATH = Path.home() / ".pinchtab" / "config.json"
DEFAULT_SERVER = "http://127.0.0.1:9869"
WA_URL = "https://web.whatsapp.com"
# macOS WhatsApp Desktop (App Store / native) message store
CHAT_DB = (
    Path.home()
    / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
)
# Core Data epoch: seconds since 2001-01-01
CORE_DATA_EPOCH = 978307200
MSG_TYPE = {
    0: "text",
    1: "image",
    2: "video",
    3: "audio",
    4: "contact",
    5: "location",
    6: "system",
    7: "sticker",
    8: "document",
    10: "gif",
    11: "deleted",
    14: "deleted",
    15: "group_invite",
}
WA_DOMAINS = [
    "web.whatsapp.com",
    "whatsapp.com",
    "www.whatsapp.com",
    "static.whatsapp.net",
    "pps.whatsapp.net",
    "media.whatsapp.net",
    "mmg.whatsapp.net",
    "graph.whatsapp.com",
    "crashlogs.whatsapp.net",
    "dit.whatsapp.net",
]


class WaError(RuntimeError):
    pass


# WhatsApp Web page-text/snap extraction drops emoji (rendered as separate spans).
# Strip them from both sides before matching, so emoji-laden messages do not
# false-fail the draft check (which would retype and corrupt the composer) or
# the post-send verification (which would wrongly report not-sent).
_EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\U0001F1E6-\U0001F1FF]")


def strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text)


def run(
    args: list[str],
    *,
    server: str | None = None,
    check: bool = True,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    cmd = ["pinchtab"]
    if server:
        cmd += ["--server", server]
    cmd += args
    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if check and (
        proc.returncode != 0
        or out.startswith("Error")
        or out.startswith("ERROR")
        or err.startswith("Error")
        or err.startswith("ERROR")
    ):
        raise WaError(err or out or f"pinchtab failed: {' '.join(cmd)}")
    return proc


def ensure_domains() -> bool:
    """Add WhatsApp hosts to PinchTab allowlist. Returns True if config changed."""
    if not CONFIG_PATH.exists():
        raise WaError(f"missing pinchtab config: {CONFIG_PATH}")
    data = json.loads(CONFIG_PATH.read_text())
    security = data.setdefault("security", {})
    domains = security.get("allowedDomains") or []
    if not isinstance(domains, list):
        domains = []
    # repair mangled stringified-array fragments if present
    fixed: list[str] = []
    buf: list[str] = []
    for item in domains:
        if not isinstance(item, str):
            continue
        s = item.strip()
        if s.startswith("[") or (buf and (s.startswith('"') or s.endswith("]"))):
            buf.append(s)
            joined = "".join(buf)
            if joined.startswith("[") and joined.endswith("]"):
                try:
                    fixed.extend(json.loads(joined))
                    buf = []
                    continue
                except json.JSONDecodeError:
                    pass
            continue
        fixed.append(s)
    if buf:
        toks = re.findall(r'"([^"\\]+)"', "".join(buf))
        fixed = toks + fixed
    seen: set[str] = set()
    cleaned: list[str] = []
    for d in fixed:
        d = d.strip().strip('"').strip(",")
        if not d or d in seen:
            continue
        seen.add(d)
        cleaned.append(d)
    changed = False
    for d in WA_DOMAINS:
        if d not in seen:
            cleaned.append(d)
            seen.add(d)
            changed = True
    if cleaned != domains:
        changed = True
    if changed:
        security["allowedDomains"] = cleaned
        CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n")
    return changed


def server_ok() -> bool:
    try:
        proc = run(["health"], check=False, timeout=10)
        return proc.returncode == 0 and "ok" in (proc.stdout or "").lower()
    except Exception:
        return False


def ensure_server() -> None:
    if server_ok():
        return
    run(["server"], check=False, timeout=30)
    for _ in range(20):
        time.sleep(0.5)
        if server_ok():
            return
    raise WaError("pinchtab server failed to become healthy")


def parse_instances(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("{") or line.startswith("Command"):
            continue
        parts = line.split()
        if len(parts) >= 4 and parts[0].startswith("inst_"):
            rows.append(
                {
                    "id": parts[0],
                    "port": parts[1],
                    "mode": parts[2],
                    "status": parts[3],
                }
            )
    return rows


def ensure_headed(profile: str = "default") -> str:
    """Return bridge URL for a running headed instance."""
    ensure_server()
    proc = run(["instance", "list"], check=False)
    rows = parse_instances(proc.stdout or "")
    headed = [
        r
        for r in rows
        if r["mode"] == "headed" and r["status"] == "running"
    ]
    if headed:
        return f"http://127.0.0.1:{headed[0]['port']}"

    # stop conflicting headless default if present
    for r in rows:
        if r["status"] == "running":
            run(["instance", "stop", r["id"]], check=False)

    if ensure_domains():
        run(["server", "restart"], check=False, timeout=60)
        time.sleep(1.5)
        ensure_server()

    start = run(
        ["instance", "start", "--profile", profile, "--mode", "headed"],
        check=False,
        timeout=60,
    )
    out = start.stdout or ""
    try:
        payload = json.loads(out)
        port = str(payload.get("port") or "")
        if port:
            # wait until running
            for _ in range(30):
                time.sleep(0.5)
                rows = parse_instances(run(["instance", "list"], check=False).stdout or "")
                if any(
                    r["port"] == port and r["status"] == "running" for r in rows
                ):
                    return f"http://127.0.0.1:{port}"
            return f"http://127.0.0.1:{port}"
    except json.JSONDecodeError:
        pass

    rows = parse_instances(run(["instance", "list"], check=False).stdout or "")
    headed = [r for r in rows if r["mode"] == "headed" and r["status"] == "running"]
    if headed:
        return f"http://127.0.0.1:{headed[0]['port']}"
    raise WaError(f"could not start headed instance:\n{out}\n{start.stderr}")


def snap(server: str) -> str:
    return run(["snap"], server=server, timeout=30).stdout or ""


def page_text(server: str) -> str:
    return run(["text"], server=server, timeout=30).stdout or ""


def current_url(server: str) -> str:
    return (run(["url"], server=server, timeout=15).stdout or "").strip()


def wa_tabs(server: str) -> list[dict]:
    """Tabs in the instance as [{id, title, url, status}], from tab --json."""
    out = run(["tab", "--json"], server=server, timeout=20).stdout or ""
    try:
        payload = json.loads(out)
    except json.JSONDecodeError:
        return []
    return payload.get("tabs") or []


def ensure_wa_tab(server: str) -> None:
    """Make an existing WhatsApp Web tab the active tab, or open one.

    The headed window is shared and can have other tabs active; snapshots and
    clicks only see the active tab, so operations must run against the
    web.whatsapp.com tab specifically (2026-09-08: a non-WhatsApp active tab
    made every search/click behave as if the page were broken).
    """
    wa = [t for t in wa_tabs(server) if "web.whatsapp.com" in (t.get("url") or "")]
    if wa:
        if wa[0].get("status") != "active":
            run(["tab", wa[0]["id"]], server=server, timeout=20)
            time.sleep(0.8)
        return
    url = current_url(server)
    if "web.whatsapp.com" not in url:
        run(["nav", WA_URL], server=server, timeout=90)
        time.sleep(2)


def login_state(server: str) -> str:
    """Return logged_in | needs_qr | unknown."""
    ensure_wa_tab(server)
    t = page_text(server)
    s = snap(server)
    low = (t + "\n" + s).lower()
    if "scan to log in" in low or "scan this qr code" in low:
        return "needs_qr"
    if (
        "type a message" in low
        or 'textbox "search or start a new chat"' in low
        or "search or start a new chat" in low
        or re.search(r'button "chats"', low)
        or "favorites" in low
        or "favourites" in low
        or re.search(r"\bunread\b", low)
    ):
        return "logged_in"
    if "chats" in low and "whatsapp" in low:
        return "logged_in"
    return "unknown"


def search_box_ref(snap_text: str) -> str | None:
    return ref_for(snap_text, r'textbox "Search or start a new chat"') or ref_for(
        snap_text, r'textbox "Search'
    )


def ui_ready(snap_text: str) -> bool:
    """True when WA Web shows an interactive control, not just chrome text."""
    return bool(
        search_box_ref(snap_text)
        or ref_for(snap_text, r'button "New chat"')
        or ref_for(snap_text, r'textbox "Type a message')
    )


def is_viewport_error(msg: str) -> bool:
    low = msg.lower()
    return "viewport" in low and (
        "outside" in low or "out of" in low or "not in" in low
    )


def wait_for_ui(server: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while True:
        try:
            if ui_ready(snap(server)):
                return True
        except (WaError, subprocess.TimeoutExpired):
            pass
        if time.time() >= deadline:
            return False
        time.sleep(0.5)


def instance_id_for_server(server: str) -> str | None:
    port = server.rsplit(":", 1)[-1].rstrip("/")
    rows = parse_instances(run(["instance", "list"], check=False).stdout or "")
    for r in rows:
        if r["port"] == port:
            return r["id"]
    headed = [r for r in rows if r["mode"] == "headed" and r["status"] == "running"]
    return headed[0]["id"] if headed else None


def recover_session(server: str, profile: str = "default") -> str:
    """Reload, re-nav, then restart the headed instance until WA UI is usable."""
    run(["reload"], server=server, check=False, timeout=60)
    if wait_for_ui(server):
        return server
    run(["nav", WA_URL], server=server, check=False, timeout=90)
    if wait_for_ui(server):
        return server
    inst = instance_id_for_server(server)
    if inst:
        if run(["instance", "restart", inst], check=False, timeout=90).returncode != 0:
            # older servers lack POST /instances/<id>/restart; stop and start on the same port
            port = server.rsplit(":", 1)[-1].rstrip("/")
            run(["instance", "stop", inst], check=False, timeout=60)
            run(
                ["instance", "start", "--profile", profile, "--mode", "headed", "--port", port],
                check=False,
                timeout=90,
            )
        time.sleep(2)
        ensure_wa_tab(server)
        if wait_for_ui(server):
            return server
    raise WaError(
        "whatsapp web session unusable after reload, re-nav, and instance restart; "
        "check the headed Helium window (off-screen or QR login)"
    )


def prepare_session(server: str, profile: str = "default") -> str:
    """Pre-send health check. Recover a stale session before any chat click."""
    ensure_wa_tab(server)
    state = login_state(server)
    if state == "needs_qr":
        raise WaError("not logged in: scan QR in the headed Helium window first")
    try:
        if ui_ready(snap(server)):
            return server
    except (WaError, subprocess.TimeoutExpired):
        pass
    return recover_session(server, profile)


def click_ref(server: str, ref: str) -> None:
    try:
        run(["click", ref], server=server)
        return
    except WaError as exc:
        if not is_viewport_error(str(exc)):
            raise
    run(["scroll", ref], server=server, check=False)
    run(["click", ref], server=server)


_OPEN_DB_TMP: dict[int, Path] = {}


def open_chat_db(readonly: bool = True) -> sqlite3.Connection:
    """Snapshot ChatStorage.sqlite (includes WAL) into a temp DB and open it."""
    if not CHAT_DB.exists():
        raise WaError(f"WhatsApp desktop DB missing: {CHAT_DB}")
    fd, name = tempfile.mkstemp(prefix="wa-ChatStorage-", suffix=".sqlite")
    os.close(fd)
    tmp = Path(name)
    try:
        src = sqlite3.connect(f"file:{CHAT_DB}?mode=ro", uri=True)
        dst = sqlite3.connect(tmp)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()
        con = sqlite3.connect(tmp)
        con.row_factory = sqlite3.Row
        _OPEN_DB_TMP[id(con)] = tmp
        return con
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def close_chat_db(con: sqlite3.Connection) -> None:
    tmp = _OPEN_DB_TMP.pop(id(con), None)
    con.close()
    if tmp is not None:
        tmp.unlink(missing_ok=True)
        for side in (f"{tmp}-wal", f"{tmp}-shm"):
            Path(side).unlink(missing_ok=True)


def find_sessions(con: sqlite3.Connection, contact: str, limit: int = 20) -> list[dict]:
    q = f"%{contact}%"
    rows = con.execute(
        """
        SELECT Z_PK, ZPARTNERNAME, ZCONTACTJID, ZSESSIONTYPE, ZARCHIVED,
               datetime(ZLASTMESSAGEDATE + ?, 'unixepoch', 'localtime') AS last_at,
               ZLASTMESSAGETEXT
        FROM ZWACHATSESSION
        WHERE ZPARTNERNAME LIKE ? COLLATE NOCASE
           OR ZCONTACTJID LIKE ? COLLATE NOCASE
        ORDER BY
          CASE WHEN ZPARTNERNAME = ? COLLATE NOCASE THEN 0
               WHEN ZPARTNERNAME LIKE ? COLLATE NOCASE THEN 1
               ELSE 2 END,
          ZLASTMESSAGEDATE DESC
        LIMIT ?
        """,
        (CORE_DATA_EPOCH, q, q, contact, q, limit),
    ).fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "session_id": r["Z_PK"],
                "name": r["ZPARTNERNAME"],
                "jid": r["ZCONTACTJID"],
                "session_type": r["ZSESSIONTYPE"],  # 0=dm, 1=group typical
                "archived": bool(r["ZARCHIVED"]),
                "last_at": r["last_at"],
            }
        )
    return out


def pick_session(con: sqlite3.Connection, contact: str) -> dict:
    sessions = find_sessions(con, contact)
    if not sessions:
        raise WaError(f"no chat session matching {contact!r} in desktop DB")
    # Prefer exact name DM (session_type 0)
    exact_dm = [
        s
        for s in sessions
        if (s["name"] or "").casefold() == contact.casefold() and s["session_type"] == 0
    ]
    if exact_dm:
        return exact_dm[0]
    exact = [s for s in sessions if (s["name"] or "").casefold() == contact.casefold()]
    if exact:
        return exact[0]
    dms = [s for s in sessions if s["session_type"] == 0]
    if dms:
        return dms[0]
    return sessions[0]


def read_messages(con: sqlite3.Connection, session_id: int, limit: int = 20) -> list[dict]:
    rows = con.execute(
        """
        SELECT m.Z_PK, m.ZISFROMME, m.ZMESSAGETYPE, m.ZMESSAGESTATUS,
               datetime(m.ZMESSAGEDATE + ?, 'unixepoch', 'localtime') AS ts,
               m.ZTEXT,
               mi.ZMOVIEDURATION, mi.ZTITLE, mi.ZMEDIALOCALPATH, mi.ZFILESIZE
        FROM ZWAMESSAGE m
        LEFT JOIN ZWAMEDIAITEM mi ON mi.Z_PK = m.ZMEDIAITEM
        WHERE m.ZCHATSESSION = ?
        ORDER BY m.ZMESSAGEDATE DESC, m.Z_PK DESC
        LIMIT ?
        """,
        (CORE_DATA_EPOCH, session_id, limit),
    ).fetchall()
    out: list[dict] = []
    for r in rows:
        mtype = r["ZMESSAGETYPE"]
        text = r["ZTEXT"]
        kind = MSG_TYPE.get(mtype, f"type_{mtype}")
        body = text
        if not body:
            if kind == "video":
                dur = r["ZMOVIEDURATION"] or 0
                body = f"[video {dur}s]"
            elif kind == "image":
                body = "[image]"
            elif kind == "audio":
                body = "[audio]"
            elif kind == "sticker":
                body = "[sticker]"
            elif kind == "document":
                body = f"[document {r['ZTITLE'] or ''}]".strip()
            elif kind.startswith("deleted"):
                body = "[deleted]"
            else:
                body = f"[{kind}]"
        out.append(
            {
                "id": r["Z_PK"],
                "ts": r["ts"],
                "from_me": bool(r["ZISFROMME"]),
                "sender": "me" if r["ZISFROMME"] else "them",
                "type": kind,
                "text": body,
                "media_path": r["ZMEDIALOCALPATH"],
            }
        )
    # chronological for display
    out.reverse()
    return out


def last_text_snippet(
    con: sqlite3.Connection, session_id: int, limit: int = 12
) -> str | None:
    """Most recent text from the chat, used as a content fingerprint.

    Two chats can share a display name (2026-09-08: Aarush Aerospace DM vs a
    bare LID contact). WhatsApp Web gives no stable per-chat handle in the
    snapshot, but the intended chat's recent text is unique enough to confirm
    which thread actually opened before anything is typed.
    """
    rows = read_messages(con, session_id, limit=limit)
    for m in reversed(rows):
        if m["type"] == "text" and m["text"] and not m["from_me"]:
            return m["text"][:120]
    for m in reversed(rows):
        if m["type"] == "text" and m["text"]:
            return m["text"][:120]
    return None


def ref_for(snap_text: str, pattern: str) -> str | None:
    rx = re.compile(pattern, re.I)
    for line in snap_text.splitlines():
        m = re.match(r"(e\d+):", line)
        if not m:
            continue
        if rx.search(line):
            return m.group(1)
    return None


def open_thread_composer_name(snap_text: str) -> str | None:
    """Name of the chat whose thread is open in the main pane, or None.

    WhatsApp Web labels the open thread's input as "Type a message to <name>"
    (direct chat) or "Type a message to group <name>" (group). The label only
    exists on the thread that is actually open, so it is the reliable way to
    tell which chat a send would land in.
    """
    m = re.search(r'textbox "Type a message to (?:group )?([^"]+)"', snap_text)
    return m.group(1) if m else None


def thread_has_message_timestamps(snap_text: str) -> bool:
    """True when the open thread pane shows any message timestamps.

    A brand new chat started from a bare contact shows no message bubbles, so
    no clock rows. A chat with history shows rows such as button "10:59 PM".
    Used to catch the Web session opening an empty impostor chat that merely
    shares the requested display name.
    """
    return re.search(r'button "\d{1,2}:\d{2}', snap_text) is not None


def open_chat(server: str, contact: str, profile: str = "default") -> None:
    prepare_session(server, profile)
    s = snap(server)
    # Already open and it is the requested chat: no search needed. Searching
    # from here can switch away or fail on chats the Web account cannot find
    # by name (2026-09-08: the Aarush Aerospace DM was open but its search row
    # did not exist in the Web session).
    if open_thread_composer_name(s) is not None:
        open_name = open_thread_composer_name(s)
        if open_name.casefold() == contact.casefold():
            return
    s = snap(server)
    search = search_box_ref(s) or ref_for(s, r"textbox val=")
    if not search:
        new_chat = ref_for(s, r'button "New chat"')
        if new_chat:
            click_ref(server, new_chat)
            time.sleep(0.5)
            s = snap(server)
            search = search_box_ref(s) or ref_for(s, r"textbox")
    if not search:
        raise WaError("could not find chat search box")

    click_ref(server, search)
    run(["fill", search, contact], server=server)
    time.sleep(1.4)

    # Open the chat by clicking its exact result row. Clicking bare text can
    # hit the search box's own typed value and refocus the input instead of
    # opening the chat (2026-09-08: the Aarush Aerospace DM would not open via
    # text: click). The loop below tries the row, falls back to text, and the
    # hard-verify guard aborts loudly instead of mis-sending into the thread
    # that happens to be open.
    open_name = None
    for attempt in range(4):
        s = snap(server)
        open_name = open_thread_composer_name(s)
        if open_name is not None and open_name.casefold() == contact.casefold():
            return
        row = ref_for(
            s,
            rf'button "{re.escape(contact)}"(\s|$)|'
            rf'listitem "{re.escape(contact)}"(\s|$)',
        )
        if row is None:
            row = ref_for(s, rf'button "{re.escape(contact)}')
        if row is not None:
            click_ref(server, row)
        else:
            click_ref(server, f"text:{contact}")
        time.sleep(0.9)
    s = snap(server)
    open_name = open_thread_composer_name(s)
    t = page_text(server)
    if contact in t.split("Chats", 1)[-1][:400] or contact in t:
        raise WaError(
            f"contact {contact!r} found in search but thread would not open; "
            "nothing was sent. re-run ensure and check the headed window"
        )
    raise WaError(
        f"refusing to send: open thread is {open_name or '<no composer>'!r}, "
        f"requested {contact!r}. nothing was sent"
    )


def send_message(
    server: str,
    contact: str,
    message: str,
    profile: str = "default",
    expect_history: bool = True,
    history_probe: str | None = None,
) -> None:
    open_chat(server, contact, profile)
    s = snap(server)
    # Re-check the open thread right before typing. open_chat verified it, but
    # the shared headed window can switch threads between the two calls.
    open_name = open_thread_composer_name(s)
    if open_name is None or open_name.casefold() != contact.casefold():
        raise WaError(
            f"thread changed before send: expected {contact!r}, "
            f"open is {open_name or '<no composer>'!r}. nothing was sent"
        )
    if expect_history and not thread_has_message_timestamps(s):
        raise WaError(
            f"open thread {contact!r} shows no message history, but the desktop "
            "DB chat has messages. The Web session likely opened a different "
            "chat with the same name (2026-09-08 Aarush incident). Do not "
            "guess: ask the user which chat they mean. nothing was sent"
        )
    if history_probe:
        t = page_text(server)
        if history_probe not in t:
            raise WaError(
                f"open thread content does not match the desktop chat: expected "
                f"recent text {history_probe[:60]!r} but it is not in the open "
                "thread. Likely a different chat with the same name. Ask the "
                "user which chat they mean. nothing was sent"
            )
    composer = ref_for(s, r'textbox "Type a message')
    if not composer:
        raise WaError("message composer not found")

    # WhatsApp composer ignores fill(); keystrokes required
    click_ref(server, composer)
    run(["type", composer, message], server=server)
    time.sleep(0.3)
    s = snap(server)
    # confirm draft landed (compare emoji-stripped: extraction drops emoji)
    if strip_emoji(message) not in strip_emoji(s) and (
        f'val="{strip_emoji(message)}"' not in strip_emoji(s)
    ):
        # retry once with keyboard insert
        run(["click", composer], server=server, check=False)
        run(["keyboard", "type", message], server=server, check=False)
        time.sleep(0.3)
        s = snap(server)
        if strip_emoji(message) not in strip_emoji(s) and (
            f'val="{strip_emoji(message)}"' not in strip_emoji(s)
        ):
            raise WaError("failed to enter message into composer (fill is broken; type failed)")

    send_btn = ref_for(s, r'button "Send"')
    if not send_btn:
        # Enter often works when Send is present but unlabeled briefly
        run(["press", "Enter"], server=server)
    else:
        click_ref(server, send_btn)

    # verify (compare emoji-stripped: page text drops emoji, causing false failures)
    deadline = time.time() + 12
    last = ""
    while time.time() < deadline:
        time.sleep(0.8)
        last = page_text(server)
        if strip_emoji(message) in strip_emoji(last):
            # pending/delivered either fine if body present in thread
            print(
                json.dumps(
                    {
                        "ok": True,
                        "contact": contact,
                        "message": message,
                        "status": "present_in_thread",
                    }
                )
            )
            return
    raise WaError(
        f"message not observed in thread after send.\nlast text snippet:\n{last[:800]}"
    )


def cmd_ensure(args: argparse.Namespace) -> int:
    changed = ensure_domains()
    if changed:
        ensure_server()
        run(["server", "restart"], check=False, timeout=60)
        time.sleep(1.5)
    server = ensure_headed(args.profile)
    try:
        server = prepare_session(server, args.profile)
        state = login_state(server)
        ready = ui_ready(snap(server))
    except WaError as exc:
        if "scan QR" in str(exc):
            state = "needs_qr"
            ready = False
        else:
            raise
    print(
        json.dumps(
            {
                "ok": True,
                "server": server,
                "domains_updated": changed,
                "login": state,
                "ui_ready": ready,
            }
        )
    )
    if state == "needs_qr":
        print(
            "ACTION: scan QR in headed Helium window (WhatsApp phone → Linked devices)",
            file=sys.stderr,
        )
        return 2
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    server = args.server or ensure_headed(args.profile)
    ensure_wa_tab(server)
    state = login_state(server)
    ready = False
    try:
        ready = ui_ready(snap(server))
    except (WaError, subprocess.TimeoutExpired):
        pass
    print(
        json.dumps(
            {
                "ok": True,
                "server": server,
                "login": state,
                "ui_ready": ready,
                "url": current_url(server),
            }
        )
    )
    if state == "needs_qr":
        return 2
    return 0 if ready else 2


def cmd_open(args: argparse.Namespace) -> int:
    server = args.server or ensure_headed(args.profile)
    open_chat(server, args.contact, args.profile)
    print(json.dumps({"ok": True, "server": server, "contact": args.contact, "opened": True}))
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    server = args.server or ensure_headed(args.profile)
    message = args.message
    if message is None and args.message_file:
        message = Path(args.message_file).read_text().rstrip("\n")
    if not message:
        raise WaError("empty message")
    # Recipient safety. Two chats can share a display name (2026-09-08: a DM
    # with history and a bare LID contact were both "Aarush Aerospace"), so the
    # name alone is not enough. Resolve the intended chat from the desktop DB
    # and refuse to guess when it is missing or ambiguous.
    con = open_chat_db()
    try:
        candidates = [
            s
            for s in find_sessions(con, args.contact, limit=100)
            if not s["archived"]
            and (s["name"] or "").casefold() == args.contact.casefold()
            and s["session_type"] in (0, 1)
        ]
    finally:
        close_chat_db(con)
    if args.jid:
        wanted = args.jid.casefold()
        candidates = [c for c in candidates if (c["jid"] or "").casefold() == wanted]
        if not candidates:
            raise WaError(
                f"no chat named {args.contact!r} with jid {args.jid!r} in the "
                "desktop DB. Ask the user which chat they mean"
            )
    if not candidates:
        raise WaError(
            f"no chat named {args.contact!r} in the desktop DB. Ask the user "
            "which chat they mean before messaging anything"
        )
    if len(candidates) > 1:
        detail = "; ".join(
            f"type={c['session_type']} jid={c['jid']} last={c['last_at']}"
            for c in candidates
        )
        raise WaError(
            f"{len(candidates)} chats are named {args.contact!r} ({detail}). "
            "Ask the user which one they mean before sending"
        )
    con = open_chat_db()
    try:
        probe = last_text_snippet(con, candidates[0]["session_id"])
    finally:
        close_chat_db(con)
    send_message(
        server,
        args.contact,
        message,
        args.profile,
        expect_history=bool(candidates[0]["last_at"]),
        history_probe=probe,
    )
    return 0


def cmd_chats(args: argparse.Namespace) -> int:
    con = open_chat_db()
    try:
        q = args.query or "%"
        if args.query:
            sessions = find_sessions(con, args.query, limit=args.limit)
        else:
            rows = con.execute(
                """
                SELECT Z_PK, ZPARTNERNAME, ZCONTACTJID, ZSESSIONTYPE, ZARCHIVED,
                       datetime(ZLASTMESSAGEDATE + ?, 'unixepoch', 'localtime') AS last_at
                FROM ZWACHATSESSION
                WHERE ZPARTNERNAME IS NOT NULL AND TRIM(ZPARTNERNAME) != ''
                ORDER BY ZLASTMESSAGEDATE DESC
                LIMIT ?
                """,
                (CORE_DATA_EPOCH, args.limit),
            ).fetchall()
            sessions = [
                {
                    "session_id": r["Z_PK"],
                    "name": r["ZPARTNERNAME"],
                    "jid": r["ZCONTACTJID"],
                    "session_type": r["ZSESSIONTYPE"],
                    "archived": bool(r["ZARCHIVED"]),
                    "last_at": r["last_at"],
                }
                for r in rows
            ]
        print(json.dumps({"ok": True, "db": str(CHAT_DB), "query": args.query, "chats": sessions}))
        return 0
    finally:
        close_chat_db(con)


def cmd_read(args: argparse.Namespace) -> int:
    con = open_chat_db()
    try:
        session = pick_session(con, args.contact)
        messages = read_messages(con, session["session_id"], limit=args.limit)
        print(
            json.dumps(
                {
                    "ok": True,
                    "source": "desktop_db",
                    "db": str(CHAT_DB),
                    "contact": session["name"],
                    "jid": session["jid"],
                    "session_id": session["session_id"],
                    "session_type": session["session_type"],
                    "count": len(messages),
                    "messages": messages,
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        close_chat_db(con)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="wa.py",
        description="WhatsApp: read desktop ChatStorage.sqlite; send via PinchTab Web",
    )
    p.add_argument("--profile", default=os.environ.get("WA_PROFILE", "default"))
    p.add_argument("--server", default=os.environ.get("WA_SERVER"))
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("ensure", help="domains + headed instance + WA tab (send path)")
    e.set_defaults(func=cmd_ensure)

    s = sub.add_parser("status", help="PinchTab Web login state")
    s.set_defaults(func=cmd_status)

    o = sub.add_parser("open", help="open a chat in PinchTab Web")
    o.add_argument("contact")
    o.set_defaults(func=cmd_open)

    snd = sub.add_parser("send", help="send a message via PinchTab Web")
    snd.add_argument("contact")
    snd.add_argument("message", nargs="?", default=None)
    snd.add_argument("--message-file", "-f")
    snd.add_argument("--jid", help="exact chat jid to disambiguate same-name chats")
    snd.set_defaults(func=cmd_send)

    ch = sub.add_parser("chats", help="list/search chats from desktop DB")
    ch.add_argument("query", nargs="?", default=None)
    ch.add_argument("--limit", type=int, default=30)
    ch.set_defaults(func=cmd_chats)

    rd = sub.add_parser("read", help="read recent messages from desktop DB")
    rd.add_argument("contact")
    rd.add_argument("--limit", type=int, default=20)
    rd.set_defaults(func=cmd_read)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except WaError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired as exc:
        print(json.dumps({"ok": False, "error": f"timeout: {exc}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
