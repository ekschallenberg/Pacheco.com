from conftest import GH, LV, gh_raw
from jobwatcher.build import build_rows, list_raw, read_history, write_history

SRC = {GH.name: GH, LV.name: LV}


def rows_by_id(raw_dir):
    return {r["posting_id"]: r for r in build_rows(raw_dir, SRC)}


def test_first_seen_last_seen_and_first_run(raw_dir, write_raw):
    write_raw("2026-01-01", GH, gh_raw(1, 2))
    write_raw("2026-01-02", GH, gh_raw(1, 2, 3))
    write_raw("2026-01-03", GH, gh_raw(1, 2, 3))
    rows = rows_by_id(raw_dir)
    one, three = rows["greenhouse-acme:1"], rows["greenhouse-acme:3"]
    assert (one["first_run"], one["first_seen"], one["last_seen"], one["status"]) == ("true", "2026-01-01", "2026-01-03", "open")
    assert (three["first_run"], three["first_seen"], three["last_seen"]) == ("false", "2026-01-02", "2026-01-03")


def test_removed_gets_that_days_date(raw_dir, write_raw):
    write_raw("2026-01-01", GH, gh_raw(1, 2))
    write_raw("2026-01-02", GH, gh_raw(1))
    two = rows_by_id(raw_dir)["greenhouse-acme:2"]
    assert (two["status"], two["removed_date"], two["last_seen"]) == ("removed", "2026-01-02", "2026-01-01")


def test_reopened_clears_removed_date_and_keeps_first_seen(raw_dir, write_raw):
    write_raw("2026-01-01", GH, gh_raw(1, 2))
    write_raw("2026-01-02", GH, gh_raw(1))
    write_raw("2026-01-03", GH, gh_raw(1, 2))
    two = rows_by_id(raw_dir)["greenhouse-acme:2"]
    assert (two["status"], two["removed_date"], two["first_seen"], two["last_seen"]) == ("open", "", "2026-01-01", "2026-01-03")
    assert two["first_run"] == "true"


def test_failed_source_day_does_not_remove_postings(raw_dir, write_raw):
    write_raw("2026-01-01", GH, gh_raw(1))
    write_raw("2026-01-01", LV, [{"id": "a", "text": "T", "hostedUrl": "u"}])
    write_raw("2026-01-02", GH, gh_raw(1))  # the lever source failed on day 2: no raw file
    assert rows_by_id(raw_dir)["lever-beta:a"]["status"] == "open"


def test_first_run_is_per_source(raw_dir, write_raw):
    write_raw("2026-01-01", GH, gh_raw(1))
    write_raw("2026-01-02", GH, gh_raw(1))
    write_raw("2026-01-02", LV, [{"id": "a", "text": "T", "hostedUrl": "u"}])  # lever's first raw file
    rows = rows_by_id(raw_dir)
    assert rows["lever-beta:a"]["first_run"] == "true"


def test_rows_sorted_and_build_is_reproducible(raw_dir, write_raw, tmp_path):
    write_raw("2026-01-01", GH, gh_raw(10, 2, 33))
    write_raw("2026-01-02", GH, gh_raw(2, 33, 4))
    first = build_rows(raw_dir, SRC)
    assert [r["posting_id"] for r in first] == sorted(r["posting_id"] for r in first)
    write_history(first, tmp_path / "a.csv")
    write_history(build_rows(raw_dir, SRC), tmp_path / "b.csv")
    assert (tmp_path / "a.csv").read_bytes() == (tmp_path / "b.csv").read_bytes()
    assert read_history(tmp_path / "a.csv")[0].keys() == first[0].keys()


def test_title_rule_change_applies_to_whole_history(raw_dir, write_raw, monkeypatch):
    write_raw("2026-01-01", GH, {"jobs": [{"id": 1, "title": "Financial Analyst", "absolute_url": "u"}]})
    write_raw("2026-01-02", GH, {"jobs": [{"id": 1, "title": "Financial Analyst", "absolute_url": "u"}]})
    assert rows_by_id(raw_dir)["greenhouse-acme:1"]["in_role"] == "true"
    monkeypatch.setattr("jobwatcher.build.in_role", lambda title: False)
    assert rows_by_id(raw_dir)["greenhouse-acme:1"]["in_role"] == "false"


def test_list_raw(raw_dir, write_raw):
    write_raw("2026-01-02", GH, gh_raw(1))
    write_raw("2026-01-01", LV, [])
    assert list_raw(raw_dir) == {"2026-01-01": ["lever-beta"], "2026-01-02": ["greenhouse-acme"]}
