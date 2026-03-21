# Anima Platform — Product Requirements

## FORK_PROMPT.md is the definitive source of truth. Read it FIRST.

## Audit Results (March 21, 2026)

### EXISTS:
- /app/ultimus/predictor.py (new — simulation engine)
- /app/ultimus/calculator.py (new — cost/feasibility)
- /app/ultimus/executor.py (new — deployment converter)
- /app/anima-machina/ (CAMEL clone, NOT rebranded)
- /app/engine/anima_runner.py (agent runner with 28 tools, browse_website subprocess fix)
- /app/backend/ (10 routers, per-agent state store, webhook with token validation)
- /app/frontend/ (14 pages, dashboard shows some real data)
- /app/ultima-x/ (Modelfile + config, NOT integrated)

### DOES NOT EXIST:
- Ultimus API (api.py), dimensions.py, knowledge.py, personas.py, config.py
- Ultimus frontend screens (goal input, simulation, Dimensions, cost review, execute)
- Rebrand (18 "camel" refs in our code)
- x402 real implementation
- Generic BYOI (Conway only)
- Spawn that provisions (records only)
- Multi-agent dashboard
- JWT auth
- Ultima X integration

### Conway credits: $0.09 (DEAD)
### Catalyst wallet: $3.00 USDC on Base

## Priority (from FORK_PROMPT.md):
1. Rebrand camel -> anima_machina in our code
2. Fix dashboard (real data or "no data", never mocks)
3. BUILD ULTIMUS (the core product)
4. Spawn via webhook
5. Production readiness
