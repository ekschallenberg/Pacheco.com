"""The watch list: every source, the applicant tracking system (ATS) that hosts it, and its public JSON URL."""
from dataclasses import dataclass

import requests

USER_AGENT = "job-watcher/1.0 (student project; daily job board snapshot)"


@dataclass(frozen=True)
class Source:
    name: str      # unique key, used in file names: data/raw/<date>/<name>.json.gz
    ats: str       # greenhouse | lever | ashby
    employer: str  # display name
    token: str     # the employer's board token at that ATS

    @property
    def url(self) -> str:
        if self.ats == "greenhouse":
            return f"https://boards-api.greenhouse.io/v1/boards/{self.token}/jobs"
        if self.ats == "lever":
            return f"https://api.lever.co/v0/postings/{self.token}?mode=json"
        if self.ats == "ashby":
            return f"https://api.ashbyhq.com/posting-api/job-board/{self.token}"
        raise ValueError(f"unknown ATS {self.ats!r}")


def _s(ats, token, employer):
    return Source(f"{ats}-{token}", ats, employer, token)


# 16 employers. No board returns more than 5,000 postings, so no search term is needed.
SOURCES = [
    _s("greenhouse", "stripe", "Stripe"),
    _s("greenhouse", "robinhood", "Robinhood"),
    _s("greenhouse", "coinbase", "Coinbase"),
    _s("greenhouse", "affirm", "Affirm"),
    _s("greenhouse", "brex", "Brex"),
    _s("greenhouse", "databricks", "Databricks"),
    _s("greenhouse", "sofi", "SoFi"),
    _s("greenhouse", "chime", "Chime"),
    _s("greenhouse", "block", "Block"),
    _s("greenhouse", "toast", "Toast"),
    _s("greenhouse", "gusto", "Gusto"),
    _s("lever", "palantir", "Palantir"),
    _s("lever", "spotify", "Spotify"),
    _s("ashby", "ramp", "Ramp"),
    _s("ashby", "notion", "Notion"),
    _s("ashby", "plaid", "Plaid"),
]

SOURCES_BY_NAME = {s.name: s for s in SOURCES}


def fetch(source: Source, timeout: int = 90, session=None, retries: int = 3):
    """Return the parsed JSON for a source, with no login. Raises on any failure."""
    http = session or requests
    last = None
    for attempt in range(retries):
        try:
            resp = http.get(source.url, timeout=timeout, headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # network error, bad status, bad JSON
            last = exc
    raise last
