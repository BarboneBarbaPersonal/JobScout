# JobScout Tracker - spec (Andrea's version only)

Date: 2026-10-17. Status: agreed. Applies only to `BarboneBarbaPersonal/JobScout`
plus its Supabase project. The shared JobScout-Template does not get it.

## Goal
One place to follow every application from "interesting" to "closed": the job board
plus a private Applications view, kept up to date with help from Gmail.

## Decisions (agreed 2026-10-17)
- Managed **inside the job board** (private view, only after logging in).
- Private data lives in **Supabase** (free Postgres database, decided 2026-10-17): email login
  on every device, row-level security so only Andrea can read or write, live sync.
  The public page and matches.json never contain it. The CV text is there too (table `profile`);
  the old jobscout-cv repo is archived after the one-time move.
- Tracks a job **only when Andrea actually applies**: an **"I applied"** button on each job card,
  plus "Add application" for jobs found elsewhere (LinkedIn, referral, recruiter).
- The slow Gemma CV analysis is removed. Each card instead shows the instant keyword match
  and an **"Ask Claude"** button that copies CV + job description as a ready prompt.
- Applications and hidden jobs are Supabase tables (replacing the Like issues and the
  "hidden jobs" issue). Existing hidden jobs are migrated.
- **Gmail is read automatically** to detect replies; reminders also by email.
  *Changed 2026-10-21:* Gmail is read on demand by a Claude skill with the Gmail connector,
  which proposes changes for Andrea to approve; reminders only on the board (see below).

## Stages
Applied -> Interviewing -> Offer -> Closed
Closed always has a reason: Rejected, Withdrawn, No answer, Accepted.

## One application = one row in the `applications` table
"I applied" creates one from a job card; "Add application" creates one for any link.
Fields:
- job: id (if scanned), link, company, title, location, source (scan / LinkedIn / referral / other)
- stage, closed reason
- applied date, CV version used (free text)
- contact person (name, email)
- next step + due date
- interviews: list of {date, type (screening / technical / panel / final), with, notes, outcome}
- offer: free text
- notes and a timeline (each stage change adds a dated line automatically).
Applications stay when the company closes the job posting.

## Board: Applications view (private)
- Columns per stage, cards show company, title, days in stage, next step (red when overdue).
- One tap to move a card; quick note; add interview; set next step.
- "Add application" form (link, company, title).
- Overview strip: applied, answered %, interviewing, offers, median days to first answer.

## Gmail check (on demand, Claude skill) - decided 2026-10-21
Replaces the earlier plan (daily GitHub Action reading Gmail with an app password). Idea taken
from MadsLorentzen/ai-job-search (`/gmail-sync`). Why: no Gmail password or Supabase service
key stored anywhere, nothing about emails can reach the public run logs, and nothing is
written without Andrea's yes.
- A skill `skills/gmail-check/SKILL.md`, run by Andrea in the Claude app ("check my
  applications"), with the **Gmail connector** (read only).
- Input: the board's "Check Gmail" button copies the open applications (company, role,
  stage, applied date) as the prompt, like "Fit my CV".
- Searches mail since the oldest open application, received only (not sent or drafts), by
  company name and job board senders (greenhouse, lever, ashby, workday, ...).
- Classifies each email: received / interview / assessment / rejection / offer / unclear.
- Proposes a list: application, suggested stage or next step, and the email it comes from
  (sender, date, subject). Unclear emails are listed, never guessed. An offer is flagged for
  Andrea's decision; accepting or declining is never inferred.
- Andrea applies the changes on the board (one click each). The skill writes nothing and
  sends nothing. Emails are never stored.

## Reminders
- Default follow-up: 7 days after Applied with no reply -> next step "Follow up" (done, T6).
- Interview: reminder the day before.
- Shown on the board (due / overdue). No reminder emails (they would need the app password).

## Way of working
Backlog = GitHub issues; one branch + pull request per issue, with tests and screenshots;
Andrea merges. Tests run automatically on every pull request.

## Phases
0. Simplify (agreed): clean-up (done), Supabase + login + migrate hidden jobs, Ask Claude instead of Gemma.
1. Pipeline: I applied button, stages, fields, Applications view, Add application.
2. Follow-ups: next step + due date, overdue highlight, default 7-day rule.
3. Gmail: on-demand skill that proposes stage changes for Andrea to approve.
4. Interviews + overview: rounds, day-before reminder, funnel numbers.

## Done means (each phase)
Tested on the real board with a test application, screenshots, and the private repo
data checked; nothing private appears in the public page or matches.json.

## Open questions
- Stage names OK as above?
- Follow-up after 7 days OK?
- Rejections: auto-close or suggest (spec says suggest)?
