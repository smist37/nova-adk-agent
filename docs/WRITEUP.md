# Four weeks shipping an ADK agent in public

A public portfolio build. Daily commits. One LinkedIn post per week.
Four weeks end-to-end. This is the honest write-up — what got built,
what I learned, what I'd do differently.

## The brief

I wanted a portfolio piece that demonstrated gen-AI engineering
capability and used Google's Agent Development Kit as the vehicle.
Agent frameworks are the new battleground — LangGraph, ADK, CrewAI,
Autogen — and hiring managers for LLM-engineer roles want proof you've
actually shipped something in one of them. A four-week public build
produces the artifact (repo + LinkedIn posts) while forcing a hard
cadence that keeps perfectionism from eating the project.

Scope, set on day one: a multi-agent podcast synthesizer. Give it a
YouTube URL plus your user profile, it fetches the transcript, extracts
the three-to-five ideas that matter to *you*, and writes a personalized
synthesis. Nothing groundbreaking — the point wasn't novelty, it was a
narrow, real capability I could build cleanly and stress-test.

## Week 1 — scaffold and the three-agent chain

Hello-world ADK agent first, then a single-agent MVP, then the
three-agent chain. ADK gives you three orchestration patterns:
sequential (framework decides the order), delegating/transfer (LLM
decides the handoff), and workflow with an explicit router. I picked
delegating because the flow is content-dependent — the coordinator
only hands off once a transcript is actually available, and only if
it's usable.

The subtle bug that ate most of Sunday was that the summarizer kept
doing the formatter's job. The agents *could* transfer, but the LLM
didn't *know* it was supposed to. The fix wasn't more logic; it was
one line in the summarizer's prompt: *"Do not produce the final
synthesis yourself — that is the formatter's job."* The thing most
multi-agent demos hide is that each agent has to be prompted to *stop*
at the right boundary. Otherwise it'll try to do the whole pipeline
itself and ignore your carefully wired sub-agents.

## Week 2 — Vertex wiring and the eval harness

Two pieces, shipped separately.

First, Vertex AI deploy wiring. The deploy function is written and
unit-tested, but the actual `deploy()` call is gated behind a
commented-out `__main__` block so importing the module has zero GCP
side effects. I deliberately didn't run a live deploy — paying for a
Vertex AgentEngine that no one is calling is a waste of billing on a
portfolio repo. The code path is proven, the config builder has tests,
the deploy doc walks through prereqs and common failure modes. If
someone clones the repo and has a real use case, the on-ramp is
twenty minutes.

Second, and more interesting: the RAGAS eval harness. Most multi-agent
demos ship with zero evaluation. I wrote a five-case test set — one
transcript, five user profiles — and measured two things: faithfulness
(did the agent fabricate?) and answer_relevancy (did the agent
personalize?). Same transcript across all five cases. Different
profiles. The test is whether the agent *personalizes*, not whether
it summarizes. A generic summary gets good faithfulness and bad
relevancy, and that's the gap I wanted to measure.

The biggest thing I took from week 2 wasn't the harness itself, it
was that **writing the eval forced me to articulate what "good" means**.
"Faithful *and* personalized *and* willing to say no when the episode
doesn't connect" was a stronger spec than anything I had in my head
before. The eval is a design tool, not a grading tool.

Also: RAGAS vs. DeepEval. I picked RAGAS because it's the most-cited
eval framework in recent agent papers and its faithfulness metric is
exactly the check I needed. DeepEval would be a better pick if I were
testing *agent behaviour* — "did the coordinator delegate correctly?"
— but for a summarizer, content fidelity is the thing. I wrote the
tradeoff into `eval/README.md` so future-me knows when to switch.

## Week 3 — A2A and the clone-and-run test

Week 3 was the payoff week. I pulled the formatter out of the in-process
chain and ran it as a standalone A2A service on port 8765. The
coordinator + summarizer live in a separate process and call the
formatter over the A2A wire protocol using ADK's `RemoteA2aAgent`.

Two things surprised me:

1. **ADK's `RemoteA2aAgent` is essentially a transparent proxy.** Four
   lines of Python and you have a remote agent. The SDK handles
   marshalling conversation state, converting between ADK's internal
   part format and A2A's wire format, and translating function calls
   across the hop. I was expecting a week's work; it was an afternoon.

2. **The agent card model is the real reason A2A exists.** A2A's
   `/.well-known/agent-card.json` is how one agent *discovers* another
   without a shared SDK. Every team that rolls their own HTTP contract
   between agents is reinventing this — usually badly, usually via a
   wiki page that goes stale. The protocol overhead of A2A buys you
   discovery, state-machine semantics, and interop.

The tradeoff is still real, though. In-process `sub_agents` beats A2A
when both agents live in the same codebase and the same deploy unit.
For the podcast synthesizer, the coordinator + summarizer share
context tightly and belong in-process. The formatter is a pure
function and is a clean candidate for a shared utility service — so
the split I wired matches the actual coupling.

Week 3 also shipped `scripts/smoketest.sh` — a fresh-venv
clone-and-install verification that runs against a blank environment.
If a hiring manager clones the repo and it doesn't install and import
cleanly, everything else is noise. Smoketest passes. Clone + `bash
scripts/smoketest.sh` works end to end.

## What didn't work / what I'd do differently

**The user-profile persistence is a `.json` file in the CWD.** That's a
footgun. If you run the agent from a different directory, you get a
fresh profile. A real deployment needs either an ADK SessionService
with persistent storage or a proper user-scoped DB. I left it as a
flat file because week 1 velocity > week 4 elegance, but it's the
first thing I'd rip out if this turned into a real product.

**The transcript fetcher uses yt-dlp as the primary path.** That works
but it's fragile — YouTube changes their caption backend often, and
yt-dlp has to chase. A production build should hit YouTube's captions
API directly (or use a caption-specific library like
`youtube-transcript-api`) with yt-dlp as the fallback, not the
primary.

**The eval set is five cases.** That's enough to catch obvious
regressions but not enough to trust the agent across a
production-scale distribution of users. A real eval set is 50-100
cases with stratification across user archetypes, transcript
lengths, and episode genres. For a portfolio artifact, five is
correct. For a product, not close.

**I didn't ship the stretch goals.** CI/CD on push, an A2A-MCP bridge
to Nova, an open-weight model fallback router, an air-gapped
security variant — all of those are interesting and all of them got
scoped docs but not production code this month. Each would be a
two-to-four-day project on its own. If I do a month two, the
open-weight router is the highest-leverage next build.

## What the repo proves

- I can build a multi-agent system in ADK, end to end, with working
  tests and a clone-and-run install.
- I care about evaluation and wrote the harness before shipping the
  LinkedIn post. Most demos skip this.
- I understand A2A well enough to split a chain across processes and
  defend the tradeoff.
- I can ship daily in public without the commits turning into padding.

## What the repo doesn't prove

- Nothing about production scale. Eval set is small, traffic is zero,
  there's no load test, no observability layer.
- Nothing about cleared-environment deploys. The security-variant
  doc exists, the Dockerfile doesn't.
- Nothing about cost at real traffic. The routing angle is
  documented but not implemented.

## What's next

If this project rolls into a month-two build, priority order:

1. **Open-weight model fallback router.** Route easy queries through
   a small open-weight model (Llama, Nous Hermes), hard queries
   through Gemini. Real cost-control pattern. Highest-leverage
   differentiator for the next LinkedIn post.
2. **CI/CD on push.** GitHub Actions running the eval suite against
   a fixed transcript. Turns the repo from "demo" to "engineered."
3. **A2A-MCP bridge.** Wire the ADK agent to Nova over A2A. Few
   people are doing this publicly.
4. **Security variant.** Dockerfile for air-gapped deployment,
   tied to the cleared-AI-engineer lane.

But the artifact exists. It builds. It passes the clone-and-run test.
It has an eval harness. It has docs. It's enough to point a recruiter
at with confidence. The month-one brief is done.

---

**Repo:** https://github.com/smist37/nova-adk-agent

**Total committed code:** ~2,500 lines Python + docs. Four weeks, five
commits per week average, zero empty commits. Four LinkedIn posts
drafted (weeks 1-4) and ready to publish on the weekly cadence.

If you're building something similar and want to compare notes, reach
out. And if you're hiring for LLM-engineer or cleared-AI roles, this
repo is the artifact.
