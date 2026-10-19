"""Large companies with their own careers systems.

phenom, successfactors, eightfold and ibm serve thousands of jobs worldwide, so
they are read for the user's countries only (`hints["countries"]`, taken from
the Locations in the sheet) unless the board link says otherwise.
"""

import json
import re

import requests

from .. import util
from .common import iso, job, join

# Country name -> two-letter code, for sites that filter by code (IBM).
COUNTRY_CODES = {
    "spain": "es", "italy": "it", "germany": "de", "france": "fr", "united kingdom": "gb",
    "uk": "gb", "ireland": "ie", "portugal": "pt", "netherlands": "nl", "belgium": "be",
    "poland": "pl", "sweden": "se", "denmark": "dk", "norway": "no", "finland": "fi",
    "austria": "at", "switzerland": "ch", "czech republic": "cz", "romania": "ro",
    "united states": "us", "usa": "us", "canada": "ca", "mexico": "mx", "brazil": "br",
    "india": "in", "australia": "au", "japan": "jp", "singapore": "sg", "israel": "il",
}


def phenom(params, hints):
    host = params["host"]
    countries = util.split_list(params.get("countries")) or hints.get("countries", [])
    jobs, start = [], 0
    while start < 3000:
        body = {"lang": params.get("lang", "en_global"), "deviceType": "desktop",
                "country": params.get("site_country", "global"), "pageName": "search-results",
                "ddoKey": "refineSearch", "sortBy": "", "subsearch": "", "from": start, "jobs": True,
                "counts": False, "all_fields": ["country", "city"], "size": 100, "clearAll": False,
                "jdsource": "facets", "isSliderEnable": False, "keywords": "", "global": True,
                "selected_fields": {"country": countries} if countries else {}, "locationData": {}}
        search = util.post_json(f"https://{host}/widgets", body).get("refineSearch") or {}
        page = (search.get("data") or {}).get("jobs") or []
        for j in page:
            jobs.append(job(f"phenom/{host}/{j['jobId']}", j.get("title"),
                            f"https://{host}/{params.get('path', 'global/en')}/job/{j['jobId']}",
                            j.get("location") or join(j.get("city"), j.get("country")),
                            iso(j.get("postedDate"))))
        start += 100
        if len(page) < 100 or start >= search.get("totalHits", 0):
            break
    return jobs


def successfactors(params, hints):
    """SAP SuccessFactors career sites: a server-rendered search page, 25 rows per page.
    One session (cookie) for the whole walk, or pages come from different servers."""
    host = params["host"]
    session = requests.Session()
    session.headers.update(util.HEADERS)
    jobs, seen, start = [], set(), 0
    for _ in range(int(params.get("max_pages", 100))):
        response = session.get(f"https://{host}/search/?q=&sortColumn=referencedate"
                               f"&sortDirection=desc&startrow={start}", timeout=util.TIMEOUT)
        response.raise_for_status()
        rows = re.findall(r'<tr class="data-row.*?</tr>', response.text, re.S)
        new = 0
        for row in rows:
            link = re.search(r'<a[^>]*class="jobTitle-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', row, re.S)
            if not link:
                continue
            url = "https://" + host + link.group(1).split("?")[0] if link.group(1).startswith("/") else link.group(1).split("?")[0]
            job_id = re.search(r"/(\d+)/?$", url)
            if not job_id or job_id.group(1) in seen:
                continue
            seen.add(job_id.group(1))
            new += 1
            place = re.search(r'class="jobLocation[^"]*"[^>]*>(.*?)</span>', row, re.S)
            date = re.search(r'class="jobDate[^"]*"[^>]*>(.*?)</span>', row, re.S)
            jobs.append(job(f"successfactors/{host}/{job_id.group(1)}", util.html_to_text(link.group(2)), url,
                            util.html_to_text(place.group(1)) if place else "",
                            iso(util.html_to_text(date.group(1))) if date else None))
        start += len(rows)
        if not rows or not new:
            break
    return jobs


def successfactors_detail(item, params):
    page = util.get(item["url"]).text
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            item["description"] = util.html_to_text(data.get("description"))
            item["posted_at"] = iso(data.get("datePosted")) or item["posted_at"]
            return item
    found = re.search(r'class="jobdescription"[^>]*>(.*?)</(?:div|span)>\s*</(?:div|span)>', page, re.S)
    item["description"] = util.html_to_text(found.group(1)) if found else ""
    return item


def eightfold(params, hints):
    host, domain = params["host"], params["domain"]
    places = util.split_list(params.get("location")) or hints.get("countries", []) or [""]
    limit = int(params.get("max_postings", 1000))
    jobs, seen = [], set()
    for place in places:
        start = 0
        while start < limit:
            data = util.get_json(f"https://{host}/api/pcsx/search", params={
                "domain": domain, "query": params.get("query", ""), "location": place, "start": start})
            positions = (data.get("data") or {}).get("positions") or []
            for p in positions:
                if p["id"] in seen:
                    continue
                seen.add(p["id"])
                names = []
                for name in p.get("locations") or []:
                    if name not in names:
                        names.append(name)
                url = p.get("positionUrl") or f"/careers/job/{p['id']}"
                jobs.append(job(f"eightfold/{domain}/{p['id']}", p.get("name"),
                                url if url.startswith("http") else f"https://{host}{url}",
                                "; ".join(names), iso(p.get("postedTs")), host=host, domain=domain, pid=p["id"]))
            start += len(positions)
            if not positions or start >= (data.get("data") or {}).get("count", 0):
                break
    return jobs


def eightfold_detail(item, params):
    extra = item["_extra"]
    data = util.get_json(f"https://{extra['host']}/api/pcsx/position_details", params={
        "position_id": extra["pid"], "domain": extra["domain"], "hl": "en"}).get("data") or {}
    item["description"] = util.html_to_text(data.get("jobDescription"))
    return item


def ibm(params, hints):
    codes = util.split_list(params.get("rc")) or [
        COUNTRY_CODES[c.lower()] for c in hints.get("countries", []) if c.lower() in COUNTRY_CODES]
    appid, scope = params.get("appid", "careers"), params.get("scope", "careers2")
    jobs = []
    for code in codes:
        start = 0
        while True:
            data = util.get_json(
                f"https://www-api.ibm.com/search/api/v1/ibmcom/appid/{appid}/responseFormat/json",
                params={"appid": appid, "scope": scope, "rc": code, "rmdt": "ALL", "query": "",
                        "fr": start, "nr": 30})
            results = (data.get("resultset") or {}).get("searchresults") or {}
            page = results.get("searchresultlist") or []
            for r in page:
                fields = {}
                for attribute in r.get("docattributes") or []:
                    fields.update(attribute)
                jobs.append(job(f"ibm/{code}/{fields.get('field_text_01', r.get('url'))}", r.get("title"),
                                r.get("url"), fields.get("field_keyword_19", ""), iso(fields.get("dcdate")),
                                util.html_to_text(fields.get("raw_body"))))
            start += len(page)
            if not page or start >= int(results.get("totalresults") or 0):
                break
    return jobs


def atlassian(params, hints):
    data = util.get_json("https://www.atlassian.com/endpoint/careers/listings")
    jobs, seen = [], set()
    for item in data:
        if item["id"] in seen:  # the feed sometimes lists a job twice
            continue
        seen.add(item["id"])
        names = []
        for name in item.get("locations") or []:
            if name not in names:
                names.append(name)
        text = "".join(item.get(key) or "" for key in ("overview", "responsibilities", "qualifications"))
        jobs.append(job(f"atlassian/{item['id']}", item.get("title"),
                        f"https://www.atlassian.com/company/careers/details/{item['id']}",
                        "; ".join(names), description=util.html_to_text(text)))
    return jobs


def dynatrace(params, hints):
    jobs, start = [], 0
    while start < 2000:
        data = util.post_json("https://www.dynatrace.com/api/coveo/search/",
                              {"q": "", "numberOfResults": 100, "firstResult": start})
        page = data.get("results") or []
        for r in page:
            raw = r.get("raw") or {}
            location = ", ".join(list(raw.get("office_locations") or []) + list(raw.get("country") or []))
            jobs.append(job(f"dynatrace/{raw.get('id')}", r.get("title"), r.get("clickUri"), location,
                            iso(raw.get("date"))))
        start += 100
        if len(page) < 100 or start >= data.get("totalCount", 0):
            break
    return jobs


def deel(params, hints):
    page = util.get("https://www.deel.com/careers/").text.replace('\\"', '"')
    jobs, seen = [], set()
    pattern = (r'"ashby_id":"([0-9a-f-]{36})","job_id":"[^"]*","title":"([^"]*)".*?"location_name":"([^"]*)"'
               r'.*?"is_listed":(true|false).*?"ashby_published_date":"([^"]*)".*?"all_locations":\[([^\]]*)\]')
    for job_id, title, location, listed, published, others in re.findall(pattern, page, re.S):
        if listed != "true" or job_id in seen:
            continue
        seen.add(job_id)
        names = [location] + [n for n in re.findall(r'"([^"]+)"', others) if n != location]
        jobs.append(job(f"deel/{job_id}", title, f"https://www.deel.com/careers/job/{job_id}/",
                        "; ".join(n for n in names if n), iso(published)))
    return jobs


def revolut(params, hints):
    """Works from a home computer; GitHub's servers get a bot check page instead."""
    page = util.get("https://www.revolut.com/careers/").text
    found = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    if not found:
        raise ValueError("Revolut sent a security check page instead of jobs")
    positions = json.loads(found.group(1))["props"]["pageProps"]["positions"]
    jobs = []
    for p in positions:
        slug = re.sub(r"[^a-z0-9]+", "-", (p.get("text") or "").lower()).strip("-")
        location = "; ".join(join(place.get("name"), place.get("country")) for place in p.get("locations") or [])
        jobs.append(job(f"revolut/{p['id']}", p.get("text"),
                        f"https://www.revolut.com/careers/position/{slug}-{p['id']}/", location))
    return jobs


def bendingspoons(params, hints):
    """Bending Spoons' own careers site: all jobs are written into the page (Next.js data)."""
    page = util.get("https://jobs.bendingspoons.com/").text
    found = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    positions = json.loads(found.group(1))["props"]["pageProps"]["list"] if found else []
    jobs = []
    for p in positions:
        if p.get("status", "active") != "active":
            continue
        places = [office.get("title", "") for office in p.get("officeLocations") or []]
        if p.get("availableAsRemoteInDefaultCountries"):
            places.append("Remote")
        description = util.html_to_text((p.get("highLevelDescription") or "")
                                        + "".join(p.get("responsibilities") or []))
        jobs.append(job(f"bendingspoons/{p['id']}", p.get("jobTitle"),
                        f"https://jobs.bendingspoons.com/positions/{p['id']}", "; ".join(places),
                        description=description))
    return jobs
