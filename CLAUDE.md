# JobScout (Andrea's personal job board)

Personal project only. The shareable version is `../JobScout-Template`: don't add personal
features (tracker, CV, Supabase) there. General rules live in `~/.claude/CLAUDE.md`.

## Commands
```bash
python -m unittest                          # must pass before any PR
SHEET_URL=<sheet link> python -m scout.main site   # full scan, page built into site/
```

## Rules that prevent mistakes
- **State lives in files, not in the conversation:** `TASKS.md` is the only task list (take the
  first unchecked task); append an entry to `PROGRESS.md` before every pull request. A new
  session or a scheduled run starts from these two files.
- **Workflow:** every change = task in TASKS.md -> branch -> pull request (what changed, how it
  was verified: tests + screenshot) -> Andrea merges. Never push to `main`, never merge a PR.
- **Public vs private:** this repo, the board page and `matches.json` are public. Never put the
  sheet link, applications, CV text, emails or keys in them. Private data (CV, hidden jobs,
  applications) lives only in Supabase (`supabase/schema.sql`). Secrets only as GitHub secrets.
- **Specs** in `docs/` (`TRACKER-SPEC.md` is the agreed plan). Update the spec when a decision changes.
- The page is plain HTML/JS with no build step.
- Job ids (`<source>/<board>/<id>`) must stay stable: hidden jobs and applications refer to them.
