"""Convert each ATS's JSON into one common set of columns."""
import re
from datetime import datetime, timezone

COLUMNS = ["posting_id", "source", "source_id", "employer", "title", "location", "department", "posted_date", "url"]


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _iso_to_utc_date(value) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _ms_to_utc_date(value) -> str:
    if value in (None, ""):
        return ""
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError, OSError):
        return ""


def _row(source, source_id, title, location, department, posted_date, url) -> dict:
    return {
        "posting_id": f"{source.name}:{source_id}",
        "source": source.name,
        "source_id": str(source_id),
        "employer": source.employer,
        "title": _clean(title),
        "location": _clean(location),
        "department": _clean(department),
        "posted_date": posted_date,
        "url": url or "",
    }


def _greenhouse(source, raw):
    # The Greenhouse list endpoint has no department, so that column stays empty.
    for job in raw.get("jobs", []):
        yield _row(source, job["id"], job.get("title"), (job.get("location") or {}).get("name"), "",
                   _iso_to_utc_date(job.get("first_published")), job.get("absolute_url"))


def _lever(source, raw):
    for job in raw:
        cats = job.get("categories") or {}
        yield _row(source, job["id"], job.get("text"), cats.get("location"), cats.get("department"),
                   _ms_to_utc_date(job.get("createdAt")), job.get("hostedUrl"))


def _ashby(source, raw):
    for job in raw.get("jobs", []):
        yield _row(source, job["id"], job.get("title"), job.get("location"), job.get("department"),
                   _iso_to_utc_date(job.get("publishedAt")), job.get("jobUrl"))


_CONVERTERS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby}


def normalize(source, raw) -> list:
    """All postings the source returned, as dicts with the common COLUMNS."""
    return list(_CONVERTERS[source.ats](source, raw))
