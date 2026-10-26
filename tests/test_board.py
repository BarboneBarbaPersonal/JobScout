"""Checks for the built board page: its security policy. Run: python -m unittest"""

import base64
import hashlib
import re
import tempfile
import unittest
from pathlib import Path

from scout import board
from scout.prefs import Preferences
from tests.test_rules import SETTINGS


class SalaryOnCards(unittest.TestCase):
    def test_platform_salary_first_then_the_ad(self):
        site = tempfile.mkdtemp()
        jobs = [{"id": "a/b/1", "title": "CSM", "url": "", "location": "Barcelona", "posted_at": None,
                 "description": "Salary: €40,000 - €50,000", "salary": "€45k–60k"},
                {"id": "a/b/2", "title": "CSM", "url": "", "location": "Barcelona", "posted_at": None,
                 "description": "Salary: €40,000 - €50,000"},
                {"id": "a/b/3", "title": "CSM", "url": "", "location": "Barcelona", "posted_at": None,
                 "description": "Great team"}]
        saved = board.build(site, Preferences(SETTINGS), jobs, {"status": "ok", "boards": 1, "boards_ok": 1,
                                                                "scanned": 3, "new_postings": 0})
        self.assertEqual([job["salary"] for job in saved], ["€45k–60k", "€40k–50k", ""])


class SecurityPolicy(unittest.TestCase):
    def setUp(self):
        site = tempfile.mkdtemp()
        board.build(site, Preferences(SETTINGS), [], {"status": "ok", "boards": 0, "boards_ok": 0,
                                                     "scanned": 0, "new_postings": 0})
        self.page = (Path(site) / "index.html").read_text(encoding="utf-8")

    def test_policy_allows_exactly_the_page_script(self):
        policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', self.page).group(1)
        script = re.search(r"<script>(.*?)</script>", self.page, re.S).group(1)
        digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode()
        self.assertIn(f"'sha256-{digest}'", policy)
        self.assertIn("default-src 'none'", policy)
        self.assertNotIn("unsafe-eval", policy)

    def test_page_talks_only_to_itself_and_supabase(self):
        # The one-time CV move from GitHub is over (jobscout-cv archived, key revoked).
        policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', self.page).group(1)
        self.assertNotIn("github", policy)
        self.assertNotIn("api.github.com", self.page)

    def test_library_has_a_fingerprint(self):
        self.assertRegex(self.page, r'supabase\.min\.js"\s+integrity="sha384-[A-Za-z0-9+/=]+"')


if __name__ == "__main__":
    unittest.main()
