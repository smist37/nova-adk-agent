"""Wire-up tests for the A2A demo. No live server, no LLM."""


def test_server_agent_imports():
    from nova_adk_agent.a2a.server_agent import root_agent

    assert root_agent.name == "a2a_formatter"


def test_client_agent_wires_remote_formatter(monkeypatch):
    # Point the agent card at a harmless URL for import purposes.
    monkeypatch.setenv("A2A_FORMATTER_URL", "http://127.0.0.1:8765")
    from nova_adk_agent.a2a.client_agent import root_agent, remote_formatter

    assert root_agent.name == "client_coordinator"
    # Chain: coordinator -> summarizer -> remote_formatter
    sub_names = {a.name for a in root_agent.sub_agents}
    assert "client_summarizer" in sub_names
    summarizer = [a for a in root_agent.sub_agents if a.name == "client_summarizer"][0]
    remote_names = {a.name for a in summarizer.sub_agents}
    assert "remote_formatter" in remote_names
    assert remote_formatter.name == "remote_formatter"
