"""Job board readers.

Each reader is a function `read(params, hints)` that returns every open job on
one board as a list of dicts:
    id, title, url, location, posted_at (ISO text or None), description
Readers whose list has no description (or only "2 Locations") also have a
`detail(job, params)` function. It is only called for jobs whose title already
matched, to keep the number of requests small.

`hints` holds the user's country names (e.g. ["Spain"]), used by the few very
large company sites that can only be read one country at a time.
"""

from . import ats, enterprise, feeds, workday

READERS = {
    "greenhouse": ats.greenhouse,
    "lever": ats.lever,
    "ashby": ats.ashby,
    "workable": ats.workable,
    "smartrecruiters": ats.smartrecruiters,
    "recruitee": ats.recruitee,
    "bamboohr": ats.bamboohr,
    "rippling": ats.rippling,
    "workday": workday.read,
    "teamtailor": feeds.teamtailor,
    "personio": feeds.personio,
    "comeet": feeds.comeet,
    "recruiterflow": feeds.recruiterflow,
    "factorial": feeds.factorial,
    "hibob": feeds.hibob,
    "htmllinks": feeds.htmllinks,
    "phenom": enterprise.phenom,
    "successfactors": enterprise.successfactors,
    "eightfold": enterprise.eightfold,
    "ibm": enterprise.ibm,
    "atlassian": enterprise.atlassian,
    "dynatrace": enterprise.dynatrace,
    "deel": enterprise.deel,
    "revolut": enterprise.revolut,
    "bendingspoons": enterprise.bendingspoons,
}

DETAILS = {
    "smartrecruiters": ats.smartrecruiters_detail,
    "bamboohr": ats.bamboohr_detail,
    "rippling": ats.rippling_detail,
    "workday": workday.detail,
    "successfactors": enterprise.successfactors_detail,
    "eightfold": enterprise.eightfold_detail,
}
