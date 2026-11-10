"""Build data/history.csv from the raw files alone (no network, deterministic).

    python -m jobwatcher.build

Raw files are processed day by day, so changing a rule (such as the title rule) applies to the whole history.
"""
import csv
import gzip
import json
import sys
from pathlib import Path

from .normalize import normalize
from .paths import HISTORY, RAW
from .role import in_role
from .sources import SOURCES, SOURCES_BY_NAME

HISTORY_COLUMNS = [
    "posting_id", "source", "source_id", "employer", "title", "location", "department", "posted_date",
    "url", "in_role", "first_run", "first_seen", "last_seen", "status", "removed_date",
]


def raw_path(raw_dir, date, source_name) -> Path:
    return Path(raw_dir) / date / f"{source_name}.json.gz"


def list_raw(raw_dir=RAW) -> dict:
    """{date: [source names with a raw file that day]}, dates sorted."""
    out = {}
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        return out
    for day in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        names = sorted(f.name[: -len(".json.gz")] for f in day.glob("*.json.gz"))
        if names:
            out[day.name] = names
    return out


def read_raw(raw_dir, date, source_name):
    with gzip.open(raw_path(raw_dir, date, source_name), "rt", encoding="utf-8") as fh:
        return json.load(fh)


def build_rows(raw_dir=RAW, sources_by_name=None) -> list:
    """Replay every raw file in date order and return the history rows, sorted by posting_id."""
    sources_by_name = sources_by_name or SOURCES_BY_NAME
    days = list_raw(raw_dir)
    first_date = {}  # source -> date of its first raw file
    rows = {}        # posting_id -> row
    for date, names in days.items():
        for name in names:
            if name not in sources_by_name:
                continue
            try:
                postings = normalize(sources_by_name[name], read_raw(raw_dir, date, name))
            except Exception as exc:  # a corrupt file is skipped, like a failed source
                print(f"skipping unreadable raw file {date}/{name}: {exc}", file=sys.stderr)
                continue
            first = first_date.setdefault(name, date)
            listed = set()
            for p in postings:
                pid = p["posting_id"]
                listed.add(pid)
                row = rows.get(pid)
                if row is None:
                    row = {"first_run": first == date, "first_seen": date, "removed_date": "", "status": "open"}
                    rows[pid] = row
                row.update(p)
                row["last_seen"] = date
                row["status"] = "open"      # a removed posting that is listed again becomes open again
                row["removed_date"] = ""
            for pid, row in rows.items():
                if row["source"] == name and row["status"] == "open" and pid not in listed:
                    row["status"] = "removed"
                    row["removed_date"] = date
    out = []
    for pid in sorted(rows):
        r = rows[pid]
        out.append({
            **{c: r[c] for c in HISTORY_COLUMNS[:9]},
            "in_role": "true" if in_role(r["title"]) else "false",
            "first_run": "true" if r["first_run"] else "false",
            "first_seen": r["first_seen"], "last_seen": r["last_seen"],
            "status": r["status"], "removed_date": r["removed_date"],
        })
    return out


def write_history(rows, path=HISTORY) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HISTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_history(path=HISTORY) -> list:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    rows = build_rows()
    write_history(rows)
    print(f"wrote {len(rows)} rows to {HISTORY}")


if __name__ == "__main__":
    main()
