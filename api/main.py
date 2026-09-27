"""API / Agent Gateway: validation + job management over the orchestrator.

Local console backend only — NOT the evaluator path (the evaluator uses
`python scripts/run_agent.py`). Run locally:

    pip install -r requirements-console.txt
    uvicorn api.main:app --port 8000

Then open http://localhost:8000/console for the interactive console,
or POST {"organisation_number": "923609016"} to /research.
"""
from __future__ import annotations

import html
import re
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator

from norway_company_agent.batch import profiles_from_bulk
from norway_company_agent.orchestrator import research_company

BULK_DEFAULT = ROOT / "smoke-test" / "brreg-enheter.csv.gz"

app = FastAPI(title="Signalpost Agent Gateway", version="0.2.0")
_JOBS: dict[str, dict[str, Any]] = {}


class ResearchRequest(BaseModel):
    organisation_number: str

    @field_validator("organisation_number")
    @classmethod
    def _nine_digits(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value or "")
        if len(digits) != 9:
            raise ValueError("organisation_number must be 9 digits")
        return digits


def _seed_profile(org: str) -> dict[str, Any]:
    if not BULK_DEFAULT.exists():
        return {"organisation_number": org, "evidence": {}}
    profiles, _ = profiles_from_bulk(str(BULK_DEFAULT), [org])
    return profiles[0]


@app.post("/research")
def research(body: ResearchRequest) -> JSONResponse:
    job_id = uuid.uuid4().hex[:12]
    try:
        seed = _seed_profile(body.organisation_number)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    result = research_company(seed)
    profile = result["profile"]
    _JOBS[job_id] = {"job_id": job_id, "organisation_number": body.organisation_number,
                     "requests": result["requests"], "profile": profile}
    return JSONResponse({
        "job_id": job_id,
        "organisation_number": body.organisation_number,
        "checklist": result["events"],
        "verification": profile.get("verification"),
        "synthesis": (profile.get("synthesis") or {}).get("summary"),
        "report_markdown": profile.get("report_markdown"),
        "requests": result["requests"],
    })


@app.get("/report/{org}")
def report(org: str) -> HTMLResponse:
    digits = re.sub(r"\D", "", org or "")
    if len(digits) != 9:
        raise HTTPException(status_code=422, detail="organisation_number must be 9 digits")
    for job in _JOBS.values():
        if job["organisation_number"] == digits and job["profile"].get("report_markdown"):
            body = "".join(f"<p>{html.escape(line)}</p>" if line and not line.startswith("#") else
                           f"<h2>{html.escape(line.strip('# ').strip())}</h2>" if line.startswith("#") else "<br>"
                           for line in job["profile"]["report_markdown"].splitlines())
            return HTMLResponse(f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
                                f"<title>Report {digits}</title></head><body>{body}</body></html>")
    raise HTTPException(status_code=404, detail="No report for this organisation yet — POST /research first.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


GATEWAY_HOST = "http://localhost:8000"


@app.get("/console-research", response_class=HTMLResponse)
def console_research(organisation_number: str = "") -> HTMLResponse:
    """Server-rendered console result so the static Pages form works with zero JS."""
    digits = re.sub(r"\D", "", organisation_number or "")
    if len(digits) != 9:
        return HTMLResponse(
            "<!doctype html><html lang='en'><body><h1>Invalid company number</h1>"
            "<p>Enter 9 digits. <a href='/console'>Back to console</a>.</p></body></html>",
            status_code=422)
    try:
        seed = _seed_profile(digits)
    except ValueError as exc:
        return HTMLResponse(
            f"<!doctype html><html lang='en'><body><h1>Company not in snapshot</h1>"
            f"<p>{html.escape(str(exc))}</p></body></html>", status_code=404)
    result = research_company(seed)
    profile = result["profile"]
    steps = "".join(
        f"<li>{'✓' if e['ok'] else '✗'} <strong>{html.escape(e['step'])}</strong> — {html.escape(e['detail'])}</li>"
        for e in result["events"])
    ver = profile.get("verification", {}) or {}
    checks = "".join(
        f"<li>[{html.escape(c.get('status', '?'))}] {html.escape(c.get('check', '?'))} — {html.escape(c.get('detail', ''))}</li>"
        for c in ver.get("checks", []))
    md = html.escape(profile.get("report_markdown") or "No report.")
    return HTMLResponse(
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Report {digits} — Signalpost console</title></head><body>"
        f"<h1>Company research report — {html.escape(str(profile.get('name') or digits))}</h1>"
        f"<h2>Researching… checklist</h2><ul>{steps}</ul>"
        f"<h2>Verification (confidence {html.escape(str(ver.get('confidence', '?')))})</h2><ul>{checks}</ul>"
        f"<h2>Report</h2><pre>{md}</pre>"
        f"<p><a href='/console'>Research another company</a></p></body></html>")


@app.get("/console", response_class=HTMLResponse)
def console() -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Signalpost console</title></head><body>"
        "<h1>Signalpost console</h1>"
        "<form action='/console-research' method='get'>"
        "<label for='org'>Company / Org No.</label>"
        "<input id='org' name='organisation_number' inputmode='numeric' pattern='[0-9 ]{9,12}' required>"
        "<button type='submit'>Research</button></form></body></html>")
