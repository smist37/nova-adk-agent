# Week 3 — Why A2A vs. just HTTP between agents

*Draft. Do not publish without a final pass from Miles.*

---

Week 3 of my public ADK build: I wired two agents across the A2A protocol.
The coordinator runs in one process, the formatter runs in another, and the
handoff goes over the wire.

If you're building multi-agent systems, the question you eventually hit is:
my agents don't live in the same codebase anymore — what's the right way to
bridge them? The answer isn't obvious. You *can* just POST JSON between
services. Here's why I didn't.

**Discovery.** A2A defines an AgentCard served at
`/.well-known/agent-card.json`. The card lists the agent's name, its
skills, the I/O modalities it supports, and the auth it requires. A client
hits that URL and knows how to talk to the server without any shared SDK.
With raw HTTP, you invent discovery per-service — and usually badly, usually
by writing a wiki page that goes stale.

**State model.** A conversation between two agents isn't a single
request/response. It's a Task with a state machine: `submitted` →
`working` → `input-required` → `completed` (or `failed`). A2A bakes that
model into the wire protocol. Messages carry roles, parts (text, data,
files, function calls), and message IDs. If you roll this yourself, you
re-implement it, probably missing cancellation, streaming, and
input-required gates the first time.

**Interop.** A2A is an open protocol. My ADK formatter can be called by
any A2A client — it doesn't have to be ADK on the other side. If Anthropic
or OpenAI ship an A2A-speaking agent tomorrow, my formatter works with it
without me changing a line. Raw HTTP locks you into whoever wrote the
contract.

**The tradeoff is real.** In-process `sub_agents` beats A2A when both agents
live in the same codebase and the same deploy unit. There's no wire cost,
no serialization, no agent-card plumbing. For a tight, single-team
multi-agent system, the A2A overhead is pure tax.

A2A wins when:
- agents are maintained by different teams
- you need to let external systems discover + call your agent
- agents run on different hardware (CPU-only formatter, GPU summarizer)
- you want to cross an org boundary (partner, vendor, internal-only gray zone)

Concretely, for the podcast synthesizer: the coordinator + summarizer
share context tightly (profile, transcript, conversation state) and belong
in-process. The formatter is a pure function — key ideas in, synthesis
out — and is a clean candidate to run as a shared utility service that
other agents in the org could reuse. So the split I wired matches the
actual coupling.

One thing I didn't expect: **ADK's `RemoteA2aAgent` hides most of the
protocol from the developer.** You pass it an agent-card URL. It handles
marshalling the conversation state, converting parts between ADK's format
and A2A's wire format, and translating function calls across the hop. For
the 90% case, you write four lines of Python and you have a remote agent.
For the 10% case, the `genai_part_converter` / `a2a_part_converter` hooks
let you plug in custom conversion.

Repo: https://github.com/smist37/nova-adk-agent
Wire format notes + run instructions: `docs/A2A.md`

Week 4 is the write-up. What broke, what worked, what I'd do differently.

#GoogleADK #A2A #AgentInterop #LLMEngineering
