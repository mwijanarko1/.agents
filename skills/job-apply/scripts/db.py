#!/usr/bin/env python3
"""SQLite store for job-apply searches, jobs, contacts, applications."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / "Documents" / "job-apply" / "job-apply.sqlite3"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS searches (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL,
  queries_json TEXT NOT NULL,
  sources_json TEXT NOT NULL,
  location TEXT,
  country TEXT,
  terms TEXT,
  run_dir TEXT,
  job_count INTEGER DEFAULT 0,
  errors_json TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  fingerprint TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  url TEXT NOT NULL,
  location TEXT,
  source TEXT,
  description TEXT,
  salary TEXT,
  remote INTEGER,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  best_score REAL,
  status TEXT NOT NULL DEFAULT 'found'
    -- found | shortlisted | tailored | applied | rejected | interview | offer | skipped
);

CREATE TABLE IF NOT EXISTS search_jobs (
  search_id INTEGER NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  matched_query TEXT,
  score REAL,
  PRIMARY KEY (search_id, job_id)
);

CREATE TABLE IF NOT EXISTS contacts (
  id INTEGER PRIMARY KEY,
  job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
  company TEXT NOT NULL,
  domain TEXT,
  job_url TEXT,
  emails_json TEXT,
  linkedin_people_json TEXT,
  linkedin_companies_json TEXT,
  hunter_json TEXT,
  raw_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'draft'
    -- draft | tailored | applied | rejected | interview | offer | withdrawn
  ,
  applied_at TEXT,
  notes TEXT,
  cv_pdf_path TEXT,
  cv_tex_path TEXT,
  description_path TEXT,
  run_dir TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL,
  kind TEXT NOT NULL,  -- search | job_upsert | contact | application | note
  job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
  search_id INTEGER REFERENCES searches(id) ON DELETE SET NULL,
  payload_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_apps_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def fingerprint(title: str, company: str, url: str = "") -> str:
    base = f"{title}|{company}".lower()
    # Prefer stable company+title; fall back to url path if title empty
    if not title.strip():
        base = url.lower()
    return re.sub(r"\W+", "", base)[:200]


def log_event(
    conn: sqlite3.Connection,
    kind: str,
    *,
    job_id: int | None = None,
    search_id: int | None = None,
    payload: dict | None = None,
) -> None:
    conn.execute(
        "INSERT INTO events (created_at, kind, job_id, search_id, payload_json) VALUES (?,?,?,?,?)",
        (now(), kind, job_id, search_id, json.dumps(payload or {})),
    )


def record_search(
    payload: dict,
    *,
    db_path: Path | None = None,
    run_dir: str | None = None,
) -> dict:
    """Persist a search_jobs.py payload. Returns {search_id, job_ids, db}."""
    conn = connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO searches
               (created_at, queries_json, sources_json, location, country, terms, run_dir, job_count, errors_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                payload.get("generated_at") or now(),
                json.dumps(payload.get("queries") or []),
                json.dumps(payload.get("sources") or []),
                payload.get("location"),
                payload.get("country"),
                payload.get("terms"),
                run_dir or payload.get("run_dir"),
                int(payload.get("count") or len(payload.get("jobs") or [])),
                json.dumps(payload.get("errors") or []),
            ),
        )
        search_id = int(cur.lastrowid)
        log_event(
            conn,
            "search",
            search_id=search_id,
            payload={"queries": payload.get("queries"), "count": payload.get("count")},
        )

        job_ids: list[int] = []
        ts = now()
        for j in payload.get("jobs") or []:
            fp = fingerprint(j.get("title", ""), j.get("company", ""), j.get("url", ""))
            existing = conn.execute("SELECT id, best_score FROM jobs WHERE fingerprint=?", (fp,)).fetchone()
            score = j.get("score")
            remote = j.get("remote")
            remote_i = None if remote is None else (1 if remote else 0)

            if existing:
                job_id = int(existing["id"])
                best = existing["best_score"]
                new_best = score if best is None else (max(best, score) if score is not None else best)
                conn.execute(
                    """UPDATE jobs SET
                         title=?, company=?, url=?, location=?, source=?,
                         description=COALESCE(?, description),
                         salary=COALESCE(NULLIF(?, ''), salary),
                         remote=COALESCE(?, remote),
                         last_seen_at=?,
                         best_score=?
                       WHERE id=?""",
                    (
                        j.get("title"),
                        j.get("company"),
                        j.get("url"),
                        j.get("location"),
                        j.get("source"),
                        j.get("description"),
                        j.get("salary") or "",
                        remote_i,
                        ts,
                        new_best,
                        job_id,
                    ),
                )
            else:
                cur = conn.execute(
                    """INSERT INTO jobs
                       (fingerprint, title, company, url, location, source, description, salary, remote,
                        first_seen_at, last_seen_at, best_score, status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'found')""",
                    (
                        fp,
                        j.get("title"),
                        j.get("company"),
                        j.get("url"),
                        j.get("location"),
                        j.get("source"),
                        j.get("description"),
                        j.get("salary") or "",
                        remote_i,
                        ts,
                        ts,
                        score,
                    ),
                )
                job_id = int(cur.lastrowid)
                log_event(conn, "job_upsert", job_id=job_id, search_id=search_id, payload={"new": True})

            conn.execute(
                """INSERT INTO search_jobs (search_id, job_id, matched_query, score)
                   VALUES (?,?,?,?)
                   ON CONFLICT(search_id, job_id) DO UPDATE SET
                     matched_query=excluded.matched_query,
                     score=excluded.score""",
                (search_id, job_id, j.get("matched_query"), score),
            )
            job_ids.append(job_id)

        conn.commit()
        return {
            "search_id": search_id,
            "job_ids": job_ids,
            "db": str(Path(db_path or DEFAULT_DB)),
            "count": len(job_ids),
        }
    finally:
        conn.close()


def record_contacts(
    found: dict,
    *,
    job_id: int | None = None,
    db_path: Path | None = None,
) -> dict:
    conn = connect(db_path)
    try:
        page = found.get("from_job_page") or {}
        cur = conn.execute(
            """INSERT INTO contacts
               (job_id, company, domain, job_url, emails_json, linkedin_people_json,
                linkedin_companies_json, hunter_json, raw_json, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                job_id,
                found.get("company") or "",
                found.get("domain"),
                found.get("job_url"),
                json.dumps(page.get("emails") or []),
                json.dumps(page.get("linkedin_people") or []),
                json.dumps(page.get("linkedin_companies") or []),
                json.dumps(found.get("hunter") or {}),
                json.dumps(found),
                now(),
            ),
        )
        contact_id = int(cur.lastrowid)
        log_event(
            conn,
            "contact",
            job_id=job_id,
            payload={"contact_id": contact_id, "company": found.get("company")},
        )
        conn.commit()
        return {"contact_id": contact_id, "job_id": job_id, "db": str(Path(db_path or DEFAULT_DB))}
    finally:
        conn.close()


def upsert_application(
    *,
    job_id: int | None = None,
    title: str | None = None,
    company: str | None = None,
    url: str | None = None,
    status: str = "draft",
    notes: str | None = None,
    cv_pdf_path: str | None = None,
    cv_tex_path: str | None = None,
    description_path: str | None = None,
    run_dir: str | None = None,
    applied: bool = False,
    db_path: Path | None = None,
) -> dict:
    conn = connect(db_path)
    try:
        if job_id is None:
            if not (title and company):
                raise SystemExit("need --job-id or --title + --company")
            fp = fingerprint(title, company, url or "")
            row = conn.execute("SELECT id FROM jobs WHERE fingerprint=?", (fp,)).fetchone()
            if row:
                job_id = int(row["id"])
            else:
                ts = now()
                cur = conn.execute(
                    """INSERT INTO jobs
                       (fingerprint, title, company, url, location, source, description, salary, remote,
                        first_seen_at, last_seen_at, best_score, status)
                       VALUES (?,?,?,?, '','manual','','',NULL,?,?,NULL,?)""",
                    (fp, title, company, url or "", ts, ts, status if status != "draft" else "found"),
                )
                job_id = int(cur.lastrowid)

        ts = now()
        applied_at = ts if (applied or status == "applied") else None
        existing = conn.execute("SELECT id FROM applications WHERE job_id=?", (job_id,)).fetchone()
        if existing:
            conn.execute(
                """UPDATE applications SET
                     status=?,
                     applied_at=COALESCE(?, applied_at),
                     notes=COALESCE(?, notes),
                     cv_pdf_path=COALESCE(?, cv_pdf_path),
                     cv_tex_path=COALESCE(?, cv_tex_path),
                     description_path=COALESCE(?, description_path),
                     run_dir=COALESCE(?, run_dir),
                     updated_at=?
                   WHERE job_id=?""",
                (
                    status,
                    applied_at,
                    notes,
                    cv_pdf_path,
                    cv_tex_path,
                    description_path,
                    run_dir,
                    ts,
                    job_id,
                ),
            )
            app_id = int(existing["id"])
        else:
            cur = conn.execute(
                """INSERT INTO applications
                   (job_id, status, applied_at, notes, cv_pdf_path, cv_tex_path, description_path, run_dir, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    job_id,
                    status,
                    applied_at,
                    notes,
                    cv_pdf_path,
                    cv_tex_path,
                    description_path,
                    run_dir,
                    ts,
                ),
            )
            app_id = int(cur.lastrowid)

        # Mirror status onto job
        job_status = status if status != "draft" else "shortlisted"
        if status == "tailored":
            job_status = "tailored"
        conn.execute("UPDATE jobs SET status=?, last_seen_at=? WHERE id=?", (job_status, ts, job_id))
        log_event(
            conn,
            "application",
            job_id=job_id,
            payload={"application_id": app_id, "status": status},
        )
        conn.commit()
        return {"application_id": app_id, "job_id": job_id, "status": status, "db": str(Path(db_path or DEFAULT_DB))}
    finally:
        conn.close()


def list_rows(kind: str, *, limit: int = 20, status: str | None = None, db_path: Path | None = None) -> list[dict]:
    conn = connect(db_path)
    try:
        if kind == "searches":
            rows = conn.execute(
                "SELECT id, created_at, queries_json, job_count, run_dir FROM searches ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        elif kind == "jobs":
            q = "SELECT id, title, company, location, source, best_score, status, url, last_seen_at FROM jobs"
            args: list = []
            if status:
                q += " WHERE status=?"
                args.append(status)
            q += " ORDER BY last_seen_at DESC LIMIT ?"
            args.append(limit)
            rows = conn.execute(q, args).fetchall()
        elif kind == "applications":
            q = """SELECT a.id, a.status, a.applied_at, a.updated_at, a.cv_pdf_path, a.notes,
                          j.title, j.company, j.url
                   FROM applications a JOIN jobs j ON j.id=a.job_id"""
            args = []
            if status:
                q += " WHERE a.status=?"
                args.append(status)
            q += " ORDER BY a.updated_at DESC LIMIT ?"
            args.append(limit)
            rows = conn.execute(q, args).fetchall()
        elif kind == "contacts":
            rows = conn.execute(
                """SELECT id, company, domain, job_id, created_at, emails_json
                   FROM contacts ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        else:
            raise SystemExit(f"unknown kind: {kind}")
        return [dict(r) for r in rows]
    finally:
        conn.close()


def stats(db_path: Path | None = None) -> dict:
    conn = connect(db_path)
    try:
        def n(table: str) -> int:
            return int(conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"])

        by_status = {
            r["status"]: r["c"]
            for r in conn.execute("SELECT status, COUNT(*) AS c FROM jobs GROUP BY status").fetchall()
        }
        app_status = {
            r["status"]: r["c"]
            for r in conn.execute("SELECT status, COUNT(*) AS c FROM applications GROUP BY status").fetchall()
        }
        return {
            "db": str(Path(db_path or DEFAULT_DB)),
            "searches": n("searches"),
            "jobs": n("jobs"),
            "contacts": n("contacts"),
            "applications": n("applications"),
            "events": n("events"),
            "jobs_by_status": by_status,
            "applications_by_status": app_status,
        }
    finally:
        conn.close()


def export_markdown(db_path: Path | None = None, out: Path | None = None) -> str:
    """Wiki-style dump of recent activity."""
    st = stats(db_path)
    apps = list_rows("applications", limit=50, db_path=db_path)
    jobs = list_rows("jobs", limit=30, db_path=db_path)
    searches = list_rows("searches", limit=10, db_path=db_path)
    lines = [
        f"# Job apply log",
        f"",
        f"DB: `{st['db']}`  ",
        f"Updated: {now()}",
        f"",
        f"## Stats",
        f"",
        f"- searches: {st['searches']}",
        f"- jobs: {st['jobs']} `{st['jobs_by_status']}`",
        f"- applications: {st['applications']} `{st['applications_by_status']}`",
        f"- contacts: {st['contacts']}",
        f"",
        f"## Applications",
        f"",
        f"| Status | Company | Title | Applied | CV |",
        f"|---|---|---|---|---|",
    ]
    for a in apps:
        lines.append(
            f"| {a.get('status')} | {a.get('company')} | {a.get('title')} | {a.get('applied_at') or ''} | {a.get('cv_pdf_path') or ''} |"
        )
    lines += ["", "## Recent jobs", "", "| Status | Score | Company | Title | Source |", "|---|---|---|---|---|"]
    for j in jobs:
        lines.append(
            f"| {j.get('status')} | {j.get('best_score')} | {j.get('company')} | {j.get('title')} | {j.get('source')} |"
        )
    lines += ["", "## Recent searches", ""]
    for s in searches:
        lines.append(f"- #{s['id']} {s['created_at']} — {s['job_count']} jobs — queries `{s['queries_json']}`")
    text = "\n".join(lines) + "\n"
    if out:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    p = argparse.ArgumentParser(description="job-apply SQLite CLI")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("stats")

    s = sub.add_parser("record-search")
    s.add_argument("--from-json", type=Path, required=True)
    s.add_argument("--run-dir")

    c = sub.add_parser("record-contacts")
    c.add_argument("--from-json", type=Path, required=True)
    c.add_argument("--job-id", type=int)

    a = sub.add_parser("apply")
    a.add_argument("--job-id", type=int)
    a.add_argument("--title")
    a.add_argument("--company")
    a.add_argument("--url", default="")
    a.add_argument("--status", default="applied")
    a.add_argument("--notes")
    a.add_argument("--cv-pdf")
    a.add_argument("--cv-tex")
    a.add_argument("--description")
    a.add_argument("--run-dir")
    a.add_argument("--applied", action="store_true")

    ls = sub.add_parser("list")
    ls.add_argument("kind", choices=["searches", "jobs", "applications", "contacts"])
    ls.add_argument("--status")
    ls.add_argument("--limit", type=int, default=20)

    ex = sub.add_parser("export-md")
    ex.add_argument("--out", type=Path, default=Path.home() / "Documents" / "job-apply" / "LOG.md")

    args = p.parse_args()
    db = args.db

    if args.cmd == "init":
        connect(db).close()
        print(json.dumps({"ok": True, "db": str(db)}))
    elif args.cmd == "stats":
        print(json.dumps(stats(db), indent=2))
    elif args.cmd == "record-search":
        payload = json.loads(args.from_json.read_text(encoding="utf-8"))
        print(json.dumps(record_search(payload, db_path=db, run_dir=args.run_dir), indent=2))
    elif args.cmd == "record-contacts":
        found = json.loads(args.from_json.read_text(encoding="utf-8"))
        print(json.dumps(record_contacts(found, job_id=args.job_id, db_path=db), indent=2))
    elif args.cmd == "apply":
        print(
            json.dumps(
                upsert_application(
                    job_id=args.job_id,
                    title=args.title,
                    company=args.company,
                    url=args.url,
                    status=args.status,
                    notes=args.notes,
                    cv_pdf_path=args.cv_pdf,
                    cv_tex_path=args.cv_tex,
                    description_path=args.description,
                    run_dir=args.run_dir,
                    applied=args.applied or args.status == "applied",
                    db_path=db,
                ),
                indent=2,
            )
        )
    elif args.cmd == "list":
        print(json.dumps(list_rows(args.kind, limit=args.limit, status=args.status, db_path=db), indent=2))
    elif args.cmd == "export-md":
        text = export_markdown(db, args.out)
        print(f"Wrote {args.out} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
