"""Rewrite the Weekend projects rows in README.md from devnadeem.com.

Reads the JSON feed, keeps the latest 3 entries, and replaces everything
between the weekend:start and weekend:end markers. Exits non-zero on a bad
feed so the workflow never commits a broken README.
"""

import json
import os
import sys
import urllib.request
from datetime import date

FEED = os.environ.get("WEEKEND_FEED", "https://devnadeem.com/weekend-projects.json")
README = os.environ.get("README_PATH", "README.md")
LATEST = 3
START = "<!-- weekend:start -->"
END = "<!-- weekend:end -->"


def cell(text: str) -> str:
    return " ".join(text.replace("|", "\\|").split())


def fmt_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


def kind_note(p: dict) -> str:
    based = (p.get("basedOn") or {}).get("name")
    if p.get("kind") == "fork" and based:
        return f" (fork of {based})"
    if p.get("kind") == "contribution" and based:
        return f" (contribution to {based})"
    return ""


def render(projects: list[dict]) -> str:
    rows = [
        "| # | Date | Project | What it does |",
        "| --- | --- | --- | --- |",
    ]
    for p in sorted(projects, key=lambda x: x["n"], reverse=True)[:LATEST]:
        rows.append(
            f"| {p['n']:02d} | {fmt_date(p['date'])} "
            f"| **[{cell(p['name'])}]({p['repo']})**{kind_note(p)} "
            f"| {cell(p['oneLiner'])} |"
        )
    return "\n".join(rows)


def main() -> int:
    req = urllib.request.Request(FEED, headers={"User-Agent": "weekend-projects-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        print("Feed has no projects; leaving README alone.", file=sys.stderr)
        return 1

    text = open(README, encoding="utf-8").read()
    if text.count(START) != 1 or text.count(END) != 1:
        print("Markers missing or duplicated in README.", file=sys.stderr)
        return 1
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{START}\n{render(projects)}\n{END}{tail}"
    if new == text:
        print("README already up to date.")
        return 0
    open(README, "w", encoding="utf-8").write(new)
    print("README updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
