"""Hiring-signal extractor over already-fetched website snapshots.

Zero extra outbound requests: reads pages captured by website.fetch_website.
Only publishes when the website identity gate is exact (publishable=True).
Otherwise returns quarantined / not_available states — never guesses.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlparse

from .evidence import evidence

JOB_PATH = re.compile(
    r"/(?:career|careers|karriere|job|jobs|stilling|stillinger|ledige?-?stillinger|vacancy|vacancies)(?:/|$|-)",
    re.I,
)
JOB_TEXT_HINTS = (
    "ledig stilling", "ledige stillinger", "we are hiring", "we're hiring",
    "join our team", "bli med", "søk jobb", "apply now",
)


def _is_job_url(url: str) -> bool:
    try:
        return bool(JOB_PATH.search(urlparse(url).path))
    except Exception:
        return False


def extract_jobs(profile: dict[str, Any]) -> dict[str, Any]:
    website = (profile.get("evidence") or {}).get("website") or {}
    value = website.get("value") or {}
    identity = value.get("identity_assessment") or {}
    org = str(profile.get("organisation_number") or "")
    source_url = value.get("final_url") or website.get("source_url") or ""
    retrieved_at = website.get("retrieved_at")
    digest = value.get("content_sha256") or website.get("content_sha256")

    if website.get("status") != "available" or not identity.get("publishable"):
        return evidence(
            "hiring", "not_available", "company_owned_hiring_signals", source_url or "https://data.brreg.no/enhetsregisteret/api/enheter",
            note="No exact-identity company site; hiring not published to avoid wrong-company claims.",
            retrieved_at=retrieved_at, content_sha256=digest, source_row_key=org,
        )

    pages = value.get("pages") or []
    job_pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in pages:
        url = str(page.get("url") or "")
        if not url or url in seen:
            continue
        title = str(page.get("title") or "")
        excerpt = str(page.get("main_text_excerpt") or "")
        hay = f"{url} {title} {excerpt[:2000]}".casefold()
        if _is_job_url(url) or any(h in hay for h in JOB_TEXT_HINTS):
            seen.add(url)
            job_pages.append({
                "url": url,
                "title": title[:300],
                "content_sha256": page.get("content_sha256"),
            })
        if len(job_pages) >= 10:
            break

    if not job_pages:
        return evidence(
            "hiring", "not_available", "company_owned_hiring_signals", source_url,
            value={"job_pages": [], "hiring_detected": False},
            note="Exact company site checked; no careers/jobs page surfaced in bounded crawl.",
            retrieved_at=retrieved_at, content_sha256=digest, source_row_key=org,
        )

    stable = sorted(p["url"] for p in job_pages)
    content = hashlib.sha256("|".join(stable).encode()).hexdigest()
    return evidence(
        "hiring", "available", "company_owned_hiring_signals", source_url,
        value={
            "hiring_detected": True,
            "job_pages": job_pages,
            "careers_url": job_pages[0]["url"],
        },
        note="Company-owned careers/jobs surface; not an independent job-board claim.",
        retrieved_at=retrieved_at, content_sha256=content, source_row_key=org,
    )
