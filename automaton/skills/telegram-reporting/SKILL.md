---
name: telegram-reporting
description: Send real-time reports and notifications to creator via Telegram Bot API.
auto-activate: true
triggers: [telegram, notify, report, alert, message creator]
---

You have a Telegram bot for communicating with your creator. Use it to report important events.

WHEN TO NOTIFY (always send these):
- State changes (waking, running, sleeping, critical, dead)
- Balance updates (credits topped up, USDC received, tier change)
- Every transaction (transfers, x402 payments, credit purchases)
- Errors that affect operation (inference failures, tool failures)
- Major milestones (first revenue, new hire, deal funded)
- Heartbeat distress signals
- When you need human input or guidance

HOW TO SEND:
Use exec tool with curl — these are YOUR bot credentials, hardcoded for reliability:
```
exec: curl -s -X POST "https://api.telegram.org/bot{{TELEGRAM_BOT_TOKEN}}/sendMessage" -H "Content-Type: application/json" -d '{"chat_id": "{{TELEGRAM_CHAT_ID}}", "text": "<message>", "parse_mode": "HTML"}'
```

Bot: @AnimaFundbot | Token: {{TELEGRAM_BOT_TOKEN}} | Chat ID: {{TELEGRAM_CHAT_ID}}

FORMAT GUIDELINES:
- Use HTML parse mode: <b>bold</b>, <code>mono</code>, <i>italic</i>
- Start with an icon: 🟢 success, 🔴 error, 💰 money, 📊 data, 🤝 social, 📚 skill
- Keep messages concise (under 500 chars)
- Include relevant numbers (amounts, balances, counts)

EXAMPLE MESSAGES:
- "🟢 <b>AWAKE</b>\nCredits: $4.50 | USDC: $10.00\nStarting revenue generation cycle."
- "💰 <b>REVENUE</b>\nEarned $0.50 from API service.\nNew balance: $5.00\nCreator share: $0.25 queued."
- "🔴 <b>CRITICAL</b>\nCredits below $0.10.\nEntering conservation mode.\nNeed funding."

IMPORTANT: Never send the private key, API keys, or sensitive wallet data via Telegram.
