# JobScout + freehire engine - merge spec

Date: 2026-10-18. Status: agreed. Personal JobScout only.

## Decision
freehire (github.com/strelov1/freehire, MIT) has a crawling engine with adapters for about
90 job board platforms (565 source files), plus location, skills and seniority dictionaries.
We run **that engine inside JobScout**. Nothing depends on the freehire.me website.

The mechanism stays ours: my Google Sheet lists the companies and the filters (roles,
languages, Barcelona / Remote / Spain ...); every hour a GitHub Action crawls exactly those
companies and publishes my board; private data stays in Supabase.

## How the engine is included (no copy of their code in this repo)
- `engine/main.go` (ours, ~150 lines): the "JobScout runner". It reads a list of boards
  (company, platform, board), runs freehire's adapters, and writes the jobs as JSON with
  freehire's reading of each location (cities, countries, regions, work mode) and skills.
- `engine/FREEHIRE_VERSION`: the freehire commit we build against (pinned).
- The scan workflow downloads freehire at that commit, drops the runner in as
  `cmd/jobscout-scan`, builds it (about 30 seconds, cached) and runs it.
- Updating the engine = changing the pinned commit in a pull request (tests run on it).
- Go is a second language in the project, but only inside the scan; nothing to install.

Prototype (2026-10-18): Adyen (Greenhouse), Criteo (Workday), Perk (Ashby): 457 jobs in about
5 seconds including Workday descriptions; locations read as cities + countries; native ids
identical to ours.

## Data flow of a scan
1. Read the sheet (unchanged).
2. Careers link -> platform + board with freehire's URL recognizer (`atsboard`), which knows
   many more platforms than our `resolve.py`. Links it can't recognize: freehire's page
   detection, then our old discovery as a last resort; listed in the scan summary.
3. The runner crawls all boards in parallel.
4. Python applies MY rules (titles, excluded words, spoken languages, places, remote scope,
   max age), now using the engine's cities / countries / work mode instead of our hand-made
   place lists.
5. Job ids stay exactly as today (`<platform>/<board>/<id>`), so hidden jobs and applications
   keep working.
6. Board page built as today.

## Taken from freehire
- Adapters for all platforms (replaces our 24 readers and most of `resolve.py`).
- Location reading: cities, countries, regions, remote / hybrid / onsite, and "remote but
  only for US/EU/UK..." phrases (replaces `scout/places.py` lists where better).
- Duplicate collapsing: one card per company + cleaned title + description.
- Skills tagging and their CV match weighting (requirements 40, keywords 30, title 20,
  seniority 10) for the match %.
- Tracker learnings for docs/TRACKER-SPEC.md: stages, "silent after N days" thresholds
  (applied 21, screening 18, interview 12, offer 5), Gmail rules (job-platform sender list,
  match by company name, keyword verdicts), stages only move forward.

## Dropped
- The freehire.me website/API as a data source, and the "Discovery" column (it needed
  freehire's global catalogue; the engine only crawls my companies).
- Our readers and discovery code, once the engine has run cleanly for a few days.

## Phases (each = one issue and one pull request)
E1 (#14). Engine runner + pinned build in the scan; same ids; old scanner kept as fallback;
    compare both boards on the same day.
E2 (#15). Careers links recognized by freehire's `atsboard`; summary of unrecognized links.
E3 (#16). Filters on the engine's location reading; work mode on cards; duplicate collapsing.
E4 (#17). Better CV match (skills tagging + weighting).
Then: remove the old readers; tracker issues #6-#9.
