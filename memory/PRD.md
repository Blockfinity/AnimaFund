# Anima Platform — Audit Summary (March 21, 2026)

## Q1: Rebrand - Our Code
Zero "camel" references in backend/, ultimus/, engine/anima_runner.py, frontend/src/
Only hits are in engine/workspace/.initial_env/ (pip vendor files — not our code)

## Q2: Rebrand - anima_machina package
1208 "camel" refs remain inside the forked package (copyright headers, logger names, env var names like CAMEL_LOGGING_LEVEL). These are expected in a forked Apache-2.0 project. Our code has zero.

## Q3: Import test
`from anima_machina.agents import ChatAgent` + Workforce + Task = OK

## Q4: predictor.py
186 lines. Round-based simulation loop (lines 120-168). Each round builds context from ALL previous agent actions. ChatAgent reused across rounds (maintains conversation history).

## Q5: 10-agent 3-round simulation tested
10 personas: DayTraderDerek, LongTermLinda, DeFiDan, InstitutionalIvy, SkepticalSam, MaxiMina, RetailRyan, MarketMakerMaggie, AnalyticalAlex, JournalistJessie. 38 total events. Coalitions formed. Strategy at 85% confidence.

## Q6: Round 2 context
Yes — each agent receives ALL other agents' Round 1 actions as context. Exact text of positions visible.

## Q7: Context management for 100 agents
Last 2 rounds included in full. Earlier rounds dropped. Each agent's ChatAgent keeps its own conversation memory. LIMITATION: agents don't see others' actions from 3+ rounds ago.

## Q8-Q9: Frontend
16 pages. Ultimus page uses react-force-graph-2d. Shows prediction list + graph when loaded.

## Q10: SSE streaming
Backend SSE endpoint exists (POST /predict/stream). Frontend does NOT use it — waits for full response.

## Q11: Dashboard data
11/14 pages return REAL_DATA. Portfolio, DealFlow, OpenClawViewer = EMPTY.

## Q12: Multi-agent selector
selectedAgent state exists. No dropdown UI. Hardcoded to 'anima-fund'.

## Q13: Routers
10 files, 2298 total lines.

## Q14: Endpoints
health, agents, provision/status, ultimus/predictions, ultimus/status, spawn/ = all return real data.

## Q15: Conway
9 cents credits. Agent NOT running.

## Q16-Q17: Runner + Wallet
anima_runner.py uses anima_machina imports. Wallet has get_wallet_balance, send_payment, sweep_public_wallet, share_wallet_address. Core address hidden at code level.

## Q18: Sandbox env
Cannot test — sandbox agent not running (9 cents credits).

## Q19-Q20: Structure
anima-machina/ has BOTH camel/ and anima_machina/ directories (246MB total — should delete camel/ to save space). Total codebase: ~854MB.
