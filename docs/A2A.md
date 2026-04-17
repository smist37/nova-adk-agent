# A2A multi-agent demo

This repo ships an A2A demo: a two-process setup where the formatter runs
as its own A2A service, and the coordinator/summarizer live in a separate
process that calls it over the A2A wire protocol.

## Why this matters

In-process `sub_agents` (what the week 1 chain uses) is fine for a demo.
In production, agents frequently live in different services, maintained by
different teams, potentially running on different hardware. A2A is how ADK
lets you bridge that gap without each side having to know about the other's
internals.

## Layout

```
┌──────────────────────────┐        ┌───────────────────────────┐
│  Process A (port 8765)   │        │  Process B (interactive)  │
│                          │        │                           │
│  a2a_formatter           │        │  client_coordinator       │
│  - served as A2A service │<───┐   │  └─ client_summarizer     │
│  - agent card at         │    │   │     └─ remote_formatter   │
│    /.well-known/         │    └───│        (RemoteA2aAgent)   │
│    agent-card.json       │   A2A  │                           │
└──────────────────────────┘        └───────────────────────────┘
```

File map:
- `nova_adk_agent/a2a/server_agent.py` — the agent that gets served.
- `nova_adk_agent/a2a/client_agent.py` — coordinator + summarizer +
  `RemoteA2aAgent` pointing at the server's agent card.

## Running the demo

In one terminal:

```bash
source .venv/bin/activate
adk api_server nova_adk_agent/a2a/server_agent.py \
    --a2a --port 8765 --host 127.0.0.1
```

This boots a FastAPI app that serves the formatter over A2A. Check that
the agent card is reachable:

```bash
curl http://127.0.0.1:8765/.well-known/agent-card.json | jq .name
# -> "a2a_formatter"
```

In a second terminal:

```bash
source .venv/bin/activate
export A2A_FORMATTER_URL=http://127.0.0.1:8765
python -c "
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
from nova_adk_agent.a2a.client_agent import root_agent
import asyncio

async def main():
    runner = InMemoryRunner(agent=root_agent, app_name='a2a-demo')
    session = await runner.session_service.create_session(
        app_name='a2a-demo', user_id='local'
    )
    msg = genai_types.Content(
        role='user',
        parts=[genai_types.Part(text='https://www.youtube.com/watch?v=...')],
    )
    async for event in runner.run_async(
        user_id='local', session_id=session.id, new_message=msg
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    print('agent>', part.text)

asyncio.run(main())
"
```

The coordinator fetches the transcript, summarizes, and hands off to the
**remote** formatter over A2A. You can confirm the hop by watching the
server terminal — each handoff logs an incoming A2A request.

## Wire format

A2A defines three first-class concepts:

1. **AgentCard** — public metadata: name, skills, supported I/O modalities,
   authentication requirements, service URL. Served at
   `/.well-known/agent-card.json`. This is how one agent *discovers* another
   without a shared SDK.
2. **Task** — a unit of work the client sends to the server. Carries a
   history of messages, a state (`submitted`, `working`, `input-required`,
   `completed`, `failed`), and the current role (user/agent).
3. **Message** — a turn inside a Task. Has a role (`user` or `agent`) and a
   list of parts. Each part is one of `TextPart`, `DataPart` (JSON),
   `FilePart` (bytes or URI), or a function-call/response.

Handoff over A2A looks like this on the wire:

```
POST /rpc
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {"type": "text", "text": "key_ideas: [...]; profile: {...}"}
      ],
      "messageId": "m_01HXZK3..."
    },
    "configuration": {
      "acceptedOutputModes": ["text"],
      "blocking": true
    }
  },
  "id": "r_01HXZK3..."
}
```

Response (streamed via SSE when `blocking=false`, a single reply when
`blocking=true`):

```
{
  "jsonrpc": "2.0",
  "result": {
    "kind": "task",
    "id": "t_01HXZK3...",
    "status": {"state": "completed"},
    "history": [
      {"role": "user", "parts": [...]},
      {"role": "agent", "parts": [
        {"type": "text", "text": "**Why this matters to you** ..."}
      ]}
    ]
  },
  "id": "r_01HXZK3..."
}
```

ADK handles this marshalling for you — `RemoteA2aAgent` is effectively a
stub proxy. The `genai_part_converter` and `a2a_part_converter` hooks on
`RemoteA2aAgent.__init__` let you override the part conversion if your
wire schema differs.

## A2A vs. just HTTP

The natural question: why not just POST JSON between agents and skip the
protocol?

- **Discovery.** AgentCards are standardized. A client can read
  `/.well-known/agent-card.json` from any A2A server and know which skills
  it exposes, what I/O modalities it supports, what auth it needs. With
  raw HTTP you invent that per-service.
- **State model.** A2A's Task / Message / State model handles multi-turn
  conversations, streaming, `input-required` gates, and cancellation. If
  you roll your own, you rebuild this (often badly).
- **Interop.** A2A is an open protocol. An ADK agent can call a non-ADK
  A2A agent, and vice versa. Raw HTTP locks you into one team's contract.

The tradeoff: A2A adds protocol overhead you don't need if both agents
live in the same codebase and the same deploy unit. For those cases, use
in-process `sub_agents` (what the week 1 chain uses).

## When this demo runs in CI

Not currently. A full end-to-end A2A test requires spinning up the server
in one process, the client in another, and an LLM budget to process the
round-trip. CI only runs the wire-up tests in `tests/`. The demo is
meant to be run locally or on a dev workstation.
