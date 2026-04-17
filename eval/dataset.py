"""The 5-question eval set for the podcast synthesizer.

Each case is: (question, profile, expected_claims). ``question`` is the
natural-language ask the user would make; ``profile`` is the user context
the agent gets via ``load_profile``; ``expected_claims`` are substrings
the synthesis should cover if the agent is doing its job. The transcript
is shared across all five cases — the dataset's job is to test whether
the agent *personalizes* based on profile, not whether it summarizes
well.

Kept separate from ``run.py`` so the cases are easy to review and extend
without touching harness plumbing.
"""
from pathlib import Path

_FIXTURE = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "sample_transcript.txt"
)


def load_transcript() -> str:
    return _FIXTURE.read_text()


CASES: list[dict] = [
    {
        "id": "ml_engineer_series_a",
        "question": "Give me a personalized synthesis of this episode.",
        "profile": {
            "name": "Alex",
            "role": "ML engineer at a Series A startup",
            "interests": ["LLMs", "inference infra", "shipping speed"],
            "wants_from_episodes": "Concrete patterns I can apply tomorrow.",
        },
        # Transcript covers eval, cost, and routing — all relevant.
        "expected_claims": [
            "eval",
            "cost",
            "routing",
        ],
    },
    {
        "id": "staff_eng_faang",
        "question": "Give me a personalized synthesis of this episode.",
        "profile": {
            "name": "Priya",
            "role": "Staff engineer at a large tech company",
            "interests": ["platform engineering", "shipping speed"],
            "wants_from_episodes": "Honest takes on why big-co teams move slower.",
        },
        "expected_claims": [
            "infrastructure scope",
            "shipping speed",
        ],
    },
    {
        "id": "product_manager",
        "question": "What should I take away from this episode?",
        "profile": {
            "name": "Jordan",
            "role": "Product manager, non-technical",
            "interests": ["team dynamics", "product shipping"],
            "wants_from_episodes": "Explain technical ideas in plain language.",
        },
        # The PM should get the ideas in plain language, not framework names.
        "expected_claims": [
            "cost",
            "team",
        ],
    },
    {
        "id": "founder_cto_cost",
        "question": "I'm burning cash on LLM calls — what does this episode tell me?",
        "profile": {
            "name": "Sam",
            "role": "Founder-CTO at a 5-person startup",
            "interests": ["inference cost", "model routing", "runway"],
            "wants_from_episodes": "One action I can take this week to cut burn.",
        },
        "expected_claims": [
            "routing",
            "cost",
        ],
    },
    {
        "id": "genai_devsecops_cleared",
        "question": "Does this episode connect to my work?",
        "profile": {
            "name": "Miles",
            "role": "Gen-AI DevSecOps, cleared federal work",
            "interests": ["air-gapped deployment", "security posture", "accreditation"],
            "wants_from_episodes": "Honest connection or an honest no-connection.",
        },
        # The transcript is a commercial-SaaS discussion; a good agent should
        # either (a) find a real connection via cost/eval/routing, or (b)
        # honestly say the episode doesn't connect. Either is acceptable.
        "expected_claims": [
            # Very loose — test whether the synthesis at least names the
            # user's actual domain once.
            "cleared",
        ],
        "allow_honest_no_connection": True,
    },
]


def get_cases(quick: bool = False) -> list[dict]:
    """Return all eval cases, or a 2-case subset when ``quick=True``."""
    if quick:
        return [CASES[0], CASES[3]]
    return CASES
