# A2A ↔ MCP bridge — design note

**Status:** design only. A stub bridge lives at
`nova_adk_agent/bridges/a2a_mcp.py` but it is not wired into the
default chain. This doc explains the shape of the problem and the
shape of the solution.

## Why this matters

ADK agents speak A2A. Nova speaks MCP (Model Context Protocol) — its
skills are MCP servers, its tools are bash scripts, its memory is a
local SQLite store behind an MCP-wrapped interface. If I want an ADK
agent to call a Nova skill, or a Nova agent to call an ADK-A2A
service, something has to translate between the two protocols.

This is the underrated surface in multi-agent systems: nobody talks
about the bridges because nobody wants to build them. But the moment
you have two agent frameworks in one org, you have a bridge problem.

## Protocol comparison

|                          | A2A                         | MCP                          |
|--------------------------|-----------------------------|------------------------------|
| Primary transport        | HTTP + JSON-RPC + SSE       | JSON-RPC over stdio or HTTP  |
| Discovery                | `/.well-known/agent-card.json` | Server lists via config     |
| Unit of work             | Task (stateful, long-lived) | Request/response             |
| State model              | State machine w/ history    | Stateless per call           |
| Typical caller           | Another agent               | An LLM host (Claude, IDE)    |
| Typical callee           | Another agent               | A tool server                |
| Identity model           | Agent-as-peer               | Server-as-utility            |

The deepest mismatch: **A2A is peer-to-peer, MCP is host-to-server.**
An A2A agent can hold state across turns and decide to invoke you
again later. An MCP tool is called, returns, and forgets.

## Two directions

### Direction A: A2A client → MCP server

An ADK agent wants to call one of Nova's MCP skills (say,
`memory.search`). Bridge shape:

1. Bridge presents itself as an A2A agent (has an agent card, serves
   A2A on a port).
2. The A2A card lists one skill per MCP tool the bridge proxies.
3. When the A2A agent sends a Task, the bridge translates the
   request's first message into an MCP `tools/call` request,
   forwards it to the MCP server, and returns the result as the
   A2A task's completed output.
4. State collapses: every A2A Task maps to a single MCP call. If the
   A2A agent expects multi-turn follow-ups, it gets `completed` on
   turn one and has to open a new Task.

Lossy but tractable. Most Nova MCP skills are single-shot anyway.

### Direction B: MCP server → A2A agent

Nova wants to call an ADK agent. This is harder because MCP doesn't
have a native "invoke another agent" primitive — MCP tools *return
data*, not conversations.

The workable shape:

1. Bridge presents itself as an MCP server with one tool per A2A
   service it proxies (e.g., `invoke_podcast_synthesizer`).
2. Each tool's schema matches the A2A agent's expected input
   (transcript, profile).
3. When the tool is called, the bridge opens an A2A Task, drives
   the conversation to completion (handling `input-required` gates
   by either auto-filling from the MCP arguments or returning an
   error), and returns the final A2A agent output as the MCP tool
   result.
4. Multi-turn A2A conversations don't survive the bridge — the MCP
   caller sees one round-trip.

This is the direction Nova actually needs. Nova calls tools; Nova
does not sustain multi-turn sessions with remote agents.

## Implementation sketch (Direction A — the one to build first)

```
nova_adk_agent/bridges/a2a_mcp.py  (stub)

from a2a.server import A2AServer
from mcp import ClientSession, StdioServerParameters

async def serve(
    mcp_server_command: list[str],
    a2a_port: int,
    tool_whitelist: list[str] | None = None,
) -> None:
    # 1. Open an MCP client session against the backing server.
    # 2. Enumerate tools via `tools/list`.
    # 3. Build an A2A AgentCard that mirrors the tool list as skills.
    # 4. Start an A2A server. For each incoming Task:
    #    - extract the tool name from the first message's metadata
    #    - extract the JSON args from the first message's parts
    #    - call mcp_session.call_tool(name, args)
    #    - return the result as the A2A task's agent message
    #    - mark the Task completed.
```

## Open questions before shipping a real bridge

1. **Auth.** A2A supports OAuth via the agent card's `authentication`
   block. MCP auth is server-specific. The bridge needs a clear story
   for "A2A caller has token X, MCP server expects token Y" — the
   default shouldn't be "no auth."
2. **Streaming.** A2A supports SSE for streaming. MCP supports
   streaming responses via `tools/call` progress notifications. Do we
   pass through or collapse? First cut: collapse, stream only the
   final result.
3. **Error semantics.** A2A has `failed` task state; MCP has JSON-RPC
   error codes. The bridge has to map between them without losing
   the error message.
4. **Long-running tasks.** If the MCP tool takes 30 seconds, does the
   A2A Task stay `working` the whole time? For the first cut: yes,
   block. Streaming progress is a later feature.

## Why not just skip the bridge?

Because it's the move that unlocks cross-framework agent composition.
If the only way to make two agent frameworks cooperate is to pick
one and port everything, you lose the value of each framework's
ecosystem. The bridge is the plug-in layer.

Practical value for this repo: I could wire the ADK podcast
synthesizer to call Nova's `memory.search` skill to fetch past
user preferences. That'd upgrade the "user profile" from a local
JSON file to a real memory layer — exactly the weakness I called
out in the week-4 write-up.
