"""Turn the Preferences tab into the rules a job must pass.

Every check here is plain whole-word matching (no AI): "tam" matches
"TAM - Spain" but not "Team Lead".
"""

import re

from . import places, util


class Preferences:
    def __init__(self, settings):
        """settings: {'setting name (lower case)': 'value'} from sheet.read_preferences."""
        self.page_title = settings.get("page title") or "My job board"
        self.core = util.split_list(settings.get("core roles"))
        self.also = util.split_list(settings.get("also interested in"))
        if not self.core and not self.also:
            raise ValueError("Preferences: fill in 'Core roles' (the job titles you want).")
        self.max_age_days = _number(settings.get("max job age (days)"), 30)

        # Locations, best first: "Location 1 (best)", "Location 2", ... (any number).
        rows = []
        for name, value in settings.items():
            found = re.fullmatch(r"location (\d+).*", name)
            if found and util.split_list(value):
                rows.append((int(found.group(1)), util.split_list(value)))
        self.locations = []  # [(label, terms, is_remote)]
        for _, terms in sorted(rows):
            is_remote = terms[0].lower() in places.REMOTE_WORDS
            self.locations.append((terms[0].title() if is_remote else terms[0],
                                   places.REMOTE_WORDS if is_remote else terms, is_remote))
        if not self.locations:
            raise ValueError("Preferences: fill in at least 'Location 1'.")

        # Words that are the user's own places: never a reason to drop a job.
        own_places = {term.lower() for _, terms, remote in self.locations if not remote for term in terms}

        # Title rule: wanted roles, minus excluded words and languages the user doesn't speak.
        spoken = set()
        for language in util.split_list(settings.get("languages i speak")):
            key = language.lower()
            spoken.add(places.LANGUAGE_ALIASES.get(key, key))
        language_words = set()
        if spoken:  # empty = no language filter
            for language, words in places.LANGUAGES.items():
                if language not in spoken:
                    language_words.update(words)
            # A market word for a spoken language ("spain" is not in any list) or an own place stays allowed.
            for language in spoken:
                language_words -= set(places.LANGUAGES.get(language, []))
            language_words -= own_places
        self.role_pattern = util.term_pattern(self.core + self.also)
        self.core_pattern = util.term_pattern(self.core)
        self.exclude_pattern = util.term_pattern(
            util.split_list(settings.get("exclude titles with")) + sorted(language_words))

        # Remote rule: a remote job naming a place outside the user's area is dropped.
        area = (settings.get("remote must be open to") or "europe").strip().lower()
        allowed_regions = set(places.AREA_REGIONS.get(area, []))
        other_regions = {r for rs in places.AREA_REGIONS.values() for r in rs} - allowed_regions
        self.remote_pattern = util.term_pattern(places.REMOTE_WORDS)
        self.elsewhere_pattern = util.term_pattern(
            [p for p in places.PLACES if p not in own_places] + sorted(other_regions))
        self.location_patterns = [(label, util.term_pattern(terms), remote)
                                  for label, terms, remote in self.locations]

    # ---- Title ----
    def title_ok(self, title):
        """True when the title names a wanted role and nothing excluded."""
        return (util.find_term(self.role_pattern, title) is not None
                and util.find_term(self.exclude_pattern, title) is None)

    def role_type(self, title):
        return "core" if util.find_term(self.core_pattern, title) else "also"

    # ---- Location ----
    def remote_ok(self, title, location):
        """Remote, and not limited to some place outside the user's area."""
        return (util.find_term(self.remote_pattern, location) is not None
                and util.find_term(self.elsewhere_pattern, location) is None
                and util.find_term(self.elsewhere_pattern, title) is None)

    def location_ok(self, title, location):
        for _, pattern, remote in self.location_patterns:
            if remote:
                if self.remote_ok(title, location):
                    return True
            elif util.find_term(pattern, location):
                return True
        return False

    def place_label(self, location):
        """The first (best) location row the job's location names, for the page."""
        for label, pattern, _ in self.location_patterns:
            if util.find_term(pattern, location):
                return label
        return "Other"

    def fit_score(self, title, location):
        """Location counts double (best row = most points), core role adds 2, other roles 1."""
        count = len(self.location_patterns)
        points = 0
        for index, (_, pattern, _) in enumerate(self.location_patterns):
            if util.find_term(pattern, location):
                points = count - index
                break
        return points * 2 + (2 if self.role_type(title) == "core" else 1)


def _number(value, default):
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default
