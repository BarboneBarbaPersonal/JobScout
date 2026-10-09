# JobScout spec: board v2 (2026-10-05)

## 1. Stats bar (top of the page)
Shown on every page build, from the run log and the saved matches:
- Last successful scan (time) and run status
- Scans in the last 24 hours
- Jobs scanned (open postings across all boards) and boards OK (e.g. 129/129)
- New postings in the last scan and in the last 24 hours (all titles)
- Matches on the board: total, Barcelona / Remote / Spain, core / adjacent roles
- New matches in the last 24 hours

Run history is kept in `runs.json` on the `gh-pages` branch (last 500 runs).

## 2. Filters (on the page, no reload)
- Location: All / Barcelona / Remote / Spain
- Role type: All / Core (TAM, CSM, CSE, FDE, SDM...) / Adjacent (everything else)
Column counts update with the filters.

## 3. 30-day rule
- At scan time: a `recency` rule (max 30 days) is added to the matcher. Jobs
  without a posting date still pass.
- On the page: a job leaves the board when its posting date is over 30 days
  old, or (no posting date) 30 days after JobScout first found it.

## 4. Schedule
Cron twice an hour (:13 and :43). GitHub drops some scheduled runs, so this
should land close to one scan per hour.

## 5. More roles (adjacent)
Added to the title rule and the prefilter:
- Account / Client: account manager, client success, client partner, partner success, renewals manager
- Customer Ops / Experience: customer operations, customer experience, escalation manager, customer support manager

## 6. More companies
User adds companies to the Google Sheet; then re-run `jobscout/discover_ats.py`
and add the found boards to `jobscout.yaml`.

## 7. Language focus (scan rule)
Only Italian / English / Spanish speaking roles. Titles naming another
language ("French speaking", "German Speaking") or a market that needs one
("DACH", "Nordics", "Japan", "Benelux") are excluded in the title rule and
the prefilter. Titles only: descriptions often list languages as "nice to
have", so checking them would drop good jobs.

## 8. Rebuild after a full rescan
When the state is reset (bootstrap run), the board is rebuilt from that scan's
matches, so jobs that no longer pass the rules disappear. Jobs that match
again keep their original "found" date.

---

# v3 (2026-10-08): CV proposals

## 9. Market search -- DROPPED (2026-10-08)
Adzuna was considered (free key, personal use allowed) and dropped by the user.
Coverage grows by adding more companies to the Google Sheet instead.

## 10. Like -> CV proposals (private repo `jobscout-cv`)
- Each card gets a **Like** button. It opens a pre-filled new issue in the private
  repo `BarboneBarbaPersonal/jobscout-cv` (title = company + job title, body = job link + JobScout id).
  Nothing about liked jobs or the CV is ever stored in the public JobScout repo.
- `jobscout-cv` holds the master CV as text plus 2-3 base versions (e.g. CSM/TAM, FDE/technical).
- A workflow runs on every new issue:
  1. fetch the job description from the link;
  2. **keyword gap (no AI)**: important terms in the job description missing from the CV;
  3. **Gemma 3 4B via Ollama** on the runner (free, no key): pick the best base version and
     write 3-5 concrete edits (keyword to add, bullet to reword or move up, summary line), plus a fit score;
  4. post the result as a comment on the issue (visible in the GitHub app).
- For important jobs the user asks Claude in a session for a polished version (on request only).
- Later option: run a bigger Gemma on the user's PC (32 GB+ RAM) for higher-quality proposals.

## Needs from the user
- OK to create the private repo `jobscout-cv` and store the CV text there.

---

# v4 (2026-10-09): CV insights inside the dashboard (no GitHub visits, no emails)

## 11. Private access key (per device)
- Dashboard settings: the user pastes a fine-grained GitHub token limited to the private
  repo `jobscout-cv` (Contents: read, Issues: read and write). Stored only in that
  browser's localStorage. Without a key the page looks and works as before (public view).
- With the key the page reads private data straight from `jobscout-cv` via the GitHub API.
  Nothing CV-related is ever written to the public JobScout repo or page.

## 12. Draft for every job (in the browser, no AI)
- The page loads `cv/master.md` and `data/vocabulary.json` from `jobscout-cv` and each job's
  description from the public `matches.json`.
- Each card shows: **match %** (share of the job's important terms found in the CV) and the
  top missing keywords.

## 13. Like -> proposals in the dashboard
- Like creates an issue in `jobscout-cv` through the API (no GitHub page opened).
- The `analyze` workflow (triggered by the new issue) writes `results/<job>.json`:
  1. main missing keywords (no AI);
  2. intro rewrite: 2-3 sentences for the Professional Summary (Gemma 3 4B), fact-checked;
  3. past roles: CV bullets ranked by relevance to the job (no AI): 2 to lead with, 2 to
     shorten; plus up to 3 short Gemma flags on big changes.
- No issue comments (so no notification emails). The card shows "Analyzing..." and then a
  **Proposals** panel, polling the results file every 30 s while open.
- Deeper edits: "CV edits for jobscout-cv issue #N" to Claude in a session (unchanged).
