# Anima Platform — Deployment Ready (March 22, 2026)

## Production Checklist
- [x] Backend: FastAPI on port 8001, all endpoints responding (health, ultimus, agents, webhook, spawn, dimensions)
- [x] Frontend: React built, 16 pages, Ultimus with graph + workbench
- [x] MongoDB: Connected via MONGO_URL env var
- [x] Anima Machina: Fully rebranded, 7/7 toolkits working, importable as anima_machina
- [x] Ultimus: Predictor (multi-round simulation), Calculator (pre-estimate), Executor (per-persona deployment)
- [x] Wallet: Build + sign USDC transactions on Base (needs ETH for gas to broadcast)
- [x] BYOI: Conway + Fly.io providers
- [x] Cleanup: automaton/ deleted (96MB), duplicate camel/ deleted (120MB), old tests removed
- [x] No hardcoded secrets in source code
- [x] requirements.txt frozen (175 packages)
- [x] Frontend build passes
- [x] sys.path configured for ultimus/ and anima-machina/ imports

## Environment Variables Required
MONGO_URL, DB_NAME, REACT_APP_BACKEND_URL, EMERGENT_LLM_KEY, OPENAI_API_KEY, OPENAI_API_BASE_URL,
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, CONWAY_API_KEY, FLY_API_TOKEN, FLY_APP_NAME,
CREATOR_WALLET, CREATOR_ETH_ADDRESS

## Architecture
- /app/backend/ — FastAPI platform API (server.py + 10 routers)
- /app/frontend/ — React dashboard (16 pages including Ultimus)
- /app/ultimus/ — Prediction engine (predictor, calculator, executor, dimensions, knowledge, api)
- /app/anima-machina/ — Agent framework (CAMEL fork, fully rebranded)
- /app/engine/ — Agent runners + skills + templates
- /app/ultima-x/ — Inference model config (Qwen 3.5-122B)
- /app/docs/ — Architecture documentation
