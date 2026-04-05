#!/usr/bin/env python3
"""AUTO-QA Agentic Loop Orchestrator.

Reads bug_report.json (a flat list of bugs with 'fixed' flags).
BrowserUse marks bugs as processed (red borders + filled fields).
Claude Code then fixes the actual source issues.
Loops until all bugs are fixed or max iterations reached.

One bug per iteration — BrowserUse highlights it, Claude Code fixes it,
then we re-run to verify and pick up the next bug.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

console = Console()
MAX_ITERATIONS = 20

# Route → files Claude Code is allowed to fix
ROUTE_FILES = {
    "/billing":  ["qa-sandbox/src/pages/Billing.jsx",  "qa-sandbox/src/pages/Billing.css"],
    "/settings": ["qa-sandbox/src/pages/Settings.jsx", "qa-sandbox/src/pages/Settings.css"],
    "/profile":  ["qa-sandbox/src/pages/Profile.jsx",  "qa-sandbox/src/pages/Profile.css"],
}

BANNER = r"""
  ___         _        _____    ___
 / _ \  _   _(_) _ __  \_   \  / _ \  __ _  ___  ___  __ _
| | | || | | | || '_ \  / /\/ | | | |/ _` |/ _ \/ __|/ _` |
| |_| || |_| | || |_) |/ /    | |_| | (_| |  __/\__ \ (_| |
 \__\_\\__,_|_|| .__/ \/      \___/ \__, |\___||___/\__,_|
               |_|                   |___/
"""

SUBTITLE = "Developer Agent  x  QA Agent  |  Closed Loop"


def print_banner():
    console.print(f"\033[96m{BANNER}\033[0m")
    console.print(f"\033[96m{'=' * 60}\033[0m")
    console.print(f"\033[1;96m{SUBTITLE}\033[0m")
    console.print(f"\033[96m{'=' * 60}\033[0m\n")


def typewriter(text: str, delay: float = 0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def load_bugs(report_path: Path) -> list[dict]:
    if not report_path.exists():
        return []
    with open(report_path) as f:
        return json.load(f)


def print_bug_summary(bugs: list[dict]):
    for b in bugs:
        status = "done" if b.get("fixed") else "pending"
        style = "green" if b.get("fixed") else "red"
        icon = "+" if b.get("fixed") else "x"
        console.print(
            f"  [{style}][{icon}] {b['id']}[/] {b.get('route', '/billing')} "
            f"{b['category']} - {b['description'][:55]}"
        )


def success_banner():
    console.print()
    console.print(Panel(
        "[bold green]ALL BUGS FIXED[/bold green]",
        border_style="green",
        padding=(1, 4),
    ))


def max_iterations_banner():
    console.print()
    console.print(Panel(
        "[bold red]MAX ITERATIONS REACHED[/bold red]\n"
        "[red]Could not fix all bugs within the iteration limit.[/red]",
        border_style="red",
        padding=(1, 4),
    ))


def build_fix_prompt(bug: dict, files: list[str]) -> str:
    """Build a targeted Claude Code prompt for fixing a single bug."""
    file_list = " and ".join(f"`{f}`" for f in files)
    return (
        f"Fix this specific bug on the page:\n\n"
        f"Bug ID: {bug['id']}\n"
        f"Route: {bug.get('route', '/billing')}\n"
        f"Category: {bug['category']} | Severity: {bug['severity']}\n"
        f"Description: {bug['description']}\n\n"
        f"Apply a surgical fix to {file_list}. "
        f"Do not modify other files. After fixing, this specific bug should no longer reproduce."
    )


async def main():
    if len(sys.argv) < 3:
        console.print("[red]Usage: python loop.py <tunnel_url> <bug_report_path>[/red]")
        sys.exit(1)

    tunnel_url = sys.argv[1]
    bug_report_path = Path(sys.argv[2])
    print_banner()

    # Ensure bug report exists with default bugs if missing
    if not bug_report_path.exists():
        console.print("[red]Bug report not found. Run run_qa.py first.[/red]")
        sys.exit(1)

    for iteration in range(1, MAX_ITERATIONS + 1):
        console.print(
            f"\n[bold cyan]-- Iteration {iteration}/{MAX_ITERATIONS} --[/bold cyan]\n"
        )

        # ── Load current bug state ─────────────────────────────────
        bugs = load_bugs(bug_report_path)
        if not bugs:
            console.print("[red]No bug report found. Aborting.[/red]")
            break

        unfixed = [b for b in bugs if not b.get("fixed")]
        fixed = [b for b in bugs if b.get("fixed")]

        if not unfixed:
            success_banner()
            console.print(f"\n  Fixed: {len(fixed)}/{len(bugs)}")
            print_bug_summary(bugs)
            return

        # Pick the first unfixed bug — this is the one we work on this iteration
        bug = unfixed[0]
        bug_id = bug["id"]
        route = bug.get("route", "/billing")
        files = ROUTE_FILES.get(route, ["qa-sandbox/src/pages/Billing.jsx"])

        console.print(
            f"[yellow][{timestamp()}] Bug {bug_id} ({bug['category']}, "
            f"{bug['severity']}): {bug['description'][:60]}...[/yellow]"
        )
        console.print(f"  [dim]Route: {route} | Files: {', '.join(files)}[/dim]")

        # ── Run QA Agent (BrowserUse) — highlight ONE bug ──────────
        console.print(
            f"\n[yellow][{timestamp()}] BrowserUse: highlighting {bug_id}...[/yellow]"
        )

        proc = await asyncio.create_subprocess_exec(
            sys.executable, "run_qa.py", tunnel_url, str(bug_report_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            console.print(
                f"  [dim]{line.decode(errors='replace').rstrip()}[/dim]",
                highlight=False,
            )
        await proc.wait()

        # ── Read updated bug report ────────────────────────────────
        bugs = load_bugs(bug_report_path)
        unfixed = [b for b in bugs if not b.get("fixed")]
        fixed = [b for b in bugs if b.get("fixed")]

        console.print(f"\n  Progress: {len(fixed)}/{len(bugs)} fixed")
        print_bug_summary(bugs)

        if not unfixed:
            success_banner()
            return

        # ── Hand off to Claude Code to fix the SAME bug in source ──
        # BrowserUse marked bug_id as fixed (highlighted). Now fix the source
        # so the bug actually goes away. We target the same bug_id.
        bug_data = next((b for b in bugs if b["id"] == bug_id), bug)

        console.print(
            f"\n[magenta][{timestamp()}] Claude Code: fixing {bug_id}...[/magenta]\n"
        )

        prompt = build_fix_prompt(bug_data, files)

        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt,
            "--allowedTools", "Edit,Read,Write",
        )
        await proc.wait()

        typewriter(f"\nFix applied for {bug_id}.", 0.03)
        typewriter("Waiting for rebuild...", 0.03)
        typewriter("Re-running QA...\n", 0.03)

        # Reset the bug we just fixed so BrowserUse can re-verify next iteration.
        # Other bugs keep their current fixed state.
        bugs = load_bugs(bug_report_path)
        for b in bugs:
            if b["id"] == bug_id:
                b["fixed"] = False
        with open(bug_report_path, "w") as f:
            json.dump(bugs, f, indent=2)

        await asyncio.sleep(3)

    max_iterations_banner()


if __name__ == "__main__":
    asyncio.run(main())
