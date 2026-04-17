"""Wire-up tests for the ADK agents.

These tests do not call the LLM. They verify that the agents import, are named
what we expect, and are composed in the shape the README claims. A full
behavioural check lives in eval/ (RAGAS) and requires GOOGLE_API_KEY.
"""
from pathlib import Path


def test_hello_agent_wireup():
    from nova_adk_agent.hello import root_agent

    assert root_agent.name == "hello_agent"
    assert any(t.__name__ == "calculator" for t in root_agent.tools)


def test_three_agent_chain_wireup():
    from nova_adk_agent.agents import root_agent
    from nova_adk_agent.agents.summarizer import summarizer
    from nova_adk_agent.agents.formatter import formatter

    # Coordinator is the entrypoint
    assert root_agent.name == "coordinator"

    # Coordinator can transfer to summarizer
    sub_names = {a.name for a in root_agent.sub_agents}
    assert "summarizer" in sub_names

    # Summarizer transfers to formatter (leaf)
    sub_sub_names = {a.name for a in summarizer.sub_agents}
    assert "formatter" in sub_sub_names
    assert formatter.sub_agents == [] or formatter.sub_agents is None


def test_sample_transcript_fixture_present():
    fixture = Path(__file__).parent / "fixtures" / "sample_transcript.txt"
    assert fixture.exists(), f"Missing fixture: {fixture}"
    text = fixture.read_text()
    assert len(text) > 500, "Fixture transcript should be reasonably sized"
    # Basic signal the fixture is about ML/startup engineering — used by eval
    assert "eval" in text.lower()
    assert "cost" in text.lower()


def test_fetch_transcript_rejects_non_youtube():
    from nova_adk_agent.transcript import fetch_transcript

    result = fetch_transcript("https://example.com/not-youtube")
    assert "error" in result
