"""Research orchestrator: the 6-step pipeline with a UI checklist.

Steps: 1 resolve entity, 2 plan research, 3 collect evidence,
4 verify evidence, 5 detect changes, 6 generate report.

Each step emits a checklist event (label + ok/fail + detail) so the
console can render the 'Researching...' progress from the diagram.
Deterministic; the only network happens in step 3 via the audited
official + website fetchers.
"""
from __future__ import annotations

from typing import Any, Callable

from .identity import apply_website_identity_gate
from .jobs import extract_jobs
from .official import fetch_official_modules
from .refresh import diff_profile
from .reports import build_markdown
from .synthesis import build_synthesis
from .verification import verify_profile
from .website import fetch_website

STEPS = ("resolve", "plan", "collect", "verify", "changes", "report")
CORE_MODULES = {"registry_live", "financials", "roles", "group", "locations"}


def research_company(profile: dict[str, Any],
                     *,
                     previous: dict[str, Any] | None = None,
                     website_enabled: bool = True,
                     on_step: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    def _emit(step: str, ok: bool, detail: str) -> None:
        evt = {"step": step, "ok": ok, "detail": detail}
        events.append(evt)
        if on_step:
            on_step(evt)

    org = str(profile.get("organisation_number") or "")
    _emit("resolve", bool(org and len(org) == 9),
          f"Company identity verified: {profile.get('name') or org} ({org})." if org else "Invalid organisation number.")

    _emit("plan", True, f"Research plan: {', '.join(sorted(CORE_MODULES))}"
          + (" + website." if website_enabled else ", website skipped."))

    records, metrics = fetch_official_modules(org, set(CORE_MODULES))
    profile.setdefault("evidence", {}).update(records)
    got = sum(1 for m in CORE_MODULES if records.get(m, {}).get("status") == "available")
    website_requests = 0
    if website_enabled:
        wrec, wmet = fetch_website(profile.get("website"))
        website_requests = int(wmet.get("requests") or 0)
        profile["evidence"]["website"] = apply_website_identity_gate(profile, wrec)["website"]
        _emit("collect", got > 0,
              f"Official website {'found' if wrec.get('status') == 'available' else 'not available'}; "
              f"financial data {'collected' if records.get('financials', {}).get('status') == 'available' else 'unavailable (honest state)'}; "
              f"key people {'identified' if records.get('roles', {}).get('status') == 'available' else 'unavailable'}.")
    else:
        _emit("collect", got > 0, f"Collected {got}/{len(CORE_MODULES)} official modules; website skipped.")

    profile["evidence"]["hiring"] = extract_jobs(profile)
    profile["verification"] = verify_profile(profile)
    profile["synthesis"] = build_synthesis(profile)
    v = profile["verification"]
    _emit("verify", True,
          f"Sources verified: confidence {v.get('confidence')} across {len(v.get('checks', []))} cross-source checks.")

    changes: list[dict[str, Any]] = diff_profile(previous, profile) if previous else []
    _emit("changes", True,
          f"{len(changes)} material change(s) vs previous snapshot." if previous else "No previous snapshot — baseline established.")

    profile["report_markdown"] = build_markdown(profile)
    _emit("report", True, "Company research report generated (JSONL envelope + Markdown, evidence cited).")
    return {"profile": profile, "events": events,
            "requests": len(metrics) + website_requests}
