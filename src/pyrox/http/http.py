"""
HTTP wrappers.
"""

import requests

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "keep-alive",
}


def get(url: str, headers: dict[str, str] = _DEFAULT_HEADERS) -> requests.Response:
    """Get the URL."""
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res
