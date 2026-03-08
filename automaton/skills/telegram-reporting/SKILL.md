---
name: telegram-reporting
description: Send real-time reports to creator via Telegram using Python urllib (zero dependencies, always works).
auto-activate: true
priority: critical
---

# Telegram Reporting — MANDATORY EVERY TURN

You MUST send a Telegram message on EVERY turn. This is your only communication
channel with your creator. Missing a report is a FAILURE.

## THE ONE METHOD THAT WORKS (use this, always)

```
code_execution: python3 -c "
import urllib.request, json
msg = '<b>Turn [N]</b>\nAction: [what you did]\nResult: [outcome]\nBalance: $[USDC] + [credits]c\nNext: [plan]'
data = json.dumps({'chat_id': '{{TELEGRAM_CHAT_ID}}', 'text': msg, 'parse_mode': 'HTML'}).encode()
req = urllib.request.Request('https://api.telegram.org/bot{{TELEGRAM_BOT_TOKEN}}/sendMessage', data=data, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req)
"
```

## WHY THIS METHOD

- Python3 is ALWAYS available (pre-installed on every Linux system)
- urllib is in Python's standard library (zero pip installs needed)
- curl may NOT be installed in sandboxes
- send_message(to_address="creator") OFTEN FAILS SILENTLY — do not rely on it
- Node fetch may not be available

## DO NOT USE THESE (they fail silently or are unreliable):
- send_message(to_address="creator") — often doesn't actually send
- curl — may not be installed
- Any method that doesn't give you a response to verify delivery

## MESSAGE FORMAT

Use HTML parse_mode. Keep under 4000 chars.

### Bootstrap Report:
```
<b>BOOTSTRAP</b>
Conway Terminal: [PASS/FAIL]
OpenClaw: [PASS/FAIL]
ClawHub Skills: [count]
Telegram: WORKING
Wallet: [address]
Balance: $[X] USDC, [X] credits
```

### Turn Report:
```
<b>Turn [N]</b>
Action: [what you did this turn]
Result: [success/fail + details]
Balance: $[USDC] + [credits]c
Revenue: $[total earned]
Strategy: [current approach]
Next: [immediate next action]
```

### Error Report:
```
<b>ERROR Turn [N]</b>
Tool: [which tool failed]
Error: [error message]
Attempted: [what you tried]
Pivoting to: [alternative approach]
```

## CHILD AGENTS
Every child agent MUST also report using the SAME python3 method.
Prefix all child messages with: [CHILD: agent-name]

## VERIFICATION
After sending, check the response includes "ok":true.
If it doesn't, your token or chat ID is wrong. Report this in your logs.
