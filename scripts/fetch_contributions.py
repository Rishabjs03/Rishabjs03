#!/usr/bin/env python3
"""
Fetch a year of daily contribution counts for a GitHub user and write
data/contributions.json (raw days + derived stats: streaks, best day, monthly
totals).

Primary source: GitHub's public, unauthenticated contributions fragment
(https://github.com/users/<user>/contributions) -- the same HTML the profile
page embeds. No token, no GraphQL.

Fallback: the public github-contributions-api (jogruber.de) in case GitHub's
markup changes or the fragment is unreachable from where this runs.

Run daily by .github/workflows/update-profile-art.yml before
render_heatmap_svg.py.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "Rishabjs03")
HTML_URL = f"https://github.com/users/{USERNAME}/contributions"
API_URL = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "contributions.json")
HEADERS = {"User-Agent": "profile-readme-bot/1.0 (+https://github.com/Rishabjs03/Rishabjs03)"}


def fetch_days_from_html():
    resp = requests.get(HTML_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day[data-date]")
    if not cells:
        raise RuntimeError("no ContributionCalendar-day cells found; markup may have changed")

    days = []
    for td in cells:
        date = td["data-date"]
        count = None
        td_id = td.get("id")
        tip = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        if tip is not None:
            text = tip.get_text(" ", strip=True)
            if re.search(r"\bno contributions\b", text, re.I):
                count = 0
            else:
                m = re.match(r"\s*([\d,]+)", text)
                if m:
                    count = int(m.group(1).replace(",", ""))
        if count is None:
            # Last resort: the cell's own text ("3 contributions on ...") or the level bucket.
            own = td.get_text(" ", strip=True)
            m = re.match(r"\s*([\d,]+)\s+contribution", own)
            if m:
                count = int(m.group(1).replace(",", ""))
            else:
                count = 0 if td.get("data-level", "0") == "0" else 1
        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def fetch_days_from_api():
    resp = requests.get(API_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    days = [{"date": c["date"], "count": int(c["count"])} for c in payload["contributions"]]
    if not days:
        raise RuntimeError("fallback API returned no days")
    days.sort(key=lambda d: d["date"])
    return days


def fetch_days():
    try:
        days = fetch_days_from_html()
        print(f"fetched {len(days)} days from {HTML_URL}")
        return days, "github.com"
    except Exception as exc:  # noqa: BLE001 - any failure -> fallback
        print(f"primary source failed ({exc}); trying fallback API", file=sys.stderr)
    days = fetch_days_from_api()
    print(f"fetched {len(days)} days from {API_URL}")
    return days, "github-contributions-api.jogruber.de"


def compute_current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today isn't over yet; don't break the streak on it
    end_idx = idx
    streak = 0
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    if streak == 0:
        return 0, None, None
    return streak, days[idx + 1]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start]["date"]
                longest_end = d["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days, source):
    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "username": USERNAME,
        "source": source,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    days, source = fetch_days()
    data = build_data(days, source)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(
        f"wrote {os.path.relpath(OUT_PATH)}: {data['total_contributions']} contributions, "
        f"current streak {data['current_streak']['length']}, longest {data['longest_streak']['length']}"
    )
