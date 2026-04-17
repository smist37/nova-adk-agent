"""Open-weight fallback router — pure-function stub.

Full design: ``docs/OPEN-WEIGHT-FALLBACK.md``.

The router decides which model tier handles a given request. No I/O. No
LLM calls. Tests pin the decision logic so the routing policy is a
first-class, reviewable artifact — not a throwaway if/else scattered
across agent code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PrivacyClass = Literal["commercial", "sensitive", "classified"]
TaskType = Literal["extract", "classify", "summarize", "format", "synthesize", "reason"]


# Tier → representative model ID. The stub returns strings, not clients.
TIER_1_MODEL = "llama-3-8b-instruct"    # Local vLLM
TIER_2_MODEL = "gemini-2.5-flash"       # Commercial default
TIER_3_MODEL = "gemini-2.5-pro"         # Commercial flagship


@dataclass
class RouteRequest:
    task_type: TaskType
    input_tokens: int
    output_tokens_hint: int = 0
    privacy_class: PrivacyClass = "commercial"
    escalate: bool = False  # caller-forced tier-3


@dataclass
class RouteDecision:
    model: str
    tier: int
    reasoning: str


class ModelRouter:
    """Pure-function routing decision.

    Kept as a class (not a free function) so a real build can subclass
    and inject a confidence scorer, a rate-limit fallback hook, or a
    metrics sink without changing the call sites.
    """

    # Task types that tier-1 open-weight models handle well.
    TIER_1_TASKS: frozenset[str] = frozenset({"extract", "classify"})

    # Hard cap on tier-1 input length (tokens). Above this, promote.
    TIER_1_MAX_INPUT_TOKENS = 2000

    # If the caller hints they want a long answer, small models fall apart.
    TIER_1_MAX_OUTPUT_TOKENS = 300

    # Long-context queries always go to tier 3 regardless of task type.
    TIER_3_MIN_INPUT_TOKENS = 50_000

    @classmethod
    def default(cls) -> "ModelRouter":
        return cls()

    def route(self, req: RouteRequest) -> RouteDecision:
        # 1. Classified / sensitive data never leaves the local model.
        if req.privacy_class in ("classified", "sensitive"):
            return RouteDecision(
                model=TIER_1_MODEL,
                tier=1,
                reasoning=f"privacy_class={req.privacy_class} → local model only",
            )

        # 2. Explicit escalation wins.
        if req.escalate:
            return RouteDecision(
                model=TIER_3_MODEL,
                tier=3,
                reasoning="caller requested escalation",
            )

        # 3. Long-context queries force tier 3.
        if req.input_tokens >= self.TIER_3_MIN_INPUT_TOKENS:
            return RouteDecision(
                model=TIER_3_MODEL,
                tier=3,
                reasoning=f"input_tokens={req.input_tokens} exceeds tier-3 threshold",
            )

        # 4. Tier-1 eligibility: task type + input length + output length.
        if (
            req.task_type in self.TIER_1_TASKS
            and req.input_tokens <= self.TIER_1_MAX_INPUT_TOKENS
            and req.output_tokens_hint <= self.TIER_1_MAX_OUTPUT_TOKENS
        ):
            return RouteDecision(
                model=TIER_1_MODEL,
                tier=1,
                reasoning=(
                    f"{req.task_type} + {req.input_tokens}in/{req.output_tokens_hint}out → "
                    "tier 1 (local, cheap)"
                ),
            )

        # 5. Default: tier 2.
        return RouteDecision(
            model=TIER_2_MODEL,
            tier=2,
            reasoning=(
                f"{req.task_type} + {req.input_tokens}in/{req.output_tokens_hint}out → "
                "tier 2 (commercial default)"
            ),
        )
