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

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Coordinator                                                   │
│  tools: fetch_transcript, load_profile, save_profile          │
└──────────────────────────┬─────────────────────────────────────┘
                           │ transfer (after transcript ready)
                           ▼
                ┌──────────────────────┐
                │  Summarizer          │
                │  output_key=key_ideas│
                └──────────┬───────────┘
                           │ transfer
                           ▼
                ┌──────────────────────┐
                │  Formatter           │
                │  (terminal)          │
                └──────────────────────┘
```

Three-agent chain via ADK's transfer pattern — the JD's exact keywords
("agent + multi-agent dev", "A2A, MCP, ADK"), implemented end-to-end.

The coordinator collects the user profile (persisted locally in
`user_profile.json`) and fetches the transcript. The summarizer extracts key
ideas in the user's vocabulary. The formatter produces the final personalized
synthesis and addresses the user by name.

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your Gemini / Vertex AI credentials
cp .env.example .env
# edit .env

# Three-agent podcast synthesizer (main entry point)
python -m nova_adk_agent

# Single-agent MVP (original, preserved for reference)
python -m nova_adk_agent.summarize

# Hello-world agent
python -m nova_adk_agent.hello
```

## Status

- [x] Repo created
- [x] Hello-world ADK agent running locally
- [x] Podcast summarizer single-agent MVP
- [x] Multi-agent orchestration (Coordinator → Summarizer → Formatter)
- [ ] README architecture diagram + learnings
- [ ] LinkedIn post

## License

MIT. Build on it, fork it, steal the patterns.
