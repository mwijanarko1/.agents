#!/usr/bin/env python3
"""Apply mac-cleanup tiers. Default is dry-run; require --apply to delete."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Reuse inventory helpers
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory import (  # noqa: E402
    HOME,
    cache_whitelist_names,
    df_data,
    du_bytes,
    env_path,
    find_user_var_folders,
    human,
)


def rm_path(path: Path, apply: bool) -> tuple[str, int]:
    """Return (status, bytes_before)."""
    if not path.exists():
        return ("missing", 0)
    size = du_bytes(path)
    if not apply:
        return ("dry-run", size)
    try:
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        else:
            shutil.rmtree(path, ignore_errors=False)
        return ("deleted", size)
    except OSError as e:
        # retry with chmod walk for stubborn caches
        try:
            if path.is_dir():
                for root, dirs, files in os.walk(path):
                    for name in dirs + files:
                        try:
                            os.chmod(os.path.join(root, name), 0o700)
                        except OSError:
                            pass
                shutil.rmtree(path, ignore_errors=True)
            if path.exists():
                return (f"failed:{e}", size)
            return ("deleted", size)
        except OSError as e2:
            return (f"failed:{e2}", size)


def collect_targets(tiers: set[str]) -> list[tuple[str, Path, str]]:
    """(tier, path, note)"""
    out: list[tuple[str, Path, str]] = []

    if "safe" in tiers:
        safe_paths = [
            HOME / ".npm" / "_cacache",
            HOME / ".npm" / "_npx",
            HOME / ".bun" / "install" / "cache",
            HOME / "Library" / "Caches" / "bun",
            HOME / ".pi" / "agent" / "tmp",
            HOME / "Library" / "Developer" / "Xcode" / "DerivedData",
            HOME / "Library" / "Developer" / "XcodeBuildMCP" / "workspaces",
            HOME / "Library" / "Application Support" / "Cursor" / "CachedData",
            HOME / "Library" / "Application Support" / "Cursor" / "CachedExtensionVSIXs",
            HOME / "Library" / "Application Support" / "Cursor" / "Cache",
            HOME / "Library" / "Application Support" / "Cursor" / "GPUCache",
            HOME / "Library" / "Application Support" / "Cursor" / "logs",
            HOME / "Library" / "Application Support" / "Cursor" / "Crashpad",
            HOME
            / "Library"
            / "Application Support"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "anysphere.cursor-agent-worker",
            HOME / "Library" / "Caches" / "net.imput.helium",
            HOME / "Library" / "Caches" / "Homebrew",
            HOME / "Library" / "Caches" / "node-gyp",
            HOME / "Library" / "Caches" / "GeoServices",
            HOME / ".cache" / "uv",
            HOME / ".cache" / "hyperframes",
            HOME / ".cache" / "chrome-devtools-mcp",
            HOME / ".cache" / "kilo",
            HOME / ".cache" / "opencode",
            HOME / ".cache" / "devin",
            HOME / ".cache" / "pi",
            HOME / ".cursor" / "worktrees",
        ]
        for p in safe_paths:
            out.append(("safe", p, "cache/temp"))

        helium = HOME / "Library" / "Application Support" / "net.imput.helium"
        for rel in (
            "GraphiteDawnCache",
            "Crashpad",
            "Default/GPUCache",
            "Default/DawnWebGPUCache",
            "Default/Code Cache",
            "Default/Service Worker/CacheStorage",
        ):
            out.append(("safe", helium / rel, "Helium rebuildable cache"))

        # Library/Caches sweep: only large non-whitelisted, skip tiny com.apple agents
        caches = HOME / "Library" / "Caches"
        wl = cache_whitelist_names()
        min_cache = 5 * 1024 * 1024
        if caches.is_dir():
            try:
                for child in caches.iterdir():
                    name = child.name
                    if name == "CloudKit":
                        continue
                    if name in wl or any(name.startswith(w) for w in wl):
                        continue
                    if name.startswith("com.apple.") and du_bytes(child) < 50 * 1024 * 1024:
                        continue
                    if du_bytes(child) < min_cache:
                        continue
                    out.append(("safe", child, "Library/Caches entry"))
            except PermissionError:
                pass

        bird = HOME / "Library" / "Caches" / "CloudKit" / "com.apple.bird"
        if bird.is_dir():
            for tmpm in bird.glob("**/MMCS/tmpm-*"):
                out.append(("safe", tmpm, "CloudKit MMCS tmpm"))

        for base in find_user_var_folders():
            x_helium = base / "X" / "net.imput.helium.code_sign_clone"
            out.append(("safe", x_helium, "Helium code_sign_clone"))
            # if X only contains that, also try clearing empty X later
            t = base / "T"
            for name in (
                "eas-build-local-nodejs",
                "eas-cli-nodejs",
                "metro-cache",
                "node-compile-cache",
                "jest_dx",
            ):
                out.append(("safe", t / name, "var T build temp"))
            if t.is_dir():
                try:
                    for child in t.iterdir():
                        if child.name.startswith("metro-file-map-"):
                            out.append(("safe", child, "metro-file-map"))
                except PermissionError:
                    pass
            out.append(("safe", base / "C" / "clang", "clang cache"))

    if "duplicates" in tiers:
        android_home = env_path("ANDROID_HOME") or env_path("ANDROID_SDK_ROOT")
        lib_android = HOME / "Library" / "Android"
        if lib_android.exists() and android_home is not None:
            try:
                if lib_android.resolve() != android_home.resolve():
                    out.append(
                        (
                            "duplicates",
                            lib_android,
                            f"duplicate; keep {android_home}",
                        )
                    )
            except OSError:
                pass

        gradle_home = env_path("GRADLE_USER_HOME")
        default_gradle = HOME / ".gradle"
        if default_gradle.exists() and gradle_home is not None:
            try:
                if default_gradle.resolve() != gradle_home.resolve():
                    out.append(
                        (
                            "duplicates",
                            default_gradle,
                            f"duplicate; keep {gradle_home}",
                        )
                    )
            except OSError:
                pass

    if "build-artifacts" in tiers:
        out.append(
            (
                "build-artifacts",
                HOME / "Library" / "Developer" / "Xcode" / "Archives",
                "Xcode Archives",
            )
        )
        roots = [
            HOME / "Documents" / "CURSOR-CODES",
            HOME / "projects",
        ]
        names = {".next", ".open-next", ".turbo", ".cxx"}
        for root in roots:
            if not root.is_dir():
                continue
            try:
                for dirpath, dirnames, _ in os.walk(root):
                    base = Path(dirpath)
                    dirnames[:] = [
                        d
                        for d in dirnames
                        if d not in {".git", "node_modules", "Pods", ".venv", "venv"}
                    ]
                    for d in list(dirnames):
                        if d in names:
                            out.append(("build-artifacts", base / d, f"remove {d}"))
                    if (
                        base.name == "app"
                        and "android" in base.parts
                        and (base / "build").is_dir()
                    ):
                        out.append(
                            ("build-artifacts", base / "build", "android app/build")
                        )
                    if len(base.relative_to(root).parts) > 8:
                        dirnames.clear()
            except (PermissionError, OSError):
                continue

    if "opt-in" in tiers:
        # Only paths that are clearly model/cache opt-in; still require --apply
        # and user must have passed opt-in intentionally.
        out.append(("opt-in", HOME / ".ollama" / "models", "Ollama models"))
        out.append(
            ("opt-in", HOME / "Library" / "Caches" / "ms-playwright", "Playwright")
        )
        out.append(("opt-in", HOME / ".cache" / "whisper", "whisper cache"))
        out.append(("opt-in", HOME / ".cache" / "huggingface", "hf cache"))

    # de-dupe
    seen: set[str] = set()
    uniq: list[tuple[str, Path, str]] = []
    for tier, path, note in out:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((tier, path, note))
    return uniq


def brew_cleanup(apply: bool) -> None:
    brew = shutil.which("brew")
    if not brew:
        print("brew: not found, skip")
        return
    cmd = [brew, "cleanup", "-s"]
    print("run:", " ".join(cmd), "(apply)" if apply else "(skipped dry-run)")
    if apply:
        subprocess.run(cmd, check=False)


def log_erase(apply: bool) -> None:
    print("log erase --all: needs admin (osascript) when applying")
    if not apply:
        return
    script = 'do shell script "log erase --all" with administrator privileges'
    subprocess.run(["osascript", "-e", script], check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="mac-cleanup clean")
    ap.add_argument(
        "--tiers",
        default="safe",
        help="comma list: safe,duplicates,build-artifacts,opt-in",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="actually delete (default is dry-run)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="force dry-run (default)",
    )
    ap.add_argument(
        "--with-brew-cleanup",
        action="store_true",
        help="also brew cleanup -s",
    )
    ap.add_argument(
        "--with-log-erase",
        action="store_true",
        help="also log erase --all (admin prompt)",
    )
    args = ap.parse_args()
    apply = bool(args.apply) and not args.dry_run
    tiers = {t.strip() for t in args.tiers.split(",") if t.strip()}

    if "opt-in" in tiers and apply:
        print(
            "WARNING: opt-in tier includes Ollama models / Playwright / model caches.",
            file=sys.stderr,
        )

    print("=== df before ===")
    print(df_data())
    print(f"mode: {'APPLY' if apply else 'DRY-RUN'}  tiers={','.join(sorted(tiers))}")
    print()

    targets = collect_targets(tiers)
    total = 0
    deleted = 0
    for tier, path, note in targets:
        if not path.exists():
            continue
        status, size = rm_path(path, apply=apply)
        if size <= 0 and status == "missing":
            continue
        total += size
        if status == "deleted":
            deleted += size
        print(f"{status:<10} {human(size):>8} [{tier}] {path}  ({note})")

    if args.with_brew_cleanup:
        brew_cleanup(apply)
    if args.with_log_erase:
        log_erase(apply)

    # recreate empty ollama models dir if removed
    if apply and "opt-in" in tiers:
        models = HOME / ".ollama" / "models"
        if not models.exists():
            models.mkdir(parents=True, exist_ok=True)

    print()
    print(f"sum touched (du): {human(total)}")
    if apply:
        print(f"sum deleted (du): {human(deleted)}")
    print("=== df after ===")
    print(df_data())
    if not apply:
        print("\nNo deletes. Re-run with --apply after user confirmation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
