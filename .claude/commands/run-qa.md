# Run QA — Bug Fix Loop

Runs BrowserUse against each bug's target route. Loops one bug at a time:
BrowserUse highlights it → Claude Code fixes the source → re-verify → next bug.

---

## Phase 1: Environment Setup

### 1a — Activate venv & start server

```bash
if [ -d ".venv" ]; then source .venv/bin/activate; echo "venv activated"; fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "Dev server already running on port 3000"
else
  echo "Starting dev server on port 3000..."
  cd qa-sandbox/ && npm run dev -- --host --port 3000 &
  DEV_PID=$!
  cd ..
  sleep 4
  echo "Dev server started (PID: $DEV_PID)"
fi
```

### 1b — Start tunnel

```bash
EXISTING=$(browser-use tunnel list 2>&1)
TUNNEL_HOST=$(echo "$EXISTING" | grep "port 3000" | awk '{print $NF}' | grep 'trycloudflare' | head -1 | sed 's|https://||')

if [ -n "$TUNNEL_HOST" ]; then
  echo "Existing tunnel: $TUNNEL_HOST"
else
  echo "Starting tunnel on port 3000..."
  ATTEMPTS=0
  while [ $ATTEMPTS -lt 3 ]; do
    browser-use tunnel 3000 &
    TUNNEL_PID=$!
    sleep 4
    TUNNEL_HOST=$(browser-use tunnel list 2>&1 | grep "port 3000" | awk '{print $NF}' | grep 'trycloudflare' | head -1 | sed 's|https://||')
    if [ -n "$TUNNEL_HOST" ]; then
      echo "Tunnel: $TUNNEL_HOST"
      break
    fi
    kill $TUNNEL_PID 2>/dev/null
    ATTEMPTS=$((ATTEMPTS + 1))
    echo "Attempt $ATTEMPTS failed, retrying..."
  done
fi
```

---

## Phase 2: Bug Fix Loop

Run the orchestrator (`loop.py`), which drives the one-bug-at-a-time cycle:

1. `loop.py` reads `bug_report.json`, picks the **first unfixed** bug
2. Calls `run_qa.py` → BrowserUse navigates to the bug's route, highlights the element with a red border
3. `loop.py` reads the updated report, sends the bug + relevant files to Claude Code
4. Claude Code applies a surgical fix to the correct page/component files
5. Loop repeats until all bugs are resolved

Each bug carries a `route` field (`/billing`, `/settings`, `/profile`) that determines:
- Which page BrowserUse visits
- Which source files Claude Code is allowed to edit

```bash
cd qa && python loop.py "$TUNNEL_HOST" bug_report.json
```

After it completes, present the results from the console output.

---

## Phase 3: Cleanup

```bash
[ -n "$DEV_PID" ] && kill $DEV_PID 2>/dev/null && echo "Dev server stopped."
[ -n "$TUNNEL_PID" ] && kill $TUNNEL_PID 2>/dev/null && echo "Tunnel stopped."
echo "Done."
```

---

## Constraints

- **One bug at a time.** Each iteration processes exactly one bug end-to-end.
- **`loop.py` is the orchestrator.** It calls `run_qa.py` and `claude` in sequence.
- **Route-aware.** Bugs have a `route` field that maps to the correct page and source files.
- **Progress is written after each bug.** `bug_report.json` updates in real-time.
- **Tunnel URLs are CLI args only.** Never write them to files.
- **Always activate .venv** before running Python.
