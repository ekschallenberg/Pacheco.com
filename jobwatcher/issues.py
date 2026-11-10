"""Daily GitHub Issue: new and removed postings, titled with the date."""
import os
import re

import requests

DATE_TITLE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
API = "https://api.github.com"


def issue_body(date, rows, status) -> str:
    new = [r for r in rows if r["first_seen"] == date and r["first_run"] == "false"]
    removed = [r for r in rows if r["removed_date"] == date]
    failed = [s["name"] for s in status["sources"] if not s["ok"]]

    def line(r):
        return f"- [{r['title'] or '(untitled)'}]({r['url']}) — {r['employer']}, {r['location'] or 'no location'}"

    parts = [f"Run {status['run_time']} UTC · {status['open']} open postings · "
             f"{len(new)} new · {len(removed)} removed", ""]
    if failed:
        parts += [f"Sources that failed today: {', '.join(failed)}", ""]
    if status["days_with_success"] == 1:
        parts += ["First run: every posting listed today counts as already open, so none are reported as new.", ""]
    parts += [f"## New postings ({len(new)})", ""] + ([line(r) for r in new] or ["None."]) + [""]
    parts += [f"## Removed postings ({len(removed)})", ""] + ([line(r) for r in removed] or ["None."])
    return "\n".join(parts) + "\n"


def _chunk(body, limit=60000):
    return body if len(body) <= limit else body[:limit] + "\n\n…list truncated…\n"


def publish_issue(date, rows, status, token=None, repo=None) -> str:
    """Open (or update) today's issue and close every other open dated issue. Returns the issue URL."""
    token = token or os.environ["GITHUB_TOKEN"]
    repo = repo or os.environ["GITHUB_REPOSITORY"]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    body = _chunk(issue_body(date, rows, status))

    existing = []
    page = 1
    while True:
        resp = requests.get(f"{API}/repos/{repo}/issues", headers=headers, timeout=60,
                            params={"state": "all", "per_page": 100, "page": page})
        resp.raise_for_status()
        batch = [i for i in resp.json() if "pull_request" not in i]
        existing += batch
        if len(resp.json()) < 100:
            break
        page += 1

    today = next((i for i in existing if i["title"] == date), None)
    if today:  # a second run on the same day updates that day's issue
        r = requests.patch(today["url"], headers=headers, timeout=60, json={"body": body, "state": "open"})
    else:
        r = requests.post(f"{API}/repos/{repo}/issues", headers=headers, timeout=60,
                          json={"title": date, "body": body})
    r.raise_for_status()
    url = r.json()["html_url"]
    for issue in existing:
        if issue["state"] == "open" and DATE_TITLE.match(issue["title"]) and issue["title"] != date:
            requests.patch(issue["url"], headers=headers, timeout=60,
                           json={"state": "closed", "state_reason": "completed"}).raise_for_status()
    return url
