"""Sanity tests for the eval harness that don't require GOOGLE_API_KEY.

The RAGAS path is exercised by ``python -m eval.run`` as an end-to-end smoke
test — it's not a unit test because it costs money.
"""
from eval.dataset import get_cases, load_transcript


def test_dataset_has_five_cases():
    cases = get_cases()
    assert len(cases) == 5
    ids = {c["id"] for c in cases}
    assert len(ids) == 5, "All case IDs must be unique"


def test_quick_subset_is_smaller():
    assert len(get_cases(quick=True)) < len(get_cases())


def test_transcript_fixture_loads():
    text = load_transcript()
    assert len(text) > 500
    assert "eval" in text.lower()


def test_run_dry_run_returns_zero():
    from eval.run import run

    rc = run(quick=True, dry_run=True)
    assert rc == 0
