"""Non-interactive helper: summarize a transcript string with the ADK agent.

Exposes ``summarize_transcript(text, profile)`` for programmatic callers — the
eval harness, CI smoke tests, and demo scripts all use this. Separate from
``summarize.py`` (interactive single-agent) and ``__main__.py`` (interactive
multi-agent chain) to keep the interactive REPL and the library surface apart.
"""
from __future__ import annotations

import asyncio
from typing import Any

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()


_SYSTEM = """\
You are a context-aware podcast synthesizer. The user has already pasted the
transcript in their first message and provided their profile. Produce a
synthesis tailored to them.

Structure:
**Why this matters to you** — 2-3 sentences connecting the episode to the
user's role/interests. Name the connection explicitly.

**Key ideas** — 3-5 bullets in the user's vocabulary. Quote or paraphrase at
least one real moment from the transcript. Do not fabricate.

**Try this** — one concrete action relevant to the user's context.
"""


def _build_agent() -> Agent:
    return Agent(
        name="summarize_text_agent",
        model="gemini-2.5-flash",
        description="One-shot transcript → personalized synthesis.",
        instruction=_SYSTEM,
    )


def summarize_transcript(
    transcript: str,
    profile: dict[str, Any] | None = None,
    *,
    app_name: str = "nova-adk-eval",
    user_id: str = "eval",
) -> str:
    """Run the summarizer over ``transcript`` and return the final text.

    ``profile`` should be a dict like
    ``{"name": "...", "role": "...", "interests": [...], "wants_from_episodes": "..."}``.
    Synchronous wrapper around the async runner.
    """
    profile = profile or {}
    agent = _build_agent()
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )

    async def _run() -> str:
        session = await session_service.create_session(
            app_name=app_name, user_id=user_id
        )
        prompt_lines = ["PROFILE:"]
        for k, v in profile.items():
            prompt_lines.append(f"  {k}: {v}")
        prompt_lines.append("\nTRANSCRIPT:\n" + transcript)
        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text="\n".join(prompt_lines))],
        )
        chunks: list[str] = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        chunks.append(part.text)
        return "\n".join(chunks).strip()

    return asyncio.run(_run())
