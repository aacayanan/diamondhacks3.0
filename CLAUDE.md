# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Diamond Hacks 3.0 — a QA testing demo with two components:

- **Frontend** (`qa-sandbox/`): React + Vite feedback form app (intentional bug: Submit button is `disabled={true}` but styled to look enabled)
- **QA Agent** (`qa/`): Python script using BrowserUse SDK v3 that automates browser testing against the form via Cloudflare tunnel

## Commands

### Frontend (run from `qa-sandbox/`)

```bash
npm run dev          # Start dev server on port 3000
npm run build        # Production build
npm run lint         # ESLint
npm run preview      # Preview production build
```

### QA Testing

The full QA workflow is automated via the `/run-qa` command (defined in `.claude/commands/run-qa.md`). The loop is one bug at a time:

1. Run `run_qa.py` → BrowserUse highlights the first unfixed bug, saves result to `bug_report.json`
2. Claude reads `bug_report.json`, explains the bug, applies a surgical fix to the source files
3. Run `loop.py` → rechecks for unfixed bugs, resets state for verification
4. Repeat from step 1 until all bugs are resolved

**Constraints for QA runs:**
- One bug at a time — never batch fixes
- Only edit files in the bug's `route` mapping (e.g. `/billing` → `Billing.jsx`)
- `TUNNEL_HOST` is passed as a CLI argument, never written to files
- Always activate `.venv` before running Python (`source .venv/Scripts/activate` on Windows)

### Python Environment

Python deps are in a local `.venv/`. The QA script needs `BROWSER_USE_API_KEY` set in `qa/.env`.

## Architecture

```
qa-sandbox/src/App.jsx             — React Router setup with routes for Dashboard, FeedbackForm, Billing, Settings, Profile
qa-sandbox/src/App.css             — Styling including disabled button styles
qa-sandbox/src/pages/FeedbackForm.jsx  — Feedback form (Name, Email, Message, Submit button at /form route)
qa/run_qa.py                       — BrowserUse agent that tests multiple routes and outputs bug reports
qa/loop.py                         — Auto-fix orchestration that uses claude code to fix bugs
qa/format_report.py                — Formats bug reports for human-readable display
```

The QA agent (`qa/run_qa.py`) creates BrowserUse workspaces, runs automated browser sessions against tunnel URLs for routes `/billing`, `/settings`, `/profile`, and outputs structured bug reports. The `loop.py` orchestrates the auto-fix workflow by passing bug reports to Claude Code for fixes.

## Intentional Bug

**Note:** The intentional bug in this demo is that the Submit button in `qa-sandbox/src/pages/FeedbackForm.jsx` has `disabled={true}` hardcoded. However, examining the current code, the submit button (line 47) does NOT currently have this attribute.

The CSS in `qa-sandbox/src/App.css` (lines 116-122) contains styles for disabled buttons that keep them looking enabled (`opacity: 1`), which suggests the bug should exist. The QA agent is designed to detect when a button appears clickable but is actually disabled in the DOM.

Do not modify source files or "fix" bugs unless explicitly asked.
