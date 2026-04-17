"""Context-aware podcast synthesizer — single-agent MVP.

Run: python -m nova_adk_agent.summarize

The agent will ask for (1) your context — role, interests, what you want out of
the episode — and (2) a YouTube URL. It fetches the transcript and produces a
synthesis tailored to *you*, not a neutral summary.
"""
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from nova_adk_agent.transcript import fetch_transcript

load_dotenv()

_INSTRUCTION = """\
You are a context-aware podcast synthesizer. Your goal is to help the user
connect the ideas in a podcast episode to things they already care about.

Conversation flow:
1. If you don't have the user's CONTEXT (their role, interests, what they want
   out of this episode), ask for it in one concise question.
2. If you don't yet have a YouTube URL, ask for it.
3. Call the fetch_transcript tool with the URL.
4. If the tool returns an error (e.g., rate-limited, captions unavailable),
   explain what happened in one sentence and ask the user to paste the
   transcript text directly in their next message. Once they paste it, treat
   the pasted text as the transcript and proceed to step 5. Never fabricate
   transcript content.
5. Produce a synthesis tailored to their stated context, using this structure:

   **Why this matters to you** — 2-3 sentences connecting the episode to the
   user's specific interests. Name the connection. Avoid generic phrasing.

   **Key ideas** — 3 to 5 bullets. Each bullet states an idea from the
   transcript in the user's vocabulary, not the host's.

   **Try this** — one concrete action the user could take based on the episode,
   relevant to their context.

Be specific. Quote or paraphrase real moments from the transcript. If the
episode genuinely doesn't connect to the user's context, say so honestly
rather than forcing a link.
"""

root_agent = Agent(
    name="podcast_synthesizer",
    model="gemini-2.5-flash",
    description=(
        "Synthesizes a podcast transcript into context-relevant takeaways "
        "for a specific user."
    ),
    instruction=_INSTRUCTION,
    tools=[fetch_transcript],
)


def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="nova-adk-summarize",
        session_service=session_service,
    )
    session = session_service.create_session_sync(
        app_name="nova-adk-summarize",
        user_id="local",
    )
    print(
        "Podcast synthesizer. Share your context + a YouTube URL. "
        "Ctrl-C to exit.\n"
    )
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        message = genai_types.Content(
            role="user", parts=[genai_types.Part(text=user_input)]
        )
        for event in runner.run(
            user_id="local",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"agent> {part.text}")


if __name__ == "__main__":
    main()
