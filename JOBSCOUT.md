# JobScout

Personal fork of [jobwatch](https://github.com/AkashKumar7902/jobwatch).
Every 30 minutes GitHub Actions polls the careers boards of my target
companies and emails me new Customer Success / TAM / CSE roles in
Barcelona, Spain or remote Europe. No AI and no tokens: matching is keyword
rules only.

## What is different from upstream

| File | Change |
|---|---|
| `jobscout.yaml` | My config: target companies, keyword rules on title and location, Gmail notifier |
| `internal/source/teamtailor.go` | New source for Teamtailor career sites (reads `jobs.rss`) |
| `internal/source/source.go` | One line that registers the Teamtailor board identity |
| `.github/workflows/jobwatch.yml` | Uses `jobscout.yaml`, no LLM key |
| `.github/workflows/dry-run.yml` | Manual test run: prints current matches, sends nothing |
| `jobscout/discover_ats.py` | Finds which job board each company uses |

## One-time setup

1. Create a Gmail app password (needs 2-Step Verification): https://myaccount.google.com/apppasswords
2. Add three repository secrets (Settings -> Secrets and variables -> Actions):
   - `JOBWATCH_SMTP_USERNAME`: the Gmail address that sends the alerts
   - `JOBWATCH_SMTP_PASSWORD`: the app password from step 1
   - `JOBWATCH_EMAIL_TO`: where the alerts go
3. Actions tab -> enable workflows (forks start with Actions disabled).
4. Actions -> **dry-run** -> Run workflow. Check the log: are these the roles you want?
5. Actions -> **jobwatch** -> Run workflow with **initialize_state** ticked.
   This records every job that is open today *without* emailing them.
6. From now on the schedule emails only newly posted matches.

## Changing what matches

Edit the two `keywords` rules under `matcher:` in `jobscout.yaml`, then run
**dry-run** again to see the effect.

## Adding companies

1. Put the company list in `jobscout/companies.csv` (export of the "Companies"
   tab of the target-companies sheet; this file is git-ignored).
2. `python jobscout/discover_ats.py`
3. Copy new lines from `jobscout/companies.found.yaml` into `jobscout.yaml`.
   `jobscout/companies.missing.csv` lists companies that need a manual look.

New boards are seeded automatically on their first run (no email flood).

## Pulling upstream fixes

```bash
git fetch upstream
git merge upstream/main
```
