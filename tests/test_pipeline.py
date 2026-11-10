import json
from datetime import datetime, timezone

from conftest import GH, LV, gh_raw
from jobwatcher.build import read_history
from jobwatcher.issues import issue_body
from jobwatcher.pipeline import run

SOURCES = [GH, LV]


def go(raw_dir, tmp_path, day, fetcher):
    now = datetime(2026, 2, day, 9, 30, tzinfo=timezone.utc)
    return run(now, SOURCES, fetcher, raw_dir, tmp_path / "history.csv", tmp_path / "status.json", publish=False)


def test_failed_source_writes_no_raw_file_and_run_survives(raw_dir, tmp_path):
    def fetcher(s):
        if s is LV:
            raise RuntimeError("boom")
        return gh_raw(1, 2)
    _, status = go(raw_dir, tmp_path, 1, fetcher)
    assert (raw_dir / "2026-02-01" / "greenhouse-acme.json.gz").exists()
    assert not (raw_dir / "2026-02-01" / "lever-beta.json.gz").exists()
    assert status["sources"] == [{"name": "greenhouse-acme", "ok": True, "count": 2},
                                 {"name": "lever-beta", "ok": False, "count": 0}]


def test_status_counts_and_second_run_same_day_counts_once(raw_dir, tmp_path):
    lever = [{"id": "a", "text": "T", "hostedUrl": "u"}]
    go(raw_dir, tmp_path, 1, lambda s: gh_raw(1, 2) if s is GH else lever)
    go(raw_dir, tmp_path, 2, lambda s: gh_raw(1, 3) if s is GH else lever)
    _, status = go(raw_dir, tmp_path, 2, lambda s: gh_raw(1, 3) if s is GH else lever)  # rerun same day
    assert status["days_with_success"] == 2
    assert status["first_run_date"] == "2026-02-01"
    assert (status["open"], status["new_today"], status["removed_today"]) == (3, 1, 1)
    assert status["run_time"] == "2026-02-02 09:30:00"
    assert json.loads((tmp_path / "status.json").read_text()) == status
    assert len(read_history(tmp_path / "history.csv")) == 4


def test_rerun_replaces_the_days_raw_files(raw_dir, tmp_path):
    go(raw_dir, tmp_path, 1, lambda s: gh_raw(1) if s is GH else [])
    go(raw_dir, tmp_path, 1, lambda s: gh_raw(1, 2) if s is GH else [])
    _, status = go(raw_dir, tmp_path, 1, lambda s: gh_raw(1, 2, 3) if s is GH else [])
    assert status["sources"][0]["count"] == 3 and status["days_with_success"] == 1


def test_issue_body_lists_new_and_removed_with_links(raw_dir, tmp_path):
    go(raw_dir, tmp_path, 1, lambda s: gh_raw(1, 2) if s is GH else [])
    rows, status = go(raw_dir, tmp_path, 2, lambda s: gh_raw(1, 3) if s is GH else [])
    body = issue_body("2026-02-02", rows, status)
    assert "[Role 3](https://x/3)" in body and "[Role 2](https://x/2)" in body
    assert "[Role 1](https://x/1)" not in body
    quiet = issue_body("2026-02-03", rows, status)
    assert quiet.count("None.") == 2
