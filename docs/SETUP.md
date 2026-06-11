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
TRUE 2025 revenue:   $211,540
NAIVE 2025 revenue:  $148,200   (what a drift-blind $sum returns)
string-typed prices: 5,840 docs (drift boundary 2024-03)
```

## 4. Run locally

```bash
adk web
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

adk deploy cloud_run \
  --project=YOUR_PROJECT \
  --region=us-central1 \
  --service_name=cartographer \
  --with_ui \
  .
```

- Answer `y` to allow unauthenticated access (judges need the URL).
- Set env vars on the service (connection string + API key):
```bash
gcloud run services update cartographer --region=us-central1 \
  --set-env-vars=GOOGLE_API_KEY=...,GOOGLE_GENAI_USE_VERTEXAI=FALSE,MDB_MCP_CONNECTION_STRING=...
```
- Atlas Network Access must allow `0.0.0.0/0` for Cloud Run egress (hackathon demo posture).

## Troubleshooting

| Symptom | Fix |
|---|---|
| MCP server exits immediately | Check `MDB_MCP_CONNECTION_STRING` quoting; test with `mongosh "$CONN_STRING"` |
| `npx` not found in deployed container | Ensure Node is in the runtime image (ADK Cloud Run images include it); else switch MCP launch to the Docker variant |
| Gemini 404 / model not found | Use `gemini-3.5-flash`; fall back `gemini-3.1-flash-lite`. Never `gemini-3-pro-preview` (discontinued 2026-03). |
| Empty survey results | Re-run the seed script; confirm you're pointing at `carto_demo` |
| HITL approval never triggers | Check the Surgeon uses the write-enabled MCP instance and tool confirmation is wired; fallback two-turn confirm is in `agents/surgeon.py` |
