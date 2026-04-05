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

### STEP 1 — Start dev servers on ports 3000, 3001, 3002
```bash
DEV_PORTS=(3000 3001 3002)
DEV_PIDS=()

for PORT in "${DEV_PORTS[@]}"; do
  if curl -s http://localhost:$PORT > /dev/null 2>&1; then
    echo "Port $PORT: RUNNING"
    DEV_PIDS+=("")
  else
    echo "Port $PORT: Starting..."
    cd qa-sandbox/ && npm run dev -- --host --port $PORT &
    DEV_PIDS+=($!)
    cd ..
  fi
done

sleep 3
echo "Dev servers ready on ports ${DEV_PORTS[*]}"
```

### STEP 2 — Tunnel setup (1 tunnel per port)
```bash
TUNNELS=()
TUNNEL_PIDS=()
TUNNEL_PORTS=(3000 3001 3002)

# Check which ports already have a tunnel
EXISTING=$(browser-use tunnel list 2>&1)

for PORT in "${TUNNEL_PORTS[@]}"; do
  # Look for an existing tunnel targeting this port
  URL=$(echo "$EXISTING" | grep "port $PORT" | awk '{print $NF}' | grep 'trycloudflare' | head -1)

  if [ -n "$URL" ]; then
    echo "Port $PORT: Existing tunnel → $URL"
    TUNNELS+=("$URL")
    TUNNEL_PIDS+=("")
  else
    echo "Port $PORT: Starting tunnel..."
    ATTEMPTS=0
    while [ $ATTEMPTS -lt 3 ]; do
      browser-use tunnel $PORT &
      PID=$!
      sleep 3
      URL=$(browser-use tunnel list 2>&1 | grep "port $PORT" | awk '{print $NF}' | grep 'trycloudflare' | head -1)
      if [ -n "$URL" ]; then
        echo "Port $PORT: Tunnel → $URL"
        TUNNELS+=("$URL")
        TUNNEL_PIDS+=("$PID")
        break
      fi
      kill $PID 2>/dev/null
      ATTEMPTS=$((ATTEMPTS + 1))
      echo "Port $PORT: Attempt $ATTEMPTS failed. Retrying..."
    done

    # Fallback to ngrok for this port
    if [ -z "$URL" ]; then
      ngrok http $PORT &
      PID=$!
      sleep 3
      URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*ngrok[^"]*' | head -1)
      if [ -n "$URL" ]; then
        echo "Port $PORT: Tunnel (ngrok) → $URL"
        TUNNELS+=("$URL")
        TUNNEL_PIDS+=("$PID")
      else
        kill $PID 2>/dev/null
        echo "⚠️ Port $PORT: Tunnel failed. Aborting."
        exit 1
      fi
    fi
  fi
done

# Strip protocol to get bare hostnames
TUNNEL_HOSTS=()
for url in "${TUNNELS[@]}"; do
  HOST=$(echo "$url" | sed 's|https://||')
  TUNNEL_HOSTS+=("$HOST")
done

echo ""
echo "=== Tunnel Hosts ==="
echo "Agent 1 (port 3000) → ${TUNNEL_HOSTS[0]}"
echo "Agent 2 (port 3001) → ${TUNNEL_HOSTS[1]}"
echo "Agent 3 (port 3002) → ${TUNNEL_HOSTS[2]}"
```

### STEP 3 — Run three QA agents in parallel
```bash
mkdir -p qa/bug_reports

python qa/run_qa.py "${TUNNEL_HOSTS[0]}" 0 & PID1=$!
python qa/run_qa.py "${TUNNEL_HOSTS[1]}" 1 & PID2=$!
python qa/run_qa.py "${TUNNEL_HOSTS[2]}" 2 & PID3=$!

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
    python qa/run_qa.py "$HOST" $((i-1))

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
for pid in "${DEV_PIDS[@]}"; do
  [ -n "$pid" ] && kill $pid 2>/dev/null
done
for pid in "${TUNNEL_PIDS[@]}"; do
  [ -n "$pid" ] && kill $pid 2>/dev/null
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
- The `DEV_PIDS` / `TUNNEL_PIDS` guards ensure only processes spawned by this session are killed — existing instances are left running.
- The approval gate in Step 5 is a single unified decision — the user approves fixes for all three agents at once.
- Each `loop.py` run in Step 6 operates independently against its own tunnel URL.
- `browser-use tunnel list` outputs in this exact format:
  `  port 3000: https://selections-land-seq-wider.trycloudflare.com`
  Extract the URL with: `browser-use tunnel list 2>&1 | awk '{print $NF}'`
  Then strip the protocol: `sed 's|https://||'`
  Do not use grep -P, grep -o, or tr. Use only awk and sed.
