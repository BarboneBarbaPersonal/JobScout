"""Smaller job board services: RSS/XML feeds and careers pages with the job
list written into the page."""

import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from .. import util
from .common import iso, job, join


def teamtailor(params, hints):
    host = params["host"]
    root = ET.fromstring(util.get(f"https://{host}/jobs.rss").content)
    jobs = []
    for item in root.iter("item"):
        places = []
        for place in item.iter():
            if place.tag.endswith("}location"):
                parts = {child.tag.split("}")[-1]: (child.text or "").strip() for child in place}
                places.append(join(parts.get("city"), parts.get("country")) or parts.get("name", ""))
        remote = next((el.text or "" for el in item.iter() if el.tag.endswith("}remoteStatus")), "")
        if remote.lower() == "fully":
            places.append("Remote")
        elif remote.lower() == "hybrid":
            places.append("Hybrid")
        jobs.append(job(f"teamtailor/{host}/{(item.findtext('guid') or '').strip()}", item.findtext("title"),
                        item.findtext("link"), "; ".join(p for p in places if p), iso(item.findtext("pubDate")),
                        util.html_to_text(item.findtext("description"))))
    return jobs


def personio(params, hints):
    host = params["host"]
    root = ET.fromstring(util.get(f"https://{host}/xml?language=en").content)
    jobs = []
    for position in root.iter("position"):
        position_id = (position.findtext("id") or "").strip()
        offices = [position.findtext("office") or ""]
        offices += [o.text or "" for o in position.findall("additionalOffices/office")]
        parts = []
        for block in position.findall("jobDescriptions/jobDescription"):
            parts += [block.findtext("name") or "", util.html_to_text(block.findtext("value"))]
        jobs.append(job(f"personio/{host}/{position_id}", position.findtext("name"),
                        f"https://{host}/job/{position_id}", "; ".join(o.strip() for o in offices if o.strip()),
                        iso(position.findtext("createdAt")), "\n".join(p for p in parts if p)))
    return jobs


def comeet(params, hints):
    slug, uid = params["company_slug"], params["company_uid"]
    page = util.get(f"https://www.comeet.com/jobs/{slug}/{uid}").text
    found = re.search(r"COMPANY_POSITIONS_DATA\s*=\s*(\[.*?\]);", page, re.S)
    jobs = []
    for pos in json.loads(found.group(1)) if found else []:
        place = pos.get("location") or {}
        location = join(place.get("city"), place.get("country")) or place.get("name", "")
        if place.get("is_remote"):
            location = join(location, "Remote", sep="; ")
        jobs.append(job(f"comeet/{slug}/{pos['uid']}", pos.get("name"), pos.get("url_active_page"),
                        location, iso(pos.get("time_updated"))))
    return jobs


def recruiterflow(params, hints):
    slug = params["company_slug"]
    page = util.get(f"https://recruiterflow.com/{slug}/jobs").text
    found = re.search(r"window\.jobsList\s*=\s*(\{.*?\});\s*\n", page, re.S)
    jobs, seen = [], set()
    for _, department_jobs in (json.loads(found.group(1)).get("department", []) if found else []):
        for item in department_jobs:
            if item["job_id"] in seen:  # the same job is listed under "Any" and its own team
                continue
            seen.add(item["job_id"])
            jobs.append(job(f"recruiterflow/{slug}/{item['job_id']}", item.get("job_name"),
                            "https://recruiterflow.com/" + (item.get("apply_link") or "").lstrip("/"),
                            join(item.get("details"), item.get("remote_type"), sep="; "),
                            iso(item.get("last_opened"))))
    return jobs


def factorial(params, hints):
    host = params["host"]
    page = util.get(f"https://{host}/").text
    names = dict(re.findall(r"<option value='(\d+)'>([^<]+)</option>", page))
    jobs = []
    for item in re.findall(r"<li class='job-offer-item.*?</li>", page, re.S):
        url = re.search(r"data-job-postings-url='([^']+)'", item)
        title = re.search(r"<span class='md:w-3/6'>\s*<div>(.*?)</div>", item, re.S)
        if not url or not title:
            continue
        place = re.search(r"data-location-id='(\d+)'", item)
        location = names.get(place.group(1), "") if place else ""
        if "data-is-remote='true'" in item:
            location = join(location, "Remote")
        job_id = re.search(r"-(\d+)/?$", url.group(1))
        jobs.append(job(f"factorial/{host}/{job_id.group(1) if job_id else url.group(1)}",
                        util.html_to_text(title.group(1)), url.group(1), location))
    return jobs


def hibob(params, hints):
    sub = params["subdomain"]
    data = util.get_json(f"https://{sub}.careers.hibob.com/api/job-ad", headers={"companyidentifier": sub})
    jobs = []
    for item in data.get("jobAdDetails", []):
        location = join(item.get("site"), item.get("country"))
        if (item.get("workspaceType") or "").lower() == "remote":
            location = join(location, "Remote")
        jobs.append(job(f"hibob/{sub}/{item['id']}", item.get("title"),
                        f"https://{sub}.careers.hibob.com/jobs/{item['id']}", location,
                        description=util.html_to_text(item.get("description"))))
    return jobs


def htmllinks(params, hints):
    """Any careers page: every link matching the `link` pattern is one job.
    The pattern may name parts of the link (?P<title>...) and (?P<location>...)."""
    page_url = params["url"]
    page = util.get(page_url).text
    pattern = re.compile(params["link"])
    jobs, seen = [], set()
    for href, text in re.findall(r'<a\b[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', page, re.S | re.I):
        href = urljoin(page_url, href)
        found = pattern.search(href)
        if not found or href in seen:
            continue
        seen.add(href)
        lines = util.html_to_text(text).splitlines()
        groups = found.groupdict()
        title = lines[0] if lines else (groups.get("title") or "").replace("-", " ").replace("_", " ")
        location = (groups.get("location") or "").replace("-", " ")
        if str(params.get("text_location", "")).lower() == "true":
            location = join(location, ", ".join(lines[1:]))
        location = join(location, params.get("location"))
        jobs.append(job("htmllinks/" + re.sub(r"^https?://", "", href), title, href, location))
    return jobs
