"""The common job board services. Each has a free public API that returns all
open jobs of one company."""

from .. import util
from .common import iso, job, join


def greenhouse(params, hints):
    token = params["board_token"]
    data = util.get_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    return [job(f"greenhouse/{token}/{j['id']}", j.get("title"), j.get("absolute_url"),
                (j.get("location") or {}).get("name", ""), iso(j.get("updated_at")),
                util.html_to_text(_unescape(j.get("content"))))
            for j in data.get("jobs", [])]


def _unescape(text):
    """Greenhouse sends its HTML escaped once more ("&lt;p&gt;")."""
    import html
    return html.unescape(text or "")


def lever(params, hints):
    site = params["site"]
    data = util.get_json(f"https://api.lever.co/v0/postings/{site}?mode=json")
    if not data:  # EU companies are only on the EU server
        try:
            data = util.get_json(f"https://api.eu.lever.co/v0/postings/{site}?mode=json")
        except Exception:
            data = []  # not on the EU server either: the board simply has no open jobs
    jobs = []
    for p in data:
        parts = [p.get("descriptionPlain") or ""]
        for block in p.get("lists") or []:
            parts += [block.get("text") or "", util.html_to_text(block.get("content"))]
        parts.append(p.get("additionalPlain") or "")
        jobs.append(job(f"lever/{site}/{p['id']}", p.get("text"), p.get("hostedUrl"),
                        (p.get("categories") or {}).get("location", ""), iso(p.get("createdAt")),
                        "\n".join(part for part in parts if part)))
    return jobs


def ashby(params, hints):
    board = params["board_name"]
    data = util.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    return [job(f"ashby/{board}/{j['id']}", j.get("title"), j.get("jobUrl"), j.get("location"),
                iso(j.get("publishedAt")), util.html_to_text(j.get("descriptionHtml")))
            for j in data.get("jobs", []) if j.get("isListed", True)]


def workable(params, hints):
    account = params["account"]
    data = util.get_json(f"https://apply.workable.com/api/v1/widget/accounts/{account}?details=true")
    jobs = []
    for j in data.get("jobs", []):
        location = join(j.get("city"), j.get("country"))
        if j.get("telecommuting"):
            location = join("Remote", location, sep=" ")
        jobs.append(job(f"workable/{account}/{j['shortcode']}", j.get("title"), j.get("url"),
                        location, iso(j.get("published_on")), util.html_to_text(j.get("description"))))
    return jobs


def smartrecruiters(params, hints):
    company = params["company_id"]
    limit = int(params.get("max_postings", 2000))
    jobs, offset = [], 0
    while offset < limit:
        data = util.get_json(f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
                             f"?limit=100&offset={offset}")
        page = data.get("content") or []
        for p in page:
            place = p.get("location") or {}
            location = join("Remote" if place.get("remote") else "", place.get("city"), sep=" ")
            jobs.append(job(f"smartrecruiters/{company}/{p['id']}", p.get("name"),
                            f"https://jobs.smartrecruiters.com/{company}/{p['id']}", location,
                            iso(p.get("releasedDate")), company=company, posting=p["id"]))
        offset += len(page)
        if not page or offset >= data.get("totalFound", 0):
            break
    return jobs


def smartrecruiters_detail(item, params):
    extra = item["_extra"]
    data = util.get_json(f"https://api.smartrecruiters.com/v1/companies/{extra['company']}"
                         f"/postings/{extra['posting']}")
    sections = (data.get("jobAd") or {}).get("sections") or {}
    parts = []
    for key in ("companyDescription", "jobDescription", "qualifications", "additionalInformation"):
        section = sections.get(key) or {}
        parts += [section.get("title") or "", util.html_to_text(section.get("text"))]
    item["description"] = "\n".join(part for part in parts if part)
    item["url"] = data.get("applyUrl") or item["url"]
    return item


def recruitee(params, hints):
    slug = params["company_slug"]
    data = util.get_json(f"https://{slug}.recruitee.com/api/offers/")
    return [job(f"recruitee/{slug}/{o['id']}", o.get("title"), o.get("careers_url"), o.get("location"),
                iso(o.get("published_at")),
                util.html_to_text((o.get("description") or "") + (o.get("requirements") or "")))
            for o in data.get("offers", [])]


def bamboohr(params, hints):
    slug = params["company_slug"]
    data = util.get_json(f"https://{slug}.bamboohr.com/careers/list")
    jobs = []
    for item in data.get("result", []):
        place = item.get("atsLocation") or {}
        location = join(place.get("city"), place.get("state"), place.get("country"))
        if item.get("isRemote"):
            location = join("Remote", location, sep=" ")
        jobs.append(job(f"bamboohr/{slug}/{item['id']}", item.get("jobOpeningName"),
                        f"https://{slug}.bamboohr.com/careers/{item['id']}", location,
                        slug=slug, job_id=item["id"]))
    return jobs


def bamboohr_detail(item, params):
    extra = item["_extra"]
    data = util.get_json(f"https://{extra['slug']}.bamboohr.com/careers/{extra['job_id']}/detail")
    opening = (data.get("result") or {}).get("jobOpening") or {}
    item["description"] = util.html_to_text(opening.get("description"))
    item["url"] = opening.get("jobOpeningShareUrl") or item["url"]
    return item


def rippling(params, hints):
    slug = params["board_slug"]
    jobs, page = [], 0
    while True:
        data = util.get_json(f"https://ats.rippling.com/api/v2/board/{slug}/jobs"
                             f"?groupJobsByLocation=true&page={page}&pageSize=1000")
        for item in data.get("items", []):
            names = []
            for place in item.get("locations") or []:
                if place.get("name") and place["name"] not in names:
                    names.append(place["name"])
            jobs.append(job(f"rippling/{slug}/{item['id']}", item.get("name"),
                            f"https://ats.rippling.com/{slug}/jobs/{item['id']}", "; ".join(names),
                            slug=slug, job_id=item["id"]))
        page += 1
        if page >= data.get("totalPages", 0):
            break
    return jobs


def rippling_detail(item, params):
    extra = item["_extra"]
    data = util.get_json(f"https://ats.rippling.com/api/v2/board/{extra['slug']}/jobs/{extra['job_id']}")
    description = data.get("description") or {}
    item["description"] = util.html_to_text((description.get("company") or "") + (description.get("role") or ""))
    item["posted_at"] = iso(data.get("createdOn"))
    return item
