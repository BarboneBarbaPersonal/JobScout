"""Thursday's deep scan: older jobs kept apart until the next deep scan. Run: python -m unittest"""

import json
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scout import board, main
from scout.prefs import Preferences
from tests.test_rules import SETTINGS

RUN = {"status": "ok", "boards": 1, "boards_ok": 1, "scanned": 2, "new_postings": 0}


def posted(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def job(id, days_ago):
    return {"id": id, "title": "Customer Success Manager", "url": "", "location": "Barcelona",
            "posted_at": posted(days_ago), "description": ""}


class DeepScan(unittest.TestCase):
    def setUp(self):
        self.prefs = Preferences(SETTINGS)  # max job age 30 days

    def test_hourly_scan_drops_old_jobs(self):
        self.assertFalse(main.keep(job("a/b/1", 45), self.prefs))

    def test_deep_scan_keeps_old_jobs_and_marks_them(self):
        old = job("a/b/1", 45)
        self.assertTrue(main.keep(old, self.prefs, deep=True))
        self.assertTrue(old["deep"])
        recent = job("a/b/2", 3)
        self.assertTrue(main.keep(recent, self.prefs, deep=True))
        self.assertNotIn("deep", recent)

    def test_hourly_scan_carries_deep_jobs_while_still_open(self):
        previous = [dict(job("a/b/1", 45), deep=True, company="X"),
                    dict(job("a/b/2", 50), deep=True, company="X"),   # closed since Thursday
                    dict(job("a/b/3", 40), deep=True, company="X")]   # already a normal match
        carried = main.carry_deep(previous, open_ids={"a/b/1", "a/b/3"}, current_ids={"a/b/3"},
                                  prefs=self.prefs)
        self.assertEqual([j["id"] for j in carried], ["a/b/1"])

    def test_board_saves_deep_jobs(self):
        site = tempfile.mkdtemp()
        jobs = [dict(job("a/b/1", 45), deep=True, company="X"), dict(job("a/b/2", 3), company="X")]
        board.build(site, self.prefs, jobs, RUN)
        saved = json.loads((Path(site) / "deep.json").read_text(encoding="utf-8"))
        self.assertEqual([j["id"] for j in saved], ["a/b/1"])


class WorkdayCities(unittest.TestCase):
    """Workday jobs from the engine carry only their first city; the full list costs one request
    per job. Since 2026-11-16 those requests made every scan run past GitHub's 55 minutes."""

    def setUp(self):
        self.prefs = Preferences(SETTINGS)
        self.opened = []
        self.real = main.DETAILS["workday"]
        main.DETAILS["workday"] = self.fake_detail

    def tearDown(self):
        main.DETAILS["workday"] = self.real

    def fake_detail(self, job, params):
        self.opened.append(job["id"])
        job["location"] = "Paris; Barcelona"
        return job

    def workday_job(self, id, title="Customer Success Manager"):
        return dict(job(id, 3), location="Paris", _extra={"api": "https://x/" + id}, title=title)

    def test_full_city_list_is_read_for_wanted_titles_only(self):
        jobs = [self.workday_job("w/1"), self.workday_job("w/2", title="Software Engineer")]
        main.fill_cities(jobs, self.prefs, deadline=time.time() + 60)
        self.assertEqual(self.opened, ["w/1"])
        self.assertEqual(jobs[0]["location"], "Paris; Barcelona")

    def test_after_the_time_budget_jobs_keep_their_first_city(self):
        jobs = [self.workday_job("w/1")]
        main.fill_cities(jobs, self.prefs, deadline=time.time() - 1)
        self.assertEqual(self.opened, [])
        self.assertEqual(jobs[0]["location"], "Paris")


if __name__ == "__main__":
    unittest.main()
