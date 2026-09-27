# SECURITY.md — Signalpost agent

Threat model: untrusted company websites + untrusted registry-linked URLs, run on
Builderr's evaluator (8 vCPU/16 GB) with outbound budget. No secrets, no LLM, $0 cost.

## Guarantees

- **No secrets in repo or runs.** Production path (`scripts/run_agent.py` →
  `run_competition_batch.py` → `build_gallery.py`) uses only keyless open data
  (Brreg NLOD 2.0). `BRAVE_SEARCH_API_KEY` and similar env reads exist solely in
  opt-in experiment scripts that the evaluator never invokes.
- **SSRF-guarded fetching** (`src/norway_company_agent/website.py`):
  `assert_public_url` allows only http/https, rejects credentials
  (`user:pass@`), localhost/`.local`, and non-global IPs (DNS-resolved,
  checked on initial URL and every redirect via `SafeRedirectHandler`).
  Byte caps (2 MB homepage / 1 MB secondary), HTML content-type check,
  registered-domain pinning for secondary pages, robots.txt respected,
  15 s timeout.
- **Allowlisted JSON API** (`src/norway_company_agent/http.py`): `fetch_json`
  refuses any host outside `https://data.brreg.no/` and
  `https://data.ppe.brreg.no/`. Org numbers are digits-validated (9 chars,
  deduped) before URL construction from hardcoded templates. 5 attempts with
  backoff for preview-API 503/500; 404/410 return honest `not_found`, never zero.
- **No command injection** (`scripts/run_agent.py`): fixed script paths under
  `ROOT`, `subprocess.run` list-form (no shell), `workers` clamped 1–32,
  `expected-count` 1–100000, `run-id` allowlisted to `[A-Za-z0-9-_.]` ≤64 chars,
  gallery return code checked, profile count re-validated before layer 2.
- **No XSS** (`scripts/build_gallery.py`): every dynamic string `html.escape`d;
  links rendered only for http(s) schemes with `rel="noopener noreferrer nofollow"`;
  page ships `<meta CSP default-src 'none'; script-src 'none'>` — zero scripts.
- **Privacy**: open Enhetsregisteret/Regnskapsregisteret only. Never calls
  `autorisert-api` (no fødselsnummer). Role names are public registry data.
- **Supply chain**: `requirements.txt` fully pinned (`==`); `uv.lock` frozen.
  No install hooks; evaluator installs with `pip install -r requirements.txt`.
- **Secrets scan**: `git grep` for private-key / `ghp_` / high-entropy key
  patterns returns nothing (verified 2026-09-27). Report suspected issues to
  the repo owner; do not open a public issue with exploit details.

## Non-goals / known limits

- DNS TOCTOU between `assert_public_url` resolution and socket connect
  (standard urllib limitation; mitigated by redirect re-checks + short timeouts).
- `tldextract` may fetch the public-suffix list on first run (cached after).
- Experiment connectors (`run_brave_*`, `run_youtube_*`, `run_linkedin_*`,
  Google-News-RSS) are discovery-only, quarantined, and excluded from scoring
  evidence; they require separate rights review before any production use.
