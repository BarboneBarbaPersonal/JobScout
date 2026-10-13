"""Read the user's Google Sheet: the "Preferences" and "Companies" tabs.

The sheet must be shared as "Anyone with the link: Viewer". Each tab is
downloaded as CSV through Google's export address - no login, no API key.
For local testing, `source` can also be a folder holding Preferences.csv and
Companies.csv.
"""

import csv
import io
import os
import re
from urllib.parse import quote

from . import util


def tab_rows(source, tab):
    """All rows of one tab as lists of strings."""
    if os.path.isdir(source):
        with open(os.path.join(source, f"{tab}.csv"), encoding="utf-8") as file:
            return list(csv.reader(file))
    match = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", source)
    if not match:
        raise ValueError("SHEET_URL does not look like a Google Sheets link")
    url = (f"https://docs.google.com/spreadsheets/d/{match.group(1)}"
           f"/gviz/tq?tqx=out:csv&headers=1&sheet={quote(tab)}")
    try:
        response = util.get(url)
    except Exception:
        response = None
    if response is None or "text/csv" not in response.headers.get("Content-Type", ""):
        raise ValueError("Is it shared as 'Anyone with the link: Viewer'?")
    return list(csv.reader(io.StringIO(response.content.decode("utf-8"))))


def read_preferences(source):
    """{'setting name (lower case)': 'value'} from the Preferences tab."""
    settings = {}
    for row in tab_rows(source, "Preferences"):
        if len(row) >= 2 and row[0].strip() and row[0].strip().lower() != "setting":
            settings[row[0].strip().lower()] = row[1].strip()
    return settings


def read_companies(source):
    """[{'name', 'website', 'careers'}] from the Companies tab (header row skipped)."""
    rows = tab_rows(source, "Companies")
    companies = []
    for row in rows[1:]:
        row = row + ["", "", ""]
        name, website, careers = row[0].strip(), row[1].strip(), row[2].strip()
        if name:
            companies.append({"name": name, "website": website, "careers": careers})
    return companies
