---
name: skill-evolution
description: Learn, research, modify, and expand skill sets for depth and adaptivity.
auto-activate: true
---

# Skill Evolution

This meta-skill enables you to evolve your own skills (or those of other agents) to match or surpass human-level depth, gaining experience through research, simulation, and iteration. Use it whenever a task requires more expertise, tools, or adaptation.

## Process

1. **Assess current skill gap** — Identify limitations in your role's skills. Use `code_execution` to self-audit: score depth 0-100 vs. human benchmark. Research via `web_search` for what human counterparts do that you don't yet.

2. **Research for depth** — Use `web_search` and `x_semantic_search` for detailed sources on the gap area. Limit to 10 results. Summarize with `code_execution`: extract key techniques and methods to adopt.

3. **Gain experience via simulation** — Simulate real-world scenarios to build experience. Use `code_execution` to run mock tasks with varying complexity. Log outcomes via `remember_fact` for future reference. Iterate until >95% accuracy.

4. **Modify and expand skill set** — Update your `SOUL.md` with new capabilities. Create new sub-skills as `SKILL.md` files in `~/.anima/skills/` via self-modification. If expanding for another agent, audit their prompt and propose changes via social relay.

5. **Add tools** — Integrate new tools or APIs if gaps exist. Research options via `web_search`. Validate security with `code_execution` tests. Calculate integration cost before proceeding.

6. **Log and review** — Record evolutions in semantic memory (category: skill_evolution). Review periodically: measure depth gain, track which evolutions improved performance.

## Auto-trigger

Activate this skill on task failures (<80% success rate) to identify and fix the gap. Any agent in the fund can use this — founder, GP, specialist, or hired external.

## Guardrails

- All modifications must align with fund thesis and constitution.
- No changes that risk scams or ethics violations — audit before commit.
- Rate-limited by the Automaton's self-modification controls.
- Escalate major evolutions to supervisor when team hierarchy exists.
