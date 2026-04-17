"""RAGAS eval runner for the podcast synthesizer.

Generates a synthesis for each case in ``eval/dataset.py``, scores it with
RAGAS (faithfulness + answer_relevancy), and writes the results to
``eval/results/YYYY-MM-DD-HHMMSS.json``. Designed to be run locally or in
CI — CI only runs ``--quick`` to keep the bill small.

Usage:
    python -m eval.run           # full set
    python -m eval.run --quick   # 2 cases, smoke test
    python -m eval.run --dry-run # build everything, don't call LLM / RAGAS

Exit codes:
    0  all soft targets met
    1  soft target missed but no hard regression
    2  hard regression (faithfulness < 0.70 or answer_relevancy < 0.70)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from eval.dataset import get_cases, load_transcript

load_dotenv()


SOFT_FAITHFULNESS = 0.85
SOFT_RELEVANCY = 0.80
HARD_FLOOR = 0.70


@dataclass
class CaseResult:
    id: str
    question: str
    answer: str
    faithfulness: float | None
    answer_relevancy: float | None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _synthesize(transcript: str, profile: dict) -> str:
    """Call the real agent. Imported here so ``--dry-run`` doesn't need it."""
    from nova_adk_agent.summarize_text import summarize_transcript

    return summarize_transcript(transcript=transcript, profile=profile)


def _score_with_ragas(cases: list[dict], answers: list[str], transcript: str) -> list[dict]:
    """Score cases with RAGAS. Returns list[{faithfulness, answer_relevancy}].

    RAGAS's ``faithfulness`` expects (question, answer, contexts), and
    ``answer_relevancy`` expects (question, answer, contexts). The transcript
    is the context for every case (single-document setup).
    """
    from datasets import Dataset
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from ragas import evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.metrics import faithfulness, answer_relevancy

    judge = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
    )
    embeddings = LangchainEmbeddingsWrapper(
        GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    )

    data = {
        "question": [c["question"] for c in cases],
        "answer": answers,
        "contexts": [[transcript] for _ in cases],
    }
    ds = Dataset.from_dict(data)
    result = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy],
        llm=judge,
        embeddings=embeddings,
    )
    # RAGAS returns a Result with per-row scores via .scores (list of dicts).
    rows = getattr(result, "scores", None) or result.to_pandas().to_dict("records")
    out = []
    for row in rows:
        out.append(
            {
                "faithfulness": float(row.get("faithfulness", 0.0) or 0.0),
                "answer_relevancy": float(row.get("answer_relevancy", 0.0) or 0.0),
            }
        )
    return out


def run(quick: bool = False, dry_run: bool = False) -> int:
    cases = get_cases(quick=quick)
    transcript = load_transcript()

    print(f"[eval] cases={len(cases)} dry_run={dry_run}")

    if dry_run:
        # Just make sure everything wires up.
        for c in cases:
            print(f"[eval][dry] would synthesize: {c['id']}")
        return 0

    if not os.environ.get("GOOGLE_API_KEY"):
        print("[eval] ERROR: GOOGLE_API_KEY not set. Skipping LLM calls.")
        return 2

    # --- Step 1: run the agent to generate answers.
    answers: list[str] = []
    results: list[CaseResult] = []
    for c in cases:
        t0 = time.time()
        try:
            answer = _synthesize(transcript, c["profile"])
        except Exception as exc:
            print(f"[eval] FAIL synthesize {c['id']}: {exc}")
            results.append(
                CaseResult(
                    id=c["id"],
                    question=c["question"],
                    answer="",
                    faithfulness=None,
                    answer_relevancy=None,
                    notes=f"synthesis_error: {exc}",
                )
            )
            answers.append("")
            continue
        dt = time.time() - t0
        print(f"[eval] synth {c['id']} ({dt:.1f}s, {len(answer)} chars)")
        answers.append(answer)
        results.append(
            CaseResult(
                id=c["id"],
                question=c["question"],
                answer=answer,
                faithfulness=None,
                answer_relevancy=None,
            )
        )

    # --- Step 2: score with RAGAS.
    try:
        scores = _score_with_ragas(cases, answers, transcript)
    except Exception as exc:
        print(f"[eval] FAIL ragas: {exc}")
        # Save partial results so we can still see the answers.
        scores = [{"faithfulness": None, "answer_relevancy": None} for _ in cases]

    for result, score in zip(results, scores):
        result.faithfulness = score["faithfulness"]
        result.answer_relevancy = score["answer_relevancy"]

    # --- Step 3: write results + decide exit code.
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{timestamp}.json"

    payload = {
        "timestamp_utc": timestamp,
        "quick": quick,
        "soft_targets": {
            "faithfulness": SOFT_FAITHFULNESS,
            "answer_relevancy": SOFT_RELEVANCY,
        },
        "hard_floor": HARD_FLOOR,
        "results": [r.to_dict() for r in results],
    }

    faith_vals = [r.faithfulness for r in results if r.faithfulness is not None]
    rel_vals = [r.answer_relevancy for r in results if r.answer_relevancy is not None]
    if faith_vals:
        payload["avg_faithfulness"] = sum(faith_vals) / len(faith_vals)
    if rel_vals:
        payload["avg_answer_relevancy"] = sum(rel_vals) / len(rel_vals)

    out_file.write_text(json.dumps(payload, indent=2))
    print(f"[eval] wrote {out_file}")

    # Decide exit code.
    min_faith = min(faith_vals) if faith_vals else 0.0
    min_rel = min(rel_vals) if rel_vals else 0.0
    avg_faith = payload.get("avg_faithfulness", 0.0)
    avg_rel = payload.get("avg_answer_relevancy", 0.0)

    print(
        f"[eval] avg_faithfulness={avg_faith:.3f} avg_answer_relevancy={avg_rel:.3f} "
        f"min_faith={min_faith:.3f} min_rel={min_rel:.3f}"
    )

    if min_faith < HARD_FLOOR or min_rel < HARD_FLOOR:
        print("[eval] HARD REGRESSION")
        return 2
    if avg_faith < SOFT_FAITHFULNESS or avg_rel < SOFT_RELEVANCY:
        print("[eval] soft target missed (non-blocking)")
        return 1
    print("[eval] all targets met")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick", action="store_true", help="2 cases only (CI / smoke)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip LLM + RAGAS, just verify wiring",
    )
    args = parser.parse_args(argv)
    return run(quick=args.quick, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
