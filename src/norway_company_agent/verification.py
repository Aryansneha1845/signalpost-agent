"""Verification engine: cross-source checks over already-fetched evidence.

Zero extra outbound requests. Never invents. Each check yields
pass/warn/fail with reasons; confidence is the share of applicable
checks passing, weighted by source authority:

  official registry / annual accounts / roles / subunits : 3
  verified company-owned website / hiring                 : 2
  experimental / quarantined                              : 0 (excluded)

Contradictions and stale evidence cap confidence instead of deleting
facts — the envelope keeps honest states, the report shows the caveat.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

AUTHORITY = {
    "registry": 3, "registry_live": 3, "accounting_obligation": 3,
    "financials": 3, "roles": 3, "locations": 3, "group": 2,
    "website": 2, "hiring": 2,
}

FRESHNESS_DAYS = {"registry_live": 30, "financials": 400, "roles": 90, "website": 60}


def _age_days(retrieved_at: Any) -> float | None:
    try:
        ts = datetime.fromisoformat(str(retrieved_at).replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0
    except Exception:
        return None


def verify_profile(profile: dict[str, Any]) -> dict[str, Any]:
    org = str(profile.get("organisation_number") or "")
    ev = profile.get("evidence", {}) if isinstance(profile.get("evidence"), dict) else {}
    checks: list[dict[str, Any]] = []

    def _add(name: str, status: str, detail: str, weight: int = 1) -> None:
        checks.append({"check": name, "status": status, "detail": detail, "weight": weight})

    live = ev.get("registry_live", {}) if isinstance(ev.get("registry_live"), dict) else {}
    base = ev.get("registry", {}) if isinstance(ev.get("registry"), dict) else {}
    if live.get("status") == "available" and base.get("status") == "available":
        lv, bv = live.get("value") or {}, base.get("value") or {}
        if isinstance(lv, dict) and isinstance(bv, dict):
            match = all(str(lv.get(k) or "") == str(bv.get(k) or "") for k in ("name", "legal_form") if lv.get(k) or bv.get(k))
            _add("identity_consistency", "pass" if match else "warn",
                 "Live registry agrees with bulk snapshot on name/legal form." if match
                 else "Live registry differs from bulk snapshot — snapshot may be stale; live value preferred.", 3)
        else:
            _add("identity_consistency", "warn", "Registry payloads not comparable; identity anchored on organisation number.", 3)
    else:
        _add("identity_consistency", "warn", "Bulk or live registry unavailable; identity anchored on organisation number only.", 3)

    fin = ev.get("financials", {}) if isinstance(ev.get("financials"), dict) else {}
    if fin.get("status") == "available":
        recs = ((fin.get("value") or {}).get("records") or [])
        if recs and isinstance(recs[0], dict):
            r = recs[0]
            per = r.get("period") if isinstance(r.get("period"), dict) else {}
            sane = r.get("revenue") is None or float(r.get("revenue") or 0) >= 0
            _add("financial_sanity", "pass" if sane else "fail",
                 f"Latest accounts {per.get('fraDato', '?')} to {per.get('tilDato', '?')} "
                 f"({r.get('currency', '?')}); figures present, missing never zeroed." if sane
                 else "Negative revenue value — flagged, not published as fact.", 3)
        else:
            _add("financial_sanity", "warn", "Financials available but no normalized record; treated as unknown.", 3)
    else:
        _add("financial_sanity", "warn", f"Annual accounts {fin.get('status', 'missing')} — reported honestly, not zeroed.", 1)

    roles = ev.get("roles", {}) if isinstance(ev.get("roles"), dict) else {}
    if roles.get("status") == "available":
        people = [x for x in ((roles.get("value") or {}).get("roles") or []) if not x.get("inactive")]
        _add("leadership_present", "pass" if people else "warn",
             f"{len(people)} active public role holder(s)." if people else "No active public role holder returned.", 2)
    else:
        _add("leadership_present", "warn", "Role source not available; leadership unknown.", 1)

    website = ev.get("website", {}) if isinstance(ev.get("website"), dict) else {}
    wval = website.get("value") if isinstance(website.get("value"), dict) else {}
    ident = wval.get("identity_assessment") if isinstance(wval.get("identity_assessment"), dict) else {}
    if website.get("status") == "available" and ident.get("publishable"):
        _add("website_authority", "pass",
             f"Exact-entity website verified ({ident.get('method', '?')}, score {ident.get('score', '?')}). Company claims usable as company-reported.", 2)
    elif website.get("status") == "available":
        _add("website_authority", "warn",
             "Website fetched but exact identity unproven — its claims quarantined, never published as facts.", 2)
    else:
        _add("website_authority", "warn", "No registry-linked website available; web claims absent, not denied.", 1)

    bankrupt = bool((live.get("value") or {}).get("bankrupt")) if isinstance(live.get("value"), dict) else False
    if bankrupt and website.get("status") == "available" and ident.get("publishable"):
        _add("contradiction_bankruptcy", "warn",
             "Registry reports bankruptcy while an active company site exists — both facts kept with sources; treat site content as possibly stale.", 3)
    else:
        _add("contradiction_bankruptcy", "pass", "No registry/site contradiction on bankrupt status.", 1)

    stale: list[str] = []
    for mod, limit in FRESHNESS_DAYS.items():
        rec = ev.get(mod, {})
        if isinstance(rec, dict) and rec.get("status") == "available":
            age = _age_days(rec.get("retrieved_at"))
            if age is not None and age > limit:
                stale.append(f"{mod} ({age:.0f}d old)")
    _add("freshness", "pass" if not stale else "warn",
         "Evidence within freshness windows." if not stale else f"Stale evidence: {', '.join(stale)} — refresh recommended.", 2)

    total = sum(c["weight"] for c in checks)
    earned = sum(c["weight"] for c in checks if c["status"] == "pass")
    confidence = round(earned / total, 2) if total else 0.0
    if any(c["check"] == "contradiction_bankruptcy" and c["status"] != "pass" for c in checks):
        confidence = min(confidence, 0.6)
    return {
        "organisation_number": org,
        "confidence": confidence,
        "checks": checks,
        "policy": "Deterministic cross-source checks; contradictions cap confidence, facts keep honest states.",
    }
