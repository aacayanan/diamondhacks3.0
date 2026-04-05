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

## Phase 2: Bug Fix Loop (one bug at a time)

Each iteration is manual — Claude drives every step.

### Step 1 — Run `run_qa.py` to highlight the first unfixed bug

```bash
cd qa && source ../.venv/Scripts/activate 2>/dev/null; python run_qa.py "$TUNNEL_HOST" bug_report.json
```

BrowserUse navigates to the bug's route, highlights the element in the DOM with a red border, and saves the result to `bug_report.json`.

### Step 2 — Read and present the bug report

Read `bug_report.json`. Present the first unfixed bug to the user:
- Bug ID, route, category, severity, description
- Which source files are affected (based on the `route` field)

Each bug carries a `route` field (`/billing`, `/settings`, `/profile`) that maps to source files:
- `/billing` → `qa-sandbox/src/pages/Billing.jsx`
- `/settings` → `qa-sandbox/src/pages/Settings.jsx`
- `/profile` → `qa-sandbox/src/pages/Profile.jsx`

### Step 3 — Recommend and apply a fix

Read the affected source files, explain the bug, then apply a surgical fix. Only edit files mapped to the bug's `route`. One fix per iteration.

### Step 4 — Run `loop.py` to recheck for remaining bugs

```bash
cd qa && python loop.py "$TUNNEL_HOST" bug_report.json
```

`loop.py` rechecks the bug report, resets state for verification, and determines if there are more unfixed bugs. If there are, repeat from Step 1.

After all bugs are resolved, present the final results.

---

## Phase 3: Cleanup

```bash
[ -n "$DEV_PID" ] && kill $DEV_PID 2>/dev/null && echo "Dev server stopped."
[ -n "$TUNNEL_PID" ] && kill $TUNNEL_PID 2>/dev/null && echo "Tunnel stopped."
echo "Done."
```

---

## Constraints

- **One bug at a time.** Never batch fixes. Each iteration: run_qa.py → read report → fix → loop.py → repeat.
- **Claude is the orchestrator.** You call `run_qa.py` and `loop.py` manually at each step.
- **Route-aware.** Only edit files mapped to the bug's `route` field.
- **Present before fixing.** Always read `bug_report.json` and explain the bug to the user before applying a fix.
- **`loop.py` rechecks.** After each fix, run `loop.py` to verify and check for more bugs.
- **Tunnel URLs are CLI args only.** Never write them to files.
- **Always activate .venv** before running Python.
