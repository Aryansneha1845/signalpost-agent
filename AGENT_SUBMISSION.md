# Signalpost agent — submission-ready

Baseline: Builderr starter + hiring/synthesis/gallery layers, regnskap throttle+retry, Windows-safe.

## One command (evaluator pastes)

```bash
pip install -r requirements.txt
curl -L 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/csv' -o brreg-enheter.csv.gz
python scripts/run_agent.py --input <BATCH.jsonl> --bulk brreg-enheter.csv.gz --out out --run-id official --expected-count 1000 --workers 8 --request-budget-per-company 2
```

- Input: JSON/JSONL/TXT of 9-digit orgnrs (same batch Builderr supplies, any size).
- Output: `out/envelopes.jsonl` (1 terminal envelope/input), `out/profiles.jsonl`, `out/run-report.json`, `out/gallery.html`.
- Validation: exact count, unique orgnrs, terminal states, zero silent drops. Missing → `not_available/blocked/ambiguous/failed`, never 0.
- Proven: `smoke-test/smoke100-out/` — 100/100 envelopes in 4m37s, 536 req, p50 716ms/p95 847ms, validation passed.

## Models / APIs / licences / cost

- Models: none ($0, template synthesis only, no LLM).
- APIs (all permitted, declared): Brønnøysund Enhetsregisteret bulk+live (NLOD 2.0), Regnskapsregisteret (preview), official roles/subunits/group, registry-listed company website (robots-checked, SSRF-guarded) + derived hiring/synthesis (zero extra req).
- No LinkedIn/Meta/Glassdoor/Indeed/Google scraping. Search/Google-News-RSS scripts in repo are discovery experiments only, not evidence.
- Expected cost: **$0 per 100-company run** (and per 1000-company official run). Requests: ~5.4/company measured (536/100); website secondary capped at 4, regnskap throttled 2.1s + 5-attempt backoff.
- Source rights: NLOD 2.0 for Brreg; company pages only with robots+terms respected; every claim has source_url, retrieved_at, content_sha256, reporting period where relevant; refresh idempotent via `scripts/run_refresh_replay.py`.

## Refresh

```bash
python scripts/run_refresh_replay.py --manifest tests/fixtures/refresh-snapshots.json --output out/refresh-demo.json
```

Expect precision 1.0, recall 1.0, evidence_complete true, idempotent true.
