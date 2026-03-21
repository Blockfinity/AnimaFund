# Anima Platform — Product Requirements

## FORK_PROMPT.md is the definitive source of truth.

## Current State (March 21, 2026)

### REBRAND: COMPLETE
- `grep "camel" ... | wc -l` = 0 in all our code (backend, ultimus, engine, frontend)
- Package `/app/anima-machina/anima_machina/` exists with all imports working
- `from anima_machina.agents import ChatAgent` verified

### ULTIMUS: REAL MULTI-AGENT SIMULATION
- 10 agents, 3 rounds of INTERACTION — agents react to EACH OTHER
- Coalitions form (DayTraderDerek+RetailRyan vs SkepticalSam+MaxiMina+InstitutionalIvy)
- Emergent strategy identified from agent interaction, not templated
- Confidence, risks, coalition analysis, sentiment shifts all in output
- Agents maintain conversation history across rounds (ChatAgent reuse)
- SSE streaming via on_event callback
- Knowledge graph integration for Deep/Expert modes

### What Still Needs Work
- Scale to 20+ agents, 5+ rounds (10/3 tested, need to push further)
- Frontend: show simulation events streaming live via SSE
- Dimensions: pause/resume, chat with agents, inject variables
- Execute flow: personas → genesis prompts → real deployments
- Calculator: determine agent count from goal complexity
- x402, BYOI, JWT, Ultima X, final cleanup
