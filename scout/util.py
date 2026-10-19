"""Small helpers shared by the whole app: web requests and word matching."""

import re
import time

import requests

TIMEOUT = 60  # seconds per request
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
HEADERS = {"User-Agent": BROWSER_UA, "Accept-Language": "en-GB,en;q=0.9"}


def get(url, **kwargs):
    """GET a URL and fail loudly on HTTP errors (the caller reports the company as failed)."""
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    return _send(requests.get, url, headers=headers, timeout=TIMEOUT, **kwargs)


def get_json(url, **kwargs):
    return get(url, **kwargs).json()


def post_json(url, body, **kwargs):
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    return _send(requests.post, url, json=body, headers=headers, timeout=TIMEOUT, **kwargs).json()


def _send(method, url, **kwargs):
    """Send the request; when the site says "too many requests" (429), wait and try again."""
    for attempt in range(4):
        response = method(url, **kwargs)
        if response.status_code != 429 or attempt == 3:
            break
        wait = response.headers.get("Retry-After", "")
        time.sleep(min(int(wait), 60) if wait.isdigit() else 10 * (attempt + 1))
    response.raise_for_status()
    return response


def html_to_text(html):
    """Very small HTML -> text: drop tags, keep line breaks between blocks."""
    if not html:
        return ""
    import html as htmllib
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", html)
    text = htmllib.unescape(re.sub(r"(?s)<[^>]+>", " ", html))
    lines = [re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def term_pattern(terms):
    """One regex that finds any of the terms as whole words, case-insensitive.
    "tam" must not match "team"; "u.s" matches "U.S."."""
    terms = [t.strip().lower() for t in terms if t and t.strip()]
    if not terms:
        return None
    parts = sorted((re.escape(t) for t in terms), key=len, reverse=True)
    return re.compile(r"(?<![\w])(?:" + "|".join(parts) + r")(?![\w])", re.IGNORECASE)


def find_term(pattern, text):
    """The first term the pattern finds in text, or None."""
    if pattern is None or not text:
        return None
    match = pattern.search(text)
    return match.group(0) if match else None


def split_list(value):
    """'a, b,c' -> ['a', 'b', 'c']"""
    return [part.strip() for part in (value or "").split(",") if part.strip()]
