import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from browser_use_sdk.v3 import AsyncBrowserUse

class BugReport(BaseModel):
    status: str = Field(description='One of "success", "bug_found", or "failed"')
    timestamp: str = Field(description="ISO 8601 timestamp of when the report was generated")
    actions_taken: list[str] = Field(description="Ordered list of steps the agent performed during testing")
    likely_file: str = Field(description="Relative path to the source file most likely containing the bug")
    notes: str = Field(description="Any additional observations or context relevant to the findings")


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
    page_url = tunnel_url

    # Initialize the BrowserUse client
    client = AsyncBrowserUse(api_key=api_key)

    # Create a workspace and link it to the client
    workspace = await client.workspaces.create(name="qa-workspace")

    # Define the task to test for visual/UX bugs
    task = f"""
    You are testing exactly ONE page: {page_url}

    Navigate to {page_url} and test only this page. Do NOT click any tabs, navigation links, menu items, or anything that changes the visible content. Only interact with form fields and buttons that are already visible on the initial page load. If you navigate away for any reason, stop immediately and return results.

    Fill out all visible form fields with placeholder test data.
    Then attempt to click the primary action button (this may be labeled Submit, Save, Save Changes, Continue, or similar).
    
    If the button cannot be clicked:
    - Inspect the DOM to find the exact reason why
    - Record the element selector, tag name, and any blocking attributes (e.g. disabled, hidden, aria-disabled)
    - Retry clicking up to 3 times before marking it as a failure
    - On each retry, re-inspect the DOM and note if anything changed
    - If all retries fail, record the final failure reason explicitly
    """
    model = "gemini-3-flash"

    # Run the BrowserUse agent with the task and model
    result = await client.run(
        task=task,
        output_schema=BugReport,
        model=model,
        workspace_id=workspace.id,
    )

    files = await client.workspaces.files(workspace.id)
    for f in files.files:
        if f.path.endswith(".png"):
            await client.workspaces.download(workspace.id, f.path, to=f"./qa/screenshots/{f.path}")
            print(f"Downloaded: {f.path}")

    # Extract the structured bug report from the agent result
    bug = result.output
    print(bug)

    bug_report_path = os.path.join(os.path.dirname(__file__), "bug_report.json")
    with open(bug_report_path, "w") as f:
        json.dump(bug.model_dump(), f, indent=2)

    # Delete the workspace
    await client.workspaces.delete(workspace.id)

    # Print a confirmation to the terminal
    print("Successfully saved bug report to bug_report.json and deleted workspace")

if __name__ == "__main__":
    asyncio.run(main())