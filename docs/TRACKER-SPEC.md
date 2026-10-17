# JobScout Tracker - spec (Andrea's version only)

Date: 2026-10-17. Status: agreed. Applies only to `BarboneBarbaPersonal/JobScout`
plus the private `BarboneBarbaPersonal/jobscout-cv`. The shared JobScout-Template does not get it.

## Goal
One place to follow every application from "interesting" to "closed": the job board
plus a private Applications view, kept up to date largely by reading Gmail.

## Decisions (agreed 2026-10-17)
- Managed **inside the job board** (private view, only when the CV key is connected).
- Data lives in the **private jobscout-cv repo**; the public page never contains it.
- Tracks a job **only when Andrea actually applies**: an **"I applied"** button on each job card,
  plus "Add application" for jobs found elsewhere (LinkedIn, referral, recruiter).
- The slow Gemma CV analysis is removed. Each card instead shows the instant keyword match
  and an **"Ask Claude"** button that copies CV + job description as a ready prompt.
- All private data (applications, hidden jobs) lives in **one file** in the private repo:
  `tracker.json` (no more issues). Devices connect once with a "connect this device" link.
- **Gmail is read automatically** to detect replies; reminders also by email.

## Stages
Applied -> Interviewing -> Offer -> Closed
Closed always has a reason: Rejected, Withdrawn, No answer, Accepted.

## One application = one entry in tracker.json
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

## Gmail check (daily, GitHub Actions in jobscout-cv)
- Reads new emails via IMAP with a **Gmail app password** stored as a secret in
  jobscout-cv (created and pasted by Andrea; never in code, never on the page).
- Matches an email to an application by company name / domain or job board sender
  (greenhouse, lever, ashby, workday, ...).
- Classifies by keywords, no AI: received ("thank you for applying"), rejection
  ("unfortunately", "not moving forward"), interview ("schedule", "availability",
  "interview"), assessment ("assignment", "test").
- Acts: received -> marks the application as confirmed; interview -> Interviewing + next step;
  rejection -> **suggests** Closed/Rejected (Andrea confirms on the board).
- Stores only sender, date, subject and the verdict. Never the email body.

## Reminders
- Default follow-up: 7 days after Applied with no reply -> next step "Follow up".
- Interview: reminder the day before.
- Delivered as one short daily email to Andrea (same app password), only on days
  with something due, and highlighted on the board.

## Phases
0. Simplify (agreed): clean-up, tracker.json + device link, Ask Claude instead of Gemma.
1. Pipeline: I applied button, stages, fields, Applications view, Add application.
2. Follow-ups: next step + due date, overdue highlight, default 7-day rule.
3. Gmail: daily read + classify + update/suggest; daily reminder email.
4. Interviews + overview: rounds, day-before reminder, funnel numbers.

## Done means (each phase)
Tested on the real board with a test application, screenshots, and the private repo
data checked; nothing private appears in the public page or matches.json.

## Open questions
- Stage names OK as above?
- Follow-up after 7 days OK?
- Rejections: auto-close or suggest (spec says suggest)?
