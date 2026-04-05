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
qa-sandbox/src/App.jsx    — Feedback form (Name, Email, Message, Submit button)
qa-sandbox/src/App.css    — Styling (note: submit button styled as enabled despite being disabled)
qa/run_qa.py              — BrowserUse agent that fills the form and tests submit
```

The QA agent (`qa/run_qa.py`) creates a BrowserUse workspace, runs an automated browser session against the tunnel URL, and outputs a structured `bug_report.json` with status, actions taken, and the likely file containing the bug.

## Intentional Bug

The Submit button in `App.jsx:41` has `disabled={true}` hardcoded. This is intentional — it tests whether the QA agent can detect a button that looks clickable but is actually disabled in the DOM. Do not "fix" this unless explicitly asked.
