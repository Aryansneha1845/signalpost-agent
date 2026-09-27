from __future__ import annotations

import json
import hashlib
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class FetchResult:
    url: str
    status: int
    elapsed_ms: int
    bytes_received: int
    body: Any = None
    error: str | None = None
    content_sha256: str | None = None
    retrieved_at: str | None = None
    effective_at: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_json(url: str, *, timeout: float = 20.0, attempts: int = 5) -> FetchResult:
    """Fetch JSON with retries. 5xx (preview Regnskapsregisteret flakiness) gets longer backoff.

    Security: allowlisted to official Brreg hosts only. The organisation number
    is digits-validated upstream and URLs are built from hardcoded templates,
    so an arbitrary-URL fetch can never be smuggled through this path.
    """
    if not url.startswith(("https://data.brreg.no/", "https://data.ppe.brreg.no/")):
        return FetchResult(url, 0, 0, 0, error="blocked_non_allowlisted_host", retrieved_at=_utc_now())
    last_error = "request failed"
    for attempt in range(attempts):
        started = time.monotonic()
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "builderr-signalpost-poc/0.1 (+https://builderr.ai)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
                elapsed = int((time.monotonic() - started) * 1000)
                return FetchResult(url, response.status, elapsed, len(raw), json.loads(raw), content_sha256=hashlib.sha256(raw).hexdigest(), retrieved_at=_utc_now())
        except urllib.error.HTTPError as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            raw = exc.read()
            if exc.code in {404, 410}:
                return FetchResult(url, exc.code, elapsed, len(raw), error=f"HTTP {exc.code}", content_sha256=hashlib.sha256(raw).hexdigest(), retrieved_at=_utc_now())
            last_error = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = type(exc).__name__
        if attempt + 1 < attempts:
            # 0.8s, 1.6s, 3.2s, 6.4s — survives transient 503/500 bursts without hammering preview API
            time.sleep(0.8 * (2**attempt))
    return FetchResult(url, 0, 0, 0, error=last_error, retrieved_at=_utc_now())
