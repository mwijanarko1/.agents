#!/usr/bin/env python3
"""Search free public job APIs. No LinkedIn apply automation."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# Local import: same scripts/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import DEFAULT_DB, record_search  # noqa: E402

UA = "job-apply-skill/1.0 (+local personal use)"


def get_json(url: str, headers: dict | None = None, timeout: int = 25):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def norm(
    *,
    title: str,
    company: str,
    url: str,
    location: str = "",
    source: str,
    description: str = "",
    salary: str = "",
    remote: bool | None = None,
) -> dict | None:
    title = (title or "").strip()
    company = (company or "").strip()
    url = (url or "").strip()
    if not title or not url:
        return None
    return {
        "title": title,
        "company": company or "Unknown",
        "url": url,
        "location": (location or "").strip(),
        "source": source,
        "description": re.sub(r"\s+", " ", (description or ""))[:1200],
        "salary": salary or "",
        "remote": remote,
    }


def score(job: dict, terms: list[str]) -> float:
    title = (job.get("title") or "").lower()
    loc = (job.get("location") or "").lower()
    desc = (job.get("description") or "").lower()
    blob = f"{title} {job.get('company','')} {loc} {desc}".lower()
    if not terms:
        base = 0.0
    else:
        # Title hits count 3x description hits
        title_hits = sum(1 for t in terms if t.lower() in title)
        other_hits = sum(1 for t in terms if t.lower() in blob and t.lower() not in title)
        base = (3 * title_hits + other_hits) / max(len(terms), 1)
    # Soft boosts for junior/grad; soft penalty for clearly senior-only titles
    if any(k in title for k in ("junior", "graduate", "grad ", "entry", "intern")):
        base += 0.35
    if any(k in title for k in ("senior", "staff", "principal", "director", "lead ")):
        base -= 0.25
    if any(k in loc for k in ("united kingdom", "uk", "london", "remote", "europe", "emea")):
        base += 0.1
    return max(base, 0.0)


def search_remoteok(query: str) -> list[dict]:
    data = get_json("https://remoteok.com/api")
    terms = [t for t in re.split(r"\s+", query.lower()) if t]
    out = []
    for row in data:
        if not isinstance(row, dict) or "id" not in row:
            continue
        tags = " ".join(row.get("tags") or [])
        text = f"{row.get('position','')} {row.get('company','')} {tags} {row.get('description','')}"
        if terms and not all(t in text.lower() for t in terms[:2]):
            # soft filter: at least one term
            if not any(t in text.lower() for t in terms):
                continue
        job = norm(
            title=row.get("position") or row.get("title") or "",
            company=row.get("company") or "",
            url=row.get("url") or row.get("apply_url") or "",
            location=row.get("location") or "Remote",
            source="remoteok",
            description=row.get("description") or "",
            salary=str(row.get("salary_min") or row.get("salary") or ""),
            remote=True,
        )
        if job:
            out.append(job)
    return out[:40]


def search_remotive(query: str) -> list[dict]:
    q = urllib.parse.quote(query)
    data = get_json(f"https://remotive.com/api/remote-jobs?search={q}&limit=50")
    out = []
    for row in data.get("jobs") or []:
        job = norm(
            title=row.get("title") or "",
            company=row.get("company_name") or "",
            url=row.get("url") or "",
            location=row.get("candidate_required_location") or "Remote",
            source="remotive",
            description=row.get("description") or "",
            salary=row.get("salary") or "",
            remote=True,
        )
        if job:
            out.append(job)
    return out


def search_jobicy(query: str) -> list[dict]:
    q = urllib.parse.quote(query)
    data = get_json(f"https://jobicy.com/api/v2/remote-jobs?count=50&tag={q}")
    out = []
    for row in data.get("jobs") or []:
        job = norm(
            title=row.get("jobTitle") or "",
            company=row.get("companyName") or "",
            url=row.get("url") or "",
            location=row.get("jobGeo") or "Remote",
            source="jobicy",
            description=row.get("jobDescription") or "",
            salary=row.get("annualSalaryMin")
            and f"{row.get('annualSalaryMin')}-{row.get('annualSalaryMax')} {row.get('salaryCurrency') or ''}"
            or "",
            remote=True,
        )
        if job:
            out.append(job)
    return out


def search_arbeitnow(query: str) -> list[dict]:
    q = urllib.parse.quote(query)
    data = get_json(f"https://www.arbeitnow.com/api/job-board-api?search={q}&page=1")
    out = []
    for row in data.get("data") or []:
        locs = ", ".join(row.get("location_names") or []) or row.get("location") or ""
        job = norm(
            title=row.get("title") or "",
            company=row.get("company_name") or "",
            url=row.get("url") or "",
            location=locs,
            source="arbeitnow",
            description=row.get("description") or "",
            remote=bool(row.get("remote")),
        )
        if job:
            out.append(job)
    return out


def search_muse(query: str) -> list[dict]:
    # page 1 only; free public API
    q = urllib.parse.quote(query)
    data = get_json(f"https://www.themuse.com/api/public/jobs?page=1&descending=true&q={q}")
    out = []
    for row in data.get("results") or []:
        locs = ", ".join(l.get("name", "") for l in (row.get("locations") or []) if isinstance(l, dict))
        company = (row.get("company") or {}).get("name") or ""
        job = norm(
            title=row.get("name") or "",
            company=company,
            url=row.get("refs", {}).get("landing_page") or "",
            location=locs,
            source="themuse",
            description=row.get("contents") or "",
        )
        if job:
            out.append(job)
    return out


def search_adzuna(query: str, country: str, location: str) -> list[dict]:
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": "50",
        "what": query,
        "content-type": "application/json",
    }
    if location:
        params["where"] = location
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1?" + urllib.parse.urlencode(params)
    data = get_json(url)
    out = []
    for row in data.get("results") or []:
        salary = ""
        if row.get("salary_min") or row.get("salary_max"):
            salary = f"{row.get('salary_min','')}-{row.get('salary_max','')} {row.get('salary_is_predicted') and '(est)' or ''}".strip()
        job = norm(
            title=row.get("title") or "",
            company=(row.get("company") or {}).get("display_name") or "",
            url=row.get("redirect_url") or "",
            location=(row.get("location") or {}).get("display_name") or "",
            source="adzuna",
            description=row.get("description") or "",
            salary=salary,
        )
        if job:
            out.append(job)
    return out


SOURCES = {
    "remoteok": lambda q, **_: search_remoteok(q),
    "remotive": lambda q, **_: search_remotive(q),
    "jobicy": lambda q, **_: search_jobicy(q),
    "arbeitnow": lambda q, **_: search_arbeitnow(q),
    "themuse": lambda q, **_: search_muse(q),
    "adzuna": lambda q, country="gb", location="", **_: search_adzuna(q, country, location),
}


def dedupe(jobs: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for j in jobs:
        key = re.sub(r"\W+", "", f"{j['title']}|{j['company']}".lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Search public job APIs")
    p.add_argument("--query", action="append", default=[], help="Search query (repeatable)")
    p.add_argument(
        "--sources",
        default="remoteok,remotive,jobicy,arbeitnow,themuse,adzuna",
        help="Comma list of sources",
    )
    p.add_argument("--country", default="gb", help="Adzuna country code (gb, us, ...)")
    p.add_argument("--location", default="United Kingdom")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--terms", default="", help="Comma terms for ranking (from CV skills)")
    p.add_argument("--out", type=Path, help="Write JSON results")
    p.add_argument("--json", action="store_true", help="Print JSON to stdout")
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite path")
    p.add_argument("--no-db", action="store_true", help="Skip SQLite write")
    p.add_argument("--run-dir", default="", help="Optional run folder to store on search row")
    args = p.parse_args()

    queries = args.query or ["software engineer typescript react"]
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    rank_terms = [t.strip() for t in args.terms.split(",") if t.strip()]
    if not rank_terms:
        rank_terms = re.split(r"\s+", " ".join(queries))

    jobs: list[dict] = []
    errors: list[str] = []

    def run_one(source: str, query: str):
        fn = SOURCES.get(source)
        if not fn:
            return source, query, [], f"unknown source {source}"
        try:
            return source, query, fn(query, country=args.country, location=args.location), None
        except Exception as e:  # noqa: BLE001 - collect per-source errors
            return source, query, [], f"{source}/{query}: {e}"

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(run_one, s, q) for q in queries for s in sources]
        for fut in as_completed(futs):
            source, query, found, err = fut.result()
            if err:
                errors.append(err)
            for j in found:
                j["matched_query"] = query
                jobs.append(j)

    jobs = dedupe(jobs)
    for j in jobs:
        j["score"] = round(score(j, rank_terms), 3)
    jobs.sort(key=lambda j: (-j["score"], j["company"].lower(), j["title"].lower()))
    jobs = jobs[: args.limit]

    run_dir = args.run_dir
    if not run_dir and args.out:
        run_dir = str(args.out.parent)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queries": queries,
        "sources": sources,
        "location": args.location,
        "country": args.country,
        "terms": ",".join(rank_terms),
        "count": len(jobs),
        "errors": errors,
        "jobs": jobs,
        "run_dir": run_dir or None,
    }

    if not args.no_db:
        db_info = record_search(payload, db_path=args.db, run_dir=run_dir or None)
        payload["db"] = db_info
        # attach job_id onto each returned job (same order as insert)
        for j, jid in zip(jobs, db_info.get("job_ids") or []):
            j["job_id"] = jid

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.json or not args.out:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Wrote {len(jobs)} jobs → {args.out}", file=sys.stderr)
        if not args.no_db:
            print(f"DB search_id={payload.get('db', {}).get('search_id')} → {args.db}", file=sys.stderr)
        if errors:
            print("Errors:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
