"""
Find which job board (ATS) each target company uses, so jobwatch can poll it.

No AI, no tokens: for every company in companies.csv we
  1. reuse an entry from jobwatch's own config.example.yaml if the name matches,
  2. look for ATS links on the company's careers pages,
  3. otherwise guess slugs (e.g. "datadog", "datadoghq") against the public ATS APIs.

Output:
  companies.found.yaml   -> ready-to-paste `companies:` entries for jobwatch
  companies.missing.csv  -> companies we could not match automatically

Run:  python jobscout/discover_ats.py
"""

import csv
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

HERE = Path(__file__).parent
UPSTREAM_CONFIG = HERE.parent / "config.example.yaml"
HEADERS = {"User-Agent": "Mozilla/5.0 (JobScout careers-page monitor)"}
TIMEOUT = 15

# Regexes that pull an ATS identity out of any link on a careers page.
# Each maps to (jobwatch source name, param name).
LINK_PATTERNS = [
    (r"(?:boards|job-boards)(?:\.eu)?\.greenhouse\.io/(?:embed/job_board\?for=)?([A-Za-z0-9_-]+)", "greenhouse", "board_token"),
    (r"boards-api\.greenhouse\.io/v1/boards/([A-Za-z0-9_-]+)", "greenhouse", "board_token"),
    (r"jobs\.(?:eu\.)?lever\.co/([A-Za-z0-9_-]+)", "lever", "site"),
    (r"jobs\.ashbyhq\.com/([A-Za-z0-9_.%-]+)", "ashby", "board_name"),
    (r"apply\.workable\.com/([A-Za-z0-9_-]+)", "workable", "account"),
    (r"jobs\.smartrecruiters\.com/([A-Za-z0-9_-]+)", "smartrecruiters", "company_id"),
    (r"([A-Za-z0-9-]+)\.recruitee\.com", "recruitee", "company_slug"),
    (r"([A-Za-z0-9-]+)\.bamboohr\.com", "bamboohr", "company_slug"),
    (r"ats\.rippling\.com/([A-Za-z0-9_-]+)", "rippling", "board_slug"),
]
WORKDAY_PATTERN = r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)"
# Boards jobwatch cannot poll yet -- we only report these.
UNSUPPORTED_PATTERNS = [
    (r"([A-Za-z0-9-]+)\.jobs\.personio\.(?:de|com)", "personio"),
    (r"([A-Za-z0-9-]+)\.teamtailor\.com", "teamtailor"),
    (r"careers\.hibob\.com/([A-Za-z0-9-]+)", "hibob"),
    (r"([A-Za-z0-9-]+)\.breezy\.hr", "breezy"),
    (r"jobs\.jobvite\.com/([A-Za-z0-9-]+)", "jobvite"),
    (r"([A-Za-z0-9-]+)\.icims\.com", "icims"),
    (r"([A-Za-z0-9-]+)\.eightfold\.ai", "eightfold"),
]
# Slugs that show up in links but are never a real company board.
BAD_SLUGS = {"embed", "api", "v1", "jobs", "job", "careers", "static", "assets", "www", "app", "search"}

CAREER_PATHS = ["", "/careers", "/careers/", "/jobs", "/company/careers", "/about/careers", "/en/careers", "/join-us"]


def get(url, **kwargs):
    """GET that never raises -- returns None on any network error."""
    try:
        return requests.get(url, headers=HEADERS, timeout=TIMEOUT, **kwargs)
    except requests.RequestException:
        return None


# ---------- 1. reuse jobwatch's verified catalog ----------

def load_upstream_entries():
    """Map lower-cased company name -> the raw YAML line from config.example.yaml."""
    entries = {}
    for line in UPSTREAM_CONFIG.read_text(encoding="utf-8").splitlines():
        match = re.match(r'\s*- \{name: "?([^",]+)"?, source:', line)
        if match:
            entries[normalize(match.group(1))] = line.strip()
    return entries


def normalize(name):
    """'HashiCorp (IBM)' -> 'hashicorp'"""
    name = re.sub(r"\(.*?\)", "", name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ---------- 2. look for ATS links on careers pages ----------

def scan_careers_pages(website):
    """Return ('supported', entry_params) or ('unsupported', label) or None."""
    unsupported = None
    pages = [f"https://{website}{path}" for path in CAREER_PATHS]
    visited = set()
    while pages:
        url = pages.pop(0)
        if url in visited or len(visited) >= 15:
            continue
        visited.add(url)
        response = get(url)
        if response is None or response.status_code != 200:
            continue
        html = response.text

        # From the homepage, also follow links that look like a careers page
        # (e.g. careers.company.com or /about/jobs) -- one level deep only.
        if url == f"https://{website}":
            for link in re.findall(r'href="(https?://[^"]*(?:career|jobs)[^"]*|/[^"]*(?:career|jobs)[^"]*)"', html, re.I)[:5]:
                pages.append(link if link.startswith("http") else f"https://{website}{link}")

        # A page can link several Workday URLs; keep the first one whose job API answers.
        for tenant, wd, site in re.findall(WORKDAY_PATTERN, html):
            host = f"{tenant}.{wd}.myworkdayjobs.com"
            if workday_board_exists(host, tenant, site):
                return "supported", ("workday", {"host": host, "tenant": tenant, "site": site})

        for pattern, source, param in LINK_PATTERNS:
            for slug in re.findall(pattern, html):
                # A link on the company's own site is trusted even if the board is empty today.
                if slug.lower() not in BAD_SLUGS and open_job_count(source, slug) is not None:
                    return "supported", (source, {param: slug})

        for pattern, label in UNSUPPORTED_PATTERNS:
            found = re.search(pattern, html)
            if found and found.group(1).lower() not in BAD_SLUGS:
                unsupported = f"{label}:{found.group(1)}"
    if unsupported:
        return "unsupported", unsupported
    return None


# ---------- 3. guess slugs against public ATS APIs ----------

def open_job_count(source, slug):
    """Number of open jobs on this board, or None if the board does not exist."""
    urls = {
        "greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
        "lever": f"https://api.lever.co/v0/postings/{slug}?mode=json",
        "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
        "workable": f"https://apply.workable.com/api/v1/widget/accounts/{slug}",
        "smartrecruiters": f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=1",
        "recruitee": f"https://{slug}.recruitee.com/api/offers/",
    }
    if source not in urls:
        return 0  # bamboohr / rippling: exists (link was on the careers page), count unknown
    response = get(urls[source])
    if response is None or response.status_code != 200:
        return None
    try:
        data = response.json()
    except ValueError:
        return None
    if source == "lever":
        if isinstance(data, list) and not data:
            # EU-hosted Lever boards live on a separate API and look empty on the US one.
            eu_response = get(f"https://api.eu.lever.co/v0/postings/{slug}?mode=json")
            if eu_response is not None and eu_response.status_code == 200 and isinstance(eu_response.json(), list):
                data = eu_response.json()
        return len(data) if isinstance(data, list) else None
    if source == "smartrecruiters":
        return data.get("totalFound", 0)
    if source == "recruitee":
        return len(data.get("offers", []))
    return len(data.get("jobs", []))


def workday_board_exists(host, tenant, site):
    """Workday's job list is a POST endpoint; 200 means the tenant/site pair is real."""
    try:
        response = requests.post(f"https://{host}/wday/cxs/{tenant}/{site}/jobs",
                                 json={"limit": 1, "offset": 0, "searchText": "", "appliedFacets": {}},
                                 headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException:
        return False
    return response.status_code == 200


def board_has_jobs(source, slug):
    """A guessed slug only counts if the board has at least one live job --
    many generic names (e.g. workable/"splunk") are old, empty boards."""
    count = open_job_count(source, slug)
    return count is not None and count > 0


def slug_candidates(company, website):
    """'Grafana Labs', 'grafana.com' -> ['grafanalabs', 'grafana', 'grafana-labs', ...]"""
    base_name = re.sub(r"\(.*?\)", "", company).strip()
    domain_root = website.split(".")[0]
    candidates = [
        normalize(base_name),
        re.sub(r"[^a-z0-9]+", "-", base_name.lower()).strip("-"),
        domain_root,
        domain_root.replace("-", ""),
        normalize(base_name) + "hq",
    ]
    # keep order, drop duplicates and empty strings
    return [c for c in dict.fromkeys(candidates) if c]


def guess_board(company, website):
    param_names = {"greenhouse": "board_token", "lever": "site", "ashby": "board_name",
                   "workable": "account", "smartrecruiters": "company_id", "recruitee": "company_slug"}
    for slug in slug_candidates(company, website):
        for source, param in param_names.items():
            if board_has_jobs(source, slug):
                return source, {param: slug}
    return None


# ---------- glue ----------

def discover(row, upstream):
    company, website = row["Company"], row["Website"].strip().lower()
    key = normalize(company)
    if key in upstream:
        return company, "upstream", upstream[key]

    result = scan_careers_pages(website) if website else None
    if result and result[0] == "supported":
        return company, "careers-page", yaml_entry(company, *result[1])
    if result and result[0] == "unsupported":
        return company, "unsupported", result[1]

    guessed = guess_board(company, website)
    if guessed:
        return company, "slug-guess", yaml_entry(company, *guessed)
    return company, "missing", ""


def yaml_entry(company, source, params):
    params_text = ", ".join(f'{key}: "{value}"' for key, value in params.items())
    return f'- {{name: "{company}", source: {source}, params: {{{params_text}}}}}'


def main():
    with open(HERE / "companies.csv", encoding="utf-8") as file:
        rows = [row for row in csv.DictReader(file) if row["Company"].strip()]
    upstream = load_upstream_entries()

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda row: discover(row, upstream), rows))

    found_lines, missing_rows = [], []
    for company, how, entry in results:
        if how in ("upstream", "careers-page", "slug-guess"):
            found_lines.append(f"  {entry}  # via {how}")
        else:
            missing_rows.append([company, how, entry])

    (HERE / "companies.found.yaml").write_text("\n".join(found_lines) + "\n", encoding="utf-8")
    with open(HERE / "companies.missing.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Company", "Reason", "Detail"])
        writer.writerows(missing_rows)

    print(f"matched {len(found_lines)} / {len(rows)} companies, {len(missing_rows)} need a manual look")


if __name__ == "__main__":
    main()
