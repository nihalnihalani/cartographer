# Cartographer — 5-Hour Build Plan

> Deadline: **June 11, 2026, 2:00 PM PT** (June 12, ~2:30 AM IST). All code newly written during the contest period (hackathon originality rule).

## Clock

| Time | Workstream | Owner | Exit criterion |
|---|---|---|---|
| 0:00–0:20 | **Accounts:** MongoDB Atlas M0 cluster + connection string; Google AI Studio API key; `gcloud auth login` + billing check. Repo scaffolding in parallel. | Human / Claude | `.env` populated; `npx mongodb-mcp-server` connects |
| 0:20–0:50 | **Seed script** (`seed/seed_messy_db.py`): orders/customers/products with planted drift; prints ground-truth vs naive numbers | Claude | Deterministic numbers verified twice |
| 0:50–2:20 | **Core agents:** Surveyors (ParallelAgent) → Historian → Mapmaker; Navigator with hazard citations; MCPToolset wiring + per-agent `tool_filter`; iterate in `adk web` | Claude | "Map this database" produces `_schema_atlas`; revenue question returns correct number with citations |
| 2:20–2:50 | **Surgeon + HITL** approval; **naive baseline agent** for the side-by-side | Claude | Repair flow works end-to-end; naive agent reproducibly wrong |
| 2:50–3:20 | **Deploy:** `adk deploy cloud_run --with_ui` → hosted URL; smoke test the deployed UI | Claude (human approves billing prompts) | Public URL loads and answers |
| 3:20–3:50 | **Repo polish:** push to GitHub, verify MIT license shows in About, README quickstart accurate, `.env.example` | Claude | Fresh-clone instructions actually work |
| 3:50–4:35 | **Record video** per [DEMO_SCRIPT.md](DEMO_SCRIPT.md); upload to YouTube | Human | Public ≤3:00 video link |
| 4:35–5:00 | **Devpost submission** per [SUBMISSION.md](SUBMISSION.md) + buffer | Both | Submitted ✅ |

## Hard submission requirements (verify all before submit)

- [ ] Hosted project URL (Cloud Run)
- [ ] Public repo, **OSI license visible in the About section** (MIT at repo root → GitHub auto-detects)
- [ ] README with setup/run instructions
- [ ] ≤3-minute public demo video (YouTube/Vimeo)
- [ ] Text description: features, technologies, data sources, learnings
- [ ] Track selected: **MongoDB**

## Risks & fallbacks

| Risk | Likelihood | Fallback |
|---|---|---|
| Atlas signup/cluster hiccup | Low | Local `mongod` via Docker; MCP server takes `mongodb://localhost:27017`. Demo unaffected; mention Atlas in roadmap. Vector index degrades to direct `find` of atlas entries — acceptable. |
| Cloud Run billing/permissions blocked | Medium | `adk api_server` on any reachable host; or Cloud Shell-hosted demo URL. Judges primarily verify repo + video. |
| ADK HITL tool-confirmation fiddly under time pressure | Medium | Two-turn explicit confirmation: Surgeon returns proposal, executes only when user replies "approve" (state-checked). Same UX on camera. |
| Parallel surveyor token burn / rate limits | Low | Cap survey at 4 collections; reduce sample size to 100/stratum. |
| `gemini-3.5-flash` quota issues | Low | Fall back to `gemini-3.1-flash-lite`; model name is a single env var. |
| Vector embeddings unavailable on M0 | Medium | Atlas summaries are also exact-match retrievable by collection name — vector search is a bonus, not a dependency. |

## Scope discipline (YAGNI list — explicitly NOT building)

- No custom frontend (ADK web UI is the front end)
- No auth/multi-tenancy
- No support for non-MongoDB databases
- No automatic (unapproved) migrations — ever; HITL is a feature, not a gap
- No streaming dashboards; surveyor progress = agent messages in the UI

## Definition of done

A judge can: open the hosted URL → ask the revenue question to the naive agent (wrong) → tell Cartographer to map the DB → ask again (right, with citations) → trigger and approve a repair — all without reading the docs.
