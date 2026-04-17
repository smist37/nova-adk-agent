"""A2A <-> MCP bridge — stub.

Design: ``docs/A2A-MCP-BRIDGE.md``.

The goal is to let an A2A client (e.g., an ADK agent) call an MCP server
(e.g., one of Nova's skill servers) without either side knowing the other's
protocol. This file intentionally does NOT ship a working bridge — it
documents the interface and raises ``NotImplementedError`` in the hot paths
so downstream code fails loudly if someone imports it expecting a
production-ready bridge.

Ship order when this becomes real:
1. Direction A (A2A client -> MCP server): tractable, single-shot, lossy
   state. Most Nova MCP skills are single-call anyway.
2. Direction B (MCP caller -> A2A service): also useful but has a harder
   state story (MCP is stateless, A2A is stateful).

This stub wires the shape so the tests in ``tests/`` can assert import
safety and interface stability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BridgeConfig:
    """Configuration for an A2A ↔ MCP bridge instance."""

    # Command to spawn the backing MCP server (stdio transport).
    # Example: ["uvx", "nova-memory-search-mcp"]
    mcp_server_command: list[str]

    # Port the bridge's A2A server listens on.
    a2a_port: int = 8766

    # Optional list of MCP tool names to expose. None = expose all.
    tool_whitelist: list[str] | None = None

    # Agent card metadata for the A2A side.
    agent_name: str = "a2a_mcp_bridge"
    agent_description: str = (
        "Bridge that exposes an MCP server as an A2A-addressable agent."
    )


class A2AMCPBridge:
    """Stub bridge. Raises NotImplementedError on use.

    The public interface is stable — downstream code can import this class
    and pass a BridgeConfig without risk. Actual I/O is stubbed out until
    the bridge is promoted from design to implementation.
    """

    def __init__(self, config: BridgeConfig) -> None:
        self.config = config
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Bring the bridge up: spawn the MCP server, open the A2A port."""
        raise NotImplementedError(
            "A2AMCPBridge.start is a design stub. See docs/A2A-MCP-BRIDGE.md "
            "for the implementation plan."
        )

    async def stop(self) -> None:
        raise NotImplementedError(
            "A2AMCPBridge.stop is a design stub. See docs/A2A-MCP-BRIDGE.md."
        )

    def agent_card(self) -> dict[str, Any]:
        """Return the agent card this bridge *would* expose.

        Safe to call without starting the bridge — this is just metadata
        derived from the config. Useful for unit tests.
        """
        return {
            "name": self.config.agent_name,
            "description": self.config.agent_description,
            "url": f"http://127.0.0.1:{self.config.a2a_port}",
            "version": "0.0.1",
            "skills": [
                {
                    "id": t,
                    "name": t,
                    "description": f"Proxied MCP tool: {t}",
                }
                for t in (self.config.tool_whitelist or ["<all-mcp-tools>"])
            ],
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
            },
        }
