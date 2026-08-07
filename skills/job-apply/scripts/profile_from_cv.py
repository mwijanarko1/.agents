#!/usr/bin/env python3
"""Derive job-search queries from cv-data.json."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_CV = Path.home() / "Documents" / "job-apply" / "CV" / "cv-data.json"

ROLE_HINTS = [
    "software engineer",
    "software developer",
    "full stack",
    "frontend",
    "backend",
    "mobile engineer",
    "ios engineer",
    "react native",
    "graduate software",
    "junior software",
    "ai engineer",
    "product engineer",
]


def load_cv(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def top_skills(cv: dict, n: int = 12) -> list[str]:
    skills = cv.get("skills", {})
    if isinstance(skills, dict):
        tech = skills.get("technical_skills") or skills.get("skills") or []
    elif isinstance(skills, list):
        tech = skills
    else:
        tech = []
    # Prefer product/eng stack over generic office tools
    prefer = {
        "TypeScript",
        "JavaScript",
        "React",
        "Next.js",
        "React Native",
        "Swift",
        "SwiftUI",
        "Python",
        "Expo",
        "Node",
        "PostgreSQL",
        "Go",
        "Rust",
        "iOS",
        "Convex",
    }
    ranked = sorted(
        [s for s in tech if isinstance(s, str)],
        key=lambda s: (0 if s in prefer else 1, s.lower()),
    )
    return ranked[:n]


def titles(cv: dict) -> list[str]:
    out: list[str] = []
    for key in ("work_experience", "additional_technical_experience"):
        for job in cv.get(key) or []:
            t = job.get("title") or job.get("role")
            if t:
                out.append(str(t))
    headline = (cv.get("personal_info") or {}).get("headline") or ""
    out.extend(re.split(r"[|•,/]", headline))
    skip = re.compile(
        r"ambassador|president|officer|marketing lead|vice president|championship|project",
        re.I,
    )
    cleaned = []
    for t in out:
        t = re.sub(r"\s+", " ", t).strip()
        if not t or skip.search(t):
            continue
        if t not in cleaned:
            cleaned.append(t)
    return cleaned


def default_queries(cv: dict, extra: list[str] | None = None) -> list[str]:
    skills = top_skills(cv)
    skill_blob = " ".join(skills[:6])
    base = [
        "software engineer typescript react",
        "react native developer",
        "ios swift engineer graduate",
        "full stack next.js typescript",
        "junior software engineer uk",
        "graduate software engineer",
        "ai product engineer",
    ]
    if skill_blob:
        base.insert(0, f"software engineer {skill_blob}")
    for t in titles(cv)[:3]:
        if len(t.split()) <= 6:
            base.append(t.lower())
    for r in ROLE_HINTS[:4]:
        base.append(r)
    if extra:
        base.extend(extra)
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for q in base:
        q = re.sub(r"\s+", " ", q).strip().lower()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out[:10]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cv", type=Path, default=DEFAULT_CV)
    p.add_argument("--query", action="append", default=[])
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    cv = load_cv(args.cv)
    info = cv.get("personal_info") or {}
    contact = info.get("contact") or {}
    profile = {
        "name": info.get("name"),
        "headline": info.get("headline"),
        "email": contact.get("email"),
        "linkedin": contact.get("linkedin"),
        "github": contact.get("github"),
        "website": contact.get("website"),
        "skills": top_skills(cv),
        "titles": titles(cv)[:8],
        "queries": default_queries(cv, args.query),
        "cv_path": str(args.cv.resolve()),
        "cv_repo": str(args.cv.resolve().parent),
    }
    if args.json:
        print(json.dumps(profile, indent=2))
    else:
        print(f"Name: {profile['name']}")
        print(f"Headline: {profile['headline']}")
        print(f"Skills: {', '.join(profile['skills'])}")
        print("Queries:")
        for q in profile["queries"]:
            print(f"  - {q}")


if __name__ == "__main__":
    main()
