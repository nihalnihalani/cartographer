#!/usr/bin/env bash
# Deploy Cartographer (ADK web UI + both agents) to Cloud Run.
#
# Prereqs:
#   1. `gcloud auth login` + a project with billing + Cloud Run/Cloud Build APIs
#   2. `.env` at repo root containing:
#        GOOGLE_API_KEY=...                      (Google AI Studio)
#        MDB_MCP_CONNECTION_STRING=mongodb+srv://... (Atlas — Cloud Run cannot
#                                                 reach a local Docker mongo)
#   3. Seed Atlas first:  python seed/seed_messy_db.py
#
# Note: we use a custom Dockerfile instead of `adk deploy cloud_run` because
# (a) the stock image lacks Node.js, which the MongoDB MCP server needs, and
# (b) we ship two agents (cartographer + naive_agent) in one UI.
# Production hardening: move secrets to Secret Manager (--set-secrets).
set -euo pipefail
cd "$(dirname "$0")/.."

set -a; source .env; set +a
: "${GOOGLE_API_KEY:?set GOOGLE_API_KEY in .env}"
: "${MDB_MCP_CONNECTION_STRING:?set MDB_MCP_CONNECTION_STRING (Atlas) in .env}"

PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

gcloud run deploy cartographer \
  --source . \
  --project "$PROJECT" \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY},GOOGLE_GENAI_USE_VERTEXAI=FALSE,MDB_MCP_CONNECTION_STRING=${MDB_MCP_CONNECTION_STRING}"

echo "Deployed. Smoke test:"
echo "  curl \$(gcloud run services describe cartographer --region $REGION --project $PROJECT --format='value(status.url)')/list-apps"
