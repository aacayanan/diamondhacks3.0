import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from browser_use_sdk.v3 import AsyncBrowserUse

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

    # Create a workspace and link it to the client
    workspace = await client.workspaces.create(name="qa-workspace")

    # Define the task to get top 3 stories from Hacker News
    task = f"""
    Your output MUST be saved as bug_report.json with EXACTLY this JSON structure and no other format:

    {{
      "status": "success" | "bug_found" | "failed",
      "timestamp": "<ISO timestamp>",
      "actions_taken": [
        "<step 1 you performed>",
        "<step 2 you performed>",
        "..."
      ],
      "likely_file": "src/App.jsx",
      "notes": "<anything else observed that may be relevant>"
    }}

    Do not deviate from this structure. All findings must map into this schema.

    ---

    Now perform the following task:

    Navigate to {tunnel_url}.

    Fill out all visible form fields with placeholder test data.
    Then attempt to click the Submit button.

    If the Submit button cannot be clicked:
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
        model=model,
        workspace_id=workspace.id,
    )

    # Extract the output (assumed to be a JSON string)
    output_data = result.output
    print(output_data)

    # The BrowserUse agent writes bug_report.json in the same directory as this script.
    # Read that file to get the JSON.
    bug_report_path = os.path.join(os.path.dirname(__file__), "bug_report.json")

    # Download the file to your local machine
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

    # Delete the workspace
    await client.workspaces.delete(workspace.id)

    # Print a confirmation to the terminal
    print("Successfully saved bug report to bug_report.json and deleted workspace")

if __name__ == "__main__":
    asyncio.run(main())