"""Checks for the matching rules and link reading. Run: python -m unittest"""

import unittest

from scout import resolve
from scout.prefs import Preferences
from scout.sources.common import iso

# Example preferences (same shape as the Preferences tab).
SETTINGS = {
    "core roles": "customer success manager, csm, tam",
    "also interested in": "account manager",
    "exclude titles with": "intern, director",
    "languages i speak": "English, Spanish",
    "location 1 (best)": "Barcelona, Catalunya",
    "location 2": "Remote",
    "location 3": "Spain, Madrid",
    "remote must be open to": "Europe",
    "max job age (days)": "30",
}


class TitleRules(unittest.TestCase):
    def setUp(self):
        self.prefs = Preferences(SETTINGS)

    def test_wanted_roles(self):
        self.assertTrue(self.prefs.title_ok("Senior Customer Success Manager"))
        self.assertTrue(self.prefs.title_ok("TAM - Enterprise"))

    def test_whole_words_only(self):
        self.assertFalse(self.prefs.title_ok("Team Lead"))  # "tam" is not in "team"

    def test_excluded_words_and_languages(self):
        self.assertFalse(self.prefs.title_ok("Director, Customer Success Manager"))
        self.assertFalse(self.prefs.title_ok("CSM - German speaking"))
        self.assertFalse(self.prefs.title_ok("Account Manager DACH"))
        self.assertTrue(self.prefs.title_ok("CSM - Spanish speaking"))

    def test_role_type(self):
        self.assertEqual(self.prefs.role_type("CSM"), "core")
        self.assertEqual(self.prefs.role_type("Account Manager"), "also")


class LocationRules(unittest.TestCase):
    def setUp(self):
        self.prefs = Preferences(SETTINGS)

    def test_own_places(self):
        self.assertTrue(self.prefs.location_ok("CSM", "Barcelona, Spain"))
        self.assertTrue(self.prefs.location_ok("CSM", "Madrid"))
        self.assertFalse(self.prefs.location_ok("CSM", "Paris, France"))

    def test_remote_in_area(self):
        self.assertTrue(self.prefs.location_ok("CSM", "Remote"))
        self.assertTrue(self.prefs.location_ok("CSM", "Remote (EMEA)"))
        self.assertTrue(self.prefs.location_ok("CSM", "Remote - Spain"))

    def test_remote_elsewhere(self):
        self.assertFalse(self.prefs.location_ok("CSM", "Remote - Germany"))
        self.assertFalse(self.prefs.location_ok("CSM", "Remote, US"))
        self.assertFalse(self.prefs.location_ok("CSM, UK", "Remote"))

    def test_place_label_and_fit(self):
        self.assertEqual(self.prefs.place_label("Barcelona"), "Barcelona")
        self.assertEqual(self.prefs.place_label("Remote - Spain"), "Remote")
        self.assertEqual(self.prefs.fit_score("CSM", "Barcelona"), 3 * 2 + 2)
        self.assertEqual(self.prefs.fit_score("Account Manager", "Madrid"), 1 * 2 + 1)


class OtherUser(unittest.TestCase):
    def test_berlin_user_keeps_german_and_drops_spain(self):
        prefs = Preferences({**SETTINGS, "languages i speak": "English, German",
                             "location 1 (best)": "Berlin", "location 3": "Germany"})
        self.assertTrue(prefs.title_ok("CSM - German speaking"))
        self.assertFalse(prefs.title_ok("CSM - Spanish speaking"))
        self.assertTrue(prefs.location_ok("CSM", "Remote - Germany"))
        self.assertFalse(prefs.location_ok("CSM", "Remote - Spain"))


class Links(unittest.TestCase):
    def test_known_services(self):
        self.assertEqual(resolve.from_link("https://job-boards.greenhouse.io/stripe"),
                         ("greenhouse", {"board_token": "stripe"}))
        self.assertEqual(resolve.from_link("https://jobs.lever.co/spotify/abc"), ("lever", {"site": "spotify"}))
        self.assertEqual(resolve.from_link("https://criteo.wd3.myworkdayjobs.com/en-US/Criteo_Career_Site"),
                         ("workday", {"host": "criteo.wd3.myworkdayjobs.com", "tenant": "criteo",
                                      "site": "Criteo_Career_Site"}))
        self.assertIsNone(resolve.from_link("https://example.com/careers"))

    def test_found_board_must_carry_company_name(self):
        glovo = {"name": "Glovo (Delivery Hero)", "website": "https://glovoapp.com"}
        self.assertTrue(resolve._same_company(glovo, {"company_id": "glovo"}))
        remote = {"name": "Remote.com", "website": "https://remote.com"}
        self.assertFalse(resolve._same_company(remote, {"board_token": "mitratech"}))


class Dates(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(iso("2026-10-01T10:00:00Z"), "2026-10-01T10:00:00Z")
        self.assertEqual(iso(1790000000000), iso(1790000000))
        self.assertEqual(iso("Mon, 05 Oct 2026 10:00:00 +0200"), "2026-10-05T08:00:00Z")
        self.assertIsNone(iso("soon"))


if __name__ == "__main__":
    unittest.main()
