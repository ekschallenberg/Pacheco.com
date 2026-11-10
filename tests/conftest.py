import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from jobwatcher.sources import Source  # noqa: E402

GH = Source("greenhouse-acme", "greenhouse", "Acme", "acme")
LV = Source("lever-beta", "lever", "Beta", "beta")
AS = Source("ashby-gamma", "ashby", "Gamma", "gamma")


def gh_raw(*ids, title="Role"):
    return {"jobs": [{"id": i, "title": f"{title} {i}", "location": {"name": "NYC"},
                      "first_published": "2026-01-05T23:30:00-05:00", "absolute_url": f"https://x/{i}"} for i in ids]}


@pytest.fixture
def raw_dir(tmp_path):
    return tmp_path / "raw"


@pytest.fixture
def write_raw(raw_dir):
    def _write(date, source, data):
        p = raw_dir / date / f"{source.name}.json.gz"
        p.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            json.dump(data, fh)
    return _write
