"""The daily run:  python -m jobwatcher.pipeline

1. fetch every source and save data/raw/<date>/<source>.json.gz (a failing source writes nothing)
2. rebuild data/history.csv from the raw files   3. write data/status.json
4. open the day's GitHub Issue (when GITHUB_TOKEN is set)
The workflow then commits data/.
"""
import gzip
import json
import os
import shutil
import sys
from datetime import datetime, timezone

from . import issues
from .build import build_rows, raw_path, write_history
from .paths import RAW
from .sources import SOURCES, fetch
from .status import build_status, write_status


def run(now=None, sources=SOURCES, fetcher=fetch, raw_dir=RAW, history_path=None, status_path=None, publish=None):
    now = now or datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    run_time = now.strftime("%Y-%m-%d %H:%M:%S")

    day_dir = raw_dir / date
    if day_dir.exists():  # a second run on the same day replaces that day's raw files
        shutil.rmtree(day_dir)
    for s in sources:
        try:
            data = fetcher(s)
        except Exception as exc:  # one source failing must not stop the run
            print(f"FAILED {s.name}: {exc}", file=sys.stderr)
            continue
        path = raw_path(raw_dir, date, s.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.GzipFile(path, "wb", mtime=0) as fh:
            fh.write(json.dumps(data, separators=(",", ":")).encode("utf-8"))
        print(f"ok {s.name}")

    by_name = {s.name: s for s in sources}
    rows = build_rows(raw_dir, by_name)
    kwargs = {} if history_path is None else {"path": history_path}
    write_history(rows, **kwargs)
    status = build_status(rows, run_time, raw_dir, sources)
    write_status(status, **({} if status_path is None else {"path": status_path}))

    if publish is None:
        publish = bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPOSITORY"))
    if publish:
        print("issue:", issues.publish_issue(date, rows, status))
    return rows, status


if __name__ == "__main__":
    run()
