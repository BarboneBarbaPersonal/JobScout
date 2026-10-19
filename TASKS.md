# TASKS

The single task list for JobScout (Andrea's). Work top to bottom: always take the first
unchecked task that is not marked "waiting". Reorder by editing this file (a pull request).
Specs: `docs/MERGE-SPEC.md` (engine), `docs/TRACKER-SPEC.md` (applications).

**Standing prompt for any session or scheduled run:**
"Read CLAUDE.md, TASKS.md and the end of PROGRESS.md. Take the next unchecked task, create a
branch, implement it, run `python -m unittest`, test it on the real board or a test scan,
append to PROGRESS.md, and open a pull request with what changed and how it was verified.
Never push to main or merge."

## Now
- [x] **T1. Remote / hybrid / onsite label on job cards** (was #16)
  - Done when: cards show the label when the platform, the location or the description states
    it; test scan compared with the live board (same ids).
  - Decided: no switch of the location filters (identical results today) and no merging of
    duplicate cards (2 of 46 cards, near-copies only).

## Next
- [ ] **T2. Archive the old jobscout-cv repo** - waiting: Andrea opens the board once on the
  laptop that had "CV insights", so the CV moves to Supabase
  - Done when: Andrea confirms Log in > My CV shows the CV; jobscout-cv archived (read-only);
    the "CV add-on repo" row removed from the sheet.
- [x] **T3. Links menu on the board** (was #4)
  - After login: Task list, Scan runs, Changes to approve, Database, All my links (Notion).
  - Decided: no database table for links (would need another SQL step); the sheet stays
    reachable through the Notion page, never on the public page.
- [x] **T4. Small fixes** (was #5)
  - Short place codes (LA, PA, US, CA...) count only in capitals, so "la oficina" or
    "La Rioja" can't drop a remote job; CA added.
  - Dropped: Revolut "degraded" (it no longer fails: 156/156 boards OK) and removing unused
    reader settings (no visible benefit, risk of breaking the old readers).
- [ ] **T5. Tracker 1: "I applied" + Applications view** (was #6, TRACKER-SPEC phase 1) - in PR;
  last step waiting: Andrea tries it with a test application on laptop and phone, then removes it
  - Done when: "I applied" on a card creates an application in Supabase; Applications view
    with columns Applied / Interviewing / Offer / Closed; "Add application" for jobs found
    elsewhere; applications stay when the job closes; tested with a test application on
    laptop and phone, then removed.
- [x] **T6. Tracker 2: follow-ups** (was #7, phase 2)
  - Done when: next step + due date per application, overdue in red, default follow-up 7 days
    after applying; tested with a backdated test application.
- [ ] **T7. Skill: fit my CV to a job posting -> Google Doc** (was #20) - in PR; waiting:
  Andrea installs the skill (skills/fit-cv.zip) and runs it once from the board
  - Run by hand in the Claude app. Output: a Google Doc "<Company> - <Role> - CV" with the CV
    rewritten for the job (facts only, gaps marked) and a fit summary (1-10, strengths, gaps).
  - Decided 2026-10-19: the master CV lives on the board (Supabase); the board's "Fit my CV"
    button sends CV + job ad to the skill.
  - Done when: tested on 3 real jobs, the docs checked for invented facts.
- [ ] **T8. Skill: interview prep** (was #21)
  - Done when: a Google Doc with company, product, team, the story to tell, 3 questions;
    tested on one real interview or a realistic example.
- [ ] **T9. Tracker 3: Gmail** (was #8, phase 3)
  - Needs Andrea: a Gmail app password, pasted by him as a GitHub secret.
  - Done when: a daily check matches replies to applications by company, classifies them
    (received / interview / rejection...), suggests stage changes on the board; only sender,
    date, subject and verdict stored.
- [ ] **T10. Tracker 4: interviews + overview** (was #9, phase 4)
  - Done when: interview rounds per application, reminder the day before, funnel numbers.

- [ ] **T13. Delete the old repos** - waiting: Andrea (my GitHub login can't delete repos)
  - JobScout-legacy and jobscout-test-friend: each repo > Settings > bottom > Delete this repository.
  - Done when: both links answer "not found".

## Later
- [ ] **T11. Review on 2026-11-19: automate the skills?** (was #22) - waiting for the date
  - If T7/T8 were used weekly: plan one scheduled agent (drafts for new high-fit jobs,
    interview prep, morning brief). Otherwise drop.
- [ ] **T12. Suggest the Workday fix to freehire** (optional)
  - Their Workday adapter keeps only a job's first city (we read the rest ourselves).
    Draft an issue for Andrea to post.

## Done
- [x] Controlled workflow: CLAUDE.md, tests on every PR, protected main (#1)
- [x] Supabase: email login, hidden jobs synced on all devices (#2)
- [x] Instant CV match + Ask Claude, one login only (#3)
- [x] freehire's engine reads the boards, old scanner as backup (#14)
- [x] Engine reads 144 of 156 boards; Teamtailor ids kept (#15)
- Dropped: better CV match with skills dictionary (#17), merged into T7.
