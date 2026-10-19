# JobScout (Andrea's)

My personal job board: every hour it checks the careers pages of the companies in my
Google Sheet and publishes the jobs that fit my preferences.

## My links
| What | Where |
|---|---|
| Job board | https://barbonebarbapersonal.github.io/JobScout/ |
| Scan runs and their summary | https://github.com/BarboneBarbaPersonal/JobScout/actions |
| My settings sheet (companies, roles, places) | Private: linked in my Notion "Job Scout" page and saved here as the `SHEET_URL` secret |
| Private data (CV, hidden jobs, applications) | Supabase project `jobscout` (log in on the board) |

The shareable version for other people is a separate project:
https://github.com/BarboneBarbaPersonal/JobScout-Template

## How it works
- **freehire's crawling engine** (github.com/strelov1/freehire, MIT) reads the job boards:
  `engine/main.go` is built inside freehire at the commit in `engine/FREEHIRE_VERSION`.
  Companies it can't read go to the old readers in `scout/sources/`.
- `scout/` reads the sheet, keeps the jobs that pass my rules (`scout/prefs.py`) and builds
  the page (`scout/board.py`, `page/board.html`).
- `.github/workflows/scan.yml` runs it every hour and publishes to the `gh-pages` branch.

## Everyday changes
- Add a company or change roles/places: edit the sheet. The next hourly scan picks it up.
- A company shows up in the scan summary as "without a job board found": paste the link of
  its job list in column C of the Companies tab.

## Run it on my PC
```bash
pip install -r requirements.txt
python -m unittest
```
`SHEET_URL=<sheet link> python -m scout.main site` builds the page into `site/`.
