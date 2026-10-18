# JobScout + freehire - merge spec

Date: 2026-10-18. Status: agreed. Personal JobScout only.

## Why
freehire (github.com/strelov1/freehire, MIT, hosted at freehire.me) crawls company careers
pages at scale (294k companies, refreshed about every 2 hours) and offers a free public API
(no key, cross-origin, 600 requests/minute). It covers 159 of our 174 companies (our own
scanner: 156). We take its data and its proven ideas, and keep what is ours: the Google Sheet
as control panel, our matching rules, the server-less setup (GitHub Pages + Supabase),
Ask Claude, and private data.

## Data flow of a scan (decided: freehire first, our scanner as backup)
1. Read the sheet (unchanged).
2. Match each company to a freehire company (`/companies?q=<name>`, exact normalized name;
   cached). The scan summary lists companies without a match.
3. Jobs of matched companies: `/jobs/search?company_slug=a,b,c...` in batches (offset + limit
   <= 10000 per query), then OUR rules decide (titles, languages, places, remote scope, age).
4. Companies freehire does not have, or every company if the API fails: our own scanner
   (today's code), so the board never depends on freehire alone.
5. Discovery: jobs matching my roles and places at companies NOT in my sheet
   (`q` on titles + `cities` / `countries` / `regions` + `work_mode`, `posted_within_days`).
   Shown in their own "Discovery" column.
6. Job ids stay exactly as today (`greenhouse/adyen/8185712`, `workday/<tenant>/<site>/<path>` ...),
   rebuilt from the job's original URL, so hidden jobs and applications keep working.
   Jobs from sources we can't map get `freehire/<public_slug>`.

## Taken from freehire
- Fields per job: work mode (remote / hybrid / onsite), cities and countries, freshness
  (fresh / stale / likely evergreen = possible ghost job), posting language, requirements.
- Duplicate collapsing: one card per company + cleaned title + description (their
  "role fingerprint"), so one job posted in 5 cities is one card.
- CV match: their weighting (requirements 40, keywords 30, job title 20, seniority 10) and
  skills dictionary, replacing our 120-word list.
- Tracker (docs/TRACKER-SPEC.md): stages (applied, screening, interview, offer, accepted,
  rejected, withdrawn), "silent after N days" thresholds (applied 21, screening 18,
  interview 12, offer 5), Gmail rules (job-platform sender list, match by company name from
  sender name or subject, keyword verdicts: acknowledgement / screening / interview /
  assessment / offer / rejection), stages only move forward.

## Kept from JobScout
Sheet, rules (languages, "remote but not limited to another country"), static page on GitHub
Pages, Supabase login and sync, Ask Claude, the hourly GitHub Action.

## Removed when stable
Our company-board discovery code (`scout/resolve.py` discovery part) once freehire matching
covers it. Readers stay only as backup.

## Risks
- freehire is young (launched Aug 2026, mainly one maintainer). Backup scanner covers outages.
- Their data may lag up to ~2 hours behind the company page. Fine for an hourly board.

## Upstream
Ask freehire to add the companies they lack: Signaturit (careers.namirial.com, SuccessFactors),
Worldsensing (BambooHR), Ocado Technology, Paack (Teamtailor, careers.paack.co), Sesame HR.

## Phases (each = one issue and one pull request)
M1. freehire data source + backup + same ids; scan summary shows which source each company used.
M2. Discovery column.
M3. Work mode, freshness/ghost label, duplicate collapsing on the cards.
M4. Better CV match (weights + skills dictionary).
Tracker issues #6-#9 then follow, using the freehire tracker learnings above.
