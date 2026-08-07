#!/usr/bin/env python3
"""Load config/scoring.yaml and score job dicts for shortlist / draft gates."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

JOB_APPLY_ROOT = Path.home() / "Documents" / "job-apply"
DEFAULT_SCORING = JOB_APPLY_ROOT / "config" / "scoring.yaml"
DEFAULT_PLAYS = JOB_APPLY_ROOT / "config" / "plays.yaml"


def load_yaml(path: Path | None = None) -> dict[str, Any]:
    p = Path(path or DEFAULT_SCORING)
    if not p.is_file():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def load_plays(path: Path | None = None) -> dict[str, Any]:
    p = Path(path or DEFAULT_PLAYS)
    if not p.is_file():
        return {}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _blob(job: dict) -> str:
    parts = [
        job.get("title") or "",
        job.get("company") or "",
        job.get("location") or "",
        job.get("description") or "",
    ]
    return " ".join(parts).lower()


def _any_in(text: str, needles: list[str] | None) -> bool:
    if not needles:
        return False
    t = text.lower()
    return any(n.lower() in t for n in needles if n)


def hard_excluded(job: dict, cfg: dict | None = None) -> tuple[bool, list[str]]:
    cfg = cfg if cfg is not None else load_yaml()
    reasons: list[str] = []
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    blob = _blob(job)
    he = cfg.get("hard_excludes") or {}
    for n in he.get("company_any") or []:
        if n.lower() in company:
            reasons.append(f"hard_exclude_company:{n}")
    for n in he.get("blob_any") or []:
        if n.lower() in blob:
            reasons.append(f"hard_exclude_blob:{n}")
    # defence signal as veto when weight is large negative and matched
    signals = cfg.get("signals") or {}
    de = signals.get("defence_exclude") or {}
    for n in de.get("company_or_blob_any") or []:
        if n.lower() in company or n.lower() in blob:
            reasons.append(f"defence_exclude:{n}")
    return (len(reasons) > 0, reasons)


def score_job(
    job: dict,
    *,
    terms: list[str] | None = None,
    cfg: dict | None = None,
) -> dict[str, Any]:
    """Return {score, action, signals, excluded, reasons}."""
    cfg = cfg if cfg is not None else load_yaml()
    title = (job.get("title") or "").lower()
    loc = (job.get("location") or "").lower()
    desc = (job.get("description") or "").lower()
    company = (job.get("company") or "").lower()
    blob = _blob(job)

    excluded, ex_reasons = hard_excluded(job, cfg)
    if excluded:
        return {
            "score": 0.0,
            "action": "skip",
            "signals": {},
            "excluded": True,
            "reasons": ex_reasons,
        }

    stack_terms = terms or list(cfg.get("stack_terms") or [])
    signal_hits: dict[str, float] = {}
    total = 0.0

    # stack_match: title 3x, else blob
    if stack_terms:
        title_hits = sum(1 for t in stack_terms if t.lower() in title)
        other_hits = sum(
            1 for t in stack_terms if t.lower() in blob and t.lower() not in title
        )
        frac = (3 * title_hits + other_hits) / max(len(stack_terms), 1)
        w = float((cfg.get("signals") or {}).get("stack_match", {}).get("weight", 2.5))
        # cap contribution roughly 0..weight
        contrib = min(frac, 1.0) * w
        if contrib:
            signal_hits["stack_match"] = round(contrib, 3)
            total += contrib

    signals = cfg.get("signals") or {}
    for name, spec in signals.items():
        if name in ("stack_match", "defence_exclude"):
            continue
        if not isinstance(spec, dict):
            continue
        w = float(spec.get("weight") or 0)
        hit = False
        if _any_in(title, spec.get("title_any")):
            hit = True
        if _any_in(loc, spec.get("location_any")):
            hit = True
        if _any_in(desc, spec.get("description_any")):
            hit = True
        if _any_in(company + " " + blob, spec.get("company_or_blob_any")):
            hit = True
        if hit:
            signal_hits[name] = w
            total += w

    thresholds = cfg.get("thresholds") or {}
    shortlist_t = float(thresholds.get("shortlist", 4.0))
    draft_t = float(thresholds.get("draft_outreach", 5.0))
    score = round(max(total, 0.0), 3)

    if score >= draft_t:
        action = "draft_outreach"
    elif score >= shortlist_t:
        action = "shortlist"
    else:
        action = "skip"

    return {
        "score": score,
        "action": action,
        "signals": signal_hits,
        "excluded": False,
        "reasons": list(signal_hits.keys()),
    }


def banned_line_hits(body: str, plays: dict | None = None) -> list[str]:
    plays = plays if plays is not None else load_plays()
    body_l = (body or "").lower()
    hits = []
    for line in plays.get("banned_lines_global") or []:
        if line.lower() in body_l:
            hits.append(line)
    return hits


def pick_play(tier: str, contact_role: str = "") -> str | None:
    """Map company size tier + role to a play id."""
    tier = (tier or "").lower().strip()
    role = (contact_role or "").lower()
    if tier in ("startup", "early", "small"):
        return "startup_founder"
    if tier in ("mid", "growth", "medium"):
        return "mid_em"
    if tier in ("large", "enterprise", "big"):
        return "large_recruiter"
    if any(k in role for k in ("founder", "cto", "head of")):
        return "startup_founder"
    if any(k in role for k in ("recruiter", "talent")):
        return "large_recruiter"
    return "mid_em"
