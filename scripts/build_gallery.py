#!/usr/bin/env python3
"""Static desktop/mobile gallery from terminal envelopes (8 UX points).

Security: all dynamic strings are html-escaped; links rendered only for
http(s) URLs, everything else as plain text; page carries a script-blocking
CSP meta (no inline scripts exist) plus rel=noopener on outbound links.

Accessibility: skip link, semantic landmarks, visible focus, table scope +
caption, AA-contrast palette, keyboard-operable (no JS traps, all content
reachable by Tab through native links).
"""
from __future__ import annotations

import argparse
import html
import json
import urllib.parse
from pathlib import Path

CONTACT_EMAIL = "submit@builderr.ai"

CSS = (
    ":root{--bg:#0f172a;--bg2:#1e293b;--accent:#f59e0b;--paper:#eef2f7;--card:#ffffff;"
    "--ink:#0f172a;--muted:#475569;--line:#dbe3ef;--green:#0e6b3a;--amber:#7a4a00;"
    "--red:#a12020;--gray:#475569;--blue:#0b4cb3}"
    "*{box-sizing:border-box}"
    "body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;margin:0;"
    "background:var(--paper);color:var(--ink)}"
    ".skip{position:absolute;left:-9999px;top:0;background:#fff;color:#111;padding:10px 14px;z-index:10;font-weight:700}"
    ".skip:focus{left:8px;top:8px}"
    ".hero{background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 55%,#0ea5e9 130%);color:#fff;"
    "padding:44px 24px 36px;box-shadow:0 6px 24px rgba(15,23,42,.45);border-bottom:4px solid var(--accent)}"
    ".hero-inner{max-width:1200px;margin:0 auto}"
    ".eyebrow{display:inline-block;background:var(--accent);color:#111;font-weight:800;font-size:12px;"
    "letter-spacing:.14em;text-transform:uppercase;border-radius:6px;padding:4px 10px;"
    "box-shadow:0 2px 0 rgba(0,0,0,.35)}"
    ".hero h1{font-size:clamp(30px,5vw,52px);margin:12px 0 8px;letter-spacing:-.02em;"
    "text-shadow:0 3px 0 rgba(0,0,0,.35)}"
    ".hero p.lede{font-size:17px;color:#dbeafe;max-width:760px}"
    ".stats{display:flex;gap:12px;flex-wrap:wrap;margin-top:18px}"
    ".stat{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.35);border-radius:12px;"
    "padding:10px 16px;min-width:130px;box-shadow:inset 0 1px 0 rgba(255,255,255,.25),0 4px 10px rgba(0,0,0,.3);"
    "backdrop-filter:blur(2px)}"
    ".stat strong{display:block;font-size:26px}"
    ".stat span{font-size:12px;color:#dbeafe}"
    "main{padding:24px 16px;display:grid;gap:18px;max-width:1200px;margin:0 auto;"
    "grid-template-columns:repeat(auto-fill,minmax(360px,1fr))}"
    ".card{background:var(--card);border-radius:16px;padding:18px;border:1px solid var(--line);"
    "border-top:6px solid var(--blue);"
    "box-shadow:0 1px 2px rgba(15,23,42,.12),0 8px 24px rgba(15,23,42,.14);"
    "transition:transform .15s ease,box-shadow .15s ease}"
    ".card:hover{transform:translateY(-4px);"
    "box-shadow:0 2px 4px rgba(15,23,42,.12),0 16px 36px rgba(15,23,42,.22)}"
    ".card h2{font-size:19px;margin:0 0 2px}"
    ".card h2 small{color:var(--muted);font-weight:600}"
    ".card p{font-size:14px;line-height:1.55;color:#1f2937}"
    ".b{display:inline-block;color:#fff;font-weight:700;font-size:11px;border-radius:999px;"
    "padding:3px 10px;margin:2px;box-shadow:inset 0 1px 0 rgba(255,255,255,.3),0 2px 4px rgba(0,0,0,.25)}"
    ".b-complete{background:var(--green)}.b-not_found{background:var(--gray)}"
    ".b-source_error,.b-blocked{background:var(--amber)}.b-failed{background:var(--red)}"
    "table{width:100%;font-size:12px;border-collapse:collapse;margin-top:8px}"
    "td,th{border-top:1px solid var(--line);padding:5px;text-align:left;vertical-align:top}"
    "th{background:#f1f5f9}"
    "a{color:var(--blue);text-decoration:underline}"
    "a:focus-visible{outline:3px solid var(--blue);outline-offset:2px}"
    "footer{background:#0f172a;color:#e2e8f0;padding:28px 24px;margin-top:8px;border-top:4px solid var(--accent)}"
    "footer .foot-inner{max-width:1200px;margin:0 auto}"
    "footer a{color:#fcd34d}"
    "footer nav ul{list-style:none;padding:0;display:flex;gap:10px;flex-wrap:wrap}"
    "footer nav a{display:inline-block;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.3);"
    "border-radius:999px;padding:6px 14px;font-weight:700;text-decoration:none;"
    "box-shadow:0 2px 0 rgba(0,0,0,.4)}"
    "footer nav a:hover{background:rgba(255,255,255,.22)}"
    "@media(max-width:600px){main{grid-template-columns:1fr}.hero{padding:32px 16px 28px}}"
)

STATE_CLASS = {
    "complete": "b-complete", "available": "b-complete",
    "not_found": "b-not_found", "not_available": "b-not_found",
    "not_applicable": "b-not_found", "ambiguous": "b-not_found",
    "source_error": "b-source_error", "blocked": "b-blocked",
    "blocked_policy": "b-blocked", "blocked_robots": "b-blocked",
    "failed": "b-failed", "submission_error": "b-failed",
}


def _safe_href(raw: object) -> tuple[str, bool]:
    url = str(raw or "")
    try:
        scheme = urllib.parse.urlparse(url).scheme.lower()
    except ValueError:
        return "", False
    if scheme in {"http", "https"}:
        return url, True
    return "", False


def card(env: dict, index: int) -> str:
    prof = env.get("profile", {}) if isinstance(env.get("profile"), dict) else {}
    org = html.escape(str(env.get("organisation_number", "?")))
    name = html.escape(str(prof.get("name") or "Unknown"))
    synth = prof.get("synthesis") if isinstance(prof.get("synthesis"), dict) else {}
    summary = html.escape(str(synth.get("summary") or "No synthesis."))
    mods = env.get("modules") if isinstance(env.get("modules"), dict) else {}
    badges = " ".join(
        _badge(str(m), v.get("state", "?") if isinstance(v, dict) else "?")
        for m, v in mods.items()
    )
    ev_rows = ""
    evidence = prof.get("evidence") if isinstance(prof.get("evidence"), dict) else {}
    for mod, rec in evidence.items():
        if not isinstance(rec, dict):
            continue
        raw_url = str(rec.get("source_url") or "")
        href, ok = _safe_href(raw_url)
        url_esc = html.escape(raw_url, quote=True)
        if ok:
            link = f"<a href='{html.escape(href, quote=True)}' rel='noopener noreferrer nofollow'>{url_esc[:70]}</a>"
        else:
            link = url_esc[:70]
        st = html.escape(str(rec.get("status") or ""))
        rt = html.escape(str(rec.get("retrieved_at") or ""))
        ev_rows += f"<tr><td>{html.escape(str(mod))}</td><td>{st}</td><td>{link}</td><td>{rt}</td></tr>"
    caption = f"Evidence for {name}, organisation {org}"
    ver = prof.get("verification") if isinstance(prof.get("verification"), dict) else {}
    conf = html.escape(str(ver.get("confidence", "?")))
    conf_badge = f"<span class='b b-complete'>confidence {conf}</span>" if ver else ""
    rep = prof.get("report_path") if isinstance(prof.get("report_path"), str) else ""
    rep_link = ""
    if rep and ".." not in rep and not rep.startswith(("/", "http:", "https:")):
        rep_link = f"<p><a href='{html.escape(rep, quote=True)}'>Full report (Markdown)</a></p>"
    return (
        f"<article class='card' aria-labelledby='c{index}'>"
        f"<h2 id='c{index}'>{name} <small>{org}</small></h2><div>{badges}{conf_badge}</div><p>{summary}</p>"
        f"{rep_link}"
        f"<table><caption class='skip'>{html.escape(caption)}</caption>"
        f"<tr><th scope='col'>Module</th><th scope='col'>State</th>"
        f"<th scope='col'>Source</th><th scope='col'>Retrieved</th></tr>{ev_rows}</table></article>"
    )


def _badge(module: str, state: str) -> str:
    cls = STATE_CLASS.get(str(state), "b-not_found")
    return f"<span class='b {cls}'>{html.escape(str(module))} · {html.escape(str(state))}</span>"


def _hero_stats(envs: list[dict]) -> str:
    total = len(envs)
    fin = sum(1 for e in envs if _ev_state(e, "financials") == "available")
    web = sum(1 for e in envs if _ev_state(e, "website") == "available")
    roles = sum(1 for e in envs if _ev_state(e, "roles") == "available")
    def _pct(n: int) -> str:
        return f"{round(100 * n / total)}%" if total else "—"
    return (
        f"<div class='stats' role='list'>"
        f"<div class='stat' role='listitem'><strong>{total}</strong><span>verified envelopes</span></div>"
        f"<div class='stat' role='listitem'><strong>{_pct(fin)}</strong><span>with filed accounts</span></div>"
        f"<div class='stat' role='listitem'><strong>{_pct(roles)}</strong><span>with role records</span></div>"
        f"<div class='stat' role='listitem'><strong>{_pct(web)}</strong><span>with live websites</span></div>"
        f"</div>"
    )


def _ev_state(env: dict, module: str) -> str:
    prof = env.get("profile", {})
    if not isinstance(prof, dict):
        return "?"
    rec = (prof.get("evidence") or {}).get(module, {})
    return str(rec.get("status") or "?") if isinstance(rec, dict) else "?"


FOOTER = """<footer><div class='foot-inner'><h2>Business details &amp; policies</h2>
<p><strong>Signalpost</strong> — verifiable Norwegian company intelligence. Operator: competition entrant
(contact: <a href="mailto:{mail}">{mail}</a>). Company facts come from Norway's public registers
under NLOD 2.0 — every claim carries its source link and retrieval date. No accounts, no tracking, no sales.</p>
<nav aria-label="Legal"><ul>
<li><a href="console.html">Console</a></li>
<li><a href="privacy.html">Privacy Policy</a></li>
<li><a href="terms.html">Terms &amp; Conditions</a></li>
<li><a href="cookies.html">Cookie Policy</a></li>
<li><a href="refunds.html">Refund Policy</a></li>
</ul></nav>
<p><strong>Cookies:</strong> this gallery sets none and runs no analytics — no consent banner required. See Cookie Policy.</p>
<p><strong>Accessibility:</strong> hit a barrier? Email <a href="mailto:{mail}">{mail}</a> and we will fix it.</p>
</div></footer>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelopes", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    envs = [json.loads(line) for line in Path(args.envelopes).read_text(encoding="utf-8").splitlines() if line.strip()]
    body = "\n".join(card(e, i) for i, e in enumerate(envs[:500]))
    stats = _hero_stats(envs)
    footer = FOOTER.format(mail=html.escape(CONTACT_EMAIL))
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='description' content='Verifiable Norwegian company profiles: filed accounts, leadership, workplaces — every fact linked to its source with retrieval dates.'>
<meta http-equiv='Content-Security-Policy' content="default-src 'none'; style-src 'unsafe-inline'; img-src https: data:; connect-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'">
<title>Signalpost — verified Norwegian company intelligence</title>
<style>{CSS}</style>
</head><body><a class='skip' href='#main'>Skip to company profiles</a>
<header class='hero'><div class='hero-inner'>
<span class='eyebrow'>Brreg-verified · NLOD open data</span>
<h1>Signalpost company intelligence</h1>
<p class='lede'>Real registry facts — filed accounts, leadership, workplaces — checked against
the exact company and pinned to source links with retrieval dates. Missing data is labelled, never zeroed.</p>
{stats}</div></header>
<main id='main'>{body}</main>{footer}</body></html>"""
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote gallery with {len(envs)} cards to {out}")


if __name__ == "__main__":
    main()
