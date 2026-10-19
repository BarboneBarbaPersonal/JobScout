"""Read job boards with freehire's crawling engine (see engine/main.go and docs/MERGE-SPEC.md).

The engine gets every company's link, recognizes the job board behind it, crawls all the
boards and prints the jobs. This module turns its output into JobScout jobs with the same
ids as before, so hidden jobs and applications keep working. Companies whose link the
engine doesn't recognize are returned, and the old scanner reads those.
"""

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from . import util
from .sources.common import iso, job as make_job

ENGINE_TIMEOUT = 45 * 60  # seconds: the whole crawl must finish well inside the hourly slot


# Boards the old scanner found that freehire's engine can read too: (old service, params) ->
# (freehire source, board). Microsoft (eightfold) and IBM stay with the old readers: freehire
# would crawl their whole worldwide catalogue, our readers ask for Spain only.
def engine_board(service, params):
    if service == "teamtailor":
        return "teamtailor", params["host"]
    if service == "comeet":
        return "comeet", f"{params['company_slug']}/{params['company_uid']}"
    if service == "recruiterflow":
        return "recruiterflow", params["company_slug"]
    if service in ("successfactors", "phenom", "factorial"):
        return service, params["host"]
    return None


def scan(companies, binary):
    """Crawl with the engine. Returns (boards, unrecognized company names).
    companies: sheet rows; a row may carry "source" and "board" when the board is known.
    boards: [{"company", "source", "board", "ok", "error", "jobs": [JobScout jobs]}]"""
    links = {c["name"]: c["careers"] or c["website"] for c in companies}
    request = json.dumps([{"name": c["name"], "link": links[c["name"]], "source": c.get("source", ""),
                           "board": c.get("board", "")} for c in companies if links[c["name"]] or c.get("source")])
    result = subprocess.run([binary], input=request, capture_output=True, text=True,
                            encoding="utf-8", timeout=ENGINE_TIMEOUT)
    if result.returncode != 0:
        raise RuntimeError(f"engine failed: {result.stderr[-300:]}")

    boards, unrecognized, jobs_by_board = [], [c["name"] for c in companies if not links[c["name"]]], {}
    for line in result.stdout.splitlines():
        item = json.loads(line)
        if item["kind"] == "unrecognized":
            unrecognized.append(item["company"])
        elif item["kind"] == "job":
            key = (item["source"], item["board"])
            jobs_by_board.setdefault(key, []).append(to_job(item, links.get(item["company"], "")))
        elif item["kind"] == "board":
            boards.append(item)
    for item in boards:
        item["ok"] = not item.get("error")
        item["jobs"] = jobs_by_board.get((item["source"], item["board"]), [])
        if item["source"] == "teamtailor":
            keep_teamtailor_ids(item)
    return boards, unrecognized


def keep_teamtailor_ids(item):
    """Old Teamtailor ids end with the job's feed code (a long uuid), freehire's with the job
    number. The board's feed links number -> code, so the old ids are kept."""
    try:
        feed = ET.fromstring(util.get(f"https://{item['board']}/jobs.rss").content)
    except Exception:
        return  # keep freehire's ids for this run rather than lose the board
    codes = {}
    for entry in feed.iter("item"):
        number = re.search(r"/jobs/(\d+)", entry.findtext("link") or "")
        if number:
            codes[number.group(1)] = (entry.findtext("guid") or "").strip()
    for job in item["jobs"]:
        number = job["id"].rsplit("/", 1)[-1]
        if codes.get(number):
            job["id"] = f"teamtailor/{item['board']}/{codes[number]}"


def to_job(item, company_link=""):
    """One engine job -> a JobScout job (same keys as the old readers, plus work mode)."""
    job = make_job(job_id(item, company_link), item["title"], item["url"].split("?utm_source")[0],
                   item["location"], iso(item.get("posted_at")), item.get("description") or "")
    job["work_mode"] = item.get("work_mode") or ""
    if item["source"] == "workday":
        # freehire keeps only a Workday job's first city; the job page lists all of them.
        host, _, site = item["board"].partition("/")
        job["_extra"] = {"api": f"https://{host}/wday/cxs/{host.split('.')[0]}/{site}{item['external_id']}"}
    return job


def job_id(item, company_link=""):
    """The id JobScout used before the engine: '<platform>/<board>/<job id>'."""
    source, board, external = item["source"], item["board"], str(item["external_id"])
    if source == "workday":
        # board = "<tenant>.wdN.myworkdayjobs.com/<site>"; old id = workday/<tenant>/<site>/<path>
        host, _, site = board.partition("/")
        return f"workday/{host.split('.')[0]}/{site}/{external.lstrip('/')}"
    if source == "comeet":
        # board = "<slug>/<company uid>"; old id = comeet/<slug>/<position uid>
        return f"comeet/{board.split('/')[0]}/{external}"
    if source == "personio":
        # The old id used the board's address as written in the sheet (.de or .com).
        host = urlparse(company_link).netloc
        if not host.endswith((".jobs.personio.de", ".jobs.personio.com")):
            host = f"{board}.jobs.personio.com"
        return f"personio/{host}/{external}"
    return f"{source}/{board}/{external}"
