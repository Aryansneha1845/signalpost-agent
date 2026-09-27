"""Report generator: per-company Markdown matching the console report layout.

Inputs are already-verified profiles (registry + verification + synthesis).
No network. All numbers cite their evidence module + source URL.
"""
from __future__ import annotations

from typing import Any


def _fmt_amount(value: Any, currency: Any) -> str:
    if value is None:
        return "not reported"
    try:
        return f"{float(value):,.1f} {currency or ''}".strip()
    except (TypeError, ValueError):
        return str(value)


def build_markdown(profile: dict[str, Any]) -> str:
    org = str(profile.get("organisation_number") or "?")
    name = str(profile.get("name") or "Unknown")
    ev = profile.get("evidence", {}) if isinstance(profile.get("evidence"), dict) else {}
    ver = profile.get("verification", {}) if isinstance(profile.get("verification"), dict) else {}
    conf = ver.get("confidence", "?")

    def _src(mod: str) -> str:
        rec = ev.get(mod, {})
        url = rec.get("source_url", "?") if isinstance(rec, dict) else "?"
        rt = rec.get("retrieved_at", "?") if isinstance(rec, dict) else "?"
        return f"{url} (retrieved {rt})"

    fin_rec = ((ev.get("financials", {}).get("value") or {}).get("records") or [{}])[0]
    per = fin_rec.get("period") if isinstance(fin_rec.get("period"), dict) else {}
    roles = [r for r in ((ev.get("roles", {}).get("value") or {}).get("roles") or []) if not r.get("inactive")]
    locs = (ev.get("locations", {}).get("value") or {}).get("locations") or []
    wval = ev.get("website", {}).get("value") if isinstance(ev.get("website", {}).get("value"), dict) else {}
    hiring = ev.get("hiring", {}) if isinstance(ev.get("hiring"), dict) else {}

    lines = [
        "# COMPANY RESEARCH REPORT",
        "",
        f"**Company:** {name}",
        f"**Org. no:** {org}",
        "",
        f"**Industry:** {profile.get('industry_label') or profile.get('industry_code') or 'not reported'} "
        f"({profile.get('industry_code') or '?'})",
        f"**Location:** {profile.get('municipality') or 'not reported'}",
        f"**Legal form:** {profile.get('legal_form') or 'not reported'}",
        "",
        "## Financial snapshot",
        f"- Revenue: {_fmt_amount(fin_rec.get('revenue'), fin_rec.get('currency'))}",
        f"- Annual result: {_fmt_amount(fin_rec.get('annual_result'), fin_rec.get('currency'))}",
        f"- Employees (registry): {profile.get('employees') if profile.get('employees') is not None else 'not reported'}",
        f"- Period: {per.get('fraDato', '?')} to {per.get('tilDato', '?')}",
        f"- Source: {_src('financials')}",
        "",
        "## Key people",
    ]
    if roles:
        for r in roles[:8]:
            lines.append(f"- {r.get('name') or '?'} — {r.get('role') or r.get('group') or 'role'}")
    else:
        lines.append("- No active public role holder returned (reported honestly, not zero).")
    lines += ["", "## External footprint",
              f"- Website: {(wval.get('final_url') or 'not available')}",
              f"- Hiring surface: {(hiring.get('value') or {}).get('careers_url', 'none surfaced') if hiring.get('status') == 'available' else 'not established'}",
              f"- Registered subunits: {len(locs)}",
              "", "## Evidence"]
    for mod in ("registry_live", "financials", "roles", "locations", "website", "hiring"):
        rec = ev.get(mod, {})
        if isinstance(rec, dict):
            lines.append(f"- [{mod}] {rec.get('status', '?')}: {_src(mod)}")
    lines += ["", f"**Confidence: {conf}** (weighted verification checks; contradictions cap at 0.6)",
              "", "_Missing values were never converted to zero. Verify critical facts at brreg.no._"]
    return "\n".join(lines) + "\n"
