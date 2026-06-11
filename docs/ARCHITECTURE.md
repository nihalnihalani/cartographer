# Cartographer — Architecture

## 1. Problem Statement

LLM agents connected to MongoDB generate queries against an *assumed* schema. Real databases accumulate **schema drift** — type changes, field renames, partial coverage, shape changes — and queries that ignore drift return **silently wrong answers** (no error, plausible number, wrong value).

Cartographer's thesis: **text-to-query is not the bottleneck; database self-knowledge is.** Before answering questions, an agent should excavate, version, and consult a map of the database's real shape.

## 2. System Overview

Three workflows hang off one root agent:

```
User ──► Cartographer (root LlmAgent, gemini-3.5-flash)
              │
              ├── "map this database"   ──► EXPEDITION (SequentialAgent)
              │                               Surveyors (ParallelAgent, per collection)
              │                               → Historian → Mapmaker
              │
              ├── any data question     ──► NAVIGATOR (LlmAgent)
              │                               reads _schema_atlas → defensive pipeline
              │
              └── "fix it" / proposals  ──► SURGEON (LlmAgent + human approval gate)
```

All database access goes through the **official MongoDB MCP server** (`mongodb-mcp-server`), launched as a stdio subprocess via ADK's `MCPToolset`.

## 3. Agent Specifications

### 3.1 Cartographer (root)
- **Type:** `LlmAgent` with `sub_agents=[expedition, navigator, surgeon]`
- **Model:** `gemini-3.5-flash`
- **Tools:** `list-databases` (orientation only)
- **Instruction sketch:** classify the user's intent — mapping request, data question, or repair request — and delegate. Refuse to answer data questions if no `_schema_atlas` exists yet; offer to run an expedition first.

### 3.2 Expedition (`SequentialAgent`)
Runs three stages in order. Output of each stage lands in session state for the next.

**Stage 1 — Surveyors (`ParallelAgent`)**
- One surveyor instance per collection (collections discovered at expedition start).
- **MCP tools:** `collection-schema`, `aggregate`, `count`
- **Sampling strategy (stratified, the core trick):**
  - newest 200 docs (`$sort: {_id: -1}, $limit: 200`)
  - oldest 200 docs (`$sort: {_id: 1}, $limit: 200`)
  - random 200 docs (`$sample`)
- **Per-field stats computed via aggregation** (`$objectToArray` + `$type`):
  - coverage % (field present in N% of sampled docs)
  - type histogram (e.g., `price: {double: 71%, string: 29%}`)
  - null rate, example values
- **Output:** structured survey report per collection (JSON in session state).

**Stage 2 — Historian (`LlmAgent`)**
- **MCP tools:** `aggregate`, `find`
- **Job:** for every field with >1 type variant, date the drift by bucketing on `_id` timestamps (ObjectId encodes creation time): *"`price` was string until ~2024-03, double after."*
- Detect **alias pairs**: fields in the same/sibling collections with similar names (`user_id`/`userId`) — confirm by sampling value overlap.
- **Output:** hazard list per collection with severity (HIGH = silently corrupts aggregates; MEDIUM = excludes documents; LOW = cosmetic).

**Stage 3 — Mapmaker (`LlmAgent`)**
- **MCP tools:** `create-collection`, `insert-many`, `create-index`
- **Job:** write the **Schema Atlas** (see §4) into the target database itself, one document per collection, plus an atlas manifest doc with version + timestamp. Create a vector index over the natural-language summaries (Atlas Vector Search; embeddings auto-generated where available, with a deterministic local-embedding fallback).

### 3.3 Navigator (`LlmAgent`)
- **MCP tools:** `find` (for `_schema_atlas`), `aggregate`, `explain`
- **Flow per question:**
  1. retrieve relevant atlas entries (vector or direct `find`)
  2. enumerate hazards relevant to the fields the question touches
  3. generate a **defensive aggregation pipeline**:
     - `$convert`/`$toDouble` with `onError`/`onNull` for type drift
     - `$ifNull` defaults for partial coverage
     - `$unionWith`/`$or` across alias fields
  4. execute, then answer with a **Hazard Citations** block: which hazards existed, how each was neutralized, how many docs were affected
  5. on request, run `explain` and summarize the plan as proof of coverage
- **Hard rule in instruction:** never generate a pipeline for a field without first checking the atlas entry for that field.

### 3.4 Surgeon (`LlmAgent` + HITL)
- **MCP tools:** `update-many`, `create-index`, `find` (write-enabled MCP instance; `find` lets it read hazards and verify filters before proposing)
- **Job:** convert HIGH hazards into **repair proposals**: a concrete migration pipeline (e.g., `update-many` with `$set: {price: {$toDouble: "$price"}}` filtered to string-typed docs), a doc-count estimate, and a rollback note.
- **Gate:** execution requires explicit human approval via ADK's tool-confirmation flow (fallback: a two-turn explicit confirm). The proposal card shows: operation, filter, affected count, reversibility.
- After execution: re-survey the affected field and update the Schema Atlas (atlas version bump).

## 4. The Schema Atlas (data format)

Collection: `_schema_atlas` (in the mapped database).

```jsonc
{
  "atlas_version": 1,
  "collection": "orders",
  "surveyed_at": "2026-06-11T18:30:00Z",
  "doc_count": 12483,
  "sample_size": 600,
  "fields": {
    "price": {
      "coverage": 1.0,
      "types": { "double": 0.71, "string": 0.29 },
      "drift": { "from": "string", "to": "double", "boundary": "2024-03", "evidence": "_id timestamp bucketing" },
      "hazards": [{
        "id": "H-ORD-001",
        "kind": "TYPE_DRIFT",
        "severity": "HIGH",
        "blast": "SUM/AVG over price silently ignores 29% of documents",
        "defense": "$convert with onError:null + $ifNull guard"
      }]
    },
    "email": {
      "coverage": 0.88,
      "types": { "string": 1.0 },
      "hazards": [{ "kind": "PARTIAL_COVERAGE", "severity": "MEDIUM",
                    "blast": "$match on email drops 12% of customers",
                    "defense": "$ifNull / explicit missing-handling" }]
    }
  },
  "aliases": [{ "fields": ["user_id", "userId"], "confidence": 0.97, "evidence": "value-overlap sample" }],
  "summary": "Orders collection; revenue fields exhibit HIGH type drift beginning 2024-03 ...",
  "summary_embedding": [ /* vector */ ]
}
```

### Hazard taxonomy

| Kind | Example | Default severity |
|---|---|---|
| `TYPE_DRIFT` | string→double on `price` | HIGH |
| `ALIAS_FIELDS` | `user_id` vs `userId` | HIGH |
| `PARTIAL_COVERAGE` | `email` in 88% of docs | MEDIUM |
| `SHAPE_DRIFT` | `address` string→object | MEDIUM |
| `ENUM_DRIFT` | status `"shipped"` vs `"SHIPPED"` | MEDIUM |
| `NULL_POLLUTION` | explicit nulls vs missing | LOW |

## 5. MCP Integration Details

```python
McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "mongodb-mcp-server", "--readOnly"],   # writes only for Surgeon
            env={"MDB_MCP_CONNECTION_STRING": os.environ["MDB_MCP_CONNECTION_STRING"]},
        ),
        timeout=30,
    ),
    tool_filter=["collection-schema", "aggregate", "count"],   # per-agent allowlist
)
```

- **Two flavors of MCP instance** (one stdio toolset per agent): read-only (`--readOnly`) for the root, Surveyors, Historian, and Navigator; write-enabled only for the Mapmaker (filtered to the atlas-authoring tools `create-collection`/`insert-many`/`create-index`) and the Surgeon (repairs, gated behind human approval). `tool_filter` is a client-side allowlist — the `--readOnly` flag is the server-side enforcement line.
- **Per-agent `tool_filter`** keeps each agent's tool surface to 3–5 tools — less token bloat, least privilege.
- Transport is **stdio** — the documented-stable path for ADK `MCPToolset` (avoids the known streamable-HTTP issue).

## 6. Seed Data (demo ground truth)

`seed/seed_messy_db.py` generates an e-commerce database with **planted, dated drift** so demo numbers are deterministic:

- `orders` (~12k docs): `price` string before 2024-03 cutoff (≈29%), double after; `status` case drift
- `customers` (~5k docs): `user_id` (old) vs `userId` (new); `email` missing in 12%
- `products` (~1k docs): `address`-style shape drift on `dimensions`
- Prints the **ground-truth answers** (true vs naive-sum revenue, all-time and 2024) for the demo script. Note: because all string prices predate the 2024-03 boundary, the demo question is all-time revenue — a 2025-scoped question would touch no drifted documents.

## 7. Deployment

- Local dev: `adk web agents` (ADK dev UI is the demo front end)
- Hosted: `adk deploy cloud_run --with_ui` → public Cloud Run URL (hackathon requirement)
- Config via env: `GOOGLE_API_KEY` (AI Studio) or Vertex project vars; `MDB_MCP_CONNECTION_STRING`

## 8. Security Posture

- Read-only MCP by default; writes isolated to one agent behind human approval
- Connection string only in env, never in agent context
- `tool_filter` least-privilege per agent
- Surgeon proposals include affected-count + rollback note before any execution
