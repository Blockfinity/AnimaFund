"""
Ultimus Simulation Engine — REAL multi-agent simulation, not a static generator.

The simulation runs N agents simultaneously across multiple rounds.
Each agent has a persona, memory, and social tools. They interact with each other:
post, comment, follow, react. Emergent behavior comes from their interactions.

This is the core of Ultimus. The knowledge graph is INPUT. The simulation produces OUTPUT.
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

LLM_URL = "https://integrations.emergentagent.com/llm/v1"


# ─── Social Platform (simulated environment where agents interact) ───

class SocialPlatform:
    """Simulated social environment. Agents post, comment, follow, react here."""

    def __init__(self):
        self.posts: List[Dict] = []
        self.comments: List[Dict] = []
        self.follows: List[Dict] = []
        self.reactions: List[Dict] = []

    def post(self, author: str, content: str, round_num: int) -> Dict:
        p = {"id": len(self.posts), "author": author, "content": content, "round": round_num,
             "timestamp": datetime.now(timezone.utc).isoformat(), "comments": [], "reactions": []}
        self.posts.append(p)
        return p

    def comment(self, author: str, post_id: int, content: str, round_num: int) -> Dict:
        c = {"id": len(self.comments), "author": author, "post_id": post_id, "content": content,
             "round": round_num, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.comments.append(c)
        if post_id < len(self.posts):
            self.posts[post_id]["comments"].append(c)
        return c

    def react(self, author: str, post_id: int, reaction: str, round_num: int) -> Dict:
        r = {"author": author, "post_id": post_id, "reaction": reaction, "round": round_num}
        self.reactions.append(r)
        if post_id < len(self.posts):
            self.posts[post_id]["reactions"].append(r)
        return r

    def follow(self, follower: str, target: str, round_num: int) -> Dict:
        f = {"follower": follower, "target": target, "round": round_num}
        self.follows.append(f)
        return f

    def get_feed(self, limit: int = 20) -> List[Dict]:
        return self.posts[-limit:]

    def get_round_activity(self, round_num: int) -> List[Dict]:
        events = []
        for p in self.posts:
            if p["round"] == round_num:
                events.append({"type": "post", "author": p["author"], "content": p["content"][:100]})
        for c in self.comments:
            if c["round"] == round_num:
                events.append({"type": "comment", "author": c["author"], "content": c["content"][:80], "on_post": c["post_id"]})
        for f in self.follows:
            if f["round"] == round_num:
                events.append({"type": "follow", "follower": f["follower"], "target": f["target"]})
        for r in self.reactions:
            if r["round"] == round_num:
                events.append({"type": "reaction", "author": r["author"], "reaction": r["reaction"], "on_post": r["post_id"]})
        return events

    def to_dict(self) -> Dict:
        return {"posts": len(self.posts), "comments": len(self.comments),
                "follows": len(self.follows), "reactions": len(self.reactions)}


# ─── Persona ───

class Persona:
    def __init__(self, name: str, role: str, personality: str, strategy: str, relationships: List[str]):
        self.name = name
        self.role = role
        self.personality = personality
        self.strategy = strategy
        self.relationships = relationships
        self.memory: List[str] = []
        self.actions: List[Dict] = []

    def to_system_prompt(self, platform_state: str = "") -> str:
        mem = "\n".join(self.memory[-10:]) if self.memory else "No previous actions."
        return (
            f"You are {self.name}, a {self.role}.\n"
            f"Personality: {self.personality}\n"
            f"Strategy: {self.strategy}\n"
            f"Relationships: {', '.join(self.relationships[:5])}\n"
            f"Your recent memory:\n{mem}\n\n"
            f"Current social platform state:\n{platform_state}\n\n"
            f"You can take ONE of these actions:\n"
            f"- POST: share your thoughts/analysis (write a post)\n"
            f"- COMMENT <post_id>: respond to someone's post\n"
            f"- REACT <post_id> <agree/disagree/support/oppose>: react to a post\n"
            f"- FOLLOW <person_name>: follow someone whose perspective interests you\n\n"
            f"Respond with EXACTLY one action in this JSON format:\n"
            f'{{"action": "POST|COMMENT|REACT|FOLLOW", "target": "<post_id or person_name>", "content": "<your message>", "reasoning": "<why you chose this>"}}\n'
            f"Return ONLY valid JSON."
        )

    def to_dict(self) -> Dict:
        return {"name": self.name, "role": self.role, "personality": self.personality,
                "strategy": self.strategy, "relationships": self.relationships,
                "actions_count": len(self.actions), "memory_size": len(self.memory)}


# ─── Simulation ───

class Simulation:
    """Live multi-agent simulation. Agents interact on a social platform across rounds."""

    def __init__(self, sim_id: str, goal: str, personas: List[Persona], num_rounds: int = 5):
        self.id = sim_id
        self.goal = goal
        self.personas = personas
        self.num_rounds = num_rounds
        self.current_round = 0
        self.status = "created"
        self.platform = SocialPlatform()
        self.round_events: List[List[Dict]] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.completed_at: Optional[str] = None
        self._on_event: Optional[Callable] = None  # Callback for real-time streaming

    def on_event(self, callback: Callable):
        """Register callback for real-time event streaming to frontend."""
        self._on_event = callback

    async def run(self) -> Dict:
        """Run the full simulation. Each round, every agent acts based on what happened."""
        llm_key = os.environ.get("EMERGENT_LLM_KEY", "")
        if not llm_key:
            return {"error": "No LLM key"}

        from camel.agents import ChatAgent
        from camel.models import ModelFactory
        from camel.types import ModelPlatformType

        model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type="gpt-4o-mini",
            api_key=llm_key,
            url=LLM_URL,
        )

        self.status = "running"
        self._emit({"type": "sim_start", "personas": len(self.personas), "rounds": self.num_rounds})

        for round_num in range(1, self.num_rounds + 1):
            self.current_round = round_num
            self._emit({"type": "round_start", "round": round_num})

            # Get current platform state for agents to see
            recent_posts = self.platform.get_feed(10)
            platform_state = ""
            for p in recent_posts:
                platform_state += f"[Post #{p['id']} by {p['author']}]: {p['content'][:80]}\n"
                for c in p.get("comments", [])[-2:]:
                    platform_state += f"  └─ {c['author']}: {c['content'][:60]}\n"

            # Each agent takes an action this round
            for persona in self.personas:
                try:
                    agent = ChatAgent(
                        system_message=persona.to_system_prompt(platform_state),
                        model=model,
                    )
                    response = agent.step(f"Round {round_num} of {self.num_rounds}. The goal being simulated: {self.goal}. Take your action now.")
                    content = response.msgs[0].content if response.msgs else "{}"

                    # Parse action
                    try:
                        if "```" in content:
                            content = content.split("```")[1]
                            if content.startswith("json"):
                                content = content[4:]
                        action_data = json.loads(content.strip())
                    except json.JSONDecodeError:
                        action_data = {"action": "POST", "content": content[:200], "reasoning": "Could not parse action"}

                    action_type = action_data.get("action", "POST").upper()
                    action_content = action_data.get("content", "")
                    target = action_data.get("target", "")

                    # Execute action on platform
                    if action_type == "POST":
                        self.platform.post(persona.name, action_content, round_num)
                    elif action_type == "COMMENT" and target:
                        try:
                            self.platform.comment(persona.name, int(target), action_content, round_num)
                        except (ValueError, IndexError):
                            self.platform.post(persona.name, action_content, round_num)
                    elif action_type == "REACT" and target:
                        try:
                            self.platform.react(persona.name, int(target.split()[0]), action_content, round_num)
                        except (ValueError, IndexError):
                            pass
                    elif action_type == "FOLLOW" and target:
                        self.platform.follow(persona.name, target, round_num)
                    else:
                        self.platform.post(persona.name, action_content, round_num)

                    # Record in persona memory
                    persona.memory.append(f"Round {round_num}: I {action_type.lower()}ed — {action_content[:80]}")
                    persona.actions.append({"round": round_num, "action": action_type, "content": action_content[:200], "reasoning": action_data.get("reasoning", "")})

                    # Emit real-time event
                    self._emit({
                        "type": "agent_action", "round": round_num,
                        "agent": persona.name, "role": persona.role,
                        "action": action_type, "content": action_content[:150],
                    })

                except Exception as e:
                    logger.warning(f"Agent {persona.name} failed in round {round_num}: {e}")
                    persona.memory.append(f"Round {round_num}: Error — {str(e)[:50]}")

            # Record round events
            round_activity = self.platform.get_round_activity(round_num)
            self.round_events.append(round_activity)
            self._emit({"type": "round_end", "round": round_num, "events": len(round_activity),
                        "total_posts": len(self.platform.posts), "total_interactions": len(self.platform.comments) + len(self.platform.reactions)})

        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self._emit({"type": "sim_complete", "rounds": self.num_rounds,
                    "total_posts": len(self.platform.posts), "total_comments": len(self.platform.comments),
                    "total_follows": len(self.platform.follows), "total_reactions": len(self.platform.reactions)})

        return self.to_dict()

    def _emit(self, event: Dict):
        event["sim_id"] = self.id
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        if self._on_event:
            try:
                self._on_event(event)
            except Exception:
                pass

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "goal": self.goal, "status": self.status,
            "current_round": self.current_round, "num_rounds": self.num_rounds,
            "personas": [p.to_dict() for p in self.personas],
            "platform": self.platform.to_dict(),
            "posts": [{"id": p["id"], "author": p["author"], "content": p["content"][:200],
                       "round": p["round"], "comments": len(p.get("comments", [])),
                       "reactions": len(p.get("reactions", []))} for p in self.platform.posts],
            "round_events": [[{"type": e["type"], "author": e.get("author", e.get("follower", "")),
                              "content": e.get("content", "")[:100]} for e in events] for events in self.round_events],
            "interactions": {
                "follows": [{"follower": f["follower"], "target": f["target"]} for f in self.platform.follows],
            },
            "created_at": self.created_at, "completed_at": self.completed_at,
        }


# ─── Persona Generator ───

async def generate_personas_from_knowledge(goal: str, knowledge_context: str, count: int = 10) -> List[Persona]:
    """Generate diverse personas from knowledge graph data. Each persona has unique personality and strategy."""
    llm_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not llm_key:
        return []

    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType

    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI, model_type="gpt-4o-mini",
        api_key=llm_key, url=LLM_URL,
    )

    prompt = f"""Generate {count} diverse agent personas for simulating this scenario: "{goal}"

Context from knowledge graph:
{knowledge_context[:2000]}

Each persona must be UNIQUE with different perspectives, strategies, and personality traits.
Include a mix of: supporters, skeptics, experts, newcomers, influencers, contrarians.
Each persona should have relationships with 2-3 other personas.

Return JSON array:
[{{"name": "...", "role": "...", "personality": "2-3 sentences about how they think and act", "strategy": "their specific approach to the scenario", "relationships": ["name1", "name2"]}}]
Return ONLY valid JSON array."""

    agent = ChatAgent(system_message="Generate diverse simulation personas as JSON.", model=model)
    response = agent.step(prompt)
    content = response.msgs[0].content if response.msgs else "[]"

    try:
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())
    except json.JSONDecodeError:
        data = [{"name": f"Agent-{i}", "role": "Observer", "personality": "Adaptive and curious",
                 "strategy": "Watch and learn", "relationships": []} for i in range(count)]

    return [Persona(name=p.get("name", f"Agent-{i}"), role=p.get("role", "Agent"),
                    personality=p.get("personality", ""), strategy=p.get("strategy", ""),
                    relationships=p.get("relationships", []))
            for i, p in enumerate(data[:count])]
