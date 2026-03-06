#!/bin/bash
# Anima Fund Engine Starter
# Wrapper for supervisor — provides stdin so the setup wizard's readline doesn't hang.
# With auto-config.json staged, all prompts are answered automatically.
# The piped empty lines are a safety net for the rare case where SIWE provisioning
# fails and readline tries to prompt for a manual API key.

cd /app/automaton
yes "" 2>/dev/null | exec node dist/index.js --run
