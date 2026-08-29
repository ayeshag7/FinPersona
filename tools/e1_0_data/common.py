"""Shared helpers for the E1.0 data panel download (v2.1 plan, Section 5.2).

Every fetch goes through `get()` so that one place owns the User-Agent, the
per-host rate limit and the attempt log.  Nothing here cleans or fills data:
files are written as served (or as parsed, byte-for-byte in value terms).

No credentials, no API keys, no account sign-ups are used anywhere.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[2]
DATASETS = REPO / "datasets"
MANIFESTS = DATASETS / "_manifests"

# Declared, non-anonymous, non-personal UA. SEC's fair-access policy asks for a
# declared UA; we identify the project and its purpose without sending anyone's
# personal e-mail address to a third party (see E1_0_DATA_REPORT.md, open Q3).
UA = "FinPersona-Bench academic research (non-commercial; env v2.1 data panel)"

# Per-host minimum seconds between requests. SEC's published ceiling is 10 req/s;
# we stay an order of magnitude under it. Yahoo is unpublished -> be gentle.
RATE = {
    "data.sec.gov": 0.35,
    "www.sec.gov": 0.35,
    "en.wikipedia.org": 0.5,
    "raw.githubusercontent.com": 0.2,
    "api.github.com": 0.5,
    "_default": 0.5,
}

_last: dict[str, float] = {}
ATTEMPTS: list[dict] = []


def _throttle(host: str) -> None:
    gap = RATE.get(host, RATE["_default"])
    prev = _last.get(host)
    if prev is not None:
        wait = gap - (time.time() - prev)
        if wait > 0:
            time.sleep(wait)
    _last[host] = time.time()


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_attempt(need: str, source: str, url: str, outcome: str, detail: str = "") -> None:
    """Record every attempt, successful or not (plan rule: report failures as failures)."""
    ATTEMPTS.append(
        {"utc": now(), "need": need, "source": source, "url": url,
         "outcome": outcome, "detail": detail[:500]}
    )
    print(f"[{outcome:7s}] {need:>3s} {source:<28s} {detail[:110]}", flush=True)


def get(url: str, *, need: str = "?", source: str = "?", tries: int = 4,
        timeout: int = 60, params: dict | None = None,
        session: requests.Session | None = None, log: bool = True):
    """GET with UA, per-host throttle and backoff. Returns Response or None."""
    from urllib.parse import urlparse

    host = urlparse(url).netloc
    sess = session or requests
    last_err = ""
    for k in range(tries):
        _throttle(host)
        try:
            r = sess.get(url, headers={"User-Agent": UA}, timeout=timeout, params=params)
            if r.status_code == 200:
                if log:
                    log_attempt(need, source, r.url, "OK", f"{len(r.content):,} bytes")
                return r
            # 403/429 from SEC = rate threshold; back off hard and retry.
            last_err = f"HTTP {r.status_code}"
            if r.status_code in (403, 429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(5 * (k + 1) ** 2)
                continue
            break
        except Exception as e:  # network/TLS/timeout
            last_err = f"{type(e).__name__}: {e}"
            if k < tries - 1:
                time.sleep(3 * (k + 1))
                continue
    if log:
        log_attempt(need, source, url, "FAIL", last_err)
    return None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_bytes(content: bytes, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"file": str(path.relative_to(REPO)), "bytes": len(content), "sha256": sha256(path)}


def write_attempts(name: str) -> None:
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    p = MANIFESTS / f"attempts_{name}.json"
    prev = json.loads(p.read_text()) if p.exists() else []
    p.write_text(json.dumps(prev + ATTEMPTS, indent=1))
    print(f"-> {p.relative_to(REPO)} ({len(prev) + len(ATTEMPTS)} attempts)")
