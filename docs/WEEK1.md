# Week 1 plan — Google ADK agent

**Goal:** ship a working ADK agent (hello-world → single-agent MVP →
multi-agent orchestration) and a LinkedIn post by Wed 2026-04-22.

## Checkpoints

| Day       | Target                                                            |
|-----------|-------------------------------------------------------------------|
| Thu 4/16  | Repo live. Hello-world ADK agent running locally. Commit #1.      |
| Fri 4/17  | Port a real capability. Single-agent podcast/transcript summarizer. |
| Sat 4/18  | Rest or extend tools (buffer day).                                |
| Sun 4/19  | Add Coordinator + Formatter agent. Three-agent chain works.       |
| Mon 4/20  | Polish README, add Mermaid architecture diagram, push.            |
| Tue 4/21  | Draft LinkedIn post. One specific technical insight.              |
| Wed 4/22  | Post goes live.                                                   |

## Rules

1. Every day ends with a commit pushed to `main`. Empty commits are
   failures — output must be real.
2. Tutorial code lives in `nova_adk_agent/hello.py` **only**. Every
   commit after that must contain original code.
3. The LinkedIn post must link to a repo that runs if a reader clones
   it. If `pip install -r requirements.txt && python -m nova_adk_agent.hello`
   doesn't work, the post doesn't ship.

## Technical insight candidates for the LinkedIn post

Pick one — specificity beats generality.

- **ADK session state vs. homegrown memory.** Nova maintains its own
  memory layer. ADK's `SessionService` is close but not identical. Tradeoffs?
- **A2A protocol vs. MCP.** Both are agent interop stories. ADK uses
  A2A; Nova's skills run as MCP servers. How do they differ in
  practice?
- **Tool definition surface area.** Nova's tools are bash scripts;
  ADK's are typed Python functions with schema inference. What's the
  migration cost for a tool-heavy agent?
- **Multi-agent orchestration patterns.** Sequential vs. delegating vs.
  workflow. Which one does ADK want you to reach for, and when is each right?

## Anti-goals

- Don't build on top of Vertex AI yet. Gemini API + local keys this week.
  GCP deployment is Week 3.
- Don't ship a second framework. This repo is about ADK. LangGraph /
  CrewAI / Autogen comparisons are a separate post, later.
- Don't let the README grow faster than the code.
