# nova-adk-agent

Porting capabilities from Nova — a personal multi-agent system running on Claude
Code — to Google's [Agent Development Kit](https://github.com/google/adk-python).

## Why this repo exists

This is Week 1 of a 4-week public portfolio build targeting gen-AI backend roles
(Google ADK / multi-agent / MCP / eval pipelines). The broader plan:

- **Week 1 — this repo.** A small, multi-agent ADK system that takes a
  podcast URL, fetches a transcript, summarizes, and formats for delivery.
  Mirrors a capability Nova already runs end-to-end in production.
- **Week 2.** Port Nova's homegrown observer/eval pattern to
  [Promptfoo](https://www.promptfoo.dev/).
- **Week 3.** Deploy the Week 1 agent to GCP Cloud Run with Terraform.
- **Week 4.** Architecture writeup of the Nova system, with ADK as the
  portability case study.

Public LinkedIn post lands at the end of each week.

## Stack

- Python 3.11+
- [`google-adk`](https://pypi.org/project/google-adk/) — Agent Development Kit
- `uv` or `pip` + `venv` for dependency management

## Architecture (target — coming during Week 1)

```
┌────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│  Coordinator   │──▶│  Summarizer      │──▶│  Formatter      │
│  agent         │   │  agent           │   │  agent          │
└────────────────┘   └──────────────────┘   └─────────────────┘
        │
        ▼
   tool: fetch_transcript(url)
```

Multi-agent orchestration via ADK's A2A protocol — the JD's exact keywords
("agent + multi-agent dev", "A2A, MCP, ADK"), implemented end-to-end.

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your Gemini / Vertex AI credentials
cp .env.example .env
# edit .env

python -m nova_adk_agent.hello
```

## Status

- [x] Repo created
- [ ] Hello-world ADK agent running locally
- [ ] Podcast summarizer single-agent MVP
- [ ] Multi-agent orchestration (Coordinator → Summarizer → Formatter)
- [ ] README architecture diagram + learnings
- [ ] LinkedIn post

## License

MIT. Build on it, fork it, steal the patterns.
