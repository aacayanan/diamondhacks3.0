#!/usr/bin/env python3
"""AUTO-QA Agentic Loop Orchestrator."""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

console = Console()
MAX_ITERATIONS = 5

BANNER = r"""
  ___         _        _____    ___
 / _ \  _   _(_) _ __  \_   \  / _ \  __ _  ___  ___  __ _
| | | || | | | || '_ \  / /\/ | | | |/ _` |/ _ \/ __|/ _` |
| |_| || |_| | || |_) |/ /    | |_| | (_| |  __/\__ \ (_| |
 \__\_\\__,_|_|| .__/ \/      \___/ \__, |\___||___/\__,_|
               |_|                   |___/
"""

SUBTITLE = "🤖 Developer Agent  ×  🌐 QA Agent  |  Closed Loop"


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


def make_status_panel(iteration: int, agent: str, status: str, report_name: str) -> Panel:
    t = Text()
    t.append(f"  Iteration: ", style="bold")
    t.append(f"{iteration} / {MAX_ITERATIONS}   ", style="cyan")
    t.append("│  ", style="dim")
    t.append("Active Agent: ", style="bold")
    agent_style = "magenta" if agent == "Claude Code" else "yellow"
    t.append(f"{agent}   ", style=agent_style)
    t.append("│  ", style="dim")
    t.append("Status: ", style="bold")
    if status == "running":
        t.append(status, style="yellow")
    elif status == "bug_found":
        t.append(status, style="red")
    elif status == "success":
        t.append(status, style="green")
    else:
        t.append(status, style="white")
    return Panel(t, title=f"[bold]AUTO-QA Orchestrator — {report_name}[/bold]", border_style="cyan")


def success_banner():
    console.print()
    console.print(Panel(
        "[bold green]✦  ALL TESTS PASSED  ✦[/bold green]",
        border_style="green",
        padding=(1, 4),
    ))
    console.print()


def max_iterations_banner():
    console.print()
    console.print(Panel(
        "[bold red]⚠  MAX ITERATIONS REACHED  ⚠[/bold red]\n"
        "[red]Could not pass all QA tests within the iteration limit.[/red]",
        border_style="red",
        padding=(1, 4),
    ))
    console.print()


async def main():
    if len(sys.argv) < 3:
        console.print("[red]Usage: python loop.py <tunnel_url> <bug_report_path>[/red]")
        sys.exit(1)

    tunnel_url = sys.argv[1]
    bug_report_path = Path(sys.argv[2])
    agent_label = f"[Agent {bug_report_path.stem.split('_')[-1]}]"
    print_banner()

    for iteration in range(1, MAX_ITERATIONS + 1):
        agent = "BrowserUse"
        status = "running"

        console.print(f"\n[bold cyan]{agent_label} ── Iteration {iteration}/{MAX_ITERATIONS} ──[/bold cyan]\n")

        # ── Clear stale report ─────────────────────────────────────
        if bug_report_path.exists():
            bug_report_path.unlink()
            console.print(f"[dim][{timestamp()}] {agent_label} Removed stale {bug_report_path.name}[/dim]")

        # ── Run QA Agent ───────────────────────────────────────────
        console.print(make_status_panel(iteration, agent, status, bug_report_path.name))
        console.print(f"[yellow][{timestamp()}] {agent_label} 🌐 Starting BrowserUse QA Agent...[/yellow]")

        proc = await asyncio.create_subprocess_exec(
            sys.executable, "run_qa.py", tunnel_url, "--report-path", str(bug_report_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            console.print(f"  [dim]{line.decode(errors='replace').rstrip()}[/dim]", highlight=False)
        await proc.wait()

        # ── Read bug report ────────────────────────────────────────
        if not bug_report_path.exists():
            console.print(f"[red][{timestamp()}] {agent_label} ERROR: No {bug_report_path.name} produced. Aborting.[/red]")
            break

        with open(bug_report_path) as f:
            report = json.load(f)

        qa_status = report.get("status", "unknown")

        # ── SUCCESS ────────────────────────────────────────────────
        if qa_status == "success":
            console.print(f"[green][{timestamp()}] {agent_label} ✅ QA status: success[/green]")
            success_banner()
            return

        # ── BUG FOUND ──────────────────────────────────────────────
        if qa_status == "bug_found":
            console.print(f"\n[red][{timestamp()}] {agent_label} 🐛 BUG FOUND[/red]")
            console.print(f"[red]  Notes: {report.get('notes', 'N/A')}[/red]")
            console.print(f"[red]  File : {report.get('likely_file', 'N/A')}[/red]\n")

            typewriter("📖 Reading bug report...", 0.03)
            typewriter("🔍 Locating the disabled attribute in App.jsx...", 0.03)
            typewriter("🔧 Preparing fix for Claude Code...\n", 0.03)

            # ── Hand off to Claude Code CLI ────────────────────────
            agent = "Claude Code"
            console.print(make_status_panel(iteration, agent, "bug_found", bug_report_path.name))
            console.print(f"[magenta][{timestamp()}] {agent_label} 🤖 Claude Code is fixing the bug...[/magenta]\n")

            bug_json = json.dumps(report, indent=2)
            prompt = (
                "A QA agent found a bug in the feedback form. Here is the bug report:\n\n"
                f"{bug_json}\n\n"
                "Fix the bug: the Submit button in src/App.jsx has `disabled={{true}}` "
                "hardcoded. Remove the disabled attribute so the button is clickable. "
                "Save the file. Do not modify anything else."
            )

            # ⚠️ No stdout=PIPE — Claude Code must inherit the terminal to work correctly
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p", prompt,
                "--allowedTools", "Edit,Read,Write",
            )
            await proc.wait()

            typewriter("\n✅ Fix applied.", 0.03)
            typewriter("⚡ Hot-reload triggered — waiting for React to rebuild...", 0.03)
            typewriter("🔄 Re-running QA agent...\n", 0.03)

            await asyncio.sleep(3)
            continue

        # ── FAILED / UNKNOWN ───────────────────────────────────────
        console.print(f"[yellow][{timestamp()}] {agent_label} WARNING: Unexpected status '{qa_status}'. Stopping.[/yellow]")
        break

    max_iterations_banner()


if __name__ == "__main__":
    asyncio.run(main())