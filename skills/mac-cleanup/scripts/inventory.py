#!/usr/bin/env python3
"""Dry-run inventory for mac-cleanup skill. No deletes."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HOME = Path.home()

HISTORY_DIR = Path.home() / ".config" / "mac-cleanup"
HISTORY_FILE = HISTORY_DIR / "history.jsonl"
DELTA_FLOOR = 25 * 1024 * 1024  # ignore changes smaller than 25 MB in diffs


@dataclass
class Item:
    tier: str
    path: str
    size_bytes: int
    reason: str
    risk: str

    @property
    def size_human(self) -> str:
        return human(self.size_bytes)


def human(n: int) -> str:
    step = 1024.0
    x = float(n)
    for unit in ("B", "K", "M", "G", "T"):
        if abs(x) < step or unit == "T":
            if unit == "B":
                return f"{int(x)}B"
            return f"{x:.1f}{unit}"
        x /= step
    return f"{n}B"


def du_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        out = subprocess.check_output(
            ["du", "-sk", str(path)], stderr=subprocess.DEVNULL, text=True
        )
        kb = int(out.split()[0])
        return kb * 1024
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return 0


def env_path(name: str) -> Path | None:
    v = os.environ.get(name)
    if not v:
        return None
    p = Path(v).expanduser()
    return p if p.exists() else None


def add(
    items: list[Item],
    tier: str,
    path: Path | str,
    reason: str,
    risk: str = "low",
    min_bytes: int = 0,
) -> None:
    p = Path(path).expanduser()
    if not p.exists():
        return
    size = du_bytes(p)
    if size < min_bytes:
        return
    items.append(
        Item(tier=tier, path=str(p), size_bytes=size, reason=reason, risk=risk)
    )


def find_user_var_folders() -> list[Path]:
    root = Path("/private/var/folders")
    if not root.is_dir():
        return []
    found: list[Path] = []
    try:
        for mid in root.iterdir():
            if not mid.is_dir():
                continue
            for uid in mid.iterdir():
                if not uid.is_dir():
                    continue
                # Heuristic: contains T or C owned dirs for this user
                if any((uid / x).is_dir() for x in ("T", "C", "X", "0")):
                    found.append(uid)
    except PermissionError:
        pass
    return found


def cache_whitelist_names() -> set[str]:
    return {
        "CloudKit",
        "ms-playwright",
        "ms-playwright-mcp",
        "ms-playwright-go",
        "JetBrains",
        "com.jetbrains",
        "ollama",
        "HuggingFace",
        "huggingface",
        "Surge",
        "com.west2online.Surge",
    }


def inventory(min_mb: float, tiers: set[str] | None) -> list[Item]:
    min_bytes = int(min_mb * 1024 * 1024)
    items: list[Item] = []

    def want(tier: str) -> bool:
        return tiers is None or tier in tiers

    # --- safe ---
    if want("safe"):
        for p, reason in [
            (HOME / ".npm" / "_cacache", "npm cache"),
            (HOME / ".npm" / "_npx", "npx cache"),
            (HOME / ".bun" / "install" / "cache", "bun install cache"),
            (HOME / "Library" / "Caches" / "bun", "bun Library cache"),
            (HOME / "Library" / "pnpm" / "store", "pnpm store"),
            (HOME / ".pi" / "agent" / "tmp", "pi agent temp"),
            (HOME / "Library" / "Developer" / "Xcode" / "DerivedData", "Xcode DerivedData"),
            (
                HOME / "Library" / "Developer" / "XcodeBuildMCP" / "workspaces",
                "XcodeBuildMCP workspaces",
            ),
            (
                HOME
                / "Library"
                / "Application Support"
                / "Cursor"
                / "CachedData",
                "Cursor CachedData",
            ),
            (
                HOME
                / "Library"
                / "Application Support"
                / "Cursor"
                / "CachedExtensionVSIXs",
                "Cursor extension VSIX cache",
            ),
            (
                HOME / "Library" / "Application Support" / "Cursor" / "Cache",
                "Cursor Cache",
            ),
            (
                HOME / "Library" / "Application Support" / "Cursor" / "GPUCache",
                "Cursor GPUCache",
            ),
            (
                HOME / "Library" / "Application Support" / "Cursor" / "logs",
                "Cursor logs",
            ),
            (
                HOME
                / "Library"
                / "Application Support"
                / "Cursor"
                / "User"
                / "globalStorage"
                / "anysphere.cursor-agent-worker",
                "Cursor agent-worker",
            ),
            (HOME / "Library" / "Caches" / "net.imput.helium", "Helium cache"),
            (HOME / "Library" / "Caches" / "Homebrew", "Homebrew cache"),
            (HOME / "Library" / "Caches" / "node-gyp", "node-gyp cache"),
            (HOME / ".cache" / "uv", "uv cache"),
            (HOME / ".cache" / "hyperframes", "hyperframes cache"),
            (HOME / ".cache" / "chrome-devtools-mcp", "chrome-devtools-mcp cache"),
            (HOME / ".cursor" / "worktrees", "Cursor agent worktrees"),
        ]:
            add(items, "safe", p, reason, min_bytes=min_bytes)

        # Library/Caches except whitelist (report large only)
        caches = HOME / "Library" / "Caches"
        wl = cache_whitelist_names()
        if caches.is_dir():
            try:
                for child in caches.iterdir():
                    name = child.name
                    if name in wl or any(name.startswith(w) for w in wl):
                        continue
                    if name == "CloudKit":
                        continue
                    add(
                        items,
                        "safe",
                        child,
                        f"Library/Caches/{name}",
                        min_bytes=max(min_bytes, 20 * 1024 * 1024),
                    )
            except PermissionError:
                pass

        # CloudKit bird MMCS tmpm only
        bird = HOME / "Library" / "Caches" / "CloudKit" / "com.apple.bird"
        if bird.is_dir():
            for tmpm in bird.glob("**/MMCS/tmpm-*"):
                add(
                    items,
                    "safe",
                    tmpm,
                    "CloudKit/iCloud Drive stuck MMCS temp",
                    risk="low",
                    min_bytes=min_bytes,
                )

        # Helium App Support caches (not full profile)
        helium = HOME / "Library" / "Application Support" / "net.imput.helium"
        for rel, reason in [
            ("GraphiteDawnCache", "Helium GraphiteDawnCache"),
            ("Crashpad", "Helium Crashpad"),
            ("Default/GPUCache", "Helium GPUCache"),
            ("Default/DawnWebGPUCache", "Helium DawnWebGPUCache"),
            ("Default/Code Cache", "Helium Code Cache"),
            ("Default/Service Worker/CacheStorage", "Helium SW CacheStorage"),
        ]:
            add(items, "safe", helium / rel, reason, min_bytes=min_bytes)

        # var/folders user temps
        for base in find_user_var_folders():
            add(
                items,
                "safe",
                base / "X",
                "var/folders X (often Helium code_sign_clone)",
                risk="low",
                min_bytes=min_bytes,
            )
            t = base / "T"
            if t.is_dir():
                for name in (
                    "eas-build-local-nodejs",
                    "eas-cli-nodejs",
                    "metro-cache",
                    "node-compile-cache",
                    "jest_dx",
                ):
                    add(items, "safe", t / name, f"var/folders T/{name}", min_bytes=min_bytes)
                try:
                    for child in t.iterdir():
                        if child.name.startswith("metro-file-map-"):
                            add(
                                items,
                                "safe",
                                child,
                                "var/folders metro-file-map",
                                min_bytes=min_bytes,
                            )
                except PermissionError:
                    pass
            add(
                items,
                "safe",
                base / "C" / "clang",
                "var/folders clang cache",
                min_bytes=min_bytes,
            )

        # diagnostics size (clean via log erase, not rm)
        add(
            items,
            "safe",
            Path("/private/var/db/diagnostics"),
            "unified logs (use: log erase --all, admin)",
            risk="low",
            min_bytes=min_bytes,
        )

    # --- duplicates ---
    if want("duplicates"):
        android_home = env_path("ANDROID_HOME") or env_path("ANDROID_SDK_ROOT")
        lib_android = HOME / "Library" / "Android"
        if lib_android.exists() and android_home is not None:
            try:
                if lib_android.resolve() != android_home.resolve():
                    add(
                        items,
                        "duplicates",
                        lib_android,
                        f"duplicate Android SDK; env points to {android_home}",
                        risk="medium",
                        min_bytes=min_bytes,
                    )
            except OSError:
                pass

        gradle_home = env_path("GRADLE_USER_HOME")
        default_gradle = HOME / ".gradle"
        if default_gradle.exists() and gradle_home is not None:
            try:
                if default_gradle.resolve() != gradle_home.resolve():
                    add(
                        items,
                        "duplicates",
                        default_gradle,
                        f"duplicate Gradle home; GRADLE_USER_HOME={gradle_home}",
                        risk="medium",
                        min_bytes=min_bytes,
                    )
            except OSError:
                pass

        # rustup multiple toolchains
        toolchains = HOME / ".rustup" / "toolchains"
        if toolchains.is_dir():
            try:
                tcs = [p for p in toolchains.iterdir() if p.is_dir()]
                if len(tcs) > 1:
                    for tc in tcs:
                        add(
                            items,
                            "duplicates",
                            tc,
                            "extra rustup toolchain (keep one active)",
                            risk="medium",
                            min_bytes=min_bytes,
                        )
            except PermissionError:
                pass

    # --- build-artifacts ---
    if want("build-artifacts"):
        add(
            items,
            "build-artifacts",
            HOME / "Library" / "Developer" / "Xcode" / "Archives",
            "Xcode Archives (loses archived builds)",
            risk="medium",
            min_bytes=min_bytes,
        )
        # common project roots
        roots = [
            HOME / "Documents" / "CURSOR-CODES",
            HOME / "Documents",
            HOME / "projects",
        ]
        names = {".next", ".open-next", ".turbo", ".cxx"}
        for root in roots:
            if not root.is_dir():
                continue
            try:
                for dirpath, dirnames, _filenames in os.walk(root):
                    base = Path(dirpath)
                    # prune huge/irrelevant
                    dirnames[:] = [
                        d
                        for d in dirnames
                        if d not in {".git", "node_modules", "Pods", ".venv", "venv"}
                    ]
                    for d in list(dirnames):
                        if d in names:
                            add(
                                items,
                                "build-artifacts",
                                base / d,
                                f"project {d}",
                                risk="low",
                                min_bytes=min_bytes,
                            )
                    # android app/build
                    if base.name == "app" and (base / "build").is_dir():
                        if "android" in base.parts:
                            add(
                                items,
                                "build-artifacts",
                                base / "build",
                                "android app/build",
                                risk="low",
                                min_bytes=min_bytes,
                            )
                    # depth limit
                    if len(base.relative_to(root).parts) > 8:
                        dirnames.clear()
            except (PermissionError, OSError):
                continue

    # --- opt-in ---
    if want("opt-in"):
        for p, reason, risk in [
            (HOME / ".ollama" / "models", "Ollama models", "high"),
            (HOME / "Library" / "Caches" / "ms-playwright", "Playwright browsers", "high"),
            (HOME / ".cache" / "whisper", "whisper model cache", "medium"),
            (HOME / ".cache" / "huggingface", "huggingface cache", "medium"),
            (HOME / ".pi" / "agent" / "sessions", "pi session history", "high"),
            (
                HOME
                / "Library"
                / "Application Support"
                / "Cursor"
                / "User"
                / "globalStorage"
                / "state.vscdb",
                "Cursor chat DB (prefer VACUUM, not delete)",
                "high",
            ),
            (Path("/private/var/vm/sleepimage"), "hibernation image (regenerates)", "medium"),
            (Path("/usr/local/texlive"), "TeX Live (strip doc/source only)", "high"),
            (
                HOME / "Library" / "Developer" / "CoreSimulator" / "Devices",
                "iOS Simulator device data (simctl erase)",
                "high",
            ),
        ]:
            add(items, "opt-in", p, reason, risk=risk, min_bytes=min_bytes)

    # de-dupe by path keep largest reason first
    by_path: dict[str, Item] = {}
    for it in items:
        prev = by_path.get(it.path)
        if prev is None or it.size_bytes > prev.size_bytes:
            by_path[it.path] = it
    out = list(by_path.values())
    out.sort(key=lambda x: (-x.size_bytes, x.tier, x.path))
    return out


def df_data() -> str:
    try:
        out = subprocess.check_output(
            ["df", "-h", "/System/Volumes/Data"], text=True
        ).strip()
        return out
    except subprocess.CalledProcessError as e:
        return f"df failed: {e}"


def df_bytes() -> dict[str, int]:
    """Machine-readable size/used/avail for the data volume (bytes)."""
    try:
        out = subprocess.check_output(["df", "-k", "/System/Volumes/Data"], text=True)
        f = out.strip().splitlines()[-1].split()
        if len(f) >= 4:
            return {
                "size_bytes": int(f[1]) * 1024,
                "used_bytes": int(f[2]) * 1024,
                "avail_bytes": int(f[3]) * 1024,
            }
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass
    return {}


def read_snapshots() -> list[dict]:
    """All stored snapshots, oldest first. Missing/corrupt lines are skipped."""
    if not HISTORY_FILE.exists():
        return []
    out: list[dict] = []
    try:
        for line in HISTORY_FILE.read_text().splitlines():
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except OSError:
        pass
    return out


def append_snapshot(items: list[Item], by_tier: dict[str, int], total: int, min_mb: float) -> None:
    rec = {
        "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "df": df_bytes(),
        "min_mb": min_mb,
        "items": [
            {"path": it.path, "tier": it.tier, "reason": it.reason, "risk": it.risk,
             "size_bytes": it.size_bytes}
            for it in items
        ],
        "totals": by_tier | {"ALL": total},
    }
    try:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        with HISTORY_FILE.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError as e:
        print(f"history write failed: {e}")


def print_df_delta(cur: dict, prev: dict) -> None:
    cd, pd = cur.get("df", {}), prev.get("df", {})
    if cd and pd:
        du = (cd["used_bytes"] - pd["used_bytes"]) / 2**30
        da = (cd["avail_bytes"] - pd["avail_bytes"]) / 2**30
        print(f"  disk since {prev.get('ts', 'last run')}: used {du:+.1f}G, free {da:+.1f}G")
    else:
        print("  (df data unavailable for comparison)")


def print_vs_last(cur: dict, prev: dict) -> None:
    print()
    print("=== vs previous snapshot ===")
    print_df_delta(cur, prev)
    if cur.get("min_mb") != prev.get("min_mb") or cur.get("tiers") or prev.get("tiers"):
        print(
            "  (runs differ in scope; candidate diffs below are still indicative, "
            "disk delta is exact)"
        )
    cur_by_path = {it["path"]: it for it in cur.get("items", [])}
    prev_by_path = {it["path"]: it for it in prev.get("items", [])}
    grew: list[tuple[dict, int]] = []
    freed: list[tuple[dict, int]] = []
    appeared: list[dict] = []
    for path, it in cur_by_path.items():
        old = prev_by_path.get(path)
        if old is None:
            if it["size_bytes"] >= DELTA_FLOOR:
                appeared.append(it)
        else:
            d = it["size_bytes"] - old["size_bytes"]
            if d >= DELTA_FLOOR:
                grew.append((it, d))
            elif d <= -DELTA_FLOOR:
                freed.append((it, -d))
    for path, old in prev_by_path.items():
        if path not in cur_by_path and old["size_bytes"] >= DELTA_FLOOR:
            freed.append((old, old["size_bytes"]))

    def row(it: dict, size_delta: int | None = None) -> str:
        label = f"{human(size_delta) if size_delta is not None else human(it['size_bytes'])}"
        return f"    {label:>8}  {it['path']}  ({it['reason']})"

    if grew:
        print(f"  grew since last run (top {min(5, len(grew))}):")
        for it, d in sorted(grew, key=lambda kv: -kv[1])[:5]:
            print(row(it, d))
    if appeared:
        print(f"  new candidates since last run (top {min(5, len(appeared))}):")
        for it in sorted(appeared, key=lambda x: -x["size_bytes"])[:5]:
            print(row(it))
    if freed:
        print(f"  shrank or disappeared since last run (top {min(5, len(freed))}):")
        for it, d in sorted(freed, key=lambda kv: -kv[1])[:5]:
            print(row(it, -d))
    if not grew and not appeared and not freed:
        print("  no candidate changes above 25 MB")


def print_history(snapshots: list[dict], limit: int) -> None:
    if not snapshots:
        print("No snapshots yet. Run the dry-run inventory to record one.")
        return
    print(f"=== history (last {min(limit, len(snapshots))} of {len(snapshots)} snapshots) ===")
    print(f"{'WHEN':<17} {'USED':>8} {'FREE':>8} {'CANDIDATES':>10}  NOTE")
    for i, snap in enumerate(snapshots[-limit:]):
        d = snap.get("df", {})
        used = human(d.get("used_bytes", 0))
        free = human(d.get("avail_bytes", 0))
        cand = human(snap.get("totals", {}).get("ALL", 0))
        note = ""
        if i > 0:
            pd = snapshots[-limit:][i - 1].get("df", {})
            if d and pd:
                du = (d["used_bytes"] - pd["used_bytes"]) / 2**30
                note = f"used {du:+.1f}G vs prior"
        print(f"{snap.get('ts', '?')[:16]:<17} {used:>8} {free:>8} {cand:>10}  {note}")
    print(f"\nHistory file: {HISTORY_FILE}")


def main() -> int:
    ap = argparse.ArgumentParser(description="mac-cleanup dry-run inventory")
    ap.add_argument("--min-mb", type=float, default=5.0, help="minimum size to list")
    ap.add_argument(
        "--tiers",
        default="",
        help="comma list: safe,duplicates,build-artifacts,opt-in (default all)",
    )
    ap.add_argument("--json", default="", help="write JSON report path")
    ap.add_argument(
        "--history",
        nargs="?",
        const=10,
        type=int,
        help="print stored snapshots (default last 10) and exit; no new snapshot",
    )
    args = ap.parse_args()
    tiers = {t.strip() for t in args.tiers.split(",") if t.strip()} or None

    if args.history is not None:
        print_history(read_snapshots(), args.history)
        return 0

    items = inventory(min_mb=args.min_mb, tiers=tiers)
    print("=== df ===")
    print(df_data())
    print()
    print(f"=== candidates ({len(items)}) min={args.min_mb}MB ===")
    print(f"{'TIER':<16} {'SIZE':>8} {'RISK':<7} PATH  (reason)")
    total = 0
    by_tier: dict[str, int] = {}
    for it in items:
        total += it.size_bytes
        by_tier[it.tier] = by_tier.get(it.tier, 0) + it.size_bytes
        print(f"{it.tier:<16} {it.size_human:>8} {it.risk:<7} {it.path}  ({it.reason})")
    print()
    print("=== totals (sum of du; APFS clones may over-count unique bytes) ===")
    for tier, sz in sorted(by_tier.items(), key=lambda kv: -kv[1]):
        print(f"  {tier:<16} {human(sz)}")
    print(f"  {'ALL':<16} {human(total)}")
    print()
    print("No deletes performed. Confirm tiers, then run clean.py --apply.")

    if tiers is None:
        snapshots = read_snapshots()
        prev = snapshots[-1] if snapshots else None
        append_snapshot(items, by_tier, total, args.min_mb)
        if prev is not None:
            cur = read_snapshots()[-1]
            print_vs_last(cur, prev)
        else:
            print(
                f"\nFirst snapshot recorded to {HISTORY_FILE}. "
                "Next full dry-run will show what changed."
            )
    else:
        print(
            "\n(Scoped --tiers run: no history snapshot recorded; run a full "
            "dry-run to capture one.)"
        )

    if args.json:
        payload = {
            "df": df_data(),
            "items": [asdict(it) | {"size_human": it.size_human} for it in items],
            "total_bytes": total,
        }
        Path(args.json).write_text(json.dumps(payload, indent=2) + "\n")
        print(f"Wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
