#!/usr/bin/env python3
"""Format a bug report JSON for human-readable display."""
import json
import sys


SEVERITY_ICONS = {"High": "H", "Medium": "M", "Low": "L"}


def format_report(path: str):
    with open(path) as f:
        data = json.load(f)

    # Report can be a list of bugs directly, or a dict with metadata + bugs
    if isinstance(data, list):
        bugs = data
        status = "bug_found" if bugs else "success"
        likely_file = "N/A"
    else:
        status = data.get("status", "unknown")
        likely_file = data.get("likely_file", "N/A")
        bugs = data.get("bugs", [])

    print(f"  Status:        {status}")
    print(f"  Likely file:   {likely_file}")

    if isinstance(bugs, list) and len(bugs) > 0:
        print(f"  Bugs found:    {len(bugs)}")
        print()
        for b in bugs:
            sev = b.get("severity", "?")
            icon = SEVERITY_ICONS.get(sev, "?")
            bid = b.get("id", "")
            element = b.get("element", "")
            desc = b.get("description", "")
            category = b.get("category", "")
            selector = b.get("selector", "N/A")
            print(f"  [{icon}] {bid}  {element}")
            print(f"      {desc}")
            print(f"      Category: {category}  |  Severity: {sev}  |  Selector: {selector}")
            print()
    elif isinstance(data, dict):
        notes = data.get("notes", "N/A")
        actions = data.get("actions_taken", [])
        if notes != "N/A":
            print(f"  Notes: {notes}")
        if actions:
            print(f"  Actions:")
            for a in actions:
                print(f"    - {a}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python format_report.py <report.json>")
        sys.exit(1)
    format_report(sys.argv[1])
