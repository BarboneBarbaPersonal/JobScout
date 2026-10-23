# Draft issue for strelov1/freehire (T12)

Andrea posts it at https://github.com/strelov1/freehire/issues/new (or asks Claude to post it).
Checked against freehire main b63b408 (2026-10-23): still open.

---

**Title:** Workday: jobs in several cities keep only the first one (`additionalLocations` ignored)

**Body:**

`internal/ingest/sources/workday.go` (`detail`) reads `jobPostingInfo.location` but not
`jobPostingInfo.additionalLocations`, so a Workday job open in several places is stored with
its first city only. Location filters then drop it for anyone searching the other places.

Example (live today): SUSE, "Premium Support Engineer"
`https://suse.wd3.myworkdayjobs.com/wday/cxs/suse/Jobsatsuse/job/Dusseldorf-Germany/Premium-Support-Engineer_71007818`
- `location`: "Dusseldorf, Germany"
- `additionalLocations`: ["Czech Republic, EMEA", "Bulgaria, EMEA", "Austria", "Spain, EMEA"]

freehire stores "Dusseldorf, Germany", so a search for Spain misses it.

Suggested fix: add `AdditionalLocations []string `json:"additionalLocations"`` to the detail
struct and join it into `Location` (e.g. `"; "`), and derive `Countries` from all of them.
The detail request is already made, so this costs no extra calls.

We work around it in our own runner by fetching the detail page again; happy to test a fix.
