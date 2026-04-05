import asyncio
import os
import sys
import json
import subprocess
import time
import re
import urllib.request
from pydantic import BaseModel
from browser_use_sdk.v3 import AsyncBrowserUse

ROUTES = ["/billing", "/settings", "/"]
DEV_PORT = 3000


class PageContext(BaseModel):
    page_type: str
    primary_user_goal: str
    page_summary: str
    visible_sections: list[str]
    interactive_elements: list[str]
    likely_risk_areas: list[str]
    suggested_manual_qa_checks: list[str]


def start_tunnel(port: int) -> tuple[int | None, str | None]:
    """Start a BrowserUse tunnel (with ngrok fallback) for the given port.
    Returns (pid, full_url) or (None, None) on failure."""
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

    # Fallback to ngrok
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
    """Read tunnel URL that maps to the specific port from browser-use tunnel list.
    Expected format: '  port 3000: https://foo-bar.trycloudflare.com'"""
    try:
        result = subprocess.run(
            ["browser-use", "tunnel", "list"],
            capture_output=True, text=True, timeout=10,
            shell=True,
        )
        output = result.stdout + result.stderr
        for line in output.strip().splitlines():
            # Match lines like "  port 3000: https://foo.trycloudflare.com"
            if f"port {port}" in line:
                match = re.search(r"(https://\S+trycloudflare\S+)", line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return None


async def run_single_agent(client, tunnel_url: str, agent_index: int) -> dict:
    """Run a two-pass QA audit for a single route in its own workspace."""
    workspace = await client.workspaces.create(name=f"qa-workspace-{agent_index}")
    report_path = os.path.join(os.path.dirname(__file__), f"bug_report_{agent_index}.json")
    screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots", f"agent_{agent_index}")
    os.makedirs(screenshot_dir, exist_ok=True)

    model = "gemini-3-flash"
    route = ROUTES[agent_index]
    target_url = f"https://{tunnel_url}{route}"
    result = {"url": target_url, "route": route, "status": "success", "bugs": 0, "error": None}

    try:
        # PASS 1: Recon / context gathering
        context_task = f"""
            Navigate to {target_url}.

            Analyze ONLY the initial page without doing a full audit.
            Determine:
            1. What kind of page this is
            2. What the user is most likely trying to accomplish here
            3. What major sections are visible
            4. What interactive elements are visible
            5. What UX risk areas are most likely on this page
            6. What a manual QA tester would most likely test first

            Return structured output only.
            """

        context_result = await client.run(
            task=context_task,
            model=model,
            output_schema=PageContext,
        )

        context = context_result.output

        # PASS 2: Targeted audit using the context
        audit_task = f"""
            You are performing a UX QA audit of ONLY the initial page at {target_url}.

            PAGE CONTEXT:
            - Page type: {context.page_type}
            - Primary user goal: {context.primary_user_goal}
            - Page summary: {context.page_summary}
            - Visible sections: {", ".join(context.visible_sections)}
            - Interactive elements: {", ".join(context.interactive_elements)}
            - Likely risk areas: {", ".join(context.likely_risk_areas)}
            - Suggested manual QA checks: {", ".join(context.suggested_manual_qa_checks)}

            Perform a focused visual and UX audit of ONLY the initial page then exit:
            1. Prioritize checks based on the page context above
            2. Check interactive elements relevant to the page's primary goal
            3. Look for visual issues: misalignment, overlap, clipping, spacing, hierarchy
            4. Check readability and contrast
            5. Test only high-value interactions on the initial page
            6. Note responsiveness issues if visible in the current viewport

            For any bugs found:
            - Use JavaScript to add a red 3px solid border around the buggy element in the DOM (e.g. element.style.border = '3px solid red') before taking the screenshot
            - Take a screenshot and save it to the workspace
            - Record the element selector if identifiable, tag name, and issue description
            - Note the bug category and severity
            - Retry interaction up to 2 times if needed
            - Save screenshots after retries when useful

            Save the final findings as bug_report.json in the workspace.
            Return a concise final summary.
            """

        audit_result = await client.run(
            task=audit_task,
            model=model,
            workspace_id=workspace.id,
        )

        # Download screenshots to agent-specific directory
        files = await client.workspaces.files(workspace.id)
        for f in files.files:
            if f.path.endswith(".png"):
                await client.workspaces.download(workspace.id, f.path, to=os.path.join(screenshot_dir, f.path))

        output_data = audit_result.output

        # Download bug_report.json and format it
        await client.workspaces.download(workspace.id, "bug_report.json", to=report_path)

        try:
            with open(report_path, "r") as f:
                parsed_data = json.load(f)
            with open(report_path, "w") as f:
                json.dump(parsed_data, f, indent=2)
            # Count bugs if present
            if isinstance(parsed_data, dict) and "bugs" in parsed_data:
                result["bugs"] = len(parsed_data["bugs"]) if isinstance(parsed_data["bugs"], list) else int(parsed_data["bugs"])
            elif isinstance(parsed_data, list):
                result["bugs"] = len(parsed_data)
        except (json.JSONDecodeError, FileNotFoundError):
            with open(report_path, "w") as f:
                f.write(str(output_data))

        if result["bugs"] > 0:
            result["status"] = "bug_found"

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        with open(report_path, "w") as f:
            json.dump(result, f, indent=2)

    finally:
        try:
            await client.workspaces.delete(workspace.id)
        except Exception:
            pass

    return result


async def main():
    # Try to get API key from environment variable first, then fall back to .env file
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        # Try to read from .env file
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
        raise ValueError("BROWSER_USE_API_KEY not found in environment variables or .env file")

    # --- Get tunnel host from CLI argument ---
    if len(sys.argv) < 2:
        print("Usage: python run_qa.py <tunnel_host>")
        print("  Example: python run_qa.py busy-hose-sitemap-enabled.trycloudflare.com")
        sys.exit(1)

    tunnel_host = sys.argv[1]
    tunnel_hosts = [tunnel_host] * len(ROUTES)  # Use same host for all routes
    tunnel_pids = [None] * len(ROUTES)  # No PIDs since we're not starting tunnels

    print(f"Using tunnel: https://{tunnel_host}")

    # --- Run single QA agent ---
    client = AsyncBrowserUse(api_key=api_key)
    task = run_single_agent(client, tunnel_host, 1)  # Use agent_index 1 for /settings route
    result = await task

    # Write consolidated result to bug_report.json
    report_path = os.path.join(os.path.dirname(__file__), "bug_report.json")
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)

    # --- Print result ---
    print("\n=== QA Result ===")
    print(f"  URL: {result['url']}")
    print(f"  Route: {result['route']}")
    print(f"  Status: {result['status']}")
    print(f"  Bugs found: {result.get('bugs', 0)}")
    if result.get('error'):
        print(f"  Error: {result['error']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
