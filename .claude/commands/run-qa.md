# Run QA Agent
Run the BrowserUse QA agent and report findings.

## Steps

1. Navigate into the sandbox and detect the port:
```bash
   cd qa-sandbox/ && npm run dev -- --host --allowed-hosts all &
   DEV_PID=$!
```
   Capture the port printed in the output (e.g. `Local: http://localhost:XXXX`).

2. Start the tunnel using the captured port:
```bash
   browser-use tunnel <PORT> &
   TUNNEL_PID=$!
```
   Capture the trycloudflare URL from the output (e.g. `https://random-words.trycloudflare.com`).

3. Extract just the hostname (no `https://`, no trailing path):
```bash
   TUNNEL_HOST=$(echo "<TUNNEL_URL>" | sed 's|https://||' | sed 's|/.*||')
```

4. Run the QA script, passing the tunnel hostname as a CLI argument:
```bash
   python qa/run_qa.py $TUNNEL_HOST
```

5. Read `qa/bug_report.json`.

6. Kill the dev server and the tunnel:
```bash
   kill $DEV_PID
   kill $TUNNEL_PID
```

7. Print a short summary of what the QA agent found.

## Constraints
- Do NOT modify any source files.
- Do NOT fix bugs. Detect and report only.
- `TUNNEL_URL` is passed as a CLI argument — never written to `.env` or any config file.

## Notes
- `--host --allowed-hosts all` is Vite-specific. If the project is migrated to another framework, replace this flag with the appropriate host bypass for that framework.
- The `DEV_PID` capture ensures clean teardown without relying on `pkill` or port-scanning.