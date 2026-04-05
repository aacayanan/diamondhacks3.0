# Run QA Agent
Run the BrowserUse QA agent, report findings, and optionally trigger the auto-fix loop.

## Steps

0. Check for a virtual environment and activate it if present:
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


1. Check if a dev server is already running on port 3000:
```bash
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "RUNNING" || echo "NOT_RUNNING"
```
   - If `RUNNING`: skip to Step 2. Set `DEV_PID=""` (no process to kill later).
   - If `NOT_RUNNING`: start the dev server:
```bash
cd qa-sandbox/ && npm run dev -- --host --port 3000 &
DEV_PID=$!
```
   Wait 3 seconds for it to boot, then continue.

2. Check if a tunnel is already running:
```bash
browser-use tunnel list
```
   - If a tunnel is listed: extract the URL and use it as `TUNNEL_HOST`. Set `TUNNEL_PID=""`. Set `TUNNEL_ATTEMPTS=0`.
   - If no tunnels are listed: attempt to start a browser-use tunnel, up to 3 times:
```bash
TUNNEL_ATTEMPTS=0
while [ $TUNNEL_ATTEMPTS -lt 3 ]; do
  browser-use tunnel 3000 &
  TUNNEL_PID=$!
  sleep 3
  TUNNEL_HOST=$(browser-use tunnel list | grep -o 'trycloudflare[^"]*' | head -1)
  if [ -n "$TUNNEL_HOST" ]; then
    break
  fi
  kill $TUNNEL_PID 2>/dev/null
  TUNNEL_ATTEMPTS=$((TUNNEL_ATTEMPTS + 1))
  echo "Tunnel attempt $TUNNEL_ATTEMPTS failed. Retrying..."
done

if [ -z "$TUNNEL_HOST" ]; then
  echo "browser-use tunnel failed 3 times. Falling back to ngrok..."
  ngrok http 3000 &
  TUNNEL_PID=$!
  sleep 3
  TUNNEL_HOST=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*ngrok[^"]*' | head -1)
  echo "Using ngrok tunnel: $TUNNEL_HOST"
fi
```

3. Extract just the hostname:
```bash
TUNNEL_HOST=$(browser-use tunnel list 2>&1 | awk '{print $NF}' | sed 's|https://||')
```

4. Run the QA script:
```bash
python qa/run_qa.py $TUNNEL_HOST
```

5. Kill only what this session started:
```bash
[ -n "$DEV_PID" ] && kill $DEV_PID
[ -n "$TUNNEL_PID" ] && kill $TUNNEL_PID
```

6. Read `qa/bug_report.json` and check the `status` field.

7. If `status` is `"success"`: print "✅ QA Passed. No bugs found." and stop.

8. If `status` is `"bug_found"`:
   - Display a structured summary table with: status, description, affected file, and actions taken pulled directly from `qa/bug_report.json`
   - Ask the user:
```bash
read -p "Bugs found. Approve auto-fix? (y/n): " APPROVE && echo $APPROVE
```
   - If `APPROVE` is `n`: print "Fix rejected. Exiting." and stop. Do not touch any files.
   - If `APPROVE` is `y`:
     a. Pass the full contents of `qa/bug_report.json` to `qa/loop.py` as context so it knows exactly what to fix — do not let loop.py re-discover the bug from scratch.
     b. Run:
```bash
python qa/loop.py $TUNNEL_HOST
```
     c. After `loop.py` completes each fix attempt, re-run `python qa/run_qa.py $TUNNEL_HOST` automatically.
     d. Read the new `qa/bug_report.json`.
     e. If `status` is `"success"`: print "✅ All bugs resolved. Loop complete." and stop.
     f. If `status` is `"bug_found"`: display the new bug summary table and ask for approval again. Rinse and repeat from step 8.
     g. If `status` is `"failed"`: print "⚠️ QA Agent failed. Manual review required." and stop.

## Constraints
- Do NOT modify any source files during Steps 1–6.
- Do NOT call `loop.py` unless the user explicitly approves with `y`.
- Always pass `qa/bug_report.json` contents as context to `loop.py` — never let it run blind.
- `TUNNEL_HOST` is always passed as a CLI argument — never hardcoded or written to any file.
- Always activate the virtual environment in Step 0 before running any `python` commands.

## Notes
- If `--allowed-hosts` is not supported by the installed Vite version, do not use the flag. Instead edit `qa-sandbox/vite.config.js` to add:
```js
server: {
  host: true,
  allowedHosts: 'all'
}
```
- The `DEV_PID` / `TUNNEL_PID` guards ensure only processes spawned by this session are killed — existing instances are left running.
- The approval gate repeats on every iteration — the user controls every fix cycle.
- `browser-use tunnel list` outputs in this exact format:
  `  port 3000: https://selections-land-seq-wider.trycloudflare.com`
  Extract the URL with: `browser-use tunnel list 2>&1 | awk '{print $NF}'`
  Then strip the protocol: `TUNNEL_HOST=$(echo "$TUNNEL_HOST" | sed 's|https://||')`
  Do not use grep -P, grep -o, or tr. Use only awk and sed.