#!/usr/bin/env python3
"""Generate standalone legal pages: privacy, terms, cookies, refunds.

All pages: no scripts, no cookies, no external assets, same AA-contrast CSS,
keyboard-friendly, linked from gallery footer. Effective date = generation date.
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

CONTACT_EMAIL = "submit@builderr.ai"

CSS = (
    "body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;margin:0;background:#fafafa;color:#1a1a1a;line-height:1.65}"
    ".wrap{max-width:720px;margin:0 auto;padding:0 20px 40px}"
    "header.site{max-width:720px;margin:0 auto;padding:40px 20px 4px}"
    "header.site h1{margin:0;font-size:clamp(24px,4vw,32px);letter-spacing:-.02em}"
    ".sheet{background:#fff;border:1px solid #e3e3e3;border-radius:10px;padding:24px;margin-top:16px}"
    "a{color:#1a56db}a:focus-visible{outline:3px solid #1a56db;outline-offset:2px}"
    "nav ul{list-style:none;padding:0;display:flex;gap:16px;flex-wrap:wrap}"
    ".notice{background:#f4f6f9;border:1px solid #e3e3e3;border-left:4px solid #1a56db;border-radius:6px;padding:12px 14px}"
    "footer{margin-top:32px;border-top:1px solid #e3e3e3;padding-top:16px;font-size:14px;color:#555}"
    ".skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:#1a1a1a;color:#fff;padding:8px}"
)

SHELL = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; script-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title} — Signalpost</title>
<style>{css}</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><h1>{title}</h1><p>Signalpost · verified company intelligence</p></header>
<div class="wrap"><nav aria-label="Legal"><ul>
<li><a href="index.html">Home</a></li><li><a href="gallery.html">Gallery</a></li><li><a href="privacy.html">Privacy</a></li>
<li><a href="terms.html">Terms</a></li><li><a href="cookies.html">Cookies</a></li>
<li><a href="refunds.html">Refunds</a></li></ul></nav>
<main id="main" class="sheet"><p><strong>Effective date:</strong> {day}</p>{body}</main>
<footer><p>Signalpost — contact <a href="mailto:{mail}">{mail}</a>.
No cookies, no analytics, no third-party embeds on these pages.</p></footer></body></html>"""

PRIVACY = """<div class="notice"><strong>Short version:</strong> this gallery shows Norwegian
<strong>public-register facts only</strong> (company identity, filed accounts, roles,
workplaces, company-owned website excerpts) with source links and retrieval dates.
It sets <strong>no cookies</strong>, runs <strong>no analytics</strong>, has
<strong>no accounts, no forms, no comments, no reviews</strong>, and collects nothing
from visitors beyond what your browser unavoidably sends to fetch these static files.</div>
<h2>1. Who we are</h2><p>Signalpost competition entrant (research gallery).
Contact: <a href="mailto:{mail}">{mail}</a>. No registered office is held out on
this page; business details appear in the gallery footer and competition submission.</p>
<h2>2. Data we show (not data we collect from you)</h2><ul>
<li>Legal identity, address, industry, employee count from Brønnøysundregistrene
Enhetsregisteret (licence NLOD 2.0).</li><li>Filed annual-account figures from
Regnskapsregisteret.</li><li>Board/role records and registered subunits (open data).</li>
<li>Company-owned website excerpts only where exact-entity identity is proven;
otherwise quarantined and labelled.</li></ul>
<p>We <strong>minimise</strong>: no national ID numbers (never calls
<code>autorisert-api</code>), no private addresses, no emails, no phone scraping,
no employee lists beyond published board roles, no reviews, no tracking.</p>
<h2>3. Personal data &amp; your rights (India DPDP Act 2023 + Norway GDPR)</h2>
<p>Role-holder <strong>names</strong> shown here are <strong>personal data</strong>
sourced from Norway's official public registers. Legal position we rely on:</p><ul>
<li><strong>Norway/EU (GDPR):</strong> processing of register-published data for a
research gallery is claimed under legitimate interest / public-task transparency
(GDPR Art. 6), strictly limited to what the register publishes. <strong>Risk flagged:</strong>
a supervisory review could disagree — see §7.</li>
<li><strong>India (DPDP Act 2023):</strong> the Act covers digital personal data in
India; data lawfully published in an official public register is outside its core
consent duties, but its <strong>purpose-limitation, accuracy, security, retention
and grievance-redressal</strong> principles are honoured here regardless.</li></ul>
<p><strong>Your rights:</strong> access, correction, erasure, grievance redressal.
Write to <a href="mailto:{mail}">{mail}</a> with the organisation number, your
relationship to the data, and what is wrong. Corrections follow the <strong>source
register</strong> — we fix our copy and point you to Brreg for the authoritative record.
Grievances are acknowledged within 7 days and resolved within 30 days.</p>
<h2>4. Retention &amp; security</h2><p>Snapshots keep source URL, retrieval time,
content hash and reporting period for audit/refresh diffs. No visitor logs are kept
by these static pages. Transport relies on the host's HTTPS. Report vulnerabilities
privately to <a href="mailto:{mail}">{mail}</a> — see SECURITY.md.</p>
<h2>5. Children</h2><p>No child-directed content; no knowing collection from children.</p>
<h2>6. Changes</h2><p>Material changes update the effective date above and the gallery footer.</p>
<h2>7. Risks flagged (no mistakes hidden)</h2><ul>
<li>Register data can lag or err — verify critical facts at <a href="https://www.brreg.no/" rel="noopener noreferrer nofollow">brreg.no</a>.</li>
<li>GDPR/DPDP interpretation for republished register names is <strong>not settled legal
advice</strong>; obtain counsel before commercial launch or large-scale hosting in the EU/India.</li>
<li>Company-website excerpts are company claims, not independent verification.</li></ul>"""

TERMS = """<h2>1. What this is</h2><p>Signalpost is a <strong>research gallery</strong>:
Norwegian company facts with source links, retrieval dates and explicit unknowns.
It is <strong>not</strong> financial, legal or investment advice, and creates
<strong>no</strong> client, advisory or employment relationship.</p>
<h2>2. Acceptable use</h2><ul><li>Verify critical decisions at the cited source
(especially <a href="https://www.brreg.no/" rel="noopener noreferrer nofollow">brreg.no</a>).</li>
<li>Do not scrape these static pages aggressively; respect robots and rate limits.</li>
<li>Do not republish role-holder names for unlawful profiling, spam or harassment.</li></ul>
<h2>3. Intellectual property</h2><p>Gallery code and summaries: competition entrant.
Underlying register data: Brønnøysundregistrene under <strong>NLOD 2.0</strong>
(reuse allowed with attribution — attribution is given per claim).
Company-website excerpts belong to their owners and are shown as evidence spans only.
<strong>Images:</strong> this gallery ships <strong>zero images</strong>, so no
third-party image copyright arises here. Do not upload images without a licence check.</p>
<h2>4. No warranties; liability limited</h2><p>Provided <strong>as is</strong>, without
warranties of completeness, currency or fitness. A small factual mistake lowers accuracy;
a wrong-company match is quarantined rather than published. To the maximum extent
permitted by law, liability for reliance on gallery content is excluded. Nothing here
limits rights you hold under applicable consumer or data-protection law.</p>
<h2>5. Changes &amp; contact</h2><p>Terms may change with the effective date above.
Contact: <a href="mailto:{mail}">{mail}</a>.</p>"""

COOKIES = """<div class="notice"><strong>Finding: no cookie consent banner is required.</strong>
These pages set <strong>zero cookies</strong>, use <strong>zero localStorage /
sessionStorage</strong>, run <strong>zero analytics</strong> and embed
<strong>zero third-party content</strong> (no fonts, videos, maps, pixels or social
widgets). Verified by CSP <code>script-src 'none'</code> and a repo-wide scan.</div>
<h2>1. Strictly-necessary storage</h2><p>None. There is no login, cart, preference or
consent state to store.</p>
<h2>2. Analytics</h2><p>None. No Google Analytics, Meta Pixel, Hotjar, Mixpanel or
equivalents on these pages. If analytics is ever added, this policy will name the
provider, purpose, retention and opt-out, and a prior consent banner will be deployed.</p>
<h2>3. Third-party embeds</h2><p>None. Outbound source links (e.g. brreg.no) open as
normal links with <code>rel="noopener noreferrer nofollow"</code>; they do not load
here and their own cookie policies apply after you leave.</p>
<h2>4. The one exception to know about</h2><p>An <strong>unshipped experiment file</strong>
(<code>scripts/build_prototype.py</code>) uses <code>localStorage</code> for a saved
workspace. It is <strong>not</strong> part of the evaluated gallery, is never generated
into these pages, and must gain its own consent flow before any hosted use.</p>
<h2>5. Product demo (<code>/app</code>)</h2><p>The interactive demo is first-party
JavaScript only: it fetches the bundled <code>companies.json</code> snapshot and keeps
state in memory. It sets <strong>no cookies</strong>, uses <strong>no
localStorage</strong>, and loads <strong>no analytics or third-party assets</strong>.</p>
<h2>6. Managing cookies generally</h2><p>Because nothing is set, there is nothing to
delete here. Browser controls remain available for other sites.</p>"""

REFUNDS = """<div class="notice"><strong>No payments are taken on this site.</strong>
There is nothing to buy, subscribe to or refund. This policy exists so that is explicit.</div>
<h2>1. Scope</h2><p>Signalpost gallery is a free research artefact for a competition.
No checkout, wallet, UPI, card or bank flow exists here.</p>
<h2>2. If that ever changes</h2><p>Any future paid tier will publish prices inclusive
of taxes, billing frequency, cancellation path and a refund window <strong>before</strong>
payment, in compliance with applicable consumer law. Until then, send billing questions to
<a href="mailto:{mail}">{mail}</a>.</p>
<h2>3. Competition prizes</h2><p>Prize disbursement (if any) is governed by the
Builderr challenge terms, not by this page.</p>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Directory for legal pages (sibling of gallery.html)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    day = date.today().isoformat()
    pages = {"privacy.html": ("Privacy Policy", PRIVACY), "terms.html": ("Terms & Conditions", TERMS),
             "cookies.html": ("Cookie Policy", COOKIES), "refunds.html": ("Refund Policy", REFUNDS)}
    for filename, (title, body) in pages.items():
        html_text = SHELL.format(title=title, day=day, css=CSS, mail=CONTACT_EMAIL,
                                 body=body.format(mail=CONTACT_EMAIL))
        (out / filename).write_text(html_text, encoding="utf-8")
        print(f"Wrote {out / filename}")


if __name__ == "__main__":
    main()
