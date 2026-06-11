# Cartographer — 3-Minute Demo Video Script

> Target: ≤ 3:00, screen recording + voiceover. Record at 1080p+. Every number below is deterministic (controlled by `seed/seed_messy_db.py`), so retakes are cheap.

## Pre-flight checklist

- [ ] Seeded database up (`python seed/seed_messy_db.py` — note the printed ground-truth numbers)
- [ ] `adk web agents` running, both the naive baseline agent and Cartographer selectable
- [ ] MongoDB Atlas UI open in a second tab (collections view)
- [ ] Browser zoom ~125% so text is readable in the recording
- [ ] Do one full dry run before recording

## Shot list

### Shot 1 — The Lie (0:00–0:30)

**Screen:** ADK web UI, agent = `naive_agent`.

**Type:** `What was total revenue?`

**It answers:** `$1,096,236.79` *(wrong — ignores 3,625 string-typed prices)*

**Voiceover:**
> "This is a standard 'chat with your database' agent on a real-world e-commerce database. Total revenue? $1,096,236.79. Confident, instant… and wrong by twenty-nine percent. No error was thrown. This bug ships in production AI systems today — because the agent doesn't actually know what's in the database."

### Shot 2 — The Excavation (0:30–1:30)

**Screen:** switch agent to `cartographer`.

**Type:** `Map this database.`

**Show:** parallel surveyor outputs streaming; highlight (mouse-circle) the key findings as they appear:
- `orders.price — double 71% / string 29% — drift boundary ≈ 2024-03`
- `customers — alias pair detected: user_id ↔ userId (confidence 0.97)`
- `customers.email — coverage 88%`

**Then:** cut to MongoDB Atlas UI tab → open `_schema_atlas` collection → click into the `orders` document → scroll the hazards array.

**Voiceover:**
> "Cartographer sends a crew of parallel surveyor agents into every collection — sampling old documents, new documents, and random documents through the official MongoDB MCP server. A historian agent dates each drift: price flipped from string to number in March 2024. And the map it builds isn't a chat answer — it's a versioned Schema Atlas written back into MongoDB itself, with a hazard list for every field."

### Shot 3 — The Truth (1:30–2:15)

**Screen:** back to ADK UI, agent = `cartographer`.

**Type:** `What was total revenue?`

**It answers:** `$1,542,667.68` + a **Hazard Citations** block:
- `H-ORD-001 TYPE_DRIFT — converted 3,625 string prices ($toDouble with onError guard)`
- `H-CUS-002 ALIAS_FIELDS — unioned user_id/userId`

**Show:** side-by-side moment — scroll so the naive `$1,096,236.79` and Cartographer's `$1,542,667.68` are both visible, or use a split screen card.

**Voiceover:**
> "Same question to Cartographer. It consults the atlas first, then writes a defensive pipeline — converting every string-typed price, handling the field alias. Real answer: $1,542,667.68. The naive agent missed twenty-nine percent of revenue — silently. And Cartographer shows its receipts: every hazard it defended against, and how many documents were affected."

### Shot 4 — The Repair (2:15–2:50)

**Type:** `Fix the price drift permanently.`

**Show:** the Surgeon's proposal card — operation, filter, `~3,625 documents affected`, rollback note — then the **approval prompt**. Click approve. Show the success message + atlas version bump to v2.

**Optional capper (if time):** switch to `naive_agent`, re-ask the revenue question → now it gets `$1,542,667.68` too.

**Voiceover:**
> "Cartographer can also close the loop. The Surgeon agent proposes a migration — exactly which documents, exactly what changes, fully reversible — but it cannot execute without human approval. I approve… 3,625 documents normalized, atlas updated. Now even the naive agent gets the right answer."

### Shot 5 — Impact Card (2:50–3:00)

**Screen:** title card (README hero or a simple slide):

> **CARTOGRAPHER**
> Schema archaeology for AI agents.
> Gemini 3.5 Flash · Google Cloud Agent Builder (ADK) · MongoDB MCP
> *Every team wiring an LLM to a production database ships the silent-wrong-answer bug today. Cartographer is the layer that stops it.*

**Voiceover:**
> "Built with Gemini and Google Cloud Agent Builder, with every database superpower coming from MongoDB's MCP server. Cartographer: because your AI should know what's actually in your database."

## Exact prompts (copy-paste during recording)

1. `What was total revenue?` (naive agent)
2. `Map this database.`
3. `What was total revenue?` (cartographer)
4. `Fix the price drift permanently.`

## Recording tips

- Pause 1–2 beats on the wrong number in Shot 1 — it's the hook.
- The Atlas-UI cutaway in Shot 2 proves the MCP writes are real; don't skip it.
- If any take stalls, just re-run — seed data makes every number reproducible.
- Upload to YouTube as **Public or Unlisted-public-link** (must be viewable by judges), title: *"CARTOGRAPHER — Google Cloud Rapid Agent Hackathon (MongoDB Track)"*.
