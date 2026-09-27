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
    "body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;background:#f6f7f9;color:#111}"
    "header{padding:16px 20px;background:#111;color:#fff}"
    "header a{color:#fff}"
    ".skip{position:absolute;left:-9999px;top:0;background:#fff;color:#111;padding:8px 12px;z-index:10}"
    ".skip:focus{left:8px;top:8px}"
    "main{padding:16px;display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(340px,1fr))}"
    ".card{background:#fff;border-radius:12px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.08)}"
    ".b{display:inline-block;background:#e6e6fa;color:#111;font-size:11px;border-radius:8px;padding:2px 8px;margin:2px}"
    "table{width:100%;font-size:12px;border-collapse:collapse}"
    "td,th{border-top:1px solid #ddd;padding:4px;text-align:left}"
    "th{background:#f0f0f5}"
    "small{color:#595959}"
    "a{color:#0b4cb3;text-decoration:underline}"
    "a:focus-visible{outline:3px solid #0b4cb3;outline-offset:2px}"
    "footer{padding:20px;background:#fff;border-top:1px solid #ddd;font-size:13px;color:#333}"
    "footer nav ul{list-style:none;padding:0;display:flex;gap:12px;flex-wrap:wrap}"
    "@media(max-width:600px){main{grid-template-columns:1fr}}"
)


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
        f"<span class='b'>{html.escape(str(m))}:{html.escape(str(v.get('state', '?') if isinstance(v, dict) else '?'))}</span>"
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
    return (
        f"<article class='card' aria-labelledby='c{index}'>"
        f"<h2 id='c{index}'>{name} <small>{org}</small></h2><div>{badges}</div><p>{summary}</p>"
        f"<table><caption class='skip'>{html.escape(caption)}</caption>"
        f"<tr><th scope='col'>module</th><th scope='col'>state</th>"
        f"<th scope='col'>source</th><th scope='col'>retrieved</th></tr>{ev_rows}</table></article>"
    )


FOOTER = """<footer><h2>Business details &amp; policies</h2>
<p><strong>Signalpost</strong> — company-research gallery. Operator: competition entrant
(contact: <a href="mailto:{mail}">{mail}</a>). Data: Norwegian public registers
under NLOD 2.0 (see Privacy). No online sales, no accounts, no tracking.</p>
<nav aria-label="Legal"><ul>
<li><a href="privacy.html">Privacy Policy</a></li>
<li><a href="terms.html">Terms &amp; Conditions</a></li>
<li><a href="cookies.html">Cookie Policy</a></li>
<li><a href="refunds.html">Refund Policy</a></li>
</ul></nav>
<p><strong>Cookies:</strong> this gallery sets no cookies and runs no analytics.
No consent banner is required. See Cookie Policy.</p>
<p><strong>Accessibility:</strong> questions or barriers? Email <a href="mailto:{mail}">{mail}</a>.</p>
</footer>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--envelopes", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    envs = [json.loads(line) for line in Path(args.envelopes).read_text(encoding="utf-8").splitlines() if line.strip()]
    body = "\n".join(card(e, i) for i, e in enumerate(envs[:500]))
    footer = FOOTER.format(mail=html.escape(CONTACT_EMAIL))
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<meta name='description' content='Verifiable Norwegian company profiles with source links and retrieval dates.'>
<meta http-equiv='Content-Security-Policy' content="default-src 'none'; style-src 'unsafe-inline'; img-src https: data:; connect-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'">
<title>Signalpost gallery &mdash; {len(envs)} companies</title>
<style>{CSS}</style>
</head><body><a class='skip' href='#main'>Skip to company profiles</a>
<header><h1>Signalpost &mdash; verifiable company gallery</h1>
<p>{len(envs)} envelopes &middot; every claim links source + retrieval time &middot; mobile + desktop</p></header>
<main id='main'>{body}</main>{footer}</body></html>"""
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote gallery with {len(envs)} cards to {out}")


if __name__ == "__main__":
    main()
