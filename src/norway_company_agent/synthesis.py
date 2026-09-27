"""Decision-useful synthesis over source-linked facts only.

Never invents. Every sentence is backed by an evidence module.
Marks unknowns explicitly. Used for 12 synthesis points.
"""
from __future__ import annotations

from typing import Any


def _latest_financial(profile: dict[str, Any]) -> dict[str, Any]:
    recs = ((profile.get("evidence", {}).get("financials", {}).get("value") or {}).get("records") or [])
    return recs[0] if recs else {}


def build_synthesis(profile: dict[str, Any]) -> dict[str, Any]:
    org = str(profile.get("organisation_number") or "")
    name = profile.get("name") or "Unknown legal name"
    form = profile.get("legal_form") or "unknown form"
    muni = profile.get("municipality") or "unknown municipality"
    employees = profile.get("employees")
    fin = _latest_financial(profile)
    roles = (profile.get("evidence", {}).get("roles", {}).get("value") or {}).get("roles", [])
    active_roles = [r for r in roles if not r.get("inactive")][:5]
    locs = (profile.get("evidence", {}).get("locations", {}).get("value") or {}).get("locations", [])
    website = profile.get("evidence", {}).get("website", {})
    wval = website.get("value") or {}
    publishable = (wval.get("identity_assessment") or {}).get("publishable", False)
    hiring = (profile.get("evidence", {}).get("hiring", {}) or {})
    hiring_val = hiring.get("value") or {}

    parts: list[str] = [f"{name} ({org}) is registered as {form} in {muni}."]
    sources: list[str] = ["registry"]
    if employees is not None:
        parts.append(f"Registered employee count: {employees}.")
    if fin:
        period = fin.get("period") or {}
        rev, res = fin.get("revenue"), fin.get("annual_result")
        if rev is None and res is None:
            parts.append("Latest filed accounts contain no normalized revenue/result; missing is not zero.")
        else:
            bits = []
            if rev is not None:
                bits.append(f"revenue {rev}")
            if res is not None:
                bits.append(f"annual result {res}")
            per = f"{period.get('fraDato','?')} to {period.get('tilDato','?')}" if isinstance(period, dict) else str(period)
            parts.append(f"Latest accounts ({per}, {fin.get('currency','?')}): " + ", ".join(bits) + ".")
        sources.append("financials")
    else:
        parts.append("No normalized annual-account record returned; not interpreted as zero.")
    if active_roles:
        names = ", ".join(f"{r.get('name','?')} ({r.get('role') or r.get('group') or 'role'})" for r in active_roles)
        parts.append(f"Active registered roles include: {names}.")
        sources.append("roles")
    else:
        parts.append("No active public role holder returned.")
    if locs:
        parts.append(f"{len(locs)} registered subunit(s); first: {locs[0].get('name','?')}.")
        sources.append("locations")
    if publishable and wval.get("description"):
        parts.append(f"Company describes itself as: {wval['description'][:280]}")
        sources.append("website")
    elif website.get("status") == "available":
        parts.append("Registry-linked website fetched but exact identity not established; its claims quarantined.")
    else:
        parts.append("Registry-linked website not available to this run.")
    if hiring.get("status") == "available" and hiring_val.get("hiring_detected"):
        parts.append(f"Hiring surface detected: {hiring_val.get('careers_url')}. Company-owned only.")
        sources.append("hiring")
    else:
        parts.append("No company-owned hiring surface surfaced in bounded crawl.")
    unknowns = []
    if not fin:
        unknowns.append("financials")
    if not active_roles:
        unknowns.append("leadership")
    if not locs:
        unknowns.append("workplaces")
    if not publishable:
        unknowns.append("verified website content")
    if unknowns:
        parts.append("Unknowns remain: " + ", ".join(unknowns) + ".")
    return {
        "organisation_number": org,
        "summary": " ".join(parts),
        "evidence_modules": sorted(set(sources)),
        "unknowns": unknowns,
        "policy": "Template over source-linked facts only; no LLM, no invented fields.",
    }
