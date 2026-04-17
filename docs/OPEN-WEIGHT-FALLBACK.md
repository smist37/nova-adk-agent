# Open-weight model fallback — routing design

**Status:** design + stub router. A production build would slot this
between the client and the model dispatcher; the stub lives at
`nova_adk_agent/routing/router.py` so the shape is testable without a
vLLM deployment.

## Problem

Every query through the podcast synthesizer currently hits Gemini 2.5
Flash. That's fine for a demo. For anything with real user volume
it's wasteful — maybe 60-80% of queries are simple enough that a small
open-weight model handles them at a tenth of the cost and a fraction
of the latency.

The routing decision: which model should handle this query?

## Routing policy

Three tiers:

| Tier | Model             | When                                      |
|------|-------------------|-------------------------------------------|
| 1    | Llama-3-8B (vLLM) | Simple extractions, keyword-level classification, short responses |
| 2    | Gemini 2.5 Flash  | The default. Structured generation, multi-paragraph synthesis, most of the agent's work |
| 3    | Gemini 2.5 Pro    | Long-context (>50k tokens), hard reasoning, fallback when Flash low-confidence |

The router decides between tiers 1 and 2. Tier 3 is reached by
explicit escalation, not by routing.

## Routing signals

The router needs cheap, reliable signals to decide. In order of
reliability:

1. **Task type** (most reliable). If the caller tags the request —
   "extract", "summarize", "format", "classify" — that's usually
   enough. Extract → tier 1. Summarize/format → tier 2.
2. **Input length.** Short inputs (<500 tokens) are usually tier 1
   candidates. Long inputs (>10k tokens) force tier 2 or 3.
3. **Output length hint.** If the caller specifies "return one
   sentence" or "return a JSON object with 3 fields," tier 1 can
   handle it. If the caller wants "a polished multi-paragraph
   synthesis with structure headers," tier 2.
4. **Confidence-based fallback.** Run tier 1, check a confidence
   signal (log-probs, a cheap classifier, or a consistency check),
   promote to tier 2 on low confidence. More expensive than static
   routing but catches edge cases.

## Why not just always use Gemini?

Three reasons:

1. **Cost.** At 1M calls/day with a cheap open model costing 10% of
   Gemini Flash, the math is ~$3k/day saved. That's infrastructure
   budget, not a rounding error.
2. **Latency.** A local vLLM server responds in 200-400ms.
   Gemini Flash is 800ms-2s for comparable work. For interactive
   agents, latency compounds.
3. **Privacy / data residency.** Some callers can't send transcripts
   to Google — classified work, HIPAA, contractual restrictions.
   Routing keeps the sensitive traffic local while letting
   everything else use the best model.

Especially relevant for cleared / federal deployments where the data
residency argument dominates. This is a cleared-AI moat: a router
that can point at a local LLama running inside an air-gap and a
commercial Gemini in the unclassified enclave.

## Interface

```python
from nova_adk_agent.routing.router import ModelRouter, RouteRequest

router = ModelRouter.default()
decision = router.route(
    RouteRequest(
        task_type="summarize",
        input_tokens=4200,
        output_tokens_hint=600,
        privacy_class="commercial",
    )
)
# decision.model = "gemini-2.5-flash"
# decision.tier = 2
# decision.reasoning = "summarize + 4.2k tokens → tier 2"
```

The router is a **pure function** of the request. No I/O, no network,
no LLM calls. That's deliberate — routing decisions have to be fast
(<1ms) and testable without infrastructure.

## Integration points

Three places the router plugs into the existing agent:

1. **Per-agent model override.** Each ADK agent gets a `model=` kwarg.
   Replace the hardcoded `"gemini-2.5-flash"` with a call to the
   router that picks based on the agent's role.
2. **Tool-call routing.** ADK tool calls often include a structured
   output schema. Short-output tools (`load_profile`) don't need a
   flagship model. The tool executor could route per-call.
3. **Fallback on quota/rate-limit.** If Gemini returns 429, the router
   can seamlessly switch to the open-weight tier for the retry.

## What the stub does

The stub (`nova_adk_agent/routing/router.py`) implements the
pure-function routing based on task type + input length + privacy
class. It returns a routing decision without actually calling any
model. A real build would add:

- vLLM client wrapper for tier 1.
- A confidence scorer (log-prob threshold or secondary classifier).
- Request-level caching (same input → same routing decision).
- Metrics (tier hit rate, fallback rate, cost per call).

These are ~1-2 days of work each, not done here because the point of
the stub is to prove the interface is stable and the decision logic
is testable.

## Failure modes to plan for

- **vLLM server down.** Router detects via health check, falls back
  to tier 2 for all traffic, fires an alert.
- **Privacy misclassification.** If a commercial query gets tagged
  `classified` by mistake, it stays on the local model — worse
  quality, but no data leak. Default should always be the more
  restrictive tier.
- **Task-type mismatch.** If the caller tags `extract` but the query
  actually needs multi-paragraph synthesis, tier 1 will produce a
  bad answer. Confidence-based fallback catches this; static routing
  doesn't.
