# JobScout

Personal fork of [jobwatch](https://github.com/AkashKumar7902/jobwatch).
Every hour GitHub Actions polls the careers boards of my target companies and
publishes matching Customer Success / TAM / CSE / Forward Deployed Engineer /
Service Delivery Manager roles on a job board web page:

**https://barbonebarbapersonal.github.io/JobScout/**

The board has three columns: **New** (first seen in the last 48 hours),
**Best fit** (top 10: Barcelona > remote > Spain, core roles first) and
**Older**. It reloads itself every 30 minutes; "Hide" dismisses a job in that
browser. No email, no AI, no tokens: matching is keyword rules only.

## What is different from upstream

| File | Change |
|---|---|
| `jobscout.yaml` | My config: target companies, keyword rules on title and location, `jsonfile` notifier |
| `internal/notify/jsonfile.go` | New notifier: appends new matches to `new_matches.jsonl` (no email) |
| `jobscout/build_page.py`, `page_template.html` | Merge matches into `matches.json` and build the board page |
| `internal/source/teamtailor.go` | New source for Teamtailor career sites (reads `jobs.rss`) |
| `internal/source/source.go` | One line that registers the Teamtailor board identity |
| `internal/notify/email.go`, `rank.go` | Optional `rank` + `top` email params (email no longer used) |
| `.github/workflows/jobwatch.yml` | Hourly, no secrets, publishes the board to the `gh-pages` branch |
| `.github/workflows/dry-run.yml` | Manual test run: prints current matches, changes nothing |
| `jobscout/discover_ats.py` | Finds which job board each company uses |

## Changing what matches

Edit the `keywords` rules under `matcher:` in `jobscout.yaml`, then run
Actions -> **dry-run** to see the effect. The fit score and the board columns
are set at the top of `jobscout/build_page.py`.

## Adding companies

1. Put the company list in `jobscout/companies.csv` (export of the "Companies"
   tab of the target-companies sheet; this file is git-ignored).
2. `python jobscout/discover_ats.py`
3. Copy new lines from `jobscout/companies.found.yaml` into `jobscout.yaml`.
   `jobscout/companies.missing.csv` lists companies that need a manual look.

## Starting over

Delete the `state` branch and run Actions -> **jobwatch** with
**initialize_state** ticked: every job matching today goes onto the board.
The first run takes about 40 minutes (Workday boards are opened job by job);
hourly runs after that are short.

## Pulling upstream fixes

```bash
git fetch upstream
git merge upstream/main
```
