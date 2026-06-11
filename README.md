# 🗺️ CARTOGRAPHER

> **Your database is lying to your AI. Cartographer maps the truth.**

A multi-agent system — built with **Gemini 3.5 Flash**, **Google Cloud Agent Builder (ADK)**, and the official **MongoDB MCP server** — that excavates the *real* schema of a messy MongoDB database, detects drift and hazards, and answers natural-language questions with queries that defend against them.

Built for the **Google Cloud Rapid Agent Hackathon** — MongoDB partner track.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Google ADK](https://img.shields.io/badge/Google-ADK%202.x-4285F4)](https://adk.dev)
[![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-8E75B2)](https://ai.google.dev)
[![MongoDB MCP](https://img.shields.io/badge/MongoDB-MCP%20Server-47A248)](https://www.mongodb.com/docs/mcp-server/)

---

## The Problem

Every "chat with your database" agent works the same way: sample one document → guess the schema → generate a query → run it. This works in demos and **fails in production**, because real MongoDB databases are schemaless in practice, not just in theory:

- **Type drift** — `price` was a string (`"49.99"`) for two years, then new docs store a number (`49.99`). `{$sum: "$price"}` **silently drops 30% of revenue**. No error. Just a confidently wrong answer.
- **Naming drift** — `user_id`, `userId`, and `uid` coexist across eras of the codebase.
- **Missing fields** — `email` exists in 88% of docs; a `$match` on it silently excludes 12% of customers.
- **Shape drift** — `address` is a string in old docs, an object `{street, city}` in new ones.

This is live community pain: see the recent Ask HN *"Why is it still so hard for LLMs to query NoSQL databases?"* The problem isn't text-to-query generation — **the agent doesn't know what's actually in the database.**

So we gave the agent an archaeologist.

## What Cartographer Does

1. **🏕️ Excavates** — a parallel crew of Surveyor agents samples every collection across time: field coverage %, every type variant, when each variant appeared.
2. **🗺️ Maps** — writes a **Schema Atlas** back into MongoDB itself: a versioned, vector-embedded, queryable map of the database's real shape, with a per-field hazard list.
3. **🧭 Navigates** — answers plain-English questions with aggregation pipelines that *defend against the hazards* (`$convert` for type drift, `$ifNull` for gaps, alias unions) — and **cites which hazards it handled**.
4. **🩺 Repairs (with permission)** — proposes normalization migrations and indexes, gated behind **human approval**. The agent plans; you authorize.

## The Money Shot

Ask a naive agent: *"What was total revenue in 2025?"* → **$148,200** — confidently wrong (it ignored 5,840 string-typed prices).

Ask Cartographer the same question → **$211,540** — *"I converted 5,840 string-typed prices and unioned the `userId` alias. The naive query missed 30% of revenue."*

That delta is the product.

## Architecture

```
                        ┌─────────────────────────────────────────┐
                        │            ROOT: Cartographer            │
                        │       (LlmAgent · gemini-3.5-flash)       │
                        └───────┬──────────────┬──────────┬───────┘
                                │              │          │
              ┌─────────────────▼───┐   ┌──────▼─────┐ ┌──▼──────────────┐
              │ EXPEDITION           │   │ NAVIGATOR  │ │ SURGEON          │
              │ (SequentialAgent)    │   │ (LlmAgent) │ │ (LlmAgent + HITL)│
              │                      │   │ answers Qs │ │ proposes fixes,  │
              │ 1. Surveyors         │   │ grounded   │ │ human approval   │
              │    (ParallelAgent —  │   │ in the     │ │ required before  │
              │    one per           │   │ Schema     │ │ update-many /    │
              │    collection)       │   │ Atlas      │ │ create-index     │
              │ 2. Historian         │   └────────────┘ └─────────────────┘
              │    (drift detector)  │
              │ 3. Mapmaker          │     All tools = official MongoDB MCP
              │    (writes Atlas)    │     server (stdio MCPToolset,
              └──────────────────────┘     per-agent tool_filter)
```

| Agent | ADK construct | MongoDB MCP tools | Job |
|---|---|---|---|
| Cartographer (root) | `LlmAgent` + `sub_agents` | `list-databases` | Routes requests to the right crew |
| Surveyors | `ParallelAgent` | `collection-schema`, `aggregate`, `count` | Stratified sampling → field coverage + type histograms |
| Historian | `LlmAgent` | `aggregate`, `find` | Dates each drift variant, detects alias pairs |
| Mapmaker | `LlmAgent` | `create-collection`, `insert-many`, `create-index` | Writes the vector-embedded `_schema_atlas` collection |
| Navigator | `LlmAgent` | `find`, `aggregate`, `explain` | Hazard-aware, defensive query generation with citations |
| Surgeon | `LlmAgent` + HITL | `update-many`, `create-index` | Migration/index proposals — executes only after approval |

**Design choices judges should notice:**
- **`tool_filter` everywhere** — each agent sees only the 3–5 MCP tools it needs. Surveyors can't write. Only the Surgeon can `update-many`, and only after human approval.
- **The map lives in the territory** — the Schema Atlas is itself a MongoDB collection with vector embeddings; the partner tech is the product's memory, not a side-call.
- **Read-only by default** — the MCP server runs with `--readOnly` for excavation and navigation; writes are a separately-gated path.
- **Receipts** — the Navigator can show `explain` output proving its pipeline touched every document variant.

## Tech Stack

- **Google Cloud Agent Builder / ADK 2.x** (`google-adk`) — multi-agent orchestration (`SequentialAgent`, `ParallelAgent`, HITL tool confirmation)
- **Gemini 3.5 Flash** — reasoning for all six agents
- **MongoDB Atlas** (M0) + **official MongoDB MCP server** (`mongodb-mcp-server`, stdio) — all database superpowers
- **Cloud Run** — hosted deployment via `adk deploy cloud_run --with_ui`

## Quickstart

```bash
# 1. Prereqs: Python 3.11+, Node 20+ (for npx), a MongoDB Atlas M0 cluster (or local mongod)
pip install google-adk

# 2. Configure
cp .env.example .env   # set GOOGLE_API_KEY + MDB_MCP_CONNECTION_STRING

# 3. Seed the deliberately-messy demo database
python seed/seed_messy_db.py

# 4. Run locally with the ADK dev UI
adk web

# 5. Deploy a hosted URL
adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=us-central1 --with_ui .
```

> Full setup details: [docs/SETUP.md](docs/SETUP.md)

## Documentation

| Doc | Contents |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system design: agents, data flow, Schema Atlas format, hazard taxonomy |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | Shot-by-shot 3-minute demo video script |
| [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) | The 5-hour build plan, risks, and fallbacks |
| [docs/SUBMISSION.md](docs/SUBMISSION.md) | Devpost submission draft + judging criteria mapping |
| [docs/SETUP.md](docs/SETUP.md) | Detailed environment setup and deployment guide |

## Why This Matters

Every team wiring an LLM to a production database ships the silent-wrong-answer bug today. Cartographer is the layer that stops it — schema archaeology as a first-class agent capability.

## License

[MIT](LICENSE)
