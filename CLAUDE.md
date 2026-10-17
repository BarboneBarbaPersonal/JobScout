# JobScout (Andrea's personal job board)

Personal project only. The shareable version is `../JobScout-Template`: don't add personal
features (tracker, CV, Supabase) there. General rules live in `~/.claude/CLAUDE.md`.

## Commands
```bash
python -m unittest                          # must pass before any PR
SHEET_URL=<sheet link> python -m scout.main site   # full scan, page built into site/
```

## Rules that prevent mistakes
- **Workflow:** every change = GitHub issue -> branch -> pull request (what changed, how it was
  verified: tests + screenshot) -> Andrea merges. Never push to `main`, never merge a PR.
- **Public vs private:** this repo, the board page and `matches.json` are public. Never put the
  sheet link, applications, CV text, emails or keys in them. Private data lives in Supabase
  (once set up) and the private `jobscout-cv` repo. Secrets only as GitHub secrets.
- **Specs** in `docs/` (`TRACKER-SPEC.md` is the agreed plan). Update the spec when a decision changes.
- The page is plain HTML/JS with no build step.
- Job ids (`<source>/<board>/<id>`) must stay stable: hidden jobs and applications refer to them.
