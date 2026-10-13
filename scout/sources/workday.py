"""Workday career sites ({tenant}.wdN.myworkdayjobs.com).

The list only says "2 Locations" and has no description, so each job whose
title matched is opened once more (detail). Workday blocks clients that open
every job, which is why that only happens after the title check.
"""

import re
from datetime import datetime, timedelta, timezone

from .. import util
from .common import job


def read(params, hints):
    host, tenant, site = params["host"], params["tenant"], params["site"]
    limit = int(params.get("max_postings", 3000))
    api = f"https://{host}/wday/cxs/{tenant}/{site}"
    jobs, seen, offset, total = [], set(), 0, 0
    while offset < limit:
        data = util.post_json(f"{api}/jobs",
                              {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""})
        page = [p for p in data.get("jobPostings") or [] if p and p.get("externalPath")]
        total = total or data.get("total", 0)  # some sites only send the total on page 1
        new = [p for p in page if p["externalPath"] not in seen]
        if page and not new:  # the site ignored the offset and sent the same page again
            break
        for p in new:
            seen.add(p["externalPath"])
            # The id keeps tenant/site (not the wdN host): tenants move between servers.
            jobs.append(job(f"workday/{tenant}/{site}/{p['externalPath'].lstrip('/')}", p.get("title"),
                            f"https://{host}/{site}{p['externalPath']}", p.get("locationsText"),
                            _posted(p.get("postedOn")), api=f"{api}{p['externalPath']}"))
        offset += 20
        if len(data.get("jobPostings") or []) < 20 or (total and offset >= total):
            break
    return jobs


def detail(item, params):
    info = util.get_json(item["_extra"]["api"]).get("jobPostingInfo") or {}
    item["description"] = util.html_to_text(info.get("jobDescription"))
    places = [info.get("location") or ""] + list(info.get("additionalLocations") or [])
    item["location"] = "; ".join(p for p in places if p) or item["location"]
    item["url"] = info.get("externalUrl") or item["url"]
    return item


def _posted(text):
    """Workday only says "Posted Today", "Posted 3 Days Ago" or "Posted 30+ Days Ago"."""
    text = (text or "").lower()
    if "today" in text:
        days = 0
    elif "yesterday" in text:
        days = 1
    else:
        found = re.search(r"(\d+)(\+?)\s*days?", text)
        if not found:
            return None
        days = int(found.group(1)) + (1 if found.group(2) else 0)
    moment = datetime.now(timezone.utc) - timedelta(days=days)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
