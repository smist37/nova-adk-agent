# eval — RAGAS-based quality harness

Runs the podcast synthesizer against a fixed set of transcript + profile
pairs and scores the output with RAGAS (`faithfulness` + `answer_relevancy`).

## Why RAGAS (and when to switch)

- **Current pick: RAGAS.** Most-cited eval framework in recent RAG / agent
  papers. Its grounded-faithfulness metric maps cleanly onto the
  "did the summary fabricate content?" check that matters most for a
  podcast synthesizer. The public mindshare is real — recruiters and
  hiring managers recognize it.
- **Switch to DeepEval when:** the eval targets *agent behaviour* more than
  *output fidelity*. DeepEval's pytest-style assertions and custom
  LLM-as-judge metrics are better for questions like "did the
  coordinator delegate to the right sub-agent?" or "did the agent
  refuse when asked to hallucinate?". RAGAS struggles with those.
- This is a reversible decision. The test cases in `eval/dataset.py`
  are framework-agnostic — the harness in `eval/run.py` is what
  would be swapped.

## How to run

```bash
pip install -r requirements.txt
# Requires GOOGLE_API_KEY set in .env — the RAGAS judge uses Gemini too.
python -m eval.run

# Fewer cases, fewer tokens, for quick smoke:
python -m eval.run --quick
```

Output lands in `eval/results/YYYY-MM-DD-HHMMSS.json` with per-case
faithfulness + answer_relevancy scores and an overall average.

## Test set

Five cases in `eval/dataset.py`, all using the fixture transcript
(`tests/fixtures/sample_transcript.txt`) with different profiles +
expected-claims:

1. **ML engineer at Series A** — expects cost/eval coverage.
2. **Staff engineer at a FAANG** — expects infra-scope coverage.
3. **Product manager, non-technical** — tests vocab translation.
4. **Founder-CTO, cost-sensitive** — expects routing coverage.
5. **Gen-AI DevSecOps in cleared work** — tests whether the agent
   forces a connection that isn't there (should gracefully say "the
   episode doesn't connect to your context" when it doesn't).

## Metrics

- **faithfulness** — does every factual claim in the synthesis trace back
  to the transcript? This catches hallucinations, which are the single
  biggest risk for a summarizer.
- **answer_relevancy** — does the synthesis actually answer "what should
  I take away from this for *my* context?" Catches generic summaries
  that ignore the profile.

Both are 0-1. `faithfulness >= 0.85` and `answer_relevancy >= 0.80` are
the current soft targets. Hard regressions (either metric drops below
0.70) fail the run.
