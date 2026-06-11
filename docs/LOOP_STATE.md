# LOOP_STATE — iteration ledger

## BLOCKED-ON-HUMAN (everything else is done or in flight)
1. **GOOGLE_API_KEY** — create `.env` from `.env.example` with a Google AI Studio key.
   Needed for: live demo flow in `adk web agents` and the deployed service. All keyless
   work (seed, tests, agent construction, UI boot) is verified green without it.
2. **Atlas connection string** — Cloud Run cannot reach the local Docker mongo.
   Set `MDB_MCP_CONNECTION_STRING=mongodb+srv://...` in `.env`, re-run
   `python seed/seed_messy_db.py`, then deploy with ONE command:
   ```
   ./deploy/deploy_cloud_run.sh
   ```
   (gcloud IS authed locally with a billing-enabled default project — check
   `gcloud config get-value project` — so only `.env` blocks the deploy.
   Script builds a custom Python+Node image because
   the stock ADK image can't run the Node-based MongoDB MCP server, and `adk deploy
   cloud_run` ships only one agent folder while the demo needs both agents.)
3. **Record demo video + Devpost submit** — per docs/DEMO_SCRIPT.md (numbers now real).

## Milestones
- [x] 1. Seed deterministic + ground truth — iter 1
- [x] 2. Agent tree + MCP wiring (verifier #1 ran post-commit) — iter 1
- [x] 3. pytest green keyless: 20 passed — iter 1
- [x] 4. adk web boots; `/list-apps` = ["cartographer","naive_agent"]; live LLM flow blocked on key
- [x] 5. Deploy: blocked on .env (exact command above); script + Dockerfile prepared, syntax-checked
- [x] 6. README quickstart rewritten to real commands; fresh-clone dry run = verifier #2
- [x] 7. SUBMISSION.md + DEMO_SCRIPT.md synced to real numbers; URLs await deploy/video

## Ground truth (canonical, printed by seed, proven by tests)
- orders 12,483 / customers 5,000 / products 1,000 in `carto_demo`
- naive total revenue **$1,096,236.79** vs true **$1,542,667.68** (3,625 string prices = 29.0%)
- 2024-only: naive $496,153.63 vs true $557,280.03
- Demo question: **"What was total revenue?"**

## Iteration 1 proof log
- Seed determinism: ran twice, `diff` clean → "DETERMINISTIC: identical output", exit=0
- Agent construction (keyless): tree cartographer→[expedition[surveyors(3)→historian→mapmaker],
  navigator, surgeon] + naive_agent; per-agent tool_filters asserted; `--readOnly` on all
  MCP instances except mapmaker (create/insert/index only) + surgeon (gated)
- pytest: `20 passed in 1.25s` with GOOGLE_API_KEY unset; pipeline tests ran live against
  seeded Mongo (naive pipeline == naive GT, defensive pipeline == true GT to the cent)
- adk web: `curl /list-apps` → `["cartographer","naive_agent"]`, `/dev-ui/` → 200
- Design deviations from docs (intentional): drift demo question is all-time revenue (not
  2025 — per ARCHITECTURE the strings predate 2024-03, so 2025 has none); Mapmaker holds
  a write MCP instance filtered to atlas-authoring tools (spec gives it write tools but
  also says "writes only for Surgeon" — least-privilege resolution).

## Iteration 2 — verifier results + fixes (final)
Two independent repo-only verifier agents ran (after milestones 2 and 4/6 per plan):

**Verifier #1 (break milestones 1-2, live Mongo + live MCP):** PASS on seed determinism,
drift planted exactly as spec'd (3,625 string prices all pre-2024-03; alias XOR exact;
600 missing emails = 12.00%), printed ground truth matches DB-computed values to the
cent, MCP server starts and serves a live `count` (12,483) over stdio, no secrets in
tree or full git history. FINDINGS → fixed in 02cf6d8: stale 2025/$148K/$211K numbers
in SETUP.md + ARCHITECTURE §6 (a 2025-scoped question touches zero drifted docs —
demo question is all-time revenue); ARCHITECTURE §5 now documents Mapmaker's filtered
write instance + Surgeon's `find`; noted tool_filter is client-side, `--readOnly` is
the server-side line.

**Verifier #2 (fresh GitHub clone @8e09faa, README-only judge run):** README Quickstart
fully reproducible — `pip install -r requirements.txt` clean on stock Python 3.14,
seed printed the exact README numbers, `pytest` 20 passed keyless, `adk web agents`
served `["cartographer","naive_agent"]`, Dockerfile/deploy script coherent, git
history secret-scan clean. FINDINGS → most were pre-02cf6d8 staleness (already fixed);
remainder fixed in final commit: SETUP.md §2 now installs from requirements.txt,
README docker command made idempotent (`docker start || docker run`), personal
account/project ids redacted from this ledger.

## HANDOFF — the only remaining work is human-only
1. Put real `GOOGLE_API_KEY` (AI Studio) + Atlas `MDB_MCP_CONNECTION_STRING` in `.env`.
2. `python seed/seed_messy_db.py` (against Atlas), then `adk web agents` — run the
   4-prompt demo flow from docs/DEMO_SCRIPT.md and smoke-test model name
   `gemini-3.5-flash` (env override: `CARTO_MODEL`, fallback `gemini-3.1-flash-lite`).
3. `./deploy/deploy_cloud_run.sh` → paste the service URL into docs/SUBMISSION.md.
4. Record the video per docs/DEMO_SCRIPT.md (numbers are now the real deterministic
   ones), upload, paste URL into docs/SUBMISSION.md, submit on Devpost.

## Known cosmetic issues
- ADK 2.2.0 deprecation warnings: ParallelAgent/SequentialAgent → "Workflow". Harmless;
  spec names these constructs.
