# Job Watcher

[![tests](https://github.com/ekschallenberg/Pacheco.com/actions/workflows/tests.yml/badge.svg)](https://github.com/ekschallenberg/Pacheco.com/actions/workflows/tests.yml)

A tool that watches the job market once a day. A GitHub Actions workflow pulls the open positions from 16 employers' public job boards, compares them with the day before, records what is new and what is gone, opens a GitHub Issue for the day, and publishes the result as an installable GitHub Pages site.

**Role watched:** financial analyst (FP&A, data/BI, credit, treasury and related analyst roles). Every posting the boards return is kept; the role only marks postings with `in_role`.

## Sources

Every board returns JSON to a request with no login. No board has more than 5,000 postings, so no search term is used.

| Source | Employer | Applicant tracking system |
|---|---|---|
| greenhouse-stripe | Stripe | Greenhouse |
| greenhouse-robinhood | Robinhood | Greenhouse |
| greenhouse-coinbase | Coinbase | Greenhouse |
| greenhouse-affirm | Affirm | Greenhouse |
| greenhouse-brex | Brex | Greenhouse |
| greenhouse-databricks | Databricks | Greenhouse |
| greenhouse-sofi | SoFi | Greenhouse |
| greenhouse-chime | Chime | Greenhouse |
| greenhouse-block | Block | Greenhouse |
| greenhouse-toast | Toast | Greenhouse |
| greenhouse-gusto | Gusto | Greenhouse |
| lever-palantir | Palantir | Lever |
| lever-spotify | Spotify | Lever |
| ashby-ramp | Ramp | Ashby |
| ashby-notion | Notion | Ashby |
| ashby-plaid | Plaid | Ashby |

## Title rule

`in_role` is `true` when the title does not match `engineer|scientist|developer|designer|sales|recruit` and either
(a) contains `FP&A` / `FP and A` / `financial planning`, or
(b) contains `analyst` or `analytics` **and** a field word: `financ`, `accounting`, `treasury`, `credit`, `investment`, `revenue`, `pricing`, `business intelligence`, `BI`, `data`, `strategy`, `risk`, `supply chain`, `planning`, `reporting`, `forecast`.
The rule lives in `jobwatcher/role.py`. Because the history is rebuilt from the raw files, changing it applies to every day.

## Rebuild the history file from the raw files

```bash
python -m jobwatcher.build
```

This reads only `data/raw/` (no network) and writes `data/history.csv`; running it again produces the same file.

## How a day works

`python -m jobwatcher.pipeline` (run by `.github/workflows/daily.yml`): fetch each source into `data/raw/<date>/<source>.json.gz` (a failing source writes no file and does not stop the run), rebuild `data/history.csv`, write `data/status.json`, open the day's Issue (titled with the UTC date, listing new and removed postings with links) and close the previous day's, then the workflow commits `data/`. A second run on the same day replaces that day's raw files and updates that day's Issue, so each day counts once.

## Files

| File | What it does |
|---|---|
| `jobwatcher/sources.py` | The watch list, each source's ATS and URL, and the fetch function |
| `jobwatcher/normalize.py` | Converts each ATS's JSON to the common columns |
| `jobwatcher/role.py` | The title rule |
| `jobwatcher/build.py` | Builds `data/history.csv` from the raw files (first seen, last seen, removed, reopened) |
| `jobwatcher/status.py` | Builds `data/status.json` |
| `jobwatcher/issues.py` | Opens/updates the daily GitHub Issue and closes older ones |
| `jobwatcher/pipeline.py` | The daily run |
| `jobwatcher/paths.py` | Fixed data paths |
| `tests/` | pytest suite: conversion per source, title rule, first/last-seen and removed logic, pipeline and status |
| `.github/workflows/daily.yml` | Runs the pipeline once a day and commits the data |
| `.github/workflows/tests.yml` | Runs pytest on every push |
| `data/raw/<date>/<source>.json.gz` | What each source returned, compressed |
| `data/history.csv` | One row per posting |
| `data/status.json` | Describes the latest run |
| `index.html` | Today page: last run, source status, four counts, new and removed postings |
| `browse.html` | Browse page: role/all switch, employer/location/days-open filters, title search, sort, apply links, starred shortlist saved in the browser |
| `market.html` | Market page: six sections, each computed in the browser from the history file |
| `assets/app.js` | Shared navigation, data loading, CSV parsing, service worker registration |
| `assets/market.js` | The Market calculations |
| `assets/charts.js` | Inline SVG charts |
| `assets/style.css` | Shared fonts and colors |
| `assets/icon-192.png`, `assets/icon-512.png` | App icons |
| `manifest.webmanifest`, `sw.js` | Make the site installable and usable offline (last loaded data) |
| `requirements.txt` | `requests`, `pytest` |

## Data files

`data/history.csv` columns: `posting_id, source, source_id, employer, title, location, department, posted_date, url, in_role, first_run, first_seen, last_seen, status, removed_date`. Dates are UTC `YYYY-MM-DD`; a column a source does not provide (`posted_date`, `department`) is empty. `first_run` is `true` for a posting listed in its source's first raw file, so its real start date is unknown.

`data/status.json` keys: `run_time`, `first_run_date`, `days_with_success`, `open`, `new_today`, `removed_today`, `sources` (each with `name`, `ok`, `count`).

## Run it locally

```bash
pip install -r requirements.txt
python -m pytest
python -m jobwatcher.pipeline
python -m http.server   # then open http://localhost:8000
```

Built with Claude Code.
