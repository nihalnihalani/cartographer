"""Baseline: the standard 'chat with your database' agent Cartographer exists to beat.

No schema inspection, no defensive pipelines — it queries the assumed schema and
returns a confident, silently wrong number on drifted data.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import LlmAgent

from cartographer import prompts
from cartographer.mcp import mongo_toolset

root_agent = LlmAgent(
    name="naive_agent",
    model=os.environ.get("CARTO_MODEL", "gemini-3.5-flash"),
    description="Naive chat-with-your-database baseline (no schema awareness).",
    instruction=prompts.NAIVE,
    # aggregate only: no find/collection-schema, so it cannot peek at documents
    # and discover the drift it is supposed to be blind to.
    tools=[mongo_toolset(["aggregate"])],
)
