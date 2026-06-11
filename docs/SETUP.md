# Cartographer — Setup & Deployment Guide

## Prerequisites

| Requirement | Why | Get it |
|---|---|---|
| Python 3.11+ | ADK runtime | python.org / pyenv |
| Node.js 20+ | runs the MongoDB MCP server via `npx` | nodejs.org |
| MongoDB Atlas account (free M0) **or** local MongoDB | the database | https://www.mongodb.com/cloud/atlas/register |
| Google AI Studio API key (or a GCP project with Vertex AI) | Gemini 3.5 Flash | https://aistudio.google.com/apikey |
| `gcloud` CLI (deploy only) | Cloud Run deployment | https://cloud.google.com/sdk |

## 1. Database

**Option A — Atlas (recommended, ~3 minutes):**
1. Create a free **M0** cluster (provisions in ~15 seconds).
2. Database Access → create a database user (password auth).
3. Network Access → allow your IP (or `0.0.0.0/0` for the hackathon demo).
4. Copy the connection string: `mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/`

**Option B — Local (zero accounts):**
```bash
docker run -d --name carto-mongo -p 27017:27017 mongo:7
# connection string: mongodb://localhost:27017
```
Note: vector search on atlas summaries degrades gracefully to exact lookup when not on Atlas.

## 2. Environment

```bash
git clone https://github.com/nihalnihalani/cartographer
cd cartographer
python -m venv .venv && source .venv/bin/activate
pip install google-adk

cp .env.example .env
```

`.env`:
```bash
# Gemini — AI Studio path (simplest)
GOOGLE_API_KEY=your-aistudio-key
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# — or Vertex AI path —
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your-project
# GOOGLE_CLOUD_LOCATION=us-central1

# MongoDB
MDB_MCP_CONNECTION_STRING=mongodb+srv://USER:PASS@cluster0.xxxxx.mongodb.net/
```

Smoke-test the MCP server independently:
```bash
MDB_MCP_CONNECTION_STRING="$MDB_MCP_CONNECTION_STRING" npx -y mongodb-mcp-server --readOnly
# should start and list tools; Ctrl-C to exit
```

## 3. Seed the demo database

```bash
python seed/seed_messy_db.py
```

This creates the `carto_demo` database (orders / customers / products) with **planted, dated schema drift** and prints the ground-truth numbers:

```
Demo question: 'What was total revenue?'
  naive agent (ignores string prices): $1,096,236.79
  correct (defensive pipeline):        $1,542,667.68
  string-typed prices overall:         3625 (29.0%, all before the 2024-03 drift boundary)
```

Run it twice — the output is byte-identical (seeded RNG, deterministic ObjectIds).

## 4. Run locally

```bash
adk web agents
```

Open http://localhost:8000, pick an agent:
- `naive_agent` — the drift-blind baseline (for the side-by-side)
- `cartographer` — the full system

Canonical flow: ask `naive_agent` the revenue question → switch to `cartographer` → `Map this database.` → ask the revenue question again → `Fix the price drift permanently.` → approve.

## 5. Deploy to Cloud Run (hosted URL)

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

./deploy/deploy_cloud_run.sh   # reads GOOGLE_API_KEY + MDB_MCP_CONNECTION_STRING from .env
```

- The script uses the repo's custom Dockerfile (Python + Node.js) rather than
  `adk deploy cloud_run`: the stock ADK image has no Node runtime for the MongoDB
  MCP server, and `adk deploy` ships a single agent folder while the demo needs
  both `cartographer` and `naive_agent` in one UI.
- `MDB_MCP_CONNECTION_STRING` must be an Atlas URI (Cloud Run can't reach a local Docker mongo), and Atlas Network Access must allow `0.0.0.0/0` for Cloud Run egress (hackathon demo posture).

## Troubleshooting

| Symptom | Fix |
|---|---|
| MCP server exits immediately | Check `MDB_MCP_CONNECTION_STRING` quoting; test with `mongosh "$CONN_STRING"` |
| `npx` not found in deployed container | Deploy with the repo's `Dockerfile` (via `deploy/deploy_cloud_run.sh`) — it installs Node 22 and pre-bakes `mongodb-mcp-server` |
| Gemini 404 / model not found | Use `gemini-3.5-flash`; fall back `gemini-3.1-flash-lite`. Never `gemini-3-pro-preview` (discontinued 2026-03). |
| Empty survey results | Re-run the seed script; confirm you're pointing at `carto_demo` |
| HITL approval never triggers | The Surgeon uses a two-turn confirm enforced by its instruction (`agents/cartographer/prompts.py`, `SURGEON`): it proposes first and only executes when your next message is an explicit "approve" |
