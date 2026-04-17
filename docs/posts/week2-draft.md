# Week 2 — How I measured my agent's quality

*Draft. Do not publish without a final pass from Miles.*

---

Most multi-agent demos ship with zero evaluation. You read the README, you
watch the demo video, you take the author's word. That's not an engineering
artifact. That's a screenshot.

Week 2 of my public 4-week ADK build: I wired up a RAGAS eval harness.
Five test cases. Two metrics. One non-negotiable rule: the harness runs
against the same agent a user would run.

**Why RAGAS and not DeepEval?** RAGAS is the most-cited eval framework in
recent RAG and agent papers — the signal value of "I used the public
standard" is real. Its faithfulness metric directly tests the thing that
matters for a summarizer: did the agent fabricate content that wasn't in
the transcript? DeepEval would be the right pick if I were testing
*agent behaviour* — "did the coordinator delegate correctly?" — but the
podcast synthesizer's job is content fidelity, so RAGAS wins. I
documented the tradeoff in the repo's `eval/README.md` so future-me (or
anyone forking) knows when to switch.

**The test set is five cases, not fifty.** Each case is one transcript
plus one user profile:
- ML engineer at a Series A startup
- Staff engineer at a large tech company
- Product manager, non-technical
- Founder-CTO who's cost-sensitive
- Gen-AI DevSecOps in cleared federal work

Same transcript for all five. Different profiles. The test isn't "did
the agent summarize?" — it's "did the agent *personalize*?" A generic
summary gets a good faithfulness score but a bad relevancy score, and
that's the gap I wanted to measure.

**Two metrics, chosen deliberately:**
- `faithfulness` — every factual claim in the synthesis must trace back
  to the transcript. Catches hallucinations.
- `answer_relevancy` — the synthesis must actually answer the user's
  question in their context. Catches generic summaries.

Soft targets: faithfulness ≥ 0.85, relevancy ≥ 0.80. Hard floor: either
dropping below 0.70 fails the run. I set the floor at 0.70 deliberately
— lower than I wanted, because the first honest pass should tell me
where the agent actually is, not where I hope it is.

**The interesting case is the fifth one.** The cleared-work profile has
no real overlap with the transcript (a commercial-SaaS discussion about
LLM startups). A good agent should say *"this episode doesn't connect
to your context"* rather than force a link. I added an
`allow_honest_no_connection` flag to the case so the harness doesn't
penalize the agent for the correct answer.

This is the thing I keep coming back to: **the eval is a design tool, not
a grading tool.** Writing the test set forced me to articulate what
"good" means for this agent. "Faithful *and* personalized *and* willing
to say no" is a stronger spec than anything I had in my head before I
sat down to write the harness.

Repo: https://github.com/smist37/nova-adk-agent
Eval harness: `python -m eval.run`

Next week: wire two agents together over A2A.

#GoogleADK #RAGAS #LLMEngineering #GenAI #AgentEval
