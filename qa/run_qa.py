import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from browser_use_sdk.v3 import AsyncBrowserUse

class PageContext(BaseModel):
    page_type: str
    primary_user_goal: str
    page_summary: str
    visible_sections: list[str]
    interactive_elements: list[str]
    likely_risk_areas: list[str]
    suggested_manual_qa_checks: list[str]

async def main():
    # Load environment variables from .env file
    load_dotenv()

    # Get API key from environment variable
    api_key = os.getenv("BROWSER_USE_API_KEY")
    if not api_key:
        raise ValueError("BROWSER_USE_API_KEY not found in environment variables")

    # Get tunnel URL from CLI arguments
    if len(sys.argv) < 2:
        print("Usage: python run_qa.py <tunnel_url>")
        sys.exit(1)
    tunnel_url = sys.argv[1]

    # Initialize the BrowserUse client
    client = AsyncBrowserUse(api_key=api_key)
    workspace = await client.workspaces.create(name="qa-workspace")

    model = "gemini-3-flash"

    # PASS 1: Recon / context gathering
    context_task = f"""
        Navigate to {tunnel_url}.

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
        You are performing a UX QA audit of ONLY the initial page at {tunnel_url}.

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

    files = await client.workspaces.files(workspace.id)
    for f in files.files:
        if f.path.endswith(".png"):
            await client.workspaces.download(workspace.id, f.path, to=f"./qa/screenshots/{f.path}")
            print(f"Downloaded: {f.path}")

    # Extract the output (assumed to be a JSON string)
    output_data = audit_result.output
    print(output_data)

    # The BrowserUse agent writes bug_report.json in the same directory as this script.
    # Read that file to get the JSON.
    bug_report_path = os.path.join(os.path.dirname(__file__), "bug_report.json")

    # Download the file to your local machine
    print(workspace.id, "Bug Report")
    for f in files.files:
        print(f.path, f.size)

    await client.workspaces.download(workspace.id, "bug_report.json", to="./bug_report.json")

    try:
        with open(bug_report_path, "r") as f:
            parsed_data = json.load(f)
        # Re-write formatted JSON
        with open(bug_report_path, "w") as f:
            json.dump(parsed_data, f, indent=2)
        print(parsed_data)
    except (json.JSONDecodeError, FileNotFoundError):
        with open(bug_report_path, "w") as f:
            f.write(output_data)

    # Print a confirmation to the terminal
    print("Successfully saved bug report to bug_report.json and deleted workspace")

    #Delete the workspace
    try:
        await client.workspaces.delete(workspace.id)
    except Exception as e:
        print(f"Warning: Failed to delete workspace: {e}")

if __name__ == "__main__":
    asyncio.run(main())
