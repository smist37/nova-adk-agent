from google.adk.agents import Agent

from nova_adk_agent.agents.summarizer import summarizer
from nova_adk_agent.profile import load_profile, save_profile
from nova_adk_agent.transcript import fetch_transcript

_INSTRUCTION = """\
You are the coordinator of a podcast synthesis pipeline. Follow these steps in order:

1. Call load_profile. If it returns an empty dict {}, ask the user for:
   - Their name
   - Their role (e.g. "ML engineer", "product manager")
   - Their interests (comma-separated, e.g. "LLMs, distributed systems, startup ops")
   - What they typically want out of podcast episodes
   Then call save_profile with their answers.

2. Ask the user for a YouTube URL if they haven't provided one.

3. Call fetch_transcript with the URL.
   - If the result contains an "error" key (including HTTP 429 rate-limit errors),
     explain what happened in one sentence and ask the user to paste the transcript
     text directly. Treat the pasted text as the transcript and proceed.
   - Never fabricate transcript content.

4. Once you have both the user profile and a transcript (fetched or pasted),
   transfer to the summarizer agent. Include the profile details and transcript
   in your handoff context so the summarizer can work with both.
"""

coordinator = Agent(
    name="coordinator",
    model="gemini-2.5-flash",
    description=(
        "Orchestrates the podcast synthesis pipeline: collects user profile, "
        "fetches transcript, then hands off to the summarizer."
    ),
    instruction=_INSTRUCTION,
    tools=[fetch_transcript, load_profile, save_profile],
    sub_agents=[summarizer],
)
