"""Cartographer agent tree (docs/ARCHITECTURE.md §2-3).

Cartographer (root LlmAgent)
├── expedition (SequentialAgent): surveyors (ParallelAgent) -> historian -> mapmaker
├── navigator  (LlmAgent, defensive pipelines from the Schema Atlas)
└── surgeon    (LlmAgent, repairs behind a two-turn human approval gate)
"""

from __future__ import annotations

import logging
import os

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from . import prompts
from .mcp import mongo_toolset

logging.basicConfig(level=logging.INFO)

MODEL = os.environ.get("CARTO_MODEL", "gemini-3.5-flash")
DB = os.environ.get("CARTO_DB", prompts.DB)

SURVEY_COLLECTIONS = ["orders", "customers", "products"]

surveyors = ParallelAgent(
    name="surveyors",
    description="Parallel per-collection schema surveyors (stratified sampling).",
    sub_agents=[
        LlmAgent(
            name=f"surveyor_{coll}",
            model=MODEL,
            description=f"Surveys the real shape of the `{coll}` collection.",
            instruction=prompts.SURVEYOR.format(coll=coll, db=DB),
            tools=[mongo_toolset(["collection-schema", "aggregate", "count"])],
            output_key=f"survey_{coll}",
        )
        for coll in SURVEY_COLLECTIONS
    ],
)

historian = LlmAgent(
    name="historian",
    model=MODEL,
    description="Dates each drift via _id timestamp bucketing; finds alias pairs.",
    instruction=prompts.HISTORIAN.format(db=DB),
    tools=[mongo_toolset(["aggregate", "find"])],
    output_key="hazards",
)

mapmaker = LlmAgent(
    name="mapmaker",
    model=MODEL,
    description="Writes the versioned Schema Atlas back into the database.",
    instruction=prompts.MAPMAKER.format(db=DB, atlas=prompts.ATLAS),
    # Write-enabled but filtered to atlas-authoring tools only: it can create
    # and insert, never read, update, or delete (least privilege).
    tools=[
        mongo_toolset(
            ["create-collection", "insert-many", "create-index"], read_only=False
        )
    ],
)

expedition = SequentialAgent(
    name="expedition",
    description="Maps the database: parallel surveyors -> historian -> mapmaker.",
    sub_agents=[surveyors, historian, mapmaker],
)

navigator = LlmAgent(
    name="navigator",
    model=MODEL,
    description="Answers data questions with atlas-informed defensive pipelines.",
    instruction=prompts.NAVIGATOR.format(db=DB, atlas=prompts.ATLAS),
    tools=[mongo_toolset(["find", "aggregate", "explain"])],
)

surgeon = LlmAgent(
    name="surgeon",
    model=MODEL,
    description="Proposes hazard repairs; executes only after explicit approval.",
    instruction=prompts.SURGEON.format(db=DB, atlas=prompts.ATLAS),
    tools=[mongo_toolset(["update-many", "create-index", "find"], read_only=False)],
)

root_agent = LlmAgent(
    name="cartographer",
    model=MODEL,
    description="Schema archaeology for AI agents: map, navigate, repair.",
    instruction=prompts.CARTOGRAPHER.format(db=DB),
    tools=[mongo_toolset(["list-databases"])],
    sub_agents=[expedition, navigator, surgeon],
)
