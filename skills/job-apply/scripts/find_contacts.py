#!/usr/bin/env python3
"""
Find public hiring-contact hints for a company/role.

Legal sources only:
- job page text (mailto, LinkedIn URLs)
- company careers / team pages when provided
- Hunter.io domain search if HUNTER_API_KEY is set

Does NOT scrape LinkedIn while logged in, buy email dumps, or auto-message anyone.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import DEFAULT_DB, record_contacts  # noqa: E402

UA = "job-apply-skill/1.0 (+local personal use)"
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
LINKEDIN_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:in|company|pub)/[A-Za-z0-9_\-%/]+",
    re.I,
)
MAILTO_RE = re.compile(r"mailto:([^\"'\s>?]+)", re.I)


def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def domain_from_url(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return ""
    host = host.split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    # strip common job-board hosts — not company domains
    boards = {
        "remoteok.com",
        "remotive.com",
        "jobicy.com",
        "arbeitnow.com",
        "themuse.com",
        "linkedin.com",
        "indeed.com",
        "glassdoor.com",
        "boards.greenhouse.io",
        "jobs.lever.co",
        "jobs.ashbyhq.com",
        "apply.workable.com",
    }
    if any(host == b or host.endswith("." + b) for b in boards):
        return ""
    return host


def extract_from_text(text: str) -> dict:
    text = unescape(text or "")
    emails = sorted(set(EMAIL_RE.findall(text)))
    mailtos = sorted({urllib.parse.unquote(m) for m in MAILTO_RE.findall(text)})
    for m in mailtos:
        if m not in emails:
            emails.append(m)
    linkedins = sorted(set(LINKEDIN_RE.findall(text)))
    # prefer people profiles first
    people = [u for u in linkedins if "/in/" in u.lower()]
    companies = [u for u in linkedins if "/company/" in u.lower()]
    return {
        "emails": emails[:20],
        "linkedin_people": people[:10],
        "linkedin_companies": companies[:5],
    }


def hunter_domain_search(domain: str) -> dict:
    key = os.environ.get("HUNTER_API_KEY")
    if not key or not domain:
        return {"enabled": bool(key), "emails": [], "note": "no key or domain"}
    url = (
        "https://api.hunter.io/v2/domain-search?"
        + urllib.parse.urlencode(
            {
                "domain": domain,
                "api_key": key,
                "department": "hr,recruiting,people",
                "limit": 10,
            }
        )
    )
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode())
    emails = []
    for row in (data.get("data") or {}).get("emails") or []:
        emails.append(
            {
                "value": row.get("value"),
                "first_name": row.get("first_name"),
                "last_name": row.get("last_name"),
                "position": row.get("position"),
                "linkedin": row.get("linkedin"),
                "confidence": row.get("confidence"),
            }
        )
    return {"enabled": True, "emails": emails, "domain": domain}


def guess_roles(company: str) -> list[str]:
    c = company.strip() or "Company"
    return [
        f"Recruiter {c}",
        f"Talent Acquisition {c}",
        f"Hiring Manager {c}",
        f"Engineering Manager {c}",
        f"People Partner {c}",
    ]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--job-url", default="")
    p.add_argument("--domain", default="", help="Company domain if known, e.g. stripe.com")
    p.add_argument("--job-id", type=int, help="Link contact row to jobs.id")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--no-db", action="store_true")
    p.add_argument("--out", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    found = {
        "company": args.company,
        "job_url": args.job_url,
        "domain": args.domain or domain_from_url(args.job_url),
        "from_job_page": {},
        "hunter": {},
        "linkedin_search_queries": guess_roles(args.company),
        "manual_next_steps": [
            "Open company LinkedIn → People → filter Recruiter / Talent / Engineering Manager",
            "Check job post footer for recruiter name",
            "Check careers page / team page for people links",
            "If applying, use the official apply URL — do not auto-message",
        ],
        "warnings": [
            "Public/OSINT only. No LinkedIn login scraping.",
            "Do not bulk-email strangers. Prefer official apply + one thoughtful note.",
        ],
    }

    if args.job_url:
        try:
            html = fetch(args.job_url)
            found["from_job_page"] = extract_from_text(html)
            if not found["domain"]:
                found["domain"] = domain_from_url(args.job_url)
        except Exception as e:  # noqa: BLE001
            found["from_job_page"] = {"error": str(e)}

    if found["domain"]:
        try:
            found["hunter"] = hunter_domain_search(found["domain"])
        except Exception as e:  # noqa: BLE001
            found["hunter"] = {"enabled": True, "error": str(e)}

    if not args.no_db:
        found["db"] = record_contacts(found, job_id=args.job_id, db_path=args.db)

    text = json.dumps(found, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    if args.json or not args.out:
        print(text)
    else:
        print(f"Wrote {args.out}")
        if not args.no_db:
            print(f"DB contact_id={found.get('db', {}).get('contact_id')} → {args.db}")


if __name__ == "__main__":
    main()
