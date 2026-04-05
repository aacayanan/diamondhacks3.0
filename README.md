# Diamond Hacks 3.0 — Closed-Loop QA Automation

An autonomous QA testing system where one AI agent finds bugs in a live web app and another AI agent fixes them, in a one-bug-at-a-time closed loop until all issues are resolved.

```
  BrowserUse (finds bugs)  -->  bug_report.json  -->  Claude Code (fixes bugs)
         ^                                                      |
         |                                                      |
         +-------------------- loop.py -------------------------+
```

## How It Works

1. **BrowserUse** navigates to a live page via Cloudflare tunnel, identifies a bug, highlights it with a red border in the DOM, and saves the result to `bug_report.json`
2. **Claude Code** reads the bug report, explains the issue, and applies a surgical fix to the affected source file
3. **loop.py** rechecks the report, resets state, and runs the next iteration
4. Repeat until all bugs are resolved

Each bug is processed individually — never batched. Bugs carry a `route` field that constrains which source files Claude Code is allowed to edit.

## Project Structure

```
.
├── CLAUDE.md                        # Project guidance for Claude Code
├── run_qa_workflow.sh               # Multi-agent parallel orchestration script
├── .claude/
│   ├── commands/run-qa.md           # /run-qa slash command definition
│   └── settings.local.json          # Permission allowlist
├── .agents/skills/browser-use/      # BrowserUse CLI skill docs
│   ├── SKILL.md                     # Full CLI reference (40+ commands)
│   └── references/
│       ├── cdp-python.md            # Low-level CDP & Python session control
│       └── multi-session.md         # Multi-browser session guide
├── qa/
│   ├── run_qa.py                    # BrowserUse bug highlighter (one bug per run)
│   ├── loop.py                      # Auto-fix orchestrator (closed-loop engine)
│   ├── format_report.py             # Human-readable bug report formatter
│   ├── bug_report.json              # Live bug state (updated each iteration)
│   └── .env                         # BROWSER_USE_API_KEY
└── qa-sandbox/                      # React + Vite test application (target)
    ├── src/pages/Billing.jsx        # /billing route
    ├── src/pages/Settings.jsx       # /settings route
    ├── src/pages/Profile.jsx        # /profile route
    └── ...
```

## Prerequisites

- **Node.js** (for the qa-sandbox frontend)
- **Python 3.10+** with a virtual environment at `.venv/`
- **BrowserUse CLI** (`browser-use` command available on PATH)
- **BrowserUse SDK v3** (`browser_use_sdk` Python package)
- **Claude Code CLI** (`claude` command)
- **A `BROWSER_USE_API_KEY`** set in `qa/.env`

## Quick Start

### 1. Install dependencies

```bash
# Frontend
cd qa-sandbox && npm install && cd ..

# Python (create venv if needed)
python -m venv .venv
source .venv/Scripts/activate    # Windows
# source .venv/bin/activate      # macOS/Linux
pip install browser-use-sdk rich
```

### 2. Set your API key

```bash
# qa/.env
BROWSER_USE_API_KEY=your_key_here
```

### 3. Run the QA loop

Use the `/run-qa` slash command in Claude Code, or run manually:

```bash
# Start the dev server
cd qa-sandbox && npm run dev -- --host --port 3000 &

# Create a tunnel
browser-use tunnel 3000

# Run a QA iteration
cd qa && python run_qa.py <tunnel_host> bug_report.json
```

## Commands

### Frontend (from `qa-sandbox/`)

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server on port 3000 |
| `npm run build` | Production build |
| `npm run lint` | ESLint |
| `npm run preview` | Preview production build |

### QA Scripts

| Command | Description |
|---------|-------------|
| `python qa/run_qa.py <host> [report.json]` | Run BrowserUse on the first unfixed bug |
| `python qa/loop.py <host> <report.json>` | Run the full closed-loop orchestrator |
| `python qa/format_report.py <report.json>` | Print a human-readable bug summary |

### Tunnel Management

| Command | Description |
|---------|-------------|
| `browser-use tunnel <port>` | Start a Cloudflare tunnel |
| `browser-use tunnel list` | List active tunnels |
| `browser-use tunnel stop --all` | Stop all tunnels |

### Multi-Agent Workflow

```bash
./run_qa_workflow.sh
```

Starts 3 parallel BrowserUse agents, each with its own tunnel, testing different routes simultaneously. Includes an approval gate before running fixes.

## The `/run-qa` Command

The `/run-qa` slash command (defined in `.claude/commands/run-qa.md`) orchestrates the full workflow:

**Phase 1 — Environment Setup**
- Activate `.venv`
- Start dev server if not running
- Start or reuse a Cloudflare tunnel

**Phase 2 — Bug Fix Loop** (one bug at a time)
1. Run `run_qa.py` to highlight the first unfixed bug
2. Read `bug_report.json` and present the bug to the user
3. Apply a surgical fix to the affected source file
4. Run `loop.py` to recheck for remaining bugs
5. Repeat until all bugs are resolved

**Phase 3 — Cleanup**
- Kill dev server and tunnel processes

## Bug Report Format

Each bug in `bug_report.json` follows this schema:

```json
{
  "id": "BUG-001",
  "route": "/billing",
  "selector": "div.card (Usage Statistics)",
  "tagName": "DIV",
  "description": "Usage Statistics card overlaps the Subscription Plan card.",
  "category": "Visual",
  "severity": "High",
  "fixed": false
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique identifier (`BUG-NNN`) |
| `route` | Target page route (`/billing`, `/settings`, `/profile`) |
| `selector` | CSS selector or element description |
| `tagName` | HTML tag type (`DIV`, `BUTTON`, `SPAN`, etc.) |
| `description` | Human-readable bug description |
| `category` | `Visual` / `Functional` / `UX` / `Functional/UX` |
| `severity` | `High` / `Medium` / `Low` |
| `fixed` | Boolean — set by BrowserUse, reset by loop.py for verification |

## Route-to-File Mapping

Bugs are scoped to specific source files based on their route:

| Route | Source Files |
|-------|-------------|
| `/billing` | `qa-sandbox/src/pages/Billing.jsx`, `Billing.css` |
| `/settings` | `qa-sandbox/src/pages/Settings.jsx`, `Settings.css` |
| `/profile` | `qa-sandbox/src/pages/Profile.jsx`, `Profile.css` |

Claude Code only edits files mapped to the bug's route — never other files.

## Architecture

### run_qa.py — Bug Highlighter

- Uses the **BrowserUse SDK v3** with the **Gemini 3-Flash** model
- Navigates to the bug's route via Cloudflare tunnel
- Finds the target element by selector/description
- Applies a red 3px border: `element.style.border = '3px solid red'`
- Fills empty form fields with sample data
- Interacts with toggles/dropdowns to demonstrate issues
- Processes **one bug per invocation** — the orchestrator handles the loop
- 60-second timeout per bug

### loop.py — Closed-Loop Orchestrator

- Reads `bug_report.json`, picks the first unfixed bug
- Calls `run_qa.py` to highlight it with BrowserUse
- Calls `claude -p "..." --allowedTools Edit,Read,Write` to fix it
- Resets the bug's `fixed` flag for re-verification
- Loops until all bugs are resolved or 20 iterations reached

### format_report.py — Report Display

- Reads a bug report JSON file
- Prints status, affected file, and each bug with severity indicators
- Supports both list and dict report formats

### run_qa_workflow.sh — Multi-Agent Orchestration

- Starts 3 parallel BrowserUse agents with separate tunnels
- Copies each agent's report to `qa/bug_reports/agent_N.json`
- Displays a unified summary using `format_report.py`
- Includes an approval gate before applying fixes
- Runs `loop.py` per agent, then re-runs QA for verification
- Saves post-fix reports as `agent_N_post_fix.json`

## Constraints

- **One bug at a time** — never batch fixes
- **Claude is the orchestrator** — it calls `run_qa.py` and `loop.py` manually at each step
- **Route-aware** — only edit files mapped to the bug's route field
- **Present before fixing** — always read and explain the bug before applying a fix
- **Tunnel URLs are CLI args only** — never written to files
- **Always activate `.venv`** before running Python

## License

MIT
