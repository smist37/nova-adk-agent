"""Client-side agent for the A2A demo.

The client is a two-stage chain:
  client_coordinator -> client_summarizer -> RemoteA2aAgent(formatter)

The summarizer hands off to a ``RemoteA2aAgent`` that points at the formatter
service running elsewhere. The wire-format handoff is A2A — the remote agent
could live in another process, another host, another organization. The ADK
runtime handles marshalling the conversation state across the hop.

Environment:
    A2A_FORMATTER_URL — base URL of the running formatter service. Defaults
    to ``http://127.0.0.1:8765`` which matches the command in docs/A2A.md.
"""
from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)

from nova_adk_agent.profile import load_profile, save_profile
from nova_adk_agent.transcript import fetch_transcript


def _formatter_card_url() -> str:
    base = os.environ.get("A2A_FORMATTER_URL", "http://127.0.0.1:8765")
    return f"{base.rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"


remote_formatter = RemoteA2aAgent(
    name="remote_formatter",
    description="Formatter running as an A2A service on a separate port.",
    agent_card=_formatter_card_url(),
)


client_summarizer = Agent(
    name="client_summarizer",
    model="gemini-2.5-flash",
    description=(
        "Extracts 3-5 key ideas from a transcript, then hands off over A2A "
        "to the remote formatter."
    ),
    instruction=(
        "You are the summarizer stage. Extract 3-5 key ideas from the "
        "transcript in the user's vocabulary. Once extracted, transfer to "
        "remote_formatter — it is a REMOTE A2A service that will write the "
        "final synthesis. Include the key ideas and profile in your handoff."
    ),
    output_key="key_ideas",
    sub_agents=[remote_formatter],
    disallow_transfer_to_parent=True,
)


client_coordinator = Agent(
    name="client_coordinator",
    model="gemini-2.5-flash",
    description=(
        "A2A-mode coordinator. Collects profile + transcript, hands off to "
        "the summarizer which then hands off to the remote formatter."
    ),
    instruction=(
        "You are the coordinator for the A2A demo. Your job:\n"
        "1. Call load_profile. If empty, collect name, role, interests, "
        "wants_from_episodes from the user and save_profile.\n"
        "2. Ask for a YouTube URL if you don't have one. Call "
        "fetch_transcript. If the result has an error, ask the user to "
        "paste the transcript.\n"
        "3. Transfer to client_summarizer, passing the profile and "
        "transcript in the handoff context.\n"
        "\n"
        "The client_summarizer will then transfer to remote_formatter, "
        "which is a separate A2A service. The user will receive the final "
        "synthesis from that remote service."
    ),
    tools=[fetch_transcript, load_profile, save_profile],
    sub_agents=[client_summarizer],
)


root_agent = client_coordinator
