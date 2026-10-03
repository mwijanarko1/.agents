#!/usr/bin/env python3
"""Send email via Himalaya v2 with hard attachment verification.

Himalaya 2.x does NOT compile MML <#part filename=...> tags. Those go out as
literal body text. Attachments must use:

  himalaya message compose --attach PATH --send

This wrapper:
  1. Verifies every --attach path exists and is non-empty
  2. Dry-runs compose and asserts each basename appears as a MIME attachment
  3. Only then sends (+ optional --save mailbox)
  4. Refuses --send if any expected attachment is missing from the dry-run MIME

Exit codes:
  0 ok
  2 usage / missing attachment file
  3 dry-run MIME missing expected attachment
  4 himalaya compose/send failed
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from email.utils import parseaddr
from pathlib import Path


def die(code: int, msg: str) -> None:
    print(f"himalaya-send: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, **kwargs)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("-a", "--account", required=True)
    p.add_argument(
        "--from-addr",
        required=True,
        help='e.g. "email@x.com"; a "Name <email>" form is reduced to the bare address',
    )
    p.add_argument("--to", action="append", required=True, help="Repeatable")
    p.add_argument("--cc", action="append", default=[])
    p.add_argument("--bcc", action="append", default=[])
    p.add_argument("-s", "--subject", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--body", help="Inline body text")
    g.add_argument("--body-file", type=Path, help="Body from file")
    p.add_argument(
        "--attach",
        action="append",
        default=[],
        type=Path,
        help="Attachment path (repeatable). Required if --require-attach.",
    )
    p.add_argument(
        "--require-attach",
        action="store_true",
        help="Fail if zero --attach paths given (use when the email must have files).",
    )
    p.add_argument(
        "--save",
        default="sent",
        help='Mailbox alias for sent copy (default: sent). Empty string skips save.',
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Compose + verify only; do not send.",
    )
    return p.parse_args()


def verify_attach_files(paths: list[Path]) -> list[Path]:
    resolved: list[Path] = []
    for raw in paths:
        path = raw.expanduser().resolve()
        if not path.is_file():
            die(2, f"attachment not found: {raw}")
        size = path.stat().st_size
        if size <= 0:
            die(2, f"attachment empty: {path}")
        resolved.append(path)
        print(f"himalaya-send: attach ok {path.name} ({size} bytes)")
    return resolved


def attachment_basenames_in_mime(mime: str) -> set[str]:
    names: set[str] = set()
    # Unfold RFC 5322 header continuation (CRLF/LF + WSP).
    unfolded = re.sub(r"\r?\n[ \t]+", " ", mime)
    # Content-Disposition: attachment; filename="X" or filename=X
    for m in re.finditer(
        r'Content-Disposition:\s*attachment\s*;.*?filename\*?=(?:UTF-8\'\'\')?"?([^";\r\n]+)"?',
        unfolded,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        names.add(Path(m.group(1).strip()).name)
    # Also catch name= on Content-Type
    for m in re.finditer(
        r'Content-Type:.*?name="?([^";\r\n]+)"?',
        unfolded,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        names.add(Path(m.group(1).strip()).name)
    return names


def build_compose_cmd(
    args: argparse.Namespace,
    attaches: list[Path],
    body_file: Path,
    send: bool,
) -> list[str]:
    cmd = [
        "himalaya",
        "-a",
        args.account,
        "message",
        "compose",
        "--from",
        # himalaya wraps the whole value in <>, so a display name breaks SMTP (Gmail 555)
        parseaddr(args.from_addr)[1] or args.from_addr,
        "--subject",
        args.subject,
        "--body-file",
        str(body_file),
    ]
    for to in args.to:
        cmd.extend(["--to", to])
    for cc in args.cc:
        cmd.extend(["--cc", cc])
    for bcc in args.bcc:
        cmd.extend(["--bcc", bcc])
    for path in attaches:
        cmd.extend(["--attach", str(path)])
    if send:
        cmd.append("--send")
        if args.save:
            cmd.extend(["--save", args.save])
    return cmd


def main() -> None:
    args = parse_args()

    if args.require_attach and not args.attach:
        die(2, "--require-attach set but no --attach paths given")

    attaches = verify_attach_files(args.attach)

    # Body file
    tmp_body: str | None = None
    if args.body_file is not None:
        body_path = args.body_file.expanduser().resolve()
        if not body_path.is_file():
            die(2, f"body file not found: {body_path}")
    else:
        fd, tmp_body = tempfile.mkstemp(prefix="himalaya-body-", suffix=".txt")
        os.write(fd, args.body.encode("utf-8"))
        os.close(fd)
        body_path = Path(tmp_body)

    try:
        # 1) Dry-run compose to MIME bytes
        dry_cmd = build_compose_cmd(args, attaches, body_path, send=False)
        dry = run(dry_cmd)
        if dry.returncode != 0:
            die(4, f"compose dry-run failed:\n{dry.stderr or dry.stdout}")

        mime = dry.stdout
        if attaches:
            found = attachment_basenames_in_mime(mime)
            missing = [p.name for p in attaches if p.name not in found]
            if missing:
                die(
                    3,
                    "dry-run MIME missing attachment(s): "
                    + ", ".join(missing)
                    + f"\nfound disposition names: {sorted(found) or '(none)'}"
                    + "\nDO NOT SEND. Fix compose/--attach before retrying.",
                )
            for p in attaches:
                # size sanity: pdf/name should appear and overall MIME larger than file
                if p.stat().st_size > 0 and len(mime) < p.stat().st_size:
                    die(3, f"dry-run MIME smaller than attachment {p.name}; refuse send")
            print(
                "himalaya-send: dry-run MIME verified attachments: "
                + ", ".join(p.name for p in attaches)
            )
        else:
            print("himalaya-send: no attachments (plain message)")

        if args.dry_run:
            print("himalaya-send: dry-run only; not sent")
            return

        # 2) Real send
        send_cmd = build_compose_cmd(args, attaches, body_path, send=True)
        sent = run(send_cmd)
        if sent.returncode != 0:
            die(4, f"send failed:\n{sent.stderr or sent.stdout}")
        out = (sent.stdout or sent.stderr or "").strip()
        print(out or "himalaya-send: sent ok")
        if attaches:
            print(
                "himalaya-send: sent with verified attachments: "
                + ", ".join(p.name for p in attaches)
            )
    finally:
        if tmp_body:
            try:
                os.unlink(tmp_body)
            except OSError:
                pass


if __name__ == "__main__":
    main()
