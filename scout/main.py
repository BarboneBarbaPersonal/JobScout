"""JobScout scan: read the sheet, check every company's job board, publish the page.

Run:  python -m scout.main [site folder]
The sheet link comes from the SHEET_URL environment variable (a GitHub secret);
for local tests it can also be a folder with Preferences.csv and Companies.csv.
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import board, engine, resolve, sheet
from .prefs import Preferences
from .sources import DETAILS, READERS

CACHE = Path(os.environ.get("JOBSCOUT_CACHE", "cache"))  # kept between runs by GitHub's cache
RECHECK_NOT_FOUND_DAYS = 7  # companies without a board: look again after this many days
WORKERS = 8                 # boards read at the same time


def main():
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")
    source = os.environ.get("SHEET_URL", "").strip()
    if not source:
        sys.exit("SHEET_URL is missing. Add it under Settings > Secrets and variables > Actions.")
    try:
        prefs = Preferences(sheet.read_preferences(source))
        companies = sheet.read_companies(source)
    except Exception as error:
        sys.exit(f"Could not read the sheet: {error}")
    print(f"{len(companies)} companies, roles: {', '.join(prefs.core + prefs.also)}")

    started = time.time()
    results, left = scan_with_engine(companies, prefs)  # 1. freehire's engine reads the links it knows
    boards, not_found = find_boards(left)                # 2. the old board finder handles the rest...
    results += engine_reads_known_boards(boards, prefs)  # 3. ...and the engine reads what it can of those
    hints = {"countries": countries(prefs)}
    with ThreadPoolExecutor(WORKERS) as pool:
        results += list(pool.map(lambda item: scan_board(item, prefs, hints), boards.items()))
    board_count = len(results)

    matches, failed, scanned, all_ids = [], [], 0, set()
    for name, ok, open_jobs, found, error in results:
        scanned += open_jobs["count"]
        all_ids.update(open_jobs["ids"])
        matches += found
        if not ok:
            failed.append((name, error))
    seen_before = set(read_cache("seen.json", []))
    new_postings = len(all_ids - seen_before) if seen_before else 0
    write_cache("seen.json", sorted(all_ids))

    run = {"status": "ok" if not failed else "degraded", "boards": board_count,
           "boards_ok": board_count - len(failed), "scanned": scanned, "new_postings": new_postings}
    jobs = board.build(site, prefs, matches, run)
    summary(companies, board_count, len(boards), jobs, failed, not_found, scanned, time.time() - started)


def scan_with_engine(companies, prefs):
    """Read every board freehire's engine recognizes. Returns (results like scan_board's,
    companies left for the old scanner). Without the engine, or if it fails, all are left."""
    binary = os.environ.get("JOBSCOUT_ENGINE", "")
    if not binary:
        return [], companies
    try:
        boards, unrecognized = engine.scan(companies, binary)
    except Exception as error:
        print(f"Engine failed, the old scanner reads every company: {error}")
        return [], companies
    results, retry = [], set(unrecognized)
    for item in boards:
        if not item["ok"]:
            # e.g. Workday answering "too many requests": the old scanner opens far fewer pages.
            print(f"Engine could not read {item['company']} ({item['error'][:120]}); old scanner retries it")
            retry.update([item["company"]] + (item.get("also") or []))
            continue
        jobs = item["jobs"]
        matches = [dict(job, company=item["company"]) for job in jobs if keep(job, prefs, all_cities)]
        results.append((item["company"], True, {"count": len(jobs), "ids": [j["id"] for j in jobs]},
                        matches, ""))
    return results, [c for c in companies if c["name"] in retry]


def all_cities(job):
    """Workday jobs from the engine carry only their first city: read the full list."""
    if job.get("_extra", {}).get("api"):
        try:
            DETAILS["workday"](job, {})
        except Exception:
            pass  # keep the first city


def engine_reads_known_boards(boards, prefs):
    """Boards found by the old board finder that freehire's engine can also read (e.g. a
    Teamtailor site on the company's own address): read them with the engine and remove them
    from `boards`. Whatever the engine can't read stays in `boards` for the old scanner."""
    known = {}
    for key, (name, service, params) in boards.items():
        target = engine.engine_board(service, params)
        if target:
            known[name] = (key, target)
    if not known:
        return []
    rows = [{"name": name, "careers": "", "website": "", "source": source, "board": board}
            for name, (key, (source, board)) in known.items()]
    results, left = scan_with_engine(rows, prefs)
    left_names = {row["name"] for row in left}
    for name, (key, _) in known.items():
        if name not in left_names:
            del boards[key]
    return results


def keep(job, prefs, more_cities=None):
    """The rules every job must pass: wanted title, wanted place, not too old.
    more_cities(job) may fill in the full city list before the place is judged."""
    if not prefs.title_ok(job["title"]):
        return False
    if not prefs.location_ok(job["title"], job["location"]) and more_cities:
        more_cities(job)
    if not prefs.location_ok(job["title"], job["location"]):
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=prefs.max_age_days)
    return not (job["posted_at"] and board.parse_time(job["posted_at"]) < cutoff)


def find_boards(companies):
    """{(service, params as text): (company name, service, params)} plus companies without a board."""
    cache = read_cache("boards.json", {})
    now = datetime.now(timezone.utc)
    boards, not_found = {}, []
    for company in companies:
        found = None
        for link in (company["careers"], company["website"] if not company["careers"] else ""):
            found = found or (resolve.from_link(link) if link else None)
        if not found:
            key = f"{company['name']}|{company['careers']}|{company['website']}"
            cached = cache.get(key)
            fresh = cached and (cached["board"] or now - datetime.fromisoformat(cached["checked"])
                                < timedelta(days=RECHECK_NOT_FOUND_DAYS))
            if fresh:
                found = cached["board"]
            else:
                found = resolve.discover(company)
                cache[key] = {"board": found, "checked": now.isoformat()}
        if not found:
            not_found.append(company["name"])
            continue
        service, params = found
        board_key = service + json.dumps(params, sort_keys=True)
        boards.setdefault(board_key, (company["name"], service, params))  # same board twice: read once
    write_cache("boards.json", cache)
    return boards, not_found


def countries(prefs):
    """Country names among the user's locations ("Spain"), for sites read per country."""
    from .sources.enterprise import COUNTRY_CODES
    names = []
    for _, terms, remote in prefs.locations:
        for term in terms:
            if not remote and term.lower() in COUNTRY_CODES and term.title() not in names:
                names.append(term.title())
    return names


def scan_board(item, prefs, hints):
    """Read one board and keep the jobs that pass all rules.
    Returns (company, ok, {count, ids}, matches, error)."""
    _, (company, service, params) = item
    jobs, error = None, ""
    for attempt in range(2):  # one retry: most failures are a slow or busy server
        try:
            jobs = READERS[service](params, hints)
            break
        except Exception as problem:
            error = f"{type(problem).__name__}: {str(problem)[:150]}"
            time.sleep(3)
    if jobs is None:
        return company, False, {"count": 0, "ids": []}, [], error

    matches = []
    for job in jobs:
        if not prefs.title_ok(job["title"]):
            continue
        if service in DETAILS:  # only now open the job page: cheaper than for every job
            try:
                job = DETAILS[service](job, params)
            except Exception:
                pass  # keep the list data; the description is a nice-to-have
        if keep(job, prefs):
            job["company"] = company
            matches.append(job)
    return company, True, {"count": len(jobs), "ids": [job["id"] for job in jobs]}, matches, ""


def summary(companies, board_count, old_boards, jobs, failed, not_found, scanned, seconds):
    """Print the result and, on GitHub, show it on the run's summary page."""
    lines = [f"## JobScout scan",
             f"- {len(jobs)} matching jobs on the board",
             f"- {scanned} open jobs checked on {board_count - len(failed)} of {board_count} job boards "
             f"({len(companies)} companies) in {seconds:.0f} s",
             f"- {board_count - old_boards} boards read by freehire's engine, {old_boards} by the old scanner"]
    if failed:
        lines.append(f"\n### Job boards that did not answer ({len(failed)})")
        lines += [f"- {name}: {error}" for name, error in failed]
    if not_found:
        lines.append(f"\n### Companies without a job board found ({len(not_found)})")
        lines.append("Add the link of the page that lists their jobs in the Companies tab, column C.")
        lines += [f"- {name}" for name in not_found]
    text = "\n".join(lines)
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as file:
            file.write(text + "\n")


def read_cache(name, default):
    try:
        return json.loads((CACHE / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_cache(name, value):
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / name).write_text(json.dumps(value, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
