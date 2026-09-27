#!/usr/bin/env python3
"""Build docs/app/companies.json from real smoke envelopes (demo-mode data).

Honest numbers only: KPIs counted from envelopes, featured companies are
real researched profiles, trend charts use real filed records.
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("smoke-test/smoke100-out/envelopes.jsonl")
OUT = Path("docs/app/companies.json")


def summarize(env: dict) -> dict:
    p = env.get("profile", {})
    ev = p.get("evidence", {}) if isinstance(p.get("evidence"), dict) else {}
    fin = ((ev.get("financials", {}).get("value") or {}).get("records") or [])
    roles = [r for r in ((ev.get("roles", {}).get("value") or {}).get("roles") or []) if not r.get("inactive")]
    locs = (ev.get("locations", {}).get("value") or {}).get("locations") or []
    wval = ev.get("website", {}).get("value") if isinstance(ev.get("website", {}).get("value"), dict) else {}
    ver = p.get("verification", {}) if isinstance(p.get("verification"), dict) else {}
    return {
        "org": env.get("organisation_number"),
        "name": p.get("name"),
        "form": p.get("legal_form"),
        "status": "Active" if not ((ev.get("registry_live", {}).get("value") or {}).get("bankrupt")) else "Bankrupt",
        "municipality": p.get("municipality"),
        "industry": p.get("industry_label") or p.get("industry_code"),
        "employees": p.get("employees"),
        "website": wval.get("final_url"),
        "website_verified": bool((wval.get("identity_assessment") or {}).get("publishable")),
        "confidence": ver.get("confidence"),
        "financials": [
            {"period": r.get("period"), "currency": r.get("currency"), "revenue": r.get("revenue"),
             "operating": r.get("operating_result"), "result": r.get("annual_result"),
             "assets": r.get("assets"), "equity": r.get("equity")}
            for r in fin[:3]
        ],
        "people": [{"name": r.get("name"), "role": r.get("role") or r.get("group"),
                    "retrieved": (ev.get("roles", {}) or {}).get("retrieved_at")} for r in roles[:8]],
        "locations": len(locs),
        "evidence": [
            {"module": m, "state": (r or {}).get("status"), "url": (r or {}).get("source_url"),
             "retrieved": (r or {}).get("retrieved_at"), "note": (r or {}).get("note")}
            for m, r in ev.items() if isinstance(r, dict)
        ],
        "summary": (p.get("synthesis") or {}).get("summary"),
        "report": p.get("report_path"),
    }


def main() -> None:
    envs = [json.loads(line) for line in SRC.read_text(encoding="utf-8").splitlines() if line.strip()]
    featured = sorted(envs, key=lambda e: (
        0 if (e.get("profile", {}).get("evidence", {}).get("website", {}) or {}).get("status") == "available" else 1,
        -(len(((e.get("profile", {}).get("evidence", {}).get("financials", {}) or {}).get("value") or {}).get("records") or [])),
    ))[:12]
    data = {
        "generated_from": "smoke-test/smoke100-out (100 real researched envelopes)",
        "stats": {
            "companies": len(envs),
            "financials": sum(1 for e in envs if ((e.get("profile", {}).get("evidence", {}) or {}).get("financials", {}) or {}).get("status") == "available"),
            "websites": sum(1 for e in envs if ((e.get("profile", {}).get("evidence", {}) or {}).get("website", {}) or {}).get("status") == "available"),
            "roles": sum(1 for e in envs if ((e.get("profile", {}).get("evidence", {}) or {}).get("roles", {}) or {}).get("status") == "available"),
        },
        "featured": [summarize(e) for e in featured],
        "companies": [{"org": e.get("organisation_number"), "name": (e.get("profile", {}) or {}).get("name"),
                       "form": (e.get("profile", {}) or {}).get("legal_form"),
                       "municipality": (e.get("profile", {}) or {}).get("municipality")} for e in envs],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(envs)} companies)")


if __name__ == "__main__":
    main()
