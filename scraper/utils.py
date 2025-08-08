import time
import re
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def create_session(timeout_seconds: int = 20, total_retries: int = 5, backoff_factor: float = 0.5) -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.request_timeout = timeout_seconds  # type: ignore[attr-defined]
    return session


def fetch_html(session: requests.Session, url: str, headers: Optional[Dict[str, str]] = None) -> str:
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    response = session.get(url, headers=merged_headers, timeout=getattr(session, "request_timeout", 20))
    response.raise_for_status()
    return response.text


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def rate_limit_sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)