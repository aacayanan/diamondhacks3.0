#!/bin/bash

# Run QA Agent workflow script
# This script combines all steps from the run-qa command

set -e  # Exit on error

echo "======================================"
echo "Diamond Hacks 3.0 - QA Agent Workflow"
echo "======================================"
echo ""

# ============================================
# STEP 0 — Activate venv
# ============================================
echo "STEP 0: Activating virtual environment..."
if [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
  echo "✅ Activated .venv"
else
  echo "⚠️ No virtual environment found. Proceeding with system Python."
fi

# ============================================
# STEP 1 — Confirm dev server on port 3000
# ============================================
echo ""
echo "STEP 1: Checking dev server..."
DEV_PID=""
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "✅ Dev server already running on port 3000"
  DEV_PID=""
else
  echo "⚠️ Dev server not running. Starting..."
  cd qa-sandbox/ && npm run dev -- --host --port 3000 &
  DEV_PID=$!
  cd ..
  sleep 3
  echo "✅ Dev server started with PID: $DEV_PID"
fi

# ============================================
# STEP 2 — Tunnel setup (3 tunnels)
# ============================================
echo ""
echo "STEP 2: Setting up tunnels..."
TUNNELS=()
TUNNEL_PIDS=()

# Get existing tunnels
mapfile -t EXISTING_TUNNELS < <(browser-use tunnel list 2>&1 | awk '/trycloudflare/ {print $NF}')

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
      URL=$(browser-use tunnel list 2>&1 | awk '/trycloudflare/ {print $NF}' | tail -1)
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

# ============================================
# STEP 3 — Run three QA agents in parallel
# ============================================
echo ""
echo "STEP 3: Running QA agents in parallel..."
mkdir -p qa/bug_reports

python qa/run_qa.py "${TUNNEL_HOSTS[0]}" & PID1=$!
python qa/run_qa.py "${TUNNEL_HOSTS[1]}" & PID2=$!
python qa/run_qa.py "${TUNNEL_HOSTS[2]}" & PID3=$!

echo "Running QA agents... PIDs: $PID1, $PID2, $PID3"

# Wait for each agent and copy their report before the next one overwrites it
wait $PID1 && cp qa/bug_report.json qa/bug_reports/agent_1.json 2>/dev/null || echo "Agent 1 failed or no report"
wait $PID2 && cp qa/bug_report.json qa/bug_reports/agent_2.json 2>/dev/null || echo "Agent 2 failed or no report"
wait $PID3 && cp qa/bug_report.json qa/bug_reports/agent_3.json 2>/dev/null || echo "Agent 3 failed or no report"

echo "All three QA agents completed."

# ============================================
# STEP 4 — Unified results summary
# ============================================
echo ""
echo "STEP 4: Displaying results..."
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

# ============================================
# STEP 5 — Unified approval gate
# ============================================
echo ""
echo "STEP 5: Approval gate"
echo "Review all 3 agent reports above."
read -p "Approve auto-fix? (y/n): " APPROVE
echo ""

if [[ "$APPROVE" != "y" && "$APPROVE" != "Y" ]]; then
  echo "Fix rejected. Cleaning up."
  # Skip to cleanup
  APPROVE="n"
else
  # ============================================
  # STEP 6 — Run loop.py per agent
  # ============================================
  echo "STEP 6: Running auto-fix loop for approved agents..."
  for i in 1 2 3; do
    REPORT="qa/bug_reports/agent_${i}.json"
    if [ ! -f "$REPORT" ]; then continue; fi

    STATUS=$(python -c "import json,sys; print(json.load(open(sys.argv[1])).get('status','unknown'))" "$REPORT")

    if [ "$STATUS" = "bug_found" ]; then
      HOST="${TUNNEL_HOSTS[$((i-1))]}"
      echo ""
      echo "── Running fix loop for Agent $i ($HOST) ──"
      echo "  Passing bug report context to loop.py..."

      # Copy the agent's bug report into the working location
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
fi

# ============================================
# STEP 7 — Cleanup
# ============================================
echo ""
echo "STEP 7: Cleaning up..."
[ -n "$DEV_PID" ] && kill $DEV_PID 2>/dev/null && echo "Killed dev server (PID: $DEV_PID)"
for pid in "${TUNNEL_PIDS[@]}"; do
  kill $pid 2>/dev/null && echo "Killed tunnel (PID: $pid)"
done
echo "Cleanup complete."
echo ""
echo "======================================"
echo "QA Agent Workflow Complete!"
echo "======================================"
