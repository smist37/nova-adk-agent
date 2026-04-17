# Week 4 — What shipping an agent in public for a month taught me

*Draft. Do not publish without a final pass from Miles.*

---

A month ago I started a public build log: one ADK agent, four weeks,
daily commits, one LinkedIn post per week. Yesterday I wrote the
write-up. Here's the reflection.

**The public cadence was the forcing function.** Without the weekly
post, week 2 would have become week 3, week 3 would have become week
5, and the repo would have gone quiet. The commitment to post on
Wednesday is what kept Tuesday from slipping. If you've been
considering a public build, the discipline isn't from the writing —
it's from the ship date.

**Daily commits are not the same as daily work.** Some days I shipped
400 lines and a new feature. Some days I fixed a prompt and added a
test and moved on. The rule wasn't "ship volume," it was "ship real
output every day." Empty commits would have been a failure — they
count against you, not for you. If you're tracking the repo activity
graph as a signal, this is the one that matters.

**Writing the eval harness was the highest-leverage thing I did all
month.** Not because the harness itself caught a bug, but because
writing the five test cases forced me to articulate what "good" meant
for this agent. "The synthesis is faithful *and* personalized *and*
willing to say no when the episode doesn't connect" — that was
stronger than anything I'd written down before. Most demos skip this
step. The demos that skip it read differently to a hiring manager.

**A2A is smaller than I expected.** I'd filed it under "big protocol,
weeks of integration work." In practice, ADK's `RemoteA2aAgent` is
four lines and it handles the wire format for you. The protocol does
real work — discovery via agent cards, state-machine semantics,
streaming — but using it is cheap. If you've been avoiding multi-process
agent architectures because "the protocol looks heavy," run the math
again.

**The stretch goals didn't ship.** Four were on the list: CI/CD, an
A2A-MCP bridge to my other agent Nova, an open-weight model fallback
router, and an air-gapped security variant. None of them made the
month-one cut. That's not a failure — scoping stretch goals as
optional is what protected the core from slipping. But it is a
pattern worth naming: the core build always takes the full month, no
matter how aggressively you plan.

**The thing that mattered wasn't the code, it was the spec I built
while writing the code.** The repo is ~2,500 lines. The README and
WRITEUP are the artifacts that actually land with a hiring manager.
Treating the write-up as the deliverable (instead of a byproduct)
would have changed how I sequenced the work.

**What I'd do differently if I ran month one again:**
1. Write the WRITEUP stub on day one and update it daily. Let it
   accumulate, don't write it at the end.
2. Ship the eval harness in week 1, not week 2. The act of writing
   the test cases sharpens the core spec too much to delay.
3. Scope the stretch goals out of month one explicitly. Plan them as
   a month two, not as "time permitting" — that framing kept me from
   committing to either the stretch or the main line.

**What I'd do the same:**
1. Daily commits, weekly post. The cadence was the thing.
2. Picking a narrow, real capability (a personalized podcast
   synthesizer) instead of a generic demo. It gave every decision a
   concrete test: does this make the synthesis better for a
   specific user?
3. Refusing to run a live Vertex deploy "just for the screenshot."
   Paying for inference nobody is calling is a red flag to
   infra-aware reviewers. Wiring the deploy path and documenting it
   clearly reads stronger than a live endpoint nobody uses.

Repo: https://github.com/smist37/nova-adk-agent
Full write-up: `docs/WRITEUP.md`

Month two planning next. If you're hiring for LLM-engineer or
cleared-AI roles, this repo is the artifact.

#GoogleADK #LLMEngineering #GenAI #PublicBuild
