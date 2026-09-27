#!/usr/bin/env python3
"""Static desktop/mobile gallery from terminal envelopes (8 UX points).

Clean minimal theme: single column, generous whitespace, one accent color,
evidence tucked into native <details> (no JS). All dynamic strings are
html-escaped; links rendered only for http(s) URLs; script-blocking CSP meta.
Accessibility: skip link, landmarks, visible focus, table scope + caption,
AA-contrast palette, fully keyboard-operable.
"""
from __future__ import annotations

import argparse
import html
import json
import urllib.parse
from pathlib import Path

CONTACT_EMAIL = "aryan0411singh@gmail.com"

CSS = (
    "body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;"
    "background:#fafafa;color:#1a1a1a;line-height:1.6}"
    ".skip{position:absolute;left:-9999px;top:0;background:#1a1a1a;color:#fff;padding:10px 14px;z-index:10}"
    ".skip:focus{left:8px;top:8px}"
    "header.site{max-width:860px;margin:0 auto;padding:48px 20px 8px}"
    "header.site h1{font-size:clamp(26px,4vw,36px);margin:0;letter-spacing:-.02em}"
    "header.site p{color:#555;max-width:640px}"
    ".meta{max-width:860px;margin:0 auto;padding:0 20px 24px;color:#555;font-size:14px}"
    "main{max-width:860px;margin:0 auto;padding:0 20px 40px;display:block}"
    ".card{background:#fff;border:1px solid #e3e3e3;border-radius:10px;padding:20px 22px;margin:0 0 16px}"
    ".card h2{font-size:19px;margin:0}"
    ".card .org{color:#666;font-size:13px;margin:2px 0 10px}"
    ".card p.summary{margin:10px 0}"
    ".facts{color:#555;font-size:13px;margin:0 0 6px}"
    ".dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:baseline}"
    ".ok{background:#1a7f37}.warn{background:#9a6700}.bad{background:#b42318}.mute{background:#666}"
    "details{border-top:1px solid #eee;margin-top:12px;padding-top:8px}"
    "summary{cursor:pointer;color:#1a56db;font-weight:600;font-size:14px}"
    "summary:focus-visible{outline:3px solid #1a56db;outline-offset:2px}"
    "table{width:100%;font-size:13px;border-collapse:collapse;margin-top:8px}"
    ".tbl{overflow-x:auto;margin:8px -4px 0;padding:0 4px}"
    ".tbl table{min-width:560px}"
    "td,th{border-top:1px solid #eee;padding:6px 4px;text-align:left;vertical-align:top}"
    "th{color:#555;font-weight:600}"
    "a{color:#1a56db}"
    "a:focus-visible{outline:3px solid #1a56db;outline-offset:2px}"
    "footer.site{border-top:1px solid #e3e3e3;background:#fff}"
    "footer.site .foot-inner{max-width:860px;margin:0 auto;padding:28px 20px;font-size:14px;color:#333}"
    "footer.site nav ul{list-style:none;padding:0;display:flex;gap:16px;flex-wrap:wrap}"
    "@media(max-width:600px){header.site{padding:32px 16px 4px}main{padding:0 12px 32px}.card{padding:16px}}"
)

DOT = {"pass": "ok", "available": "ok", "complete": "ok",
       "warn": "warn", "not_found": "mute", "not_available": "mute", "not_applicable": "mute",
       "ambiguous": "warn", "source_error": "warn", "blocked": "warn",
       "fail": "bad", "failed": "bad"}


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
    ver = prof.get("verification") if isinstance(prof.get("verification"), dict) else {}
    conf = html.escape(str(ver.get("confidence", "?")))
    rep = prof.get("report_path") if isinstance(prof.get("report_path"), str) else ""
    rep_link = ""
    if rep and ".." not in rep and not rep.startswith(("/", "http:", "https:")):
        rep_link = f" · <a href='{html.escape(rep, quote=True)}'>Full report</a>"
    evidence = prof.get("evidence") if isinstance(prof.get("evidence"), dict) else {}
    rows = ""
    for mod, rec in evidence.items():
        if not isinstance(rec, dict):
            continue
        st = str(rec.get("status") or "?")
        dot = DOT.get(st, "mute")
        raw_url = str(rec.get("source_url") or "")
        href, ok = _safe_href(raw_url)
        url_esc = html.escape(raw_url, quote=True)
        link = (f"<a href='{html.escape(href, quote=True)}' rel='noopener noreferrer nofollow'>{url_esc[:72]}</a>"
                if ok else url_esc[:72])
        rt = html.escape(str(rec.get("retrieved_at") or "—"))
        rows += (f"<tr><td><span class='dot {dot}' aria-hidden='true'></span>{html.escape(str(mod))}</td>"
                 f"<td>{html.escape(st)}</td><td>{link}</td><td>{rt}</td></tr>")
    caption = f"Evidence for {name}, organisation {org}"
    return (
        f"<article class='card' aria-labelledby='c{index}'>"
        f"<h2 id='c{index}'>{name}</h2>"
        f"<div class='org'>Org {org} · Confidence {conf}{rep_link}</div>"
        f"<p class='summary'>{summary}</p>"
        f"<details><summary>Evidence and sources</summary>"
        f"<div class='tbl'><table><caption class='skip'>{html.escape(caption)}</caption>"
        f"<tr><th scope='col'>Module</th><th scope='col'>State</th>"
        f"<th scope='col'>Source</th><th scope='col'>Retrieved</th></tr>{rows}</table></div></details></article>"
    )


FOOTER = """<footer class='site'><div class='foot-inner'>
<h2>Signalpost</h2>
<p>Verifiable Norwegian company facts from public registers (NLOD 2.0). Every claim links its source.
Contact: <a href="mailto:{mail}">{mail}</a>. No accounts, no tracking, no sales.</p>
<nav aria-label="Legal"><ul>
<li><a href="index.html">Home</a></li>
<li><a href="app/">Product demo</a></li>
<li><a href="console.html">Console</a></li>
<li><a href="privacy.html">Privacy</a></li>
<li><a href="terms.html">Terms</a></li>
<li><a href="cookies.html">Cookies</a></li>
<li><a href="refunds.html">Refunds</a></li>
</ul></nav>
<p>This gallery sets no cookies and runs no analytics. Questions on access? Email <a href="mailto:{mail}">{mail}</a>.</p>
</div></footer>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelopes", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    envs = [json.loads(line) for line in Path(args.envelopes).read_text(encoding="utf-8").splitlines() if line.strip()]
    total = len(envs)
    fin = sum(1 for e in envs if _ev_state(e, "financials") == "available")
    body = "\n".join(card(e, i) for i, e in enumerate(envs[:500]))
    footer = FOOTER.format(mail=html.escape(CONTACT_EMAIL))
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='description' content='Verifiable Norwegian company profiles: filed accounts, leadership, workplaces — every fact linked to its source with retrieval dates.'>
<meta http-equiv='Content-Security-Policy' content="default-src 'none'; style-src 'unsafe-inline'; img-src https: data:; connect-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'">
<title>Signalpost — verified Norwegian company intelligence</title>
<style>{CSS}</style>
</head><body><a class='skip' href='#main'>Skip to company profiles</a>
<header class='site'><h1>Signalpost</h1>
<p>Verified Norwegian company intelligence. Registry facts with source links and retrieval dates —
missing data is labelled, never zeroed.</p></header>
<div class='meta'>{total} companies · {fin} with filed accounts · data: Brreg NLOD open registers</div>
<main id='main'>{body}</main>{footer}</body></html>"""
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote gallery with {len(envs)} cards to {out}")


def _ev_state(env: dict, module: str) -> str:
    prof = env.get("profile", {})
    if not isinstance(prof, dict):
        return "?"
    rec = (prof.get("evidence") or {}).get(module, {})
    return str(rec.get("status") or "?") if isinstance(rec, dict) else "?"


if __name__ == "__main__":
    main()
