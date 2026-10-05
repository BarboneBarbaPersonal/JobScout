# JobScout spec: board v2 (2026-10-05)

## 1. Stats bar (top of the page)
Shown on every page build, from the run log and the saved matches:
- Last successful scan (time) and run status
- Scans in the last 24 hours
- Jobs scanned (open postings across all boards) and boards OK (e.g. 129/129)
- New postings in the last scan and in the last 24 hours (all titles)
- Matches on the board: total, Barcelona / Remote / Spain, core / adjacent roles
- New matches in the last 24 hours

Run history is kept in `runs.json` on the `gh-pages` branch (last 500 runs).

## 2. Filters (on the page, no reload)
- Location: All / Barcelona / Remote / Spain
- Role type: All / Core (TAM, CSM, CSE, FDE, SDM...) / Adjacent (everything else)
Column counts update with the filters.

## 3. 30-day rule
- At scan time: a `recency` rule (max 30 days) is added to the matcher. Jobs
  without a posting date still pass.
- On the page: a job leaves the board when its posting date is over 30 days
  old, or (no posting date) 30 days after JobScout first found it.

## 4. Schedule
Cron twice an hour (:13 and :43). GitHub drops some scheduled runs, so this
should land close to one scan per hour.

## 5. More roles (adjacent)
Added to the title rule and the prefilter:
- Account / Client: account manager, client success, client partner, partner success, renewals manager
- Customer Ops / Experience: customer operations, customer experience, escalation manager, customer support manager

## 6. More companies
User adds companies to the Google Sheet; then re-run `jobscout/discover_ats.py`
and add the found boards to `jobscout.yaml`.

## 7. Language focus (scan rule)
Only Italian / English / Spanish speaking roles. Titles naming another
language ("French speaking", "German Speaking") or a market that needs one
("DACH", "Nordics", "Japan", "Benelux") are excluded in the title rule and
the prefilter. Titles only: descriptions often list languages as "nice to
have", so checking them would drop good jobs.

## 8. Rebuild after a full rescan
When the state is reset (bootstrap run), the board is rebuilt from that scan's
matches, so jobs that no longer pass the rules disappear. Jobs that match
again keep their original "found" date.
