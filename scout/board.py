"""Build the job board page from this scan's matches.

The board is exactly this scan's matches (closed jobs disappear at once); a job
we already knew keeps the date we first found it. Files written to `site/`:
index.html (the page), matches.json (jobs, read by the CV add-on), runs.json
(scan history for the stats bar).
"""

import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

NEW_FOR_HOURS = 48  # a job counts as "New" for this long after we first saw it
KEEP_RUNS = 500     # scans remembered for the stats bar
PAGE_DIR = Path(__file__).resolve().parent.parent / "page"


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def build(site, prefs, matches, run, now=None):
    site = Path(site)
    site.mkdir(parents=True, exist_ok=True)
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Keep the first "found" date of jobs we already knew.
    old = {job["id"]: job for job in read_json(site / "matches.json", [])}
    jobs = []
    for job in matches:
        job = {key: value for key, value in job.items() if not key.startswith("_")}
        job["found_at"] = old[job["id"]]["found_at"] if job["id"] in old else stamp
        # Jobs without a posting date leave the board this many days after we found them.
        if job.get("posted_at") is None and now - parse_time(job["found_at"]) > timedelta(days=prefs.max_age_days):
            continue
        jobs.append(job)

    runs = (read_json(site / "runs.json", []) + [{**run, "time": stamp, "new_matches": sum(
        1 for job in jobs if job["id"] not in old)}])[-KEEP_RUNS:]

    page_jobs = []
    for job in jobs:
        page_job = {key: value for key, value in job.items() if key != "description"}
        page_jobs.append({**page_job, "place": prefs.place_label(job["location"]),
                          "role": prefs.role_type(job["title"]),
                          "fit": prefs.fit_score(job["title"], job["location"])})
    places = [label for label, _, _ in prefs.locations]
    data = {"jobs": page_jobs, "stats": stats(page_jobs, runs, places, now),
            "places": places, "page_title": prefs.page_title,
            "new_for_hours": NEW_FOR_HOURS, "max_age_days": prefs.max_age_days}

    (site / "matches.json").write_text(json.dumps(jobs, indent=1, ensure_ascii=False), encoding="utf-8")
    (site / "runs.json").write_text(json.dumps(runs, indent=1), encoding="utf-8")
    template = (PAGE_DIR / "board.html").read_text(encoding="utf-8")
    # Embedded as JSON; "</" is escaped so job text can never close the <script> tag.
    embedded = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = template.replace("{{CSP}}", security_policy(template)).replace("{{DATA}}", embedded)
    (site / "index.html").write_text(page, encoding="utf-8")
    return jobs


SUPABASE = "pffopwzydbjdblojhcwm.supabase.co"


def security_policy(template):
    """Content-Security-Policy for the page: only the page's own inline script (identified by
    its SHA-256 fingerprint) and the pinned Supabase library may run; the page may only connect
    to itself, Supabase (login, data, live sync) and GitHub (one-time CV move)."""
    script = re.search(r"<script>(.*?)</script>", template, re.S).group(1)
    digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
    return "; ".join([
        "default-src 'none'",
        f"script-src 'sha256-{digest}' https://cdn.jsdelivr.net",
        "style-src 'unsafe-inline'",
        f"connect-src 'self' https://{SUPABASE} wss://{SUPABASE} https://api.github.com",
        "img-src 'self' data:",
        "base-uri 'none'",
        "form-action 'none'",
    ])


def stats(jobs, runs, places, now):
    day_ago = now - timedelta(hours=24)
    recent = [run for run in runs if parse_time(run["time"]) >= day_ago]
    last = runs[-1] if runs else {}
    counts = {place: 0 for place in places + ["Other"]}
    for job in jobs:
        counts[job["place"]] = counts.get(job["place"], 0) + 1
    return {
        "updated": now.isoformat(),
        "last_scan": last.get("time"),
        "last_status": last.get("status"),
        "scans_24h": len(recent),
        "scanned": last.get("scanned"),
        "boards": last.get("boards"),
        "boards_ok": last.get("boards_ok"),
        "new_postings_last": last.get("new_postings"),
        "new_postings_24h": sum(run.get("new_postings", 0) for run in recent),
        "new_matches_24h": sum(1 for job in jobs if parse_time(job["found_at"]) >= day_ago),
        "total": len(jobs),
        "places": counts,
        "core": sum(1 for job in jobs if job["role"] == "core"),
    }
