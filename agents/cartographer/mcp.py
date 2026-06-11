"""MongoDB MCP wiring (official `mongodb-mcp-server` over stdio).

Two flavors of toolset (docs/ARCHITECTURE.md §5):
  read-only  — Cartographer root, Surveyors, Historian, Navigator
  write      — Mapmaker (atlas authoring tools only) and Surgeon (repairs,
               gated behind explicit human approval in its instruction)

Every toolset carries a per-agent `tool_filter` allowlist for least privilege.
"""

from __future__ import annotations

import logging
import os

from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp import StdioServerParameters

log = logging.getLogger("cartographer.mcp")

DEFAULT_URI = "mongodb://localhost:27017"


def connection_string() -> str:
    uri = os.environ.get("MDB_MCP_CONNECTION_STRING")
    if not uri:
        log.warning(
            "MDB_MCP_CONNECTION_STRING not set; falling back to %s", DEFAULT_URI
        )
        uri = DEFAULT_URI
    return uri


def mongo_toolset(tool_filter: list[str], *, read_only: bool = True) -> McpToolset:
    """Build an MCP toolset for the official MongoDB MCP server.

    The stdio subprocess is spawned lazily by ADK at first tool use, so
    constructing agents stays cheap and works without a running database.
    """
    args = ["-y", "mongodb-mcp-server"]
    if read_only:
        args.append("--readOnly")
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=args,
                env={"MDB_MCP_CONNECTION_STRING": connection_string()},
            ),
            timeout=30,
        ),
        tool_filter=tool_filter,
    )
