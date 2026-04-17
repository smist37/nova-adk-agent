"""The A2A ↔ MCP bridge is a stub. These tests verify the interface and
fail loudly if someone accidentally imports it expecting a working bridge.
"""
import pytest

from nova_adk_agent.bridges.a2a_mcp import A2AMCPBridge, BridgeConfig


def test_bridge_config_defaults():
    cfg = BridgeConfig(mcp_server_command=["echo", "hello"])
    assert cfg.a2a_port == 8766
    assert cfg.agent_name == "a2a_mcp_bridge"


def test_bridge_instantiation_is_safe():
    bridge = A2AMCPBridge(
        BridgeConfig(mcp_server_command=["echo", "hello"])
    )
    assert not bridge.running
    # agent_card() is pure metadata, safe to call without start()
    card = bridge.agent_card()
    assert card["name"] == "a2a_mcp_bridge"
    assert card["url"].endswith(":8766")


def test_bridge_start_raises_not_implemented():
    bridge = A2AMCPBridge(
        BridgeConfig(mcp_server_command=["echo", "hello"])
    )
    import asyncio

    with pytest.raises(NotImplementedError, match="design stub"):
        asyncio.run(bridge.start())
