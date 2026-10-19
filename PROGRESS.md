# PROGRESS

Append-only log. Newest entry at the bottom. Each entry: date, task, what changed, how it was
verified, what is open or next. Read the last entries to know where things stand.

## 2026-10-13 - v2 of JobScout
- Rewrote JobScout as our own Python project (MIT), driven by the Google Sheet "JobScout -
  Andrea" (Preferences + Companies tabs, link stored as the SHEET_URL secret).
- Switched the live page to it (old Go fork renamed JobScout-legacy).
- Verified: side-by-side scans, same matches minus stale ones.

## 2026-10-15/16 - Shareable version split off
- JobScout-Template created as the simple public version (separate repo). This repo is
  personal only.

## 2026-10-17 - Simplify + controlled workflow
- Removed template leftovers; one sheet only; old local folders deleted.
- CLAUDE.md, tests on every PR, main protected (#1, PR #11).
- Supabase project `jobscout`: email login, hidden jobs synced across devices (#2, PR #12).
  Andrea created his user and turned sign-ups off.

## 2026-10-18/19 - Ask Claude, freehire engine
- Gemma analysis replaced by instant match + "Ask Claude"; CV in Supabase (`profile`),
  copied once from jobscout-cv on first visit (#3, PR #13). Andrea ran schema.sql.
- freehire's crawling engine runs inside the scan (pinned build + engine/main.go), old readers
  as backup and for 12 company-specific sites; same job ids (#14 PR #19, #15 PR #23).
  Verified: test scans vs live board, 46 of 46 jobs identical + new real finds; ~13.5 min/scan.
- Decisions: Discovery column dropped (needs freehire's catalogue); CV skill-dictionary match
  dropped; Allianz/Microsoft/IBM/SAP stay on old readers (worldwide crawl / unreadable).
- Repo normalized to Linux line endings (.gitattributes).

## 2026-10-19 - Tasks in files
- TASKS.md (single task list, replaces the GitHub issues and the Roadmap issue) and this
  PROGRESS.md added. Standing prompt in TASKS.md.
- Open: T1 (work-mode label) is in a PR waiting for merge; T2 waits for Andrea to open the
  board on the "CV insights" laptop.

## 2026-10-19 - T1 work-mode label
- Cards show remote / hybrid / onsite: from the platform field, then the location text, then
  the description (freehire's WorkModeFromDescription, added to engine/main.go).
- Dropped on purpose: location filters on the engine's reading (identical results today) and
  merging duplicate cards (2 of 46, only near-copies).
- Repo normalized to Linux line endings (.gitattributes); a CLAUDE.md conflict from that was
  resolved keeping the TASKS rule.
- Verified: tests pass; test scan from the branch: 156/156 boards, 47 matches, all 47 with the
  same ids as the live board; labels on 22 of 47 jobs (13 before).
- Next: T2 waits for Andrea (open the board on the "CV insights" laptop); then T3 links menu.

## 2026-10-19 - T3 links menu
- After login the account box shows "My links": Task list, Scan runs, Changes to approve,
  Database, All my links (Notion). The sheet link stays off the public page (it is in Notion).
- Fixed a bug from #2: the email login form stayed visible when logged in (a layout style beat
  the "hidden" attribute); now hidden elements are always hidden.
- Verified: tests pass; local page with the live jobs, simulated login: links only after login,
  correct addresses, login form hidden, fits phone width (screenshots).
- Next: T2 waits for Andrea; T4 small fixes.

## 2026-10-19 - T4 small fixes
- Short place codes (US, UK, CA, LA, PA, TX...) now count only in capitals; before, "la", "pa",
  "us" as ordinary words could wrongly drop a remote job. CA (California/Canada) was missing.
- Dropped two T4 items (see TASKS.md) after checking they no longer matter.
- Verified: test written first (failed), now 18 tests pass; all 46 live jobs still pass the
  rules; test scan from the branch: 47 of 47 jobs identical to the live board (preventive fix).
- Next: T2 waits for Andrea; then T5 tracker 1 ("I applied" + Applications view).

## 2026-10-19 - T5 tracker 1
- After login: "I applied" on each job card (creates an application in Supabase; the card
  then shows "applied"); "My applications (N)" switches the page to 4 columns (Applied,
  Interviewing, Offer, Closed) with a stage dropdown (Closed asks the reason), notes, Remove,
  and a dated history; "Add application" form for jobs found elsewhere (LinkedIn, referral,
  recruiter, other). Live sync to other devices. No database change needed (table from #2).
- Verified: tests pass; local page with the live jobs and a pretend in-memory database: apply,
  move to Interviewing, notes, add by hand, close as rejected, remove, back to the board; phone
  width without sideways scrolling (screenshots).
- Not verified yet: the real database (needs Andrea's login). Andrea: try one test
  application on laptop and phone, then Remove it.
- Next: T6 follow-ups.
