"""Build data/status.json describing the latest run."""
import json
from pathlib import Path

from .build import list_raw, read_raw
from .normalize import normalize
from .paths import RAW, STATUS
from .sources import SOURCES


def build_status(rows, run_time, raw_dir=RAW, sources=SOURCES) -> dict:
    days = list_raw(raw_dir)
    dates = sorted(days)
    latest = dates[-1] if dates else ""
    ok_names = set(days.get(latest, []))
    entries = []
    for s in sources:
        count = 0
        if s.name in ok_names:
            try:
                count = len(normalize(s, read_raw(raw_dir, latest, s.name)))
            except Exception:
                ok_names.discard(s.name)
        entries.append({"name": s.name, "ok": s.name in ok_names, "count": count})
    return {
        "run_time": run_time,
        "first_run_date": dates[0] if dates else "",
        "days_with_success": len(dates),
        "open": sum(r["status"] == "open" for r in rows),
        "new_today": sum(r["first_seen"] == latest and r["first_run"] == "false" for r in rows),
        "removed_today": sum(r["removed_date"] == latest for r in rows),
        "sources": entries,
    }


def write_status(status, path=STATUS) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=2)
        fh.write("\n")
