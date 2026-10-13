# JobScout (v2, our own code) - spec

Date: 2026-10-13. Replaces the jobwatch fork (no license) with our own, MIT-licensed code.

## Goal
Anyone can get a personal job board by sharing **one Google Sheet** with two tabs:
- **Preferences** - what jobs I want (roles, exclusions, languages, locations, age).
- **Companies** - which companies to watch (name, website, optional careers link).

The app scans those companies' career sites every hour (GitHub Actions, free on a
public repo), keeps the jobs that fit the preferences, and publishes a job board page
(GitHub Pages). No AI, no API keys, no paid services.

## Users and setup (non-technical, browser only)
1. Make a copy of the template Google Sheet, fill both tabs, share it as
   "Anyone with the link: Viewer".
2. On GitHub: "Use this template" -> new public repo.
3. Settings -> Secrets and variables -> Actions -> New secret `SHEET_URL` = the sheet link.
   (A secret, not a file: the repo is public, a file would show the link to everyone.)
4. Settings -> Pages -> deploy from branch `gh-pages`; Actions -> enable; run "Scan" once.
5. Page: `https://<user>.github.io/<repo>/`.

## The Google Sheet
### Tab "Preferences" (one setting per row: Setting | Value | Help)
| Setting | Example |
|---|---|
| Page title | Andrea's job board |
| Core roles | technical account manager, customer success manager, forward deployed engineer, ... |
| Also interested in | account manager, implementation manager, onboarding specialist, ... |
| Exclude titles with | intern, director, vp, solutions engineer, ... |
| Languages I speak | English, Spanish, Italian |
| Location 1 (best) | Barcelona, Catalunya, Catalonia |
| Location 2 | Remote |
| Location 3 | Spain, Madrid, Valencia, España |
| Remote must be open to | Europe (Europe / Worldwide / Anywhere) |
| Max job age (days) | 30 |
| CV add-on repo (optional, not in the template) | BarboneBarbaPersonal/jobscout-cv |
Each location row: the first word is the label, the rest are other names that count.
"Remote" is special: remote roles that name a country/region outside the chosen area
are dropped (built-in list of countries and big cities).

### Tab "Companies" (Company | Website | Careers page link | Notes)
- Careers page link is optional; when given it is used directly (most reliable).
- Otherwise the app finds the job board from the website (cached between runs).

## How a run works (full scan, no "already seen" state)
1. Read the sheet (CSV export of each tab; needs link sharing).
2. For each company: resolve its job board (careers link -> board, else cached
   discovery, else discover from website).
3. Fetch all open jobs from each board (parallel). Title rule first; only jobs passing
   the title rule get their detail page fetched when a board needs it (Workday).
4. Keep jobs that pass: title (core/also, minus excludes), language, location
   (location 1/2/3 or remote-in-area), max age.
5. Board = this run's matches; a job keeps its first "found" date from the previous
   board. Closed jobs disappear immediately.
6. Publish `index.html`, `matches.json`, `runs.json` to `gh-pages`. The board cache
   (company -> job board) stays in GitHub's build cache, never on the public page, so
   the full company list and the preferences are not published.

## Job board readers (our own code, `scout/sources/`)
Generic ATS: greenhouse, lever, ashby, workable, smartrecruiters, recruitee, bamboohr,
workday, teamtailor, personio, comeet, recruiterflow, factorial, hibob, phenom,
successfactors, eightfold, page links (generic).
Company-specific: atlassian, dynatrace, deel, ibm, revolut (blocked from GitHub's
servers by a bot check - documented as a known limitation).

## Setup guide page (`page/setup.html`)
Published next to `index.html` and linked from the board header ("Get your own JobScout"),
so anyone a user shares their board with finds the setup. Step cards with ticks
(progress kept in the browser), template sheet "Make a copy" link, "Use this template"
link, direct links into the user's own repo built from their GitHub username, and a
"Check my sheet" button that reads both tabs from the browser. The README just links here.

## Page (from today's dashboard)
Stats bar, Location and Role filters (Core / Also / ...), New / Best fit / Older
columns, Hide (shared via CV add-on when connected), Like + CV insights (optional add-on).

## Licensing
MIT. No code copied from jobwatch; public job-board APIs and page formats are facts.

## Switch-over
Build in repo `jobscout-next`; run side by side with the current JobScout and compare
matches. When equal or better: rename old repo to `JobScout-legacy`, rename the new
one to `JobScout` (same page URL), move the board data, update the CV add-on.

## Out of scope (now)
Email notifications, AI in the scanner, LinkedIn/Indeed.
