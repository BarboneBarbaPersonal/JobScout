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

    def test_library_has_a_fingerprint(self):
        self.assertRegex(self.page, r'supabase\.min\.js"\s+integrity="sha384-[A-Za-z0-9+/=]+"')


if __name__ == "__main__":
    unittest.main()
