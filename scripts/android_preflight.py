#!/usr/bin/env python3
"""Fail fast when no Android device is ready for screen-state or mobile-mcp."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

SEAGATE_VOLUME = Path("/Volumes/Mikhail Seagate 2TB SSD")
DEFAULT_SDK = SEAGATE_VOLUME / "AndroidDev" / "sdk"


def parse_ready_serials(adb_devices_output: str) -> list[str]:
    ready: list[str] = []
    lines = adb_devices_output.splitlines()
    body = lines[1:] if lines and lines[0].lower().startswith("list of devices") else lines
    for line in body:
        text = line.strip()
        if not text or text.startswith("*"):
            continue
        parts = text.split()
        if len(parts) >= 2 and parts[1] == "device":
            ready.append(parts[0])
    return ready


def resolve_adb(sdk: Path) -> str | None:
    found = shutil.which("adb")
    if found:
        return found
    candidate = sdk / "platform-tools" / "adb"
    if candidate.is_file():
        return str(candidate)
    return None


def diagnose(sdk: Path) -> str:
    if not SEAGATE_VOLUME.exists():
        return (
            "Seagate volume is not mounted at "
            f"{SEAGATE_VOLUME}. Android SDK, emulator images, and Xcode live there."
        )
    if not sdk.exists():
        return f"ANDROID_HOME is missing: {sdk}"
    return "No device in state 'device'. Plug in a phone or boot an emulator before screen-state / mobile-mcp."


def main() -> int:
    sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or DEFAULT_SDK)
    adb = resolve_adb(sdk)
    if adb is None:
        print(f"android-preflight: adb not found. {diagnose(sdk)}", file=sys.stderr)
        return 2
    try:
        proc = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"android-preflight: adb failed: {exc}", file=sys.stderr)
        return 2
    output = proc.stdout or ""
    ready = parse_ready_serials(output)
    if not ready:
        print(f"android-preflight: no connected device. {diagnose(sdk)}", file=sys.stderr)
        text = output.strip() or "(empty adb devices)"
        print(text, file=sys.stderr)
        return 1
    print("\n".join(ready))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
