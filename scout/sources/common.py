"""Helpers every reader uses: build a job, read dates in any format."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def job(id, title, url, location="", posted_at=None, description="", **extra):
    """One job, always with the same keys. `extra` = data a detail() call needs later."""
    return {"id": id, "title": " ".join((title or "").split()), "url": url or "",
            "location": " ".join((location or "").split()), "posted_at": posted_at,
            "description": description or "", **({"_extra": extra} if extra else {})}


def iso(value):
    """Any date (ISO text, RFC 822 text, unix seconds or milliseconds) -> '2026-10-13T09:00:00Z'.
    Unknown or unreadable -> None (the job then counts as "date unknown")."""
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            seconds = float(value)
            if seconds > 1e11:  # milliseconds
                seconds /= 1000
            moment = datetime.fromtimestamp(seconds, timezone.utc)
        else:
            text = str(value).strip()
            try:
                moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                try:
                    moment = parsedate_to_datetime(text)  # "Mon, 06 Oct 2026 10:00:00 +0200"
                except (TypeError, ValueError):
                    moment = None
                    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%b %d, %Y", "%d %b %Y"):
                        try:
                            moment = datetime.strptime(text, fmt)
                            break
                        except ValueError:
                            pass
                    if moment is None:
                        return None
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, OverflowError, OSError):
        return None


def join(*parts, sep=", "):
    """Join the non-empty parts, without repeating one."""
    seen = []
    for part in parts:
        part = (part or "").strip() if isinstance(part, str) else ""
        if part and part not in seen:
            seen.append(part)
    return sep.join(seen)
