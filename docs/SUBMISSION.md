# Cartographer — Devpost Submission Draft

> Hackathon: **Google Cloud Rapid Agent Hackathon** · Track: **MongoDB**

## Project name

**CARTOGRAPHER — schema archaeology for AI agents**

## Elevator pitch (tagline field)

Your database is lying to your AI. Cartographer excavates the real schema of messy MongoDB databases — drift, aliases, gaps — and answers questions with queries that defend against them.

## Inspiration

A week before this hackathon, an Ask HN thread asked: *"Why is it still so hard for LLMs to query NoSQL databases?"* The answers all pointed at the same wound: document databases have no enforced schema, so every "chat with your data" agent generates queries against a guess. On real databases — with type drift, renamed fields, partial coverage — those queries return **silently wrong answers**. No exception. No warning. Just a confident, wrong number.

We realized the bottleneck isn't text-to-query generation. It's that the agent doesn't *know* the database. So we built it an archaeologist.

## What it does

Cartographer is a multi-agent system that:

1. **Excavates** — parallel Surveyor agents sample every collection across time (oldest, newest, random strata) and measure what fields *actually* exist: coverage %, type histograms, value shapes.
2. **Dates the drift** — a Historian agent uses ObjectId timestamps to date every schema change (*"`price` flipped string→double around 2024-03"*) and detects alias fields (`user_id` ↔ `userId`).
3. **Maps** — a Mapmaker agent writes a versioned, vector-embedded **Schema Atlas** back into MongoDB itself, with a severity-ranked hazard list per field.
4. **Navigates** — when you ask a question, the Navigator consults the atlas first, then generates a *defensive* aggregation pipeline (`$convert` guards, `$ifNull` defaults, alias unions) and answers **with hazard citations**: exactly what it defended against and how many documents were affected.
5. **Repairs, with consent** — a Surgeon agent proposes normalization migrations and indexes, but cannot execute without explicit human approval.

In our demo database, a naive agent reports total revenue as **$1,096,236.79**. Cartographer reports **$1,542,667.68** — and explains that the naive query silently dropped 3,625 string-typed prices: 29% of revenue, gone without an error. (Both numbers are deterministic: `seed/seed_messy_db.py` prints the ground truth, and the pytest suite proves the pipelines reproduce it.)

## How we built it

- **Google Cloud Agent Builder — Agent Development Kit (ADK 2.x)** orchestrates six agents: a root router (`LlmAgent` + `sub_agents`), a `SequentialAgent` expedition containing a `ParallelAgent` surveyor fan-out, plus Navigator and Surgeon agents. Human-in-the-loop approval gates all writes.
- **Gemini 3.5 Flash** powers every agent's reasoning.
- **MongoDB MCP server** (official, via `npx`, stdio transport) provides every database capability: `collection-schema`, `aggregate`, `count`, `find`, `explain`, `create-collection`, `insert-many`, `create-index`, `update-many`. We run **two MCP instances** — read-only for excavation/navigation, write-enabled for the Surgeon only — and use ADK's `tool_filter` so each agent sees just the 3–5 tools it needs (least privilege, minimal token bloat).
- **MongoDB Atlas** hosts the data; the Schema Atlas itself is a MongoDB collection with vector-embedded summaries — the partner technology is the product's memory, not a side-call.
- **Cloud Run** hosts the live deployment via `deploy/deploy_cloud_run.sh` — a custom image (Python + Node.js), because the MongoDB MCP server is a Node subprocess the stock ADK image can't run.

## Challenges we ran into

- Detecting *when* drift happened (not just that it exists) — solved by bucketing on ObjectId-encoded timestamps.
- Making six agents share one evolving picture of the database — solved by making the Schema Atlas a first-class, versioned collection instead of conversation state.
- Keeping write power safe in an agent system — solved with a separate write-enabled MCP instance, isolated to one agent, behind human approval.

## Accomplishments we're proud of

- A demo where the *wrongness of the status quo is measurable on screen* — $1.10M vs $1.54M on the same database, reproducible to the cent.
- Hazard citations: every answer shows its defensive work, turning a black-box query into an auditable one.
- Least-privilege MCP design (`tool_filter` per agent, read-only by default).

## What we learned

- ObjectIds are an underused free time-series — they let an agent reconstruct schema history with zero extra metadata.
- ADK's workflow agents (Sequential/Parallel) make the excavation pipeline almost declarative.
- The MCP `tool_filter` pattern matters: full tool surfaces bloat context and invite misuse.

## What's next

- Continuous cartography: change-stream-triggered re-surveys so the atlas never goes stale.
- Hazard-aware index advisor using `explain` + the performance advisor tools.
- Support for Atlas Search hybrid retrieval over atlas summaries at enterprise scale.

## Built with

`gemini-3.5-flash` · `google-adk` (Agent Builder) · `mongodb-mcp-server` · MongoDB Atlas · Cloud Run · Python

## Links

- **Hosted project:** `<CLOUD_RUN_URL>` ← fill at submit time
- **Repository:** https://github.com/nihalnihalani/cartographer (MIT license)
- **Demo video:** `<YOUTUBE_URL>` ← fill at submit time

---

## Judging criteria mapping (internal — for our reference)

| Criterion (equal weight) | Our answer |
|---|---|
| **Technological implementation** | 6-agent ADK system (Parallel + Sequential + HITL), dual read/write MCP instances, per-agent `tool_filter`, drift-dating via ObjectId bucketing, defensive pipeline generation, self-referential vector-embedded schema store |
| **Design / UX** | Wrong-vs-right reveal; hazard citations on every answer; approval cards with affected-count + rollback note; zero-learning-curve chat UI |
| **Potential impact** | Every team connecting LLMs to production document databases hits silent-wrong-answer bugs — Cartographer is the missing trust layer; pain validated by live community discussion this month |
| **Creativity** | Reframes "chat with your data" as the bug, not the feature; schema archaeology (surveyors/historian/cartographer/surgeon) as a novel agent pattern |
