"""
Build the JobScout job board web page.

Inputs:
  new_matches.jsonl      new matches from this run (written by the jsonfile notifier)
  <site>/matches.json    every match seen so far (kept on the gh-pages branch)

Outputs:
  <site>/matches.json    updated list
  <site>/index.html      the board: New / Best fit / Older

Run:  python jobscout/build_page.py new_matches.jsonl site
"""

import html
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

NEW_FOR_HOURS = 48     # a job counts as "New" for this long after we first saw it
FORGET_AFTER_DAYS = 45 # jobs older than this drop off the board (likely closed)
BEST_FIT_COUNT = 10

# Location preference: earlier = better. First term found in the location wins.
LOCATION_TIERS = [
    (3, "Barcelona", ["barcelona", "catalunya", "cataluña", "catalonia"]),
    (2, "Remote", ["remote", "distributed", "worldwide", "anywhere", "home based"]),
    (1, "Spain", ["spain", "españa", "espana", "madrid"]),
]
# Role preference: core target roles score higher than adjacent ones.
CORE_ROLES = ["technical account manager", "tam", "customer success manager", "csm",
              "customer success engineer", "cse", "forward deployed", "fde",
              "service delivery manager", "sdm", "csam", "customer success architect"]
ADJACENT_ROLES = ["customer success", "implementation", "onboarding", "engagement manager",
                  "customer engineer", "service delivery"]


def has_word(text, term):
    """Whole-word, case-insensitive check ("tam" must not match "team")."""
    text = f" {text.lower()} "
    for separator in ",;:()[]/|-–—.":
        text = text.replace(separator, " ")
    return f" {term} " in text


def location_tier(location):
    for score, label, terms in LOCATION_TIERS:
        if any(has_word(location, term) for term in terms):
            return score, label
    return 0, "Other"


def role_score(title):
    if any(has_word(title, role) for role in CORE_ROLES):
        return 2
    if any(has_word(title, role) for role in ADJACENT_ROLES):
        return 1
    return 0


def fit_score(job):
    """0-8: location counts double, because where matters most to me."""
    location_points, _ = location_tier(job["location"])
    return location_points * 2 + role_score(job["title"])


def load_jobs(site):
    path = site / "matches.json"
    if path.exists():
        return {job["id"]: job for job in json.loads(path.read_text(encoding="utf-8"))}
    return {}


def merge_new(jobs, new_matches_path):
    """Add this run's matches. A job we already know keeps its first found_at."""
    if not new_matches_path.exists():
        return
    for line in new_matches_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            job = json.loads(line)
            jobs.setdefault(job["id"], job)


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def job_card(job, now):
    _, place = location_tier(job["location"])
    score = fit_score(job)
    found = parse_time(job["found_at"])
    age_days = (now - found).days
    age_text = "today" if age_days == 0 else f"{age_days}d ago"
    return f"""
      <article class="card" data-id="{html.escape(job['id'])}">
        <div class="top">
          <span class="company">{html.escape(job['company'])}</span>
          <span class="fit fit{min(score, 8) // 3}" title="Fit score {score}/8">fit {score}</span>
        </div>
        <a class="title" href="{html.escape(job['url'])}" target="_blank" rel="noopener">{html.escape(job['title'])}</a>
        <div class="meta"><span class="place p-{place.lower()}">{place}</span> {html.escape(job['location'])}</div>
        <div class="bottom"><span>found {age_text}</span><button class="hide" type="button">Hide</button></div>
      </article>"""


def column(title, note, jobs, now):
    cards = "".join(job_card(job, now) for job in jobs) or '<p class="empty">Nothing here yet.</p>'
    return f"""
    <section class="column">
      <h2>{title} <span class="count">{len(jobs)}</span></h2>
      <p class="note">{note}</p>
      {cards}
    </section>"""


def build_html(jobs, now):
    by_fit = lambda job: (-fit_score(job), job["found_at"])
    new_jobs = sorted([j for j in jobs if now - parse_time(j["found_at"]) < timedelta(hours=NEW_FOR_HOURS)], key=by_fit)
    best_fit = sorted(jobs, key=by_fit)[:BEST_FIT_COUNT]
    best_ids = {j["id"] for j in best_fit}
    new_ids = {j["id"] for j in new_jobs}
    older = sorted([j for j in jobs if j["id"] not in new_ids and j["id"] not in best_ids], key=by_fit)

    updated = now.strftime("%d %b %Y, %H:%M UTC")
    template = (Path(__file__).parent / "page_template.html").read_text(encoding="utf-8")
    return (template
            .replace("{{UPDATED}}", updated)
            .replace("{{TOTAL}}", str(len(jobs)))
            .replace("{{COLUMNS}}",
                     column("New", f"First seen in the last {NEW_FOR_HOURS} hours", new_jobs, now)
                     + column("Best fit", "Barcelona &gt; remote &gt; Spain, core roles first", best_fit, now)
                     + column("Older", f"Still on the board (dropped after {FORGET_AFTER_DAYS} days)", older, now)))


def main():
    new_matches_path, site = Path(sys.argv[1]), Path(sys.argv[2])
    site.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    jobs = load_jobs(site)
    merge_new(jobs, new_matches_path)
    # Forget jobs we first saw long ago -- most of them are closed by now.
    cutoff = now - timedelta(days=FORGET_AFTER_DAYS)
    kept = [job for job in jobs.values() if parse_time(job["found_at"]) >= cutoff]

    (site / "matches.json").write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    (site / "index.html").write_text(build_html(kept, now), encoding="utf-8")
    print(f"board: {len(kept)} jobs")


if __name__ == "__main__":
    main()
