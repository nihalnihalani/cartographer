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
   (gcloud IS authed — account nihal.nihalani@gmail.com, project sage-inn-298821 —
   so only `.env` blocks the deploy. Script builds a custom Python+Node image because
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

## Known cosmetic issues
- ADK 2.2.0 deprecation warnings: ParallelAgent/SequentialAgent → "Workflow". Harmless;
  spec names these constructs.
