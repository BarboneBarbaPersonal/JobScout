"""Find a company's job board from the links in the Companies tab.

1. The careers link names a known job board service -> read the board from the link.
2. A few big companies have their own systems -> built-in list below.
3. Otherwise open the careers page (or the website) and look for a link to a
   known service with the company's name in it.
Step 3 makes web requests, so its answers are remembered between runs (cache).
"""

import re
from urllib.parse import urlparse

from . import util

# Links that name a job board service: (service, pattern, names of the pattern's parts).
PATTERNS = [
    ("workday", r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)",
     ("tenant", "shard", "site")),
    ("greenhouse", r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_-]+)",
     ("board_token",)),
    ("greenhouse", r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)", ("board_token",)),
    ("lever", r"jobs\.(?:eu\.)?lever\.co/([A-Za-z0-9_-]+)", ("site",)),
    ("ashby", r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)", ("board_name",)),
    ("workable", r"apply\.workable\.com/([A-Za-z0-9_-]+)", ("account",)),
    ("smartrecruiters", r"(?:jobs|careers)\.smartrecruiters\.com/([A-Za-z0-9_-]+)", ("company_id",)),
    ("recruitee", r"([A-Za-z0-9-]+)\.recruitee\.com", ("company_slug",)),
    ("bamboohr", r"([A-Za-z0-9-]+)\.bamboohr\.com", ("company_slug",)),
    ("rippling", r"ats\.rippling\.com/([A-Za-z0-9_-]+)", ("board_slug",)),
    ("teamtailor", r"([A-Za-z0-9-]+\.teamtailor\.com)", ("host",)),
    ("personio", r"([A-Za-z0-9-]+\.jobs\.personio\.(?:de|com))", ("host",)),
    ("hibob", r"([A-Za-z0-9-]+)\.careers\.hibob\.com", ("subdomain",)),
    ("comeet", r"comeet\.com/jobs/([A-Za-z0-9_-]+)/([0-9A-Za-z.]+)", ("company_slug", "company_uid")),
    ("recruiterflow", r"recruiterflow\.com/([A-Za-z0-9_-]+)", ("company_slug",)),
]
NOT_A_NAME = {"embed", "api", "v1", "jobs", "job", "careers", "static", "assets", "www", "app", "search"}

# Companies with their own careers systems, by the careers link's address.
KNOWN = [
    (r"dynatrace\.com", "dynatrace", {}),
    (r"deel\.com", "deel", {}),
    (r"revolut\.com", "revolut", {}),
    (r"atlassian\.com", "atlassian", {}),
    (r"ibm\.com", "ibm", {"appid": "careers", "scope": "careers2"}),
    (r"careers\.microsoft\.com", "eightfold", {"host": "apply.careers.microsoft.com", "domain": "microsoft.com"}),
    (r"careers\.allianz\.com", "phenom", {"host": "careers.allianz.com", "path": "global/en"}),
    (r"careers\.factorial\.com", "factorial", {"host": "careers.factorial.com"}),
    (r"coralogix\.com", "htmllinks", {
        "url": "https://coralogix.com/careers/",
        "link": r"https://coralogix\.com/careers/co/(?P<location>[^/]+)/[^/]+/(?P<title>[^/]+)/all/"}),
    (r"aiven\.io", "htmllinks", {"url": "https://aiven.io/careers/job", "link": r"/careers/job/[0-9]+",
                                 "text_location": "true"}),
    (r"jobs\.sap\.com", "successfactors", {"host": "jobs.sap.com"}),
    (r"bendingspoons\.com", "bendingspoons", {}),
]


def from_link(link):
    """(service, params) when the link itself says which board it is, else None."""
    try:
        host = urlparse(_with_scheme(link)).netloc
    except ValueError:
        return None
    for pattern, service, params in KNOWN:
        if re.search(pattern, host + "/"):
            return service, dict(params)
    return _service_in(link)


def _service_in(text):
    """The first job board service link found anywhere in the text (a link or a whole page)."""
    for service, pattern, names in PATTERNS:
        for found in re.finditer(pattern, text):
            if found.group(1).lower() in NOT_A_NAME:
                continue
            params = dict(zip(names, found.groups()))
            if service == "workday":
                params = {"host": f"{params['tenant']}.{params['shard']}.myworkdayjobs.com",
                          "tenant": params["tenant"], "site": params["site"]}
            return service, params
    return None


def discover(company):
    """Look for the board by opening the company's own pages. Returns (service, params) or None.
    A board found this way must carry the company's name: a careers page can also
    link to a customer's or partner's board, and a wrong board is worse than none."""
    pages = []
    if company["careers"]:
        careers = _with_scheme(company["careers"])
        found = _probe_host(urlparse(careers).netloc)  # careers sites on their own address (teamtailor, SAP)
        if found:
            return found
        pages.append(careers)
    if company["website"]:
        site = _with_scheme(company["website"]).rstrip("/")
        pages += [site, site + "/careers", site + "/jobs", site + "/company/careers", site + "/about/careers"]
    for page in pages:
        try:
            html = util.get(page).text
        except Exception:
            continue
        found = _service_in(html)
        if found and _same_company(company, found[1]) and _has_board(found):
            return found
    return None


def _same_company(company, params):
    """True when the board's name looks like the company's name or website."""
    board = re.sub(r"[^a-z0-9]", "", " ".join(str(v) for v in params.values()).lower())
    names = [re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", company["name"]).lower())]
    if company["website"]:
        names.append(urlparse(_with_scheme(company["website"])).netloc.lower()
                     .removeprefix("www.").split(".")[0].replace("-", ""))
    return any(name and (name in board or board in name) for name in names)


def _has_board(found):
    """The board answers (an empty board is fine; a deleted one is not)."""
    from .sources import READERS
    try:
        READERS[found[0]](found[1], {})
        return True
    except Exception:
        return False


def _probe_host(host):
    if not host:
        return None
    try:
        rss = util.get(f"https://{host}/jobs.rss")
        if b"<rss" in rss.content[:500]:
            return "teamtailor", {"host": host}
    except Exception:
        pass
    try:
        page = util.get(f"https://{host}/search/?q=&startrow=0")
        if "jobTitle-link" in page.text:
            return "successfactors", {"host": host}
    except Exception:
        pass
    return None


def _with_scheme(link):
    return link if re.match(r"https?://", link or "") else f"https://{link}"
