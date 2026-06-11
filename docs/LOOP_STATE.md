# LOOP_STATE — iteration ledger

## BLOCKED-ON-HUMAN
1. ~~GOOGLE_API_KEY~~ **RESOLVED 2026-06-12 ~01:0x** — replacement key works;
   `gemini-3.5-flash` smoke test returns OK and the FULL live demo flow is verified
   (see Iteration 3 below).
2. **Atlas connection string is still the placeholder** (`USER:PASS@cluster0.xxxxx` —
   DNS lookup fails). Cloud Run cannot reach the local Docker mongo. Set a real
   `MDB_MCP_CONNECTION_STRING=mongodb+srv://...` in `.env`, re-run
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
- [x] 4. adk web boots; `/list-apps` = ["cartographer","naive_agent"]; FULL live demo flow
       verified end-to-end 2026-06-12 (see Iteration 3 proof)
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

## Iteration 3 — LIVE demo flow verified (2026-06-12, replacement API key)
Driven through the ADK API (`POST /run`) against local Mongo, all four demo shots:
1. **The Lie** — naive_agent: "What was total revenue?" → ran plain
   `{$sum: "$price"}` → answered **$1,096,236.79** (planted wrong number, to the cent).
2. **The Excavation** — cartographer: "Map this database." → 55 tool calls;
   `_schema_atlas` written: 3 collection docs + manifest, drift dated ~2024-03;
   all 3 docs pass `validate_atlas_doc` → VALID.
3. **The Truth** — same question → navigator consulted atlas, answered
   **$1,542,667.68** with naive-vs-defensive table ("$446,430.89 / 28.9% damage
   avoided") + hazard citations and the defensive `$convert` pipeline shown.
4. **The Repair** — "Fix the price drift permanently." → proposal card
   (filter, 3,625-doc estimate, rollback note, zero writes during proposal —
   DB checked) → "approve" → $match/$set/$merge migration → DB verified:
   0 string prices remain, plain `$sum` now returns $1,542,667.68.
After verification the DB was RE-SEEDED to restore the drifted demo state
(3,625 string prices back; `_schema_atlas` dropped) so the video starts clean.

Two live-run fixes shipped (caught only by running against the real model):
- **naive_agent was too smart**: it `find`-peeked 5 docs, saw string prices, and
  added `$toDouble` on its own → returned the TRUE number, killing the demo hook.
  Fix: tool_filter reduced to `["aggregate"]` (cannot peek) + instruction gives
  documented field names only and forbids conversions. Re-tested → wrong number
  reproduced exactly.
- **Surgeon's update-many failed**: the MCP tool rejects pipeline-style updates
  (`MCP error -32602: expected object, received array`) and classic updates can't
  compute `$toDouble` from the field. Fix: surgeon executes value-transformations
  via `aggregate` `$match/$set/$merge` (write instance); update-many reserved for
  static-value fixes. Re-tested → 3,625 docs migrated, surgeon self-verified 0 left.

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
