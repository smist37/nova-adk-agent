"""Tests for the open-weight fallback router.

These are pure-function tests — no LLM, no network. They pin the routing
policy so a policy change shows up in the test diff, not silently in
production.
"""
from nova_adk_agent.routing.router import (
    TIER_1_MODEL,
    TIER_2_MODEL,
    TIER_3_MODEL,
    ModelRouter,
    RouteRequest,
)


def _router() -> ModelRouter:
    return ModelRouter.default()


def test_short_extract_goes_to_tier_1():
    d = _router().route(
        RouteRequest(task_type="extract", input_tokens=300, output_tokens_hint=100)
    )
    assert d.tier == 1
    assert d.model == TIER_1_MODEL


def test_summarize_goes_to_tier_2_by_default():
    d = _router().route(
        RouteRequest(task_type="summarize", input_tokens=4000, output_tokens_hint=400)
    )
    assert d.tier == 2
    assert d.model == TIER_2_MODEL


def test_long_input_forces_tier_3():
    d = _router().route(
        RouteRequest(task_type="summarize", input_tokens=80_000)
    )
    assert d.tier == 3
    assert d.model == TIER_3_MODEL


def test_explicit_escalation_wins_over_default():
    d = _router().route(
        RouteRequest(task_type="extract", input_tokens=100, escalate=True)
    )
    assert d.tier == 3


def test_classified_data_stays_local_even_for_reasoning():
    d = _router().route(
        RouteRequest(
            task_type="reason",
            input_tokens=30_000,
            privacy_class="classified",
            escalate=True,
        )
    )
    # Privacy check is the first gate — it wins over escalation.
    assert d.tier == 1
    assert d.model == TIER_1_MODEL


def test_large_output_hint_promotes_tier_1_candidate():
    d = _router().route(
        RouteRequest(task_type="extract", input_tokens=500, output_tokens_hint=5000)
    )
    # Extract would be tier 1, but a 5k-token output demands tier 2.
    assert d.tier == 2


def test_tier_1_only_for_whitelisted_task_types():
    d = _router().route(
        RouteRequest(task_type="synthesize", input_tokens=100, output_tokens_hint=100)
    )
    # Synthesize is not in TIER_1_TASKS, so it falls through to tier 2
    # regardless of how cheap the query looks.
    assert d.tier == 2
