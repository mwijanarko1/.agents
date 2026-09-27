#!/usr/bin/env python3
"""Compare Google Trends phrases through a PinchTab browser session."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Any


def run(args: list[str], env: dict[str, str] | None = None) -> str:
    result = subprocess.run(args, text=True, capture_output=True, env=env)
    output = result.stdout.strip()
    error = result.stderr.strip()
    if result.returncode or output.startswith(("Error", "ERROR")) or error.startswith(("Error", "ERROR")):
        raise RuntimeError(error or output or f"Command failed: {' '.join(args)}")
    return output


def parse_trends_json(raw: str) -> dict[str, Any]:
    marker = raw.find(")]}'")
    body = raw[marker + 4 :] if marker >= 0 else raw
    return json.loads(body.lstrip(",\n\r\t "))


def stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {
            "average": None,
            "peak": None,
            "latestComplete": None,
            "changePercent": None,
            "direction": "insufficient data",
        }
    average = sum(values) / len(values)
    change = None
    direction = "insufficient data"
    if len(values) >= 16:
        previous = sum(values[-16:-8]) / 8
        recent = sum(values[-8:]) / 8
        if previous > 0:
            change = (recent - previous) / previous * 100
            direction = "rising" if change > 10 else "falling" if change < -10 else "flat"
    return {
        "average": round(average, 1),
        "peak": max(values),
        "latestComplete": values[-1],
        "changePercent": round(change, 1) if change is not None else None,
        "direction": direction,
    }


def explore_url(phrases: list[str], geo: str, window: str) -> str:
    request = {
        "comparisonItem": [
            {"keyword": phrase, "geo": geo, "time": window} for phrase in phrases
        ],
        "category": 0,
        "property": "",
    }
    encoded = urllib.parse.quote(json.dumps(request, separators=(",", ":")))
    return f"https://trends.google.com/trends/api/explore?hl=en-GB&tz=0&req={encoded}"


def widget_url(widget: dict[str, Any], endpoint: str) -> str:
    request = urllib.parse.quote(json.dumps(widget["request"], separators=(",", ":")))
    token = urllib.parse.quote(widget["token"])
    return (
        f"https://trends.google.com/trends/api/widgetdata/{endpoint}"
        f"?hl=en-GB&tz=0&req={request}&token={token}"
    )


def related_phrase(widget: dict[str, Any]) -> str | None:
    try:
        keywords = widget["request"]["restriction"]["complexKeywordsRestriction"]["keyword"]
        return keywords[0]["value"]
    except (KeyError, IndexError, TypeError):
        return None


def self_test() -> None:
    assert parse_trends_json(")]}'\n{\"ok\":true}") == {"ok": True}
    assert parse_trends_json(")]}',\n{\"ok\":true}") == {"ok": True}
    assert stats([10] * 16)["direction"] == "flat"
    assert stats([10] * 8 + [20] * 8)["direction"] == "rising"
    print("trends-check: self-test passed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phrases", nargs="*", help="Candidate phrases, four per comparison batch")
    parser.add_argument("--anchor", help="Shared phrase used to normalize every batch")
    parser.add_argument("--geo", default="GB", help="Google Trends country code (default: GB)")
    parser.add_argument("--time", default="today 1-m", help="Google Trends time window (default: past month)")
    parser.add_argument("--allow-signed-in-profile", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0
    if not args.anchor or not args.phrases:
        parser.error("--anchor and at least one candidate phrase are required")
    if not shutil.which("pinchtab"):
        raise RuntimeError("pinchtab is not installed")

    candidates = list(dict.fromkeys(p for p in args.phrases if p != args.anchor))
    if not candidates:
        parser.error("provide at least one candidate different from the anchor")

    token = ""
    tab_id = ""
    env = os.environ.copy()
    results: dict[str, dict[str, Any]] = {}
    related: dict[str, dict[str, Any]] = {}

    try:
        session_output = run(["pinchtab", "session", "create", "--agent-id", "blog-content-pipeline"])
        token = next(
            (line for line in reversed(session_output.splitlines()) if line.startswith("ses_")),
            session_output.splitlines()[-1],
        )
        env["PINCHTAB_SESSION"] = token

        page = "https://trends.google.com/trends/explore?" + urllib.parse.urlencode(
            {"geo": args.geo, "q": args.anchor}
        )
        snapshot = run(
            ["pinchtab", "nav", page, "--snap", "--dismiss-banners", "--print-tab-id"], env
        )
        tab_id = snapshot.splitlines()[0]
        if "Google Account:" in snapshot and not args.allow_signed_in_profile:
            raise RuntimeError(
                "PinchTab profile is signed in to Google. Use an unauthenticated profile, "
                "or rerun with --allow-signed-in-profile after user approval."
            )

        for offset in range(0, len(candidates), 4):
            batch = [args.anchor, *candidates[offset : offset + 4]]
            url = explore_url(batch, args.geo, args.time)
            raw = run(
                ["pinchtab", "eval", f"fetch({json.dumps(url)}).then(r=>r.text())", "--await-promise"],
                env,
            )
            widgets = parse_trends_json(raw)["widgets"]
            timeline_widget = next(widget for widget in widgets if widget["id"] == "TIMESERIES")
            timeline_raw = run(
                [
                    "pinchtab",
                    "eval",
                    f"fetch({json.dumps(widget_url(timeline_widget, 'multiline'))}).then(r=>r.text())",
                    "--await-promise",
                ],
                env,
            )
            points = parse_trends_json(timeline_raw)["default"]["timelineData"]
            complete = [point for point in points if not point.get("isPartial", False)]
            series = [[point["value"][index] for point in complete] for index in range(len(batch))]
            anchor_average = stats(series[0])["average"]

            for index, phrase in enumerate(batch[1:], start=1):
                result = stats(series[index])
                result["relativeToAnchor"] = (
                    round(result["average"] / anchor_average * 100, 1)
                    if result["average"] is not None and anchor_average
                    else None
                )
                results[phrase] = result

            for widget in widgets:
                if not widget["id"].startswith("RELATED_QUERIES"):
                    continue
                phrase = related_phrase(widget)
                if not phrase or phrase == args.anchor or phrase in related:
                    continue
                related_raw = run(
                    [
                        "pinchtab",
                        "eval",
                        f"fetch({json.dumps(widget_url(widget, 'relatedsearches'))}).then(r=>r.text())",
                        "--await-promise",
                    ],
                    env,
                )
                ranked = parse_trends_json(related_raw).get("default", {}).get("rankedList", [])
                related[phrase] = {
                    "topRelated": [item["query"] for item in ranked[0].get("rankedKeyword", [])[:5]]
                    if ranked
                    else [],
                    "risingRelated": [
                        {"query": item["query"], "change": item.get("formattedValue", item.get("value"))}
                        for item in ranked[1].get("rankedKeyword", [])[:5]
                    ]
                    if len(ranked) > 1
                    else [],
                }
                time.sleep(1)
            time.sleep(1)

        output = {
            "geo": args.geo,
            "window": args.time,
            "anchor": args.anchor,
            "retrievedAt": datetime.now(timezone.utc).isoformat(),
            "note": "Scores are relative Google Trends interest, not search volume.",
            "results": [
                {"phrase": phrase, **results[phrase], **related.get(phrase, {})}
                for phrase in candidates
            ],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    finally:
        if token:
            env["PINCHTAB_SESSION"] = token
            if tab_id:
                subprocess.run(["pinchtab", "close", tab_id], env=env, capture_output=True)
            try:
                info = json.loads(run(["pinchtab", "session", "info"], env))
                subprocess.run(
                    ["pinchtab", "session", "revoke", info["id"]], env=env, capture_output=True
                )
            except Exception:
                pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, json.JSONDecodeError, KeyError, StopIteration) as error:
        print(f"trends-check: {error}", file=sys.stderr)
        raise SystemExit(1)
