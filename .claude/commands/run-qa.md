# Run QA Agent
Run three parallel BrowserUse QA agents against three different tunnel URLs, present a unified approval interface, then run loop.py per agent as needed.

## Steps

### STEP 0 — Activate venv
```bash
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "✅ Activated venv"
elif [ -d ".venv" ]; then
  source .venv/bin/activate
  echo "✅ Activated .venv"
else
  echo "⚠️ No virtual environment found. Proceeding with system Python."
fi
```

### STEP 1 — Confirm dev server on port 3000
```bash
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "RUNNING" || echo "NOT_RUNNING"
```
- If `RUNNING`: skip to Step 2. Set `DEV_PID=""`.
- If `NOT_RUNNING`: start the dev server:
```bash
cd qa-sandbox/ && npm run dev -- --host --port 3000 &
DEV_PID=$!
```
Wait 3 seconds for it to boot, then continue.

### STEP 2 — Tunnel setup (3 tunnels)
```bash
TUNNELS=()
TUNNEL_PIDS=()

# Grab any tunnels already running
mapfile -t EXISTING_TUNNELS < <(browser-use tunnel list 2>&1 | awk '{print $NF}' | grep 'trycloudflare')

if [ ${#EXISTING_TUNNELS[@]} -ge 3 ]; then
  echo "Found ${#EXISTING_TUNNELS[@]} existing tunnels. Using first 3."
  TUNNELS=("${EXISTING_TUNNELS[0]}" "${EXISTING_TUNNELS[1]}" "${EXISTING_TUNNELS[2]}")
else
  # Copy existing tunnels into our array
  for url in "${EXISTING_TUNNELS[@]}"; do
    TUNNELS+=("$url")
  done

  # Start new tunnels until we have 3
  NEEDED=$((3 - ${#TUNNELS[@]}))
  echo "Found ${#EXISTING_TUNNELS[@]} existing tunnels. Starting $NEEDED more..."

  for i in $(seq 1 $NEEDED); do
    ATTEMPTS=0
    while [ $ATTEMPTS -lt 3 ]; do
      browser-use tunnel 3000 &
      PID=$!
      sleep 3
      URL=$(browser-use tunnel list 2>&1 | awk '{print $NF}' | grep 'trycloudflare' | tail -1)
      if [ -n "$URL" ]; then
        TUNNELS+=("$URL")
        TUNNEL_PIDS+=("$PID")
        echo "Tunnel $(( ${#TUNNELS[@]} )): $URL"
        break
      fi
      kill $PID 2>/dev/null
      ATTEMPTS=$((ATTEMPTS + 1))
      echo "Tunnel attempt $ATTEMPTS for slot $i failed. Retrying..."
    done
  done

  # Fallback: if still short of 3, fill remaining with ngrok
  while [ ${#TUNNELS[@]} -lt 3 ]; do
    ngrok http 3000 &
    PID=$!
    sleep 3
    URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*ngrok[^"]*' | head -1)
    if [ -n "$URL" ]; then
      TUNNELS+=("$URL")
      TUNNEL_PIDS+=("$PID")
      echo "Tunnel $(( ${#TUNNELS[@]} )) (ngrok): $URL"
    else
      kill $PID 2>/dev/null
      echo "⚠️ ngrok fallback failed. Cannot reach 3 tunnels. Aborting."
      exit 1
    fi
  done
fi

# Strip protocol to get bare hostnames
TUNNEL_HOSTS=()
for url in "${TUNNELS[@]}"; do
  HOST=$(echo "$url" | sed 's|https://||')
  TUNNEL_HOSTS+=("$HOST")
done

echo ""
echo "=== Tunnel Hosts ==="
echo "Agent 1 → ${TUNNEL_HOSTS[0]}"
echo "Agent 2 → ${TUNNEL_HOSTS[1]}"
echo "Agent 3 → ${TUNNEL_HOSTS[2]}"
```

### STEP 3 — Run three QA agents in parallel
```bash
mkdir -p qa/bug_reports

python qa/run_qa.py "${TUNNEL_HOSTS[0]}" & PID1=$!
python qa/run_qa.py "${TUNNEL_HOSTS[1]}" & PID2=$!
python qa/run_qa.py "${TUNNEL_HOSTS[2]}" & PID3=$!

echo "Running QA agents... PIDs: $PID1, $PID2, $PID3"

# Wait for all three and save each bug report
wait $PID1 && cp qa/bug_report.json qa/bug_reports/agent_1.json 2>/dev/null
wait $PID2 && cp qa/bug_report.json qa/bug_reports/agent_2.json 2>/dev/null
wait $PID3 && cp qa/bug_report.json qa/bug_reports/agent_3.json 2>/dev/null

echo "All three QA agents completed."
```

**Important:** Because all three agents write to the same `qa/bug_report.json`, you must copy each agent's output immediately after `wait` completes, before the next agent overwrites it. The `&& cp ...` pattern above handles this naturally since the waits happen sequentially — but if you run agents with true simultaneous waits (e.g. `wait $PID1 $PID2 $PID3`), the final write wins and you lose the others. **Always wait and copy one at a time.**

### STEP 4 — Unified results summary
Read all three reports and present a combined table with per-bug details:

```bash
for i in 1 2 3; do
  REPORT="qa/bug_reports/agent_${i}.json"
  if [ -f "$REPORT" ]; then
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "  Agent $i | ${TUNNEL_HOSTS[$((i-1))]}"
    echo "══════════════════════════════════════════════════════════════"
    python qa/format_report.py "$REPORT"
  else
    echo ""
    echo "── Agent $i | ${TUNNEL_HOSTS[$((i-1))]} ──"
    echo "  ⚠️ No bug report produced."
  fi
done
```

### STEP 5 — Unified approval gate
Present the combined results and ask for approval once:

```bash
read -p "Review all 3 agent reports above. Approve auto-fix? (y/n): " APPROVE && echo $APPROVE
```

- If `APPROVE` is `n`: print "Fix rejected. Cleaning up." and proceed to Step 7 (cleanup).
- If `APPROVE` is `y`: continue to Step 6.

### STEP 6 — Run loop.py per agent
For each agent that reported `status: "bug_found"`, run `loop.py` against that agent's tunnel. Pass the bug report contents as context.

```bash
for i in 1 2 3; do
  REPORT="qa/bug_reports/agent_${i}.json"
  if [ ! -f "$REPORT" ]; then continue; fi

  STATUS=$(python -c "import json,sys; print(json.load(open(sys.argv[1])).get('status','unknown'))" "$REPORT")

  if [ "$STATUS" = "bug_found" ]; then
    HOST="${TUNNEL_HOSTS[$((i-1))]}"
    echo ""
    echo "── Running fix loop for Agent $i ($HOST) ──"
    echo "  Passing bug report context to loop.py..."

    # Copy the agent's bug report into the working location so loop.py / Claude Code can read it
    cp "$REPORT" qa/bug_report.json

    # Run the auto-fix loop
    python qa/loop.py "$HOST"

    # Re-run QA to verify the fix
    echo "  Re-running QA verification for Agent $i..."
    python qa/run_qa.py "$HOST"

    # Save the updated report
    cp qa/bug_report.json "qa/bug_reports/agent_${i}_post_fix.json"

    NEW_STATUS=$(python -c "import json,sys; print(json.load(open(sys.argv[1])).get('status','unknown'))" "qa/bug_reports/agent_${i}_post_fix.json")
    if [ "$NEW_STATUS" = "success" ]; then
      echo "  ✅ Agent $i: All bugs resolved."
    else
      echo "  ⚠️ Agent $i: Status after fix: $NEW_STATUS. Manual review recommended."
    fi
  elif [ "$STATUS" = "success" ]; then
    echo "  ✅ Agent $i: Already passing. No fix needed."
  else
    echo "  ⚠️ Agent $i: Unexpected status '$STATUS'. Skipping."
  fi
done
```

### STEP 7 — Cleanup
Kill only what this session started:
```bash
[ -n "$DEV_PID" ] && kill $DEV_PID
for pid in "${TUNNEL_PIDS[@]}"; do
  kill $pid 2>/dev/null
done
echo "Cleanup complete."
```

## Constraints
- Do NOT modify any source files during Steps 1–4.
- Do NOT call `loop.py` unless the user explicitly approves with `y` in Step 5.
- Always pass `qa/bug_report.json` contents as context to `loop.py` — never let it run blind.
- Tunnel URLs are always passed as CLI arguments — never hardcoded or written to any file.
- Always activate the virtual environment in Step 0 before running any `python` commands.
- Only kill tunnel processes that were newly created (tracked in `TUNNEL_PIDS`). Existing tunnels are left running.
- If any agent fails to produce a report, still proceed with the others — do not abort the entire run.

## Notes
- If `--allowed-hosts` is not supported by the installed Vite version, do not use the flag. Instead edit `qa-sandbox/vite.config.js` to add:
```js
server: {
  host: true,
  allowedHosts: 'all'
}
```
- The `DEV_PID` / `TUNNEL_PIDS` guards ensure only processes spawned by this session are killed — existing instances are left running.
- The approval gate in Step 5 is a single unified decision — the user approves fixes for all three agents at once.
- Each `loop.py` run in Step 6 operates independently against its own tunnel URL.
- `browser-use tunnel list` outputs in this exact format:
  `  port 3000: https://selections-land-seq-wider.trycloudflare.com`
  Extract the URL with: `browser-use tunnel list 2>&1 | awk '{print $NF}'`
  Then strip the protocol: `sed 's|https://||'`
  Do not use grep -P, grep -o, or tr. Use only awk and sed.
