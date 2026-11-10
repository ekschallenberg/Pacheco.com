from conftest import AS, GH, LV
from jobwatcher.normalize import COLUMNS, normalize


def test_greenhouse_to_common_columns():
    raw = {"jobs": [{"id": 77, "title": "  Financial Analyst ", "location": {"name": "New York"},
                     "first_published": "2026-03-04T21:00:00-05:00", "absolute_url": "https://g/77"}]}
    (row,) = normalize(GH, raw)
    assert list(row) == COLUMNS
    assert row == {"posting_id": "greenhouse-acme:77", "source": "greenhouse-acme", "source_id": "77",
                   "employer": "Acme", "title": "Financial Analyst", "location": "New York", "department": "",
                   "posted_date": "2026-03-05",  # 21:00 at -05:00 is 02:00 UTC the next day
                   "url": "https://g/77"}


def test_lever_to_common_columns():
    raw = [{"id": "abc-1", "text": "Data Analyst", "categories": {"location": "Remote", "department": "Finance"},
            "createdAt": 1772668800000, "hostedUrl": "https://l/abc-1"}]
    (row,) = normalize(LV, raw)
    assert row["posting_id"] == "lever-beta:abc-1"
    assert (row["title"], row["location"], row["department"]) == ("Data Analyst", "Remote", "Finance")
    assert row["posted_date"] == "2026-03-05"
    assert row["url"] == "https://l/abc-1"


def test_ashby_to_common_columns():
    raw = {"jobs": [{"id": "u-9", "title": " FP&A Manager", "location": "Austin", "department": "Finance",
                     "publishedAt": "2026-04-07T17:12:35.753+00:00", "jobUrl": "https://a/u-9"}]}
    (row,) = normalize(AS, raw)
    assert row["posting_id"] == "ashby-gamma:u-9"
    assert row["title"] == "FP&A Manager"
    assert row["posted_date"] == "2026-04-07"
    assert row["employer"] == "Gamma"


def test_missing_columns_are_left_empty():
    (row,) = normalize(LV, [{"id": "x", "text": "T", "hostedUrl": "u"}])
    assert row["posted_date"] == "" and row["department"] == "" and row["location"] == ""
    (row,) = normalize(GH, {"jobs": [{"id": 1, "title": "T", "absolute_url": "u"}]})
    assert row["posted_date"] == "" and row["location"] == ""


def test_every_posting_is_kept():
    assert len(normalize(GH, {"jobs": [{"id": i, "title": "Chef", "absolute_url": "u"} for i in range(5)]})) == 5
