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
