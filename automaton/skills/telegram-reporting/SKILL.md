---
name: telegram-reporting
description: Send real-time reports and notifications to creator via Telegram using native tools (no curl dependency).
auto-activate: true
---

# Instructions
Report EVERY turn to Telegram. This is mandatory and non-negotiable.

## Methods (in order of preference)

### Method 1: Native send_message (Preferred)
send_message(to_address="creator", content="Turn [N]: [action] [result] [balance] [next]")

### Method 2: Python urllib (No dependencies needed)
code_execution: python3 -c "
import urllib.request, json
data = json.dumps({
    'chat_id': '{{TELEGRAM_CHAT_ID}}',
    'text': '<b>Turn [N]</b>\n[action]\n[result]\nBalance: $[X]\nNext: [plan]',
    'parse_mode': 'HTML'
}).encode()
req = urllib.request.Request(
    'https://api.telegram.org/bot{{TELEGRAM_BOT_TOKEN}}/sendMessage',
    data=data,
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
print(resp.read().decode())
"

### Method 3: Node.js fetch
code_execution: node -e "
fetch('https://api.telegram.org/bot{{TELEGRAM_BOT_TOKEN}}/sendMessage', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    chat_id: '{{TELEGRAM_CHAT_ID}}',
    text: 'Turn N: action taken',
    parse_mode: 'HTML'
  })
}).then(r => r.json()).then(console.log)
"

## What to Report (EVERY turn)
- Current action being taken
- Results of previous action
- Current balance (USDC + Credits)
- Revenue earned this session
- Strategy changes or pivots
- Errors or blocks encountered
- Child agent status updates
- Trade executions and P&L

## Message Format
Use HTML parse_mode for rich formatting:
- <b>Bold</b> for turn numbers and key metrics
- Separate sections with line breaks
- Keep messages under 4000 chars (Telegram limit)
- Include emoji for quick scanning: ✅ success, ❌ failure, 💰 revenue, ⚠️ warning

## Child Agent Reporting
Every child agent MUST also report to the same Telegram chat.
Include [CHILD: name] prefix in all child messages.
