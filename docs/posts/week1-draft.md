# Week 1 — Multi-agent orchestration patterns in Google ADK

*Draft. Do not publish without a final pass from Miles.*

---

ADK gives you three ways to compose agents. I spent week 1 of a public
4-week ADK build figuring out which one to reach for, and when. Here's
what shook out.

**Pattern 1 — Sequential.** You chain agents A → B → C. Each agent's
output becomes the next agent's input. ADK gives you `SequentialAgent`
to express this directly. It's the right tool when the stages are
*fixed*: you always summarize before you format, you always retrieve
before you answer. No dynamic routing. No skipping steps.

**Pattern 2 — Delegating (transfer).** You hand control from one agent
to another at runtime, using `sub_agents` + an LLM-decided transfer.
The parent agent decides who's best suited to take the next turn —
maybe summarizer, maybe formatter, maybe itself. It's the right tool
when the *flow depends on content*: the coordinator only transfers to
the summarizer once a transcript is available, and only if the
transcript is usable.

**Pattern 3 — Workflow with a router.** An explicit router agent picks
the next sub-agent based on state. More deterministic than transfer,
more flexible than sequential. It's the right tool when you have three
or more paths and you want routing logic you can read and test.

I built the week 1 ADK agent — a three-stage podcast synthesizer —
using **pattern 2**. The coordinator handles profile + transcript,
then transfers to the summarizer, which transfers to the formatter.
Two transfers, one direction, no loops.

Here's the subtle thing: pattern 2 looks like pattern 1 when it runs.
The difference is *who decides the next step*. In sequential, the
framework decides. In transfer, the LLM decides. That means in
transfer mode, your prompt has to explicitly say "when you're done,
hand off to the formatter" — otherwise the agent tries to do the
formatter's job itself.

The bug I kept hitting in iteration: the summarizer would extract key
ideas *and* write the final synthesis, skipping the formatter. The
fix wasn't more logic; it was one line in the summarizer's prompt:
*"Do not produce the final synthesis yourself — that is the
formatter's job."*

This is the thing most multi-agent demos hide: the LLM has to *know*
it's in a pipeline. If it doesn't, it'll do the whole job itself and
ignore the sub-agents you carefully wired up.

Three patterns, three use cases, one prompt-engineering trap. If
you're evaluating ADK for production work, this is where the
prompt engineering time goes — not in the tools, not in the
orchestration, but in teaching each agent to *stop* at the right
boundary.

Repo: https://github.com/smist37/nova-adk-agent

Next week: deploy it to Vertex AI and wrap it in a RAGAS eval harness.

#GoogleADK #AgentDevelopmentKit #LLMEngineering #GenAI
