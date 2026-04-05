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

The full QA workflow is automated via the `/run-qa` command (defined in `.claude/commands/run-qa.md`). The steps are:

1. Start dev server: `cd qa-sandbox/ && npm run dev -- --host --allowed-hosts all &` and capture `DEV_PID`
2. Start Cloudflare tunnel: `browser-use tunnel <PORT>` and capture the `TUNNEL_URL`
3. Extract hostname and run: `python qa/run_qa.py $TUNNEL_HOST`
4. Read `qa/bug_report.json` for results
5. Kill dev server: `kill $DEV_PID`

**Constraints for QA runs:**
- Do NOT modify source files or fix bugs — detect and report only
- `TUNNEL_URL` is passed as a CLI argument, never written to files

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
