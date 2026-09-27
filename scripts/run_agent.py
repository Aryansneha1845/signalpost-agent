#!/usr/bin/env python3
"""One-command Signalpost agent: input org list -> envelopes + gallery + report.

Usage (evaluator pastes one line):
  python scripts/run_agent.py --input smoke-companies.jsonl --bulk brreg-enheter.csv.gz --out out --run-id smoke-001 --expected-count 100

Wraps the audited competition batch, then adds zero-extra-request
hiring + synthesis + gallery layers. $0 third-party cost.

Security: no shell, no secrets, fixed script paths under ROOT, bounded
workers/count, all URLs validated downstream (Brreg allowlist + public-URL
SSRF guards), gallery output HTML-escaped with script-blocking CSP.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from norway_company_agent.jobs import extract_jobs
from norway_company_agent.reports import build_markdown
from norway_company_agent.synthesis import build_synthesis
from norway_company_agent.verification import verify_profile


def _positive_int(value: str, *, minimum: int, maximum: int, name: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{name} must be an integer")
    if not minimum <= number <= maximum:
        raise argparse.ArgumentTypeError(f"{name} must be between {minimum} and {maximum}")
    return number


def main() -> None:
    ap = argparse.ArgumentParser(description="Signalpost one-command agent")
    ap.add_argument("--input", required=True, help="JSON/JSONL/TXT organisation-number list")
    ap.add_argument("--bulk", required=True, help="Frozen Brreg bulk CSV snapshot")
    ap.add_argument("--out", default="out", help="Output directory")
    ap.add_argument("--run-id", default="local-001")
    ap.add_argument("--expected-count", type=lambda v: _positive_int(v, minimum=1, maximum=100000, name="expected-count"), default=5)
    ap.add_argument("--workers", type=lambda v: _positive_int(v, minimum=1, maximum=32, name="workers"), default=8)
    args = ap.parse_args()

    if len(args.run_id) > 64 or not all(c.isalnum() or c in "-_." for c in args.run_id):
        ap.error("run-id must be 1-64 chars of [A-Za-z0-9-_.]")
    batch_script = ROOT / "scripts" / "run_competition_batch.py"
    gallery_script = ROOT / "scripts" / "build_gallery.py"
    pages_script = ROOT / "scripts" / "build_site_pages.py"
    if not batch_script.is_file() or not gallery_script.is_file() or not pages_script.is_file():
        raise SystemExit("Evaluator scripts missing under fixed ROOT — refusing to run")

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    profiles_p = outdir / "profiles.jsonl"
    envelopes_p = outdir / "envelopes.jsonl"
    report_p = outdir / "run-report.json"

    cmd = [sys.executable, str(batch_script),
           "--organisations", args.input, "--bulk", args.bulk,
           "--profiles-output", str(profiles_p), "--output", str(envelopes_p),
           "--report", str(report_p), "--run-id", args.run_id,
           "--expected-count", str(args.expected_count), "--workers", str(args.workers)]
    print("+ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2700)
    print(proc.stdout[-3000:])
    if proc.returncode != 0:
        print(proc.stderr[-3000:])
        raise SystemExit(proc.returncode)

    # Layer 2: hiring + verification + synthesis (no extra network).
    profiles = [json.loads(line) for line in profiles_p.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(profiles) != args.expected_count:
        raise SystemExit(f"Refusing to continue: {len(profiles)} profiles != expected {args.expected_count}")
    reports_dir = outdir / "reports"
    reports_dir.mkdir(exist_ok=True)
    for p in profiles:
        p.setdefault("evidence", {})["hiring"] = extract_jobs(p)
        p["verification"] = verify_profile(p)
        p["synthesis"] = build_synthesis(p)
        p["report_markdown"] = build_markdown(p)
        (reports_dir / f"{p['organisation_number']}.md").write_text(p["report_markdown"], encoding="utf-8")
        p["report_path"] = f"reports/{p['organisation_number']}.md"
    profiles_p.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in profiles), encoding="utf-8")

    envelopes = [json.loads(line) for line in envelopes_p.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_org = {p["organisation_number"]: p for p in profiles}
    for e in envelopes:
        if e.get("organisation_number") in by_org:
            e["profile"] = by_org[e["organisation_number"]]
    envelopes_p.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in envelopes), encoding="utf-8")

    gal = outdir / "gallery.html"
    g = subprocess.run([sys.executable, str(gallery_script),
                        "--envelopes", str(envelopes_p), "--output", str(gal)],
                       capture_output=True, text=True, timeout=600)
    print(g.stdout[-1000:])
    if g.returncode != 0:
        print(g.stderr[-1000:])
        raise SystemExit(g.returncode)

    p = subprocess.run([sys.executable, str(pages_script), "--out", str(outdir)],
                       capture_output=True, text=True, timeout=600)
    print(p.stdout[-1000:])
    if p.returncode != 0:
        print(p.stderr[-1000:])
        raise SystemExit(p.returncode)

    rep = json.loads(report_p.read_text(encoding="utf-8"))
    rep["layers"] = {"hiring": "company_owned_zero_extra_requests", "synthesis": "template_no_llm", "gallery": str(gal), "third_party_cost_usd": 0}
    report_p.write_text(json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"envelopes": len(envelopes), "gallery": str(gal), "report": str(report_p)}, indent=2))


if __name__ == "__main__":
    main()
