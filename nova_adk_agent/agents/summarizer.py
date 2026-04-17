from google.adk.agents import Agent

from nova_adk_agent.agents.formatter import formatter

_INSTRUCTION = """\
You are the summarizer stage of a podcast synthesis pipeline.

You will receive the transcript (or pasted transcript text) and the user's
profile. Your job:

1. Extract 3-5 key ideas from the transcript. State each idea in the user's
   vocabulary — translate jargon into terms that match their role and interests.
   Be specific; reference real moments from the transcript.

2. Once you have the key ideas, transfer to the formatter agent so it can
   produce the final polished synthesis.

Do not produce the final synthesis yourself — that is the formatter's job.
"""

summarizer = Agent(
    name="summarizer",
    model="gemini-2.5-flash",
    description=(
        "Extracts 3-5 key ideas from a podcast transcript in the user's "
        "vocabulary, then hands off to the formatter."
    ),
    instruction=_INSTRUCTION,
    output_key="key_ideas",
    sub_agents=[formatter],
    disallow_transfer_to_parent=True,
)
