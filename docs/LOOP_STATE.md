# LOOP_STATE — iteration ledger

## BLOCKED-ON-HUMAN
- **GOOGLE_API_KEY missing** — no `.env`; live agent runs (adk web demo, deployed smoke test)
  need a Google AI Studio key in `.env`. Everything keyless-testable proceeds.
- **No Atlas connection string** — using local Docker Mongo (`docker run -d --name carto-mongo
  -p 27017:27017 mongo:7`, `mongodb://localhost:27017`). To swap to Atlas: set
  `MDB_MCP_CONNECTION_STRING` in `.env` and re-run the seed. Vector index on the atlas
  summaries requires Atlas; local Mongo degrades to direct `find` (per BUILD_PLAN fallback).
- **gcloud auth** — not yet verified; Cloud Run deploy may need `gcloud auth login`.

## Milestones (from /loop goal)
- [x] 1. Seed script deterministic + ground truth — DONE iter 1
- [ ] 2. 6 ADK agents + naive baseline, MCP wiring
- [ ] 3. pytest suite green (keyless)
- [ ] 4. adk web boots, full demo flow
- [ ] 5. Cloud Run deploy OR documented blocker
- [ ] 6. README quickstart verified, .env.example complete
- [ ] 7. SUBMISSION.md real numbers/URLs

## Iteration 1 (start epoch 1781195394; hard stop epoch 1781198994)
**Shipped:** env setup (Python 3.12 venv via uv, google-adk 2.2.0, pymongo, pytest; Docker
mongo:7 as `carto-mongo` on :27017), `seed/seed_messy_db.py`, pinned `requirements.txt`.

**Proof (seed run twice, diffed):**
```
exit=0
DETERMINISTIC: identical output
{
  "orders": 12483,
  "string_priced_orders": 3625,
  "revenue_all_time_true": 1542667.68,
  "revenue_all_time_naive": 1096236.79,
  "revenue_2024_true": 557280.03,
  "revenue_2024_naive": 496153.63,
  "string_priced_2024": 492
}
All-time:  naive $1,096,236.79  vs  true $1,542,667.68
  string-typed prices overall:         3625 (29.0%)
```

**Design note:** DEMO_SCRIPT.md's aspirational numbers ($148,200/$211,540, 2025) conflicted
with ARCHITECTURE.md (price string *before* 2024-03 → 2025 has no strings). ARCHITECTURE
is the anchor spec, so the seed follows it; the headline demo question is now
**"What was total revenue?" (all-time): naive $1,096,236.79 vs true $1,542,667.68 (29% missing)**.
DEMO_SCRIPT.md + SUBMISSION.md numbers to be synced in milestone 7.

**Next:** Milestone 2 — agent package per ARCHITECTURE §3/§5 (root Cartographer, Expedition
Sequential[Parallel surveyors → Historian → Mapmaker], Navigator, Surgeon + naive_agent).
