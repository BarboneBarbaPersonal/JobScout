"""Checks that jobs read by freehire's engine keep JobScout's old ids. Run: python -m unittest"""

import unittest

from scout import engine


class JobIds(unittest.TestCase):
    def test_same_ids_as_before(self):
        cases = [
            ({"source": "greenhouse", "board": "adyen", "external_id": "8185712"}, "", "greenhouse/adyen/8185712"),
            ({"source": "ashby", "board": "perk", "external_id": "c3bb2b26"}, "", "ashby/perk/c3bb2b26"),
            ({"source": "workday", "board": "criteo.wd3.myworkdayjobs.com/Criteo_Career_Site",
              "external_id": "/job/Barcelona/Customer-Success-Manager_r21186"}, "",
             "workday/criteo/Criteo_Career_Site/job/Barcelona/Customer-Success-Manager_r21186"),
            ({"source": "personio", "board": "hornetsecurity", "external_id": "2799665"},
             "https://hornetsecurity.jobs.personio.de", "personio/hornetsecurity.jobs.personio.de/2799665"),
            ({"source": "personio", "board": "checkmk-gmbh", "external_id": "1"}, "https://checkmk.com",
             "personio/checkmk-gmbh.jobs.personio.com/1"),
        ]
        for item, link, expected in cases:
            self.assertEqual(engine.job_id(item, link), expected)

    def test_engine_job_becomes_jobscout_job(self):
        job = engine.to_job({"source": "greenhouse", "board": "adyen", "external_id": "1", "title": "Account  Manager",
                             "url": "https://job-boards.greenhouse.io/adyen/jobs/1?utm_source=freehire.me",
                             "location": "Madrid", "posted_at": "2026-10-01T10:00:00Z",
                             "description": "text", "work_mode": "hybrid"})
        self.assertEqual((job["id"], job["title"], job["url"], job["posted_at"], job["work_mode"]),
                         ("greenhouse/adyen/1", "Account Manager", "https://job-boards.greenhouse.io/adyen/jobs/1",
                          "2026-10-01T10:00:00Z", "hybrid"))


if __name__ == "__main__":
    unittest.main()
