import asyncio
import os
import sys
import json
import subprocess
import time
import re
import urllib.request
from browser_use_sdk.v3 import AsyncBrowserUse

DEV_PORT = 3000

# Route → source files that Claude Code can fix
ROUTE_FILES = {
    "/billing":  ["qa-sandbox/src/pages/Billing.jsx",  "qa-sandbox/src/pages/Billing.css"],
    "/settings": ["qa-sandbox/src/pages/Settings.jsx", "qa-sandbox/src/pages/Settings.css"],
    "/profile":  ["qa-sandbox/src/pages/Profile.jsx",  "qa-sandbox/src/pages/Profile.css"],
}

# Default bug report — billing page bugs
DEFAULT_BUGS = [
    {
        "id": "BUG-001",
        "route": "/billing",
        "selector": "div.card (Usage Statistics)",
        "tagName": "DIV",
        "description": "Usage Statistics card overlaps the Subscription Plan card, obscuring the Enterprise tier.",
        "category": "Visual",
        "severity": "High",
        "fixed": False
    },
    {
        "id": "BUG-002",
        "route": "/billing",
        "selector": "span ($19/mo, $49/mo, $199/mo)",
        "tagName": "SPAN",
        "description": "Pricing Toggle Bug: The price labels in plan cards do not update when switching to Annual billing.",
        "category": "Functional",
        "severity": "High",
        "fixed": False
    },
    {
        "id": "BUG-003",
        "route": "/billing",
        "selector": "button (Update Plan)",
        "tagName": "BUTTON",
        "description": "Low Discoverability: The primary 'Update Plan' action is far from the selection area at the bottom of the page.",
        "category": "UX",
        "severity": "Medium",
        "fixed": False
    },
    {
        "id": "BUG-004",
        "route": "/billing",
        "selector": "button (Add Payment Method)",
        "tagName": "BUTTON",
        "description": "Redundant Buttons: Multiple 'Add Payment Method' buttons are present, which may be confusing.",
        "category": "UX",
        "severity": "Low",
        "fixed": False
    },
    {
        "id": "BUG-005",
        "route": "/billing",
        "selector": "tr (INV-004)",
        "tagName": "TR",
        "description": "Actionability: 'Pending' invoice INV-004 lacks necessary actions (e.g. Pay) compared to 'Paid' ones.",
        "category": "UX",
        "severity": "Medium",
        "fixed": False
    },
    {
        "id": "BUG-006",
        "route": "/billing",
        "selector": "button (Update Plan)",
        "tagName": "BUTTON",
        "description": "Lack of Feedback: Clicking 'Update Plan' provides no success message, toast, or navigation, leaving the user uncertain of the result.",
        "category": "Functional/UX",
        "severity": "Medium",
        "fixed": False
    }
]


def start_tunnel(port: int) -> tuple[int | None, str | None]:
    """Start a BrowserUse tunnel (with ngrok fallback) for the given port."""
    try:
        proc = subprocess.Popen(
            ["browser-use", "tunnel", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        time.sleep(5)
        url = get_tunnel_url_for_port(port)
        if url:
            return (proc.pid, url)
        proc.kill()
    except FileNotFoundError:
        pass

    try:
        proc = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        time.sleep(5)
        req = urllib.request.Request("http://localhost:4040/api/tunnels")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        for t in data.get("tunnels", []):
            url = t.get("public_url", "")
            if "ngrok" in url:
                return (proc.pid, url)
        proc.kill()
    except Exception:
        pass

    return (None, None)


def get_tunnel_url_for_port(port: int) -> str | None:
    """Read tunnel URL for the given port from browser-use tunnel list."""
    try:
        result = subprocess.run(
            ["browser-use", "tunnel", "list"],
            capture_output=True, text=True, timeout=10,
            shell=True,
        )
        output = result.stdout + result.stderr
        for line in output.strip().splitlines():
            if f"port {port}" in line:
                match = re.search(r"(https://\S+trycloudflare\S+)", line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return None


async def process_single_bug(client, tunnel_url: str, bug: dict) -> dict:
    """Send one bug to BrowserUse: navigate to the bug's route, find the element,
    add a red border, fill any input fields, then return."""

    route = bug.get("route", "/billing")
    target_url = f"https://{tunnel_url}{route}"
    model = "gemini-3-flash"

    task = f"""
Navigate to {target_url}.

You are highlighting a known bug on the page. Here is the bug:

- Bug ID: {bug['id']}
- Element: {bug['selector']}
- Tag: {bug['tagName']}
- Description: {bug['description']}
- Category: {bug['category']}
- Severity: {bug['severity']}

Do these steps:

1. Wait for the page to fully load.
2. Find the element described by the selector/description above.
3. Use JavaScript to add a red 3px solid border around it:
   element.style.border = '3px solid red'
4. If there are any empty text inputs, email fields, or textareas visible on the page, fill them with sample data (e.g. "Test User", "test@example.com", "This is a test message").
5. If the bug involves a billing cycle toggle or select dropdown, interact with it (e.g. switch to Annual) to demonstrate the issue.
6. Report back: did you find the element and apply the border? Did you fill any fields?

Return a short JSON summary like:
{{"bug_id": "{bug['id']}", "border_applied": true, "fields_filled": ["name", "email"], "notes": "..."}}
"""

    try:
        result = await asyncio.wait_for(client.run(task=task, model=model), timeout=60)
        return result.output
    except asyncio.TimeoutError:
        return {"bug_id": bug['id'], "border_applied": False, "fields_filled": [], "notes": "Timed out waiting for BrowserUse API response (browser session may have completed but API didn't return)"}


async def run_bug_loop(client, tunnel_url: str, bugs: list[dict], report_path: str):
    """Process the first unfixed bug only. The orchestrator (loop.py) handles
    the fix-verify cycle and re-invokes us for the next bug."""

    for i, bug in enumerate(bugs):
        if bug.get("fixed"):
            continue

        print(f"  [{bug['id']}] processing: {bug['description'][:60]}...", flush=True)

        try:
            output = await process_single_bug(client, tunnel_url, bug)
            timed_out = isinstance(output, dict) and "Timed out" in output.get("notes", "")
            bug["fixed"] = True
            print(f"  [{bug['id']}] {'timeout' if timed_out else 'done'}", flush=True)
        except Exception as e:
            bug["fixed"] = False
            print(f"  [{bug['id']}] failed: {e}", flush=True)

        # Write updated bug list so the looper can parse progress
        with open(report_path, "w") as f:
            json.dump(bugs, f, indent=2)

        return  # Only process one bug per invocation

    print("  No unfixed bugs to process.")


async def main():
    # Get API key
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        if key == "BROWSER_USE_API_KEY":
                            api_key = value
                            break
    if not api_key:
        raise ValueError("BROWSER_USE_API_KEY not found")

    # Get tunnel host from CLI
    if len(sys.argv) < 2:
        print("Usage: python run_qa.py <tunnel_host> [bug_report.json]")
        sys.exit(1)

    tunnel_host = sys.argv[1]

    # Load bugs: from file if provided, else use defaults
    bugs_path = sys.argv[2] if len(sys.argv) > 2 else None
    if bugs_path and os.path.exists(bugs_path):
        with open(bugs_path, "r") as f:
            bugs = json.load(f)
        print(f"Loaded {len(bugs)} bugs from {bugs_path}")
    else:
        bugs = json.loads(json.dumps(DEFAULT_BUGS))  # deep copy
        print(f"Using {len(bugs)} default billing bugs")

    # Ensure all bugs have required fields
    for i, bug in enumerate(bugs):
        if "id" not in bug:
            bug["id"] = f"BUG-{i+1:03d}"
        if "fixed" not in bug:
            bug["fixed"] = False

    unfixed = [b for b in bugs if not b.get("fixed")]
    if unfixed:
        route = unfixed[0].get("route", "/billing")
        print(f"Target: https://{tunnel_host}{route}")
    print(f"Bugs to process: {len(unfixed)}")

    # Write initial bug list
    report_path = os.path.join(os.path.dirname(__file__), "bug_report.json")
    with open(report_path, "w") as f:
        json.dump(bugs, f, indent=2)

    # Run one bug through BrowserUse — loop.py handles the fix-verify cycle
    client = AsyncBrowserUse(api_key=api_key)
    await run_bug_loop(client, tunnel_host, bugs, report_path)

    # Final summary
    fixed = [b for b in bugs if b.get("fixed")]
    failed = [b for b in bugs if not b.get("fixed")]

    print(f"\n=== QA Complete ===")
    print(f"  Processed: {len(fixed)}/{len(bugs)}")
    if failed:
        print(f"  Failed: {len(failed)}")
        for b in failed:
            print(f"    - {b['id']}: {b['description'][:50]}")
    print(f"  Report: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
