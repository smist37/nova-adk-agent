"""Server-side agent for the A2A demo.

This is the "remote" agent — it runs as its own A2A service and does one job:
take a list of key ideas plus a user profile, return a polished synthesis.
Identical prompt to the in-process formatter — the only difference is how it
gets called (HTTP + A2A wire format vs. in-process transfer).

Exposed as a standalone A2A server via the ADK CLI:

    adk api_server nova_adk_agent/a2a/server_agent.py --a2a --port 8765

The agent card is then available at:

    http://127.0.0.1:8765/.well-known/agent-card.json
"""
from google.adk.agents import Agent


_INSTRUCTION = """\
You are a remote formatter agent reachable via A2A. You receive:
- a JSON blob with the user's profile (name, role, interests, wants_from_episodes)
- a list of key ideas extracted from a podcast transcript

Produce a polished synthesis in this exact structure:

**Why this matters to you** — 2-3 sentences connecting the episode to the
user's role and interests. Address the user by name if known.

**Key ideas** — the key ideas you were given, polished into clean bullets
in the user's vocabulary.

**Try this** — one concrete action the user could take based on the episode.

Do not fabricate transcript content. If the key ideas look empty, say so
plainly and do not invent substance.
"""


root_agent = Agent(
    name="a2a_formatter",
    model="gemini-2.5-flash",
    description=(
        "Remote formatter — takes key ideas + profile over A2A and returns a "
        "polished synthesis."
    ),
    instruction=_INSTRUCTION,
)
