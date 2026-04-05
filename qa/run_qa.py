import asyncio
import os
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

    # Initialize the BrowserUse client
    client = AsyncBrowserUse(api_key=api_key)

    # Create a workspace and link it to the client
    workspace = await client.workspaces.create(name="qa-workspace")

    # Define the task to get top 3 stories from Hacker News
    # task = "Navigate to https://news.ycombinator.com/ and find the top 3 stories. Then go to https://tldr.tech/ and get the top story"
    # task = "Navigate to https://href-networks-seemed-robust.trycloudflare.com/ and get all the form data. Put john doe boiler sample to fill it out and then return a json of the web contents."
    task = """
    Navigate to href-networks-seemed-robust.trycloudflare.com/. 

Fill out all visible form fields with placeholder test data. 
Then attempt to click the Submit button.

If the Submit button cannot be clicked:
- Inspect the DOM to find the exact reason why
- Record the element selector, tag name, and any blocking attributes (e.g. disabled, hidden, aria-disabled)
- Retry clicking up to 3 times before marking it as a failure
- On each retry, re-inspect the DOM and note if anything changed
- If all retries fail, record the final failure reason explicitly

Save your full findings as bug_report.json in the workspace using this structure:
{
  "status": "success" | "bug_found" | "failed",
  "timestamp": "<ISO timestamp>",
  "actions_taken": [
    "<step 1 you performed>",
    "<step 2 you performed>",
    "..."
  ],
"likely_file": "src/App.jsx",
  "notes": "<anything else observed that may be relevant>"

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

    # Attempt to parse as JSON to validate and re-serialize for consistent formatting
    try:
        parsed_data = json.loads(output_data)
        # Write formatted JSON to file
        with open("qa/bug_report.json", "w") as f:
            json.dump(parsed_data, f, indent=2)
    except json.JSONDecodeError:
        # If output is not valid JSON, write the raw string (though task expects JSON)
        with open("qa/bug_report.json", "w") as f:
            f.write(output_data)

    # Delete the workspace
    await client.workspaces.delete(workspace.id)

    # Print a confirmation to the terminal
    print("Successfully saved bug report to bug_report.json and deleted workspace")

if __name__ == "__main__":
    asyncio.run(main())