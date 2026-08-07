#!/usr/bin/env python3
"""Detect how a listing wants applications: email | web | linkedin | unknown.

Channel follows the listing (and URL), not a fixed policy.
Used by search_jobs and by the agent before Step 4 apply.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from typing import Any

# Public ATS / careers form hosts → web
WEB_HOST_MARKERS = (
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "boards.eu.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
    "jobs.workable.com",
    "jobs.smartrecruiters.com",
    "careers.smartrecruiters.com",
    "bamboohr.com",
    "jobs.bamboohr.com",
    "teamtailor.com",
    "apply.workable.com",
    "myworkdayjobs.com",
    "wd1.myworkdaysite.com",
    "wd3.myworkdaysite.com",
    "wd5.myworkdaysite.com",
    "icims.com",
    "taleo.net",
    "successfactors.com",
    "oraclecloud.com",
    "recruitee.com",
    "personio.de",
    "personio.com",
    "jobvite.com",
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "workable.com",
    "rippling.com",
    "dover.com",
    "wellfound.com",
    "angel.co",
    "otta.com",
    "ycombinator.com",
    "workatastartup.com",
    "pinpointhq.com",
    "breezy.hr",
    "polymer.co",
    "notion.site",  # often hosted careers; still a form/page
)

LINKEDIN_HOST_MARKERS = (
    "linkedin.com",
    "lnkd.in",
)

EMAIL_TEXT_PATTERNS = [
    re.compile(r"\bapply\s+by\s+e-?mail\b", re.I),
    re.compile(r"\bemail\s+(?:your|a|the)?\s*(?:cv|resume|application|cover)\b", re.I),
    re.compile(r"\bsend\s+(?:your|a|the)?\s*(?:cv|resume|application)\b", re.I),
    re.compile(r"\bsend\s+(?:an?\s+)?email\b", re.I),
    re.compile(r"\bapplications?\s+(?:to|via|by)\s+e-?mail\b", re.I),
    re.compile(r"\bplease\s+email\b", re.I),
    re.compile(r"\bemail\s+us\s+at\b", re.I),
    re.compile(r"\bmail\s+your\s+(?:cv|resume)\b", re.I),
    re.compile(r"\bto\s+apply[,\s]+(?:please\s+)?email\b", re.I),
    re.compile(r"\bforward\s+(?:your\s+)?(?:cv|resume)\s+to\b", re.I),
]

WEB_TEXT_PATTERNS = [
    re.compile(r"\bapply\s+(?:online|on\s+our\s+website|via\s+our\s+(?:website|careers)|through\s+our)\b", re.I),
    re.compile(r"\bclick\s+(?:here\s+)?to\s+apply\b", re.I),
    re.compile(r"\bsubmit\s+(?:your\s+)?application\s+online\b", re.I),
    re.compile(r"\beasy\s+apply\b", re.I),
    re.compile(r"\bapply\s+now\b", re.I),
    re.compile(r"\bapplication\s+form\b", re.I),
]

MAILTO_RE = re.compile(r"mailto:([^\s\"'<>]+)", re.I)
# Full addresses only (do not let a preceding keyword eat into the local-part)
EMAIL_ANY_RE = re.compile(r"\b([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)
APPLY_NEAR_EMAIL_RE = re.compile(
    r"(?:apply|e-?mail|send|contact|cv|resume|application).{0,80}?"
    r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})",
    re.I | re.S,
)


def _host(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url or "").netloc.lower()
    except Exception:
        return ""
    host = host.split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def _url_is_mailto(url: str) -> str | None:
    u = (url or "").strip()
    if u.lower().startswith("mailto:"):
        return urllib.parse.unquote(u[7:].split("?")[0]).strip() or None
    m = MAILTO_RE.search(u)
    if m:
        return urllib.parse.unquote(m.group(1).split("?")[0]).strip() or None
    return None


def _host_matches(host: str, markers: tuple[str, ...]) -> str | None:
    for m in markers:
        if host == m or host.endswith("." + m) or m in host:
            return m
    return None


def detect_apply_channel(
    *,
    url: str = "",
    description: str = "",
    title: str = "",
    source: str = "",
) -> dict[str, Any]:
    """Return channel + confidence + signals for routing apply.

    Channels:
      email    — listing wants CV by email / mailto
      web      — public ATS or careers form / apply online
      linkedin — LinkedIn job / Easy Apply surface
      unknown  — inspect listing; ask Mikhail if still unclear
    """
    url = url or ""
    text = f"{title or ''}\n{description or ''}"
    signals: list[str] = []
    host = _host(url)
    mailto = _url_is_mailto(url)

    # 1) Hard URL signals
    if mailto:
        signals.append(f"mailto_url:{mailto}")
        return {
            "channel": "email",
            "confidence": "high",
            "signals": signals,
            "apply_email": mailto,
            "reason": "Job URL is mailto",
            "url_host": host or None,
        }

    li = _host_matches(host, LINKEDIN_HOST_MARKERS)
    if li or (source or "").lower() in ("linkedin", "li"):
        signals.append(f"linkedin_host:{li or source}")
        if re.search(r"easy\s*apply", text, re.I):
            signals.append("easy_apply_text")
        return {
            "channel": "linkedin",
            "confidence": "high",
            "signals": signals,
            "apply_email": None,
            "reason": "LinkedIn job URL / source",
            "url_host": host or None,
        }

    web_m = _host_matches(host, WEB_HOST_MARKERS)
    if web_m:
        signals.append(f"ats_host:{web_m}")
        return {
            "channel": "web",
            "confidence": "high",
            "signals": signals,
            "apply_email": None,
            "reason": f"Known ATS/careers host ({web_m})",
            "url_host": host or None,
        }

    # 2) Explicit text instructions (email beats generic "apply now")
    email_hits = [p.pattern for p in EMAIL_TEXT_PATTERNS if p.search(text)]
    web_hits = [p.pattern for p in WEB_TEXT_PATTERNS if p.search(text)]
    apply_emails = sorted({m.group(1) for m in APPLY_NEAR_EMAIL_RE.finditer(text)})
    if not apply_emails and email_hits:
        # Fall back to any address in the blurb when email-apply language is present
        apply_emails = sorted({m.group(1) for m in EMAIL_ANY_RE.finditer(text)})

    if email_hits or apply_emails:
        signals.extend(f"email_text:{h}" for h in email_hits[:5])
        for e in apply_emails[:3]:
            signals.append(f"apply_email_in_text:{e}")
        # If both email and web text, prefer email when a concrete address or strong email verb exists
        conf = "high" if (apply_emails or any("email" in h.lower() or "send" in h.lower() for h in email_hits)) else "medium"
        return {
            "channel": "email",
            "confidence": conf,
            "signals": signals + ([f"web_text_also:{w}" for w in web_hits[:2]] if web_hits else []),
            "apply_email": apply_emails[0] if apply_emails else None,
            "reason": "Listing text instructs email apply",
            "url_host": host or None,
        }

    if web_hits:
        signals.extend(f"web_text:{h}" for h in web_hits[:5])
        return {
            "channel": "web",
            "confidence": "medium",
            "signals": signals,
            "apply_email": None,
            "reason": "Listing text points to online apply",
            "url_host": host or None,
        }

    # 3) Soft defaults from host / source boards (aggregator pages → often web apply)
    if host:
        signals.append(f"host:{host}")
        # Aggregators / company sites with /jobs / /careers → treat as web lead
        if any(x in (url or "").lower() for x in ("/job", "/jobs", "/career", "/apply", "/vacancy", "/opening")):
            signals.append("url_path_jobish")
            return {
                "channel": "web",
                "confidence": "low",
                "signals": signals,
                "apply_email": None,
                "reason": "Job-like URL path; assume web until listing says email",
                "url_host": host,
            }
        return {
            "channel": "web",
            "confidence": "low",
            "signals": signals,
            "apply_email": None,
            "reason": "Has job URL; default web (confirm on page if email-only)",
            "url_host": host,
        }

    signals.append("no_url_no_text_signal")
    return {
        "channel": "unknown",
        "confidence": "low",
        "signals": signals,
        "apply_email": None,
        "reason": "No URL or apply instructions; inspect listing",
        "url_host": None,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Detect apply channel for a job listing")
    p.add_argument("--url", default="")
    p.add_argument("--description", default="")
    p.add_argument("--title", default="")
    p.add_argument("--source", default="")
    p.add_argument("--from-json", type=str, help="Path to job JSON object or jobs list")
    p.add_argument("--json", action="store_true", help="Print JSON (default)")
    args = p.parse_args()

    if args.from_json:
        data = json.loads(open(args.from_json, encoding="utf-8").read())
        jobs = data.get("jobs") if isinstance(data, dict) and "jobs" in data else data
        if isinstance(jobs, list):
            out = []
            for j in jobs:
                det = detect_apply_channel(
                    url=j.get("url") or "",
                    description=j.get("description") or "",
                    title=j.get("title") or "",
                    source=j.get("source") or "",
                )
                out.append({**{k: j.get(k) for k in ("title", "company", "url", "source") if k in j}, **det})
            print(json.dumps(out, indent=2))
            return 0
        if isinstance(data, dict):
            det = detect_apply_channel(
                url=data.get("url") or args.url,
                description=data.get("description") or args.description,
                title=data.get("title") or args.title,
                source=data.get("source") or args.source,
            )
            print(json.dumps(det, indent=2))
            return 0

    det = detect_apply_channel(
        url=args.url,
        description=args.description,
        title=args.title,
        source=args.source,
    )
    print(json.dumps(det, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
