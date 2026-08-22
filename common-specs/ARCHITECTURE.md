# Ultimate Memory Stack — Architecture

> **Status:** stable (ships with UMS v4.0.0) · **Authors:** see /AUTHORS.md
> **In one sentence:** a 7-layer architecture (Layer 0–6) separating protocol, storage, compliance, search, caching, graph, and cryptographic concerns — each layer tier-gated to activate as its infrastructure unblocks.
>
> Version history lives in [`CHANGELOG.md`](../CHANGELOG.md).

---

## 1. Overview — Why Layered

The Ultimate Memory Stack uses a **7-layer architecture (Layer 0 through Layer 6)** to separate concerns:

- **Layer 0** is the operational protocol (rules; no content)
- **Layer 1** is the persistent storage (markdown vault; no logic)
- **Layer 2** is compliance + audit (regulatory boundary)
- **Layers 3–6** are capability layers (search, caching, graph, crypto) — each gated by deployment tier

**Why layered:**
1. **Separation of concerns** — protocol rules don't mix with storage; storage doesn't mix with search
2. **Tier-gated activation** — higher layers activate when their infrastructure unblocks (ideal-first: build for the ideal state)
3. **Edition-aware** — the same architecture supports any edition; PROFILE.md selects which layers are mandatory vs optional vs disabled
4. **Deployment portability** — each machine deploys at their highest available tier; the stack does not require all infrastructure to function

**Two foundational principles from the research base** (Letta + Cline + MemoryOS + 9 others, 210 sources):
- **Markdown as source of truth** — every layer must defer to Layer 1 (markdown vault) as authoritative. Higher layers are indexes, caches, or signatures — never primary storage.
- **Per-entry metadata over inline tags** — YAML frontmatter (SCHEMA_A18) is the convergent pattern. Avoid inline tags ([FINAL], [TENTATIVE]) that don't survive consolidation.

> **Editions note:** the public release ships the **general edition**. HIPAA/PHI is out of scope for this edition. See [`CONTRIBUTING.md`](../CONTRIBUTING.md). The defaults referenced throughout this document describe the shipped general edition's configuration.

---

## 2. Layer Inventory

| Layer | Name | Min Tier | Default | Active in current release? |
|-------|------|----------|---------|-----------------|
| **0** | Protocol & Budget | T0 | Required | YES |
| **1** | Markdown Vault | T0 | Required | YES |
| **2** | Compliance & Audit | T0 | Opt-in (preset-driven) | YES |
| **3** | Hybrid Search | T1 | Optional | Designed-in, dormant at T0 |
| **4** | Caching & Compression | T0 base / T3 advanced / T4 Dreaming | Optional | Active at T0; expands at T3/T4 |
| **5** | Graph Backends | T2 | Optional | Designed-in, dormant at T0 |
| **6** | Cryptographic Signatures | T3 | — | **NOT IMPLEMENTED** (designed only; no code) |

**Tier glossary:**
- **T0** — Anywhere (current Claude Code default install, no infrastructure)
- **T1** — + Ollama (local embedding model for vector search)
- **T2** — + Node.js (graph DBs, file watchers, indexing daemons)
- **T3** — + Code Execution unblocked (crypto, advanced compaction, Python analytics)
- **T4** — + Skills + Anthropic Dreaming beta (offline memory reorganization)

---

## 3. Documentation Discipline (Standing Rule)

**Every layer + every feature carries this canonical block:**

```markdown
### <Feature/Layer Name>

**Purpose**: <one sentence — what's the user-facing goal?>

**Rationale**: <2-3 sentences — why this approach over alternatives>

**Sound reasoning**: <evidence chain — what research, production examples, decisions backed this>

**Scope — CAN**:
- <thing it does>

**Scope — CANNOT**:
- <explicit boundary>

**Active in current release**: <yes / designed-in / no>

**Deployment tier**: <T0 / T1 / T2 / T3 / T4>

**Cross-references**: <related decisions, schemas, incidents>
```

This is **non-negotiable**. Undocumented features do not ship. If a feature lacks any of the 5 blocks (purpose, rationale, sound reasoning, scope CAN, scope CANNOT) it gets flagged and either documented or removed.

**Worked example** (Layer 2 / Audit Log B1):

> **Purpose**: Provide an append-only audit trail of all memory read/write operations for forensic capability and regulatory compliance. (Tamper-*evidence* depends on Layer 6 / C4 signing, which is designed but not yet implemented — see `SCHEMA_audit_log.md` §1.)
>
> **Rationale**: Without audit log, post-incident investigation is blind. Letta and production memory systems implement this after vulnerability research. HIPAA §164.312(b) requires audit controls. JSONL chosen over SQLite because grep-friendly, no DB driver needed at T0, append-only crash-safe.
>
> **Sound reasoning**: Production research (Letta) shows audit log is a convergent production pattern. A real prompt-injection incident during development demonstrated the forensic-blind state. JSONL append-only avoids the corruption modes of binary log formats.
>
> **Scope — CAN**: Log every memory read/write with timestamp, source_agent, source_session, entry_id, action_type, entry_summary. Provide /audit-search forensic queries. Rotate by date.
>
> **Scope — CANNOT**: Log full content of entries (only summaries — keep log size manageable, PHI-free). Provide cryptographic chain-of-custody (Layer 6 signatures do that). Replace OS-level audit logging.
>
> **Active in current release**: Yes (opt-in / configurable per compliance preset).
>
> **Deployment tier**: T0 (markdown JSONL works anywhere).
>
> **Cross-references**: SCHEMA_audit_log.md, B1 (audit feature).

---

## 4. Layer 0 — Protocol & Budget

### Purpose
Operational rules for HOW Claude loads, prioritizes, and conflicts-resolves memory. The protocol layer defines behavior; no content lives here.

### Rationale
Without a protocol layer, every session re-derives its own approach to memory. Layer 0 locks behavior across sessions and across deployments. Operational consistency is what makes the system feel coherent across time.

### Sound reasoning
- Anthropic's official guidance positions CLAUDE.md + `.claude/rules/` as the auto-load mechanism. Layer 0 piggybacks on this.
- Letta production patterns: explicit context budget + 3-tier load order is the convergent design after 18 months production
- Cline auto-load: `.clinerules` provides the same auto-load shape; Layer 0 standardizes it
- Survey evidence: 11 of 12 systems surveyed have an explicit protocol layer

### Scope — CAN
- Set context budget (≤15% / ≤30% / ≤45% by tier; ≥25% reserved for work; 40% absolute ceiling)
- Define load order (Tier 1 always / Tier 2 if resuming / Tier 3 on demand)
- Resolve conflicts via 9-level hierarchy (compliance > live instruction > security > feedback > FINAL decisions > session state > TENTATIVE > project context > user profile)
- Trigger self-test suite (T1–T7) at session start
- Trigger heartbeat checkpoints (~30 min)
- Define risk scoring rubric (6-factor MAX-score: blast radius / reversibility / protected files / test coverage / novelty / user data impact)
- Trigger cascade failure detection (3 unrelated errors / 5 min → STOP)
- Document decision promotion pattern (inline → decisions.md at >5)
- Standing rules (no secrets, no PII/PHI, schema versioning)

### Scope — CANNOT
- Store actual content (Layer 1's job)
- Enforce compliance rules (Layer 2's job; Layer 0 invokes Layer 2)
- Perform search or retrieval (Layer 3's job)
- Cryptographic verification (Layer 6's job)

### Active features in the current release (all Tier A)
1. Adaptive context loading (3 tiers)
2. Tiered context budget (15/30/45% with 25% reserved + 40% ceiling)
3. 9-level conflict resolution hierarchy
4. Risk scoring rubric (6-factor)
5. Cascade failure detection
6. Self-test suite (T1–T7)
7. Self-trimming protocol (every 10 sessions, suggestions-only)
8. Heartbeat checkpoint
9. Decision promotion pattern
10. Documentation discipline
11. Schema versioning
12. Standing rules (no secrets, no PII/PHI)

### Deployment tier
**T0.** No infrastructure required. Works on Claude Code default install.

### Cross-references
- `MEMORY_PROTOCOL.md` (operational details)
- `SCHEMA_A18` (entry metadata; protocol enforces frontmatter)
- `memory/sessions/session_state.md` (lifeline artifact)

---

## 5. Layer 1 — Markdown Vault

### Purpose
Persistent storage. Every memory entry is a markdown file with YAML frontmatter. Organized into 8 standard categories + per-project memory banks. This is the **source of truth** — higher layers index/cache/sign but never replace.

### Rationale
- Human-readable + grep-able (no opaque DB at T0)
- Compatible with VS Code, GitHub, any text editor or markdown viewer
- Cross-platform (Windows / Mac / Linux)
- No driver / runtime dependencies
- Letta + Cline + MemoryOS + 9 others all converge on markdown-or-text-based convention
- Survives any backend swap (graph DB can fail; markdown files persist)

### Sound reasoning
- Survey: 11 of 12 systems surveyed use markdown or text-based primary storage; 1 uses pure SQLite (for compatibility, not capability)
- The memory stack is one layer of a broader agent architecture; storage must be portable
- Cline 6-file memory-bank convention (projectbrief / productContext / systemPatterns / techContext / activeContext / progress) chosen as per-project standard (SCHEMA_A3)
- YAML frontmatter (SCHEMA_A18) avoids the inline-tag pitfalls of v1.0/v2.0 — survives consolidation, machine-parseable, extensible

### Scope — CAN
- Store entries with YAML frontmatter (SCHEMA_A18: id, created_at, last_updated, last_validated, expires_at, source_agent, source_session, source_uri, pattern_key, recurrence_count, first_seen, last_seen, confidence, status, content_sha256)
- Organize into 8 standard categories: `sessions/` `decisions/` `feedback/` `projects/` `security/` `references/` `user/` `archive/`
- Per-project memory bank under `projects/<slug>/memory-bank/` (6-file Cline convention, SCHEMA_A3)
- Override-file convention: `<edition>/overrides/X.override.md` REPLACES sections of `common-specs/X.md` of the same name; other sections inherit
- CAS-style concurrency: `content_sha256` enables safe replace-class operations
- Pattern-key promotion: recurrence counter triggers promotion to higher-confidence storage
- Mtime-based versioning (filesystem timestamps as ordering)
- Hand-editable OR programmatically updated

### Scope — CANNOT
- Provide semantic search (Layer 3 if T1+)
- Provide graph traversal (Layer 5 if T2+)
- Cryptographic verification (Layer 6 if T3+)
- Concurrent multi-writer without CAS — Layer 0 enforces content_sha256 check to prevent silent corruption
- Store PII/PHI (Layer 2 redacts before Layer 1 writes)

### Active features in the current release
- 6-file per-project memory bank (A3, Tier A)
- YAML frontmatter on every entry (A18, Tier A)
- **Bi-temporal annotations** (`valid_at` / `invalid_at` in SCHEMA_A18, B5 Tier B — available, opt-in)
- **Wiki-link inline syntax** (`[[ID]]` body references parsed into A18 cross-reference YAML; auto-sync at T2+)
- Pattern-key recurrence promotion (A8 + B6, Tier A/B)
- Override-file convention (B4, Tier B)
- CAS concurrency control (B3, Tier B)
- Standard 8 categories + archive (Tier A foundation)
- File size limits + consolidation protocol (Tier A from v2.0)

### Obsidian-vault compatibility (by design)

Layer 1's directory structure + YAML frontmatter + wiki-link convention are 100% compatible with an [Obsidian](https://obsidian.md/) vault. Open `memory/` in Obsidian and:
- Frontmatter is recognized automatically (Properties view)
- Wiki-links `[[DEC-024]]` become clickable navigation
- Graph view renders memory cross-references visually
- Plugin ecosystem (Smart Connections, Dataview, etc.) works out of the box
- Search, tags, and templates all available without any conversion

**Why this matters:** users who already use Obsidian for personal knowledge management can adopt the Ultimate Memory Stack as a special-purpose vault inside their existing PKM workflow. The memory stack does not require Obsidian — it's a markdown-first filesystem store — but is purposefully compatible with it.

**Research evidence:** *"By 2026, when developers extend the agent-memory pattern toward an always-on second brain they almost universally settle on Obsidian as the storage layer."* We don't fight that gravity; we use it.

### Hot/cold tiering (v4.0.0)

Three categories — `sessions/`, `decisions/`, `feedback/` — rotate their oldest content into a companion `memory/archive/<category>/ARCHIVE_INDEX.md` once the hot file hits its `MEMORY_PROTOCOL.md` §11 line cap: the full entry section moves to `<category>-archive.md` (append-only, nothing deleted), and a one-liner pointer lands in the ARCHIVE_INDEX so the rotated entry stays findable by ID without loading the archive file itself. The always-loaded surface (session state, user profile, the master index) stays small as a vault ages; everything rotated out stays one on-demand read away.

This backports a field-proven pattern from the maintainer's own production Claude Code deployment: measured over ~87 days, the always-loaded index went 26.5KB → ~12KB across two tiering iterations with zero information loss — the same architecture adapted to UMS's per-category layout, not a code transplant. Full mechanics, rotation procedure, and rehydration: `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (E12).

### Deployment tier
**T0.** Files only. Works on any filesystem. Obsidian-compat is purely passive — no Obsidian install required.

### Cross-references
- `SCHEMA_A3_per_project_memory_bank.md`
- `SCHEMA_A18_per_entry_metadata.md`
- `MEMORY_PROTOCOL.md` §FileSizeLimits + §StandardCategories + §11.6 (tiered archive)
- `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (E12) — full rotation/rehydration procedure
- `common-specs/templates/ARCHIVE_INDEX.template.md`

---

## 6. Layer 2 — Compliance & Audit

### Purpose
Regulated-data handling and forensic capability. Audit trail of read/write operations. Quarantine workflow for suspicious entries. Compliance preset selection (none / enterprise / custom; `healthcare` is not available in this edition).

### Rationale
- Regulated-data deployments may require HIPAA §164.312 technical safeguards — audit controls, access controls, integrity controls
- The compliance layer supports opt-in presets (`none` / `enterprise` / `custom`) plus stackable extensions (`gdpr` / `soc2` / `pci-dss`) for these deployment shapes; `healthcare` is not selectable in this edition
- Without audit log: post-incident investigation is blind. Memory poisoning happens; you need forensic capability.
- Without quarantine: validated-bad entries either get loaded (and bias future behavior) or silently dropped (and lose evidence)
- 3-preset hybrid (B7) handles real-world deployment shapes without requiring users to compose compliance from scratch

### Sound reasoning
- HIPAA §164.312(b) is explicit: "Implement hardware, software, and/or procedural mechanisms that record and examine activity in information systems that contain or use electronic protected health information."
- A real prompt-injection incident during development demonstrated the end-to-end vulnerability — bad entry passed validation, polluted memory, propagated for multiple sessions before detection
- Letta + 5 production memory systems implement audit + quarantine after vulnerability research
- The 3-preset hybrid resolves a real design tension — neither single toggle nor 4-toggle matrix; just "what deployment shape do you fit"

### Scope — CAN
- Log every memory read/write to JSONL audit trail (B1; opt-in / configurable)
- Quarantine entries failing validation-on-read (B2)
- Enforce active compliance preset (B7): `none` / `enterprise` / `custom`
- Detect PII/PHI per the active compliance preset and route to quarantine (redaction is not included in this edition)
- Detect memory poisoning patterns and route to quarantine
- Provide the `/audit-quarantine` review workflow (surfaced via a one-line approval toast at session start)
- Track quarantine release decisions back to audit log
- Run cross-entry consistency checks (e.g., DEC-### references must resolve)

### Scope — CANNOT
- Store actual PII/PHI — NEVER (even in quarantine, redact the content)
- Encrypt content at rest (defer to OS-level disk encryption; not memory stack's job)
- Provide attribution beyond `source_agent` + `source_session` (forensic correlation across deployments is admin-level concern)
- Replace human review of quarantined entries — Layer 2 surfaces; user decides

### Active features in the current release
- Audit log JSONL (B1, opt-in / configurable)
- Quarantine queue + workflow (B2)
- 3-preset compliance hybrid (B7) + custom override
- Memory poisoning defenses (B8): provenance + validation-on-read + quarantine (signatures NOT IMPLEMENTED)
- PII detection-pattern framework (enterprise/custom presets); PHI patterns are not included in this edition

### Deployment tier
- **T0** base: markdown JSONL audit log + quarantine queue (works anywhere)
- **T3** enhanced: *intended* — cryptographic signatures (Layer 6) would attach to audit-log entries for chain-of-custody. NOT IMPLEMENTED; do not rely on it.

### Cross-references
- `SCHEMA_audit_log.md` (JSONL format spec)
- `SCHEMA_quarantine.md` (workflow spec)
- `SCHEMA_compliance_profile.md` (3-preset + custom)

---

## 7. Layer 3 — Hybrid Search

### Purpose
Fast, relevance-ranked retrieval of memory entries. Vector embeddings + lexical matching + recency, weighted. Surfaces top-K results to context based on natural-language queries.

### Rationale
At T0, retrieval is grep-only — works for small memory but doesn't scale to 100+ projects or topic-based queries ("what did we decide about X?"). Production research (Letta, MemoryOS, Cognee, MemGPT) shows hybrid search is the convergent production pattern.

### Sound reasoning
- Letta: vector + keyword + recency, weighted, in production for 18 months — proven pattern
- MemoryOS: hybrid retrieval as core feature, documented in their paper
- Anthropic guidance: prompt caching + sub-agent context, but no native search — leaves search as an integration concern
- Embedding model options: Ollama local (privacy-sensitive deployments, T1), OpenAI/Cohere/Voyage cloud (T2+)
- Lexical layer: BM25 or simple TF-IDF — well-understood, deterministic, complements vector

### Scope — CAN
- Index memory entries via embedding model (Ollama at T1; cloud APIs at T2)
- Lexical search via BM25 or TF-IDF (Node.js at T2, or shell `grep` fallback at T0)
- Hybrid ranking (vector × lexical × recency, weights configurable)
- Cache embeddings to disk (per-file content_sha256; recompute on change)
- Surface top-K results to context based on query
- Filter results by category, deployment tier marker, edition, status

### Scope — CANNOT
- Replace markdown vault (Layer 1 stays authoritative)
- Generate new content (retrieval only)
- Cross-reference memory across deployments (single-deployment scope; cross-deployment is admin-level)
- Embed PHI (Layer 2 redacts before indexing; embeddings are derived data and inherit redaction)
- Operate without an embedding model (T0 falls back to grep — provided by Layer 0's standard tools)

### Active features in the current release
- **DESIGNED-IN, DORMANT at T0.** All capabilities specified; activation gated by tier.
- **B9 Ollama local semantic search** (Tier B, opt-in): privacy-friendly, no cloud dependency, T1+ minimum
- **B10 Embedding-cache-as-derived-index** (Tier B, required architecture): indexes live at `memory/.index/`, gitignored, regenerable from Layer 1
- **B11 Hybrid retrieval** (semantic + BM25 + entity, mem0-pattern): opt-in v2.2 — depends on B9 + B10 existing first
- **C9 Transformers.js embeddings** (Tier C, Node.js 18+): alternative embedding backend if Ollama path (B9) isn't viable on a deployment
- T1 activation (Ollama or Transformers.js) → vector search functional
- T2 activation (Node.js) → indexing daemon, file-watcher, automatic refresh, hybrid retrieval (B11)
- T3 activation (Code Exec) → custom reranking, advanced query parsing

### Inspiration model — Obsidian Smart Connections

The reference pattern for "markdown source-of-truth + embeddings as derived cache" is **Obsidian Smart Connections** ([brianpetro/obsidian-smart-connections](https://github.com/brianpetro/obsidian-smart-connections), 786k+ downloads as of early 2026):
- Markdown files remain the canonical store (Layer 1)
- Embeddings generated locally via TaylorAI/bge-micro-v2 (384 dimensions)
- On-device retrieval — no cloud dependency
- Embedding index = derived data; regenerable from markdown at any time

As the research notes: *"Markdown files and vector retrieval are not mutually exclusive — markdown is the canonical storage and vectors are a derived, regenerable index. This is the architecturally correct way to mix them."* Our Layer 1 + Layer 3 split mirrors this exactly.

### Deployment tier
- **T1** minimum (Ollama via B9, or Transformers.js via C9)
- **T2** recommended (Node.js for indexing daemon, B11 hybrid retrieval)
- **T3** optional (Code Exec for ad-hoc reindex jobs, custom reranking)

### Cross-references
- `SCHEMA_A18` §pattern_key + §last_validated (feeds search index)
- B9 (Ollama opt-in) · B10 (cache-as-derived-index) · B11 (hybrid retrieval) · C9 (Transformers.js alternative)
- Obsidian Smart Connections (reference architecture — see Inspiration model above)

---

## 8. Layer 4 — Caching & Compression

### Purpose
Reduce token cost via Anthropic prompt cache + context compression. At T4, includes Anthropic Dreaming (offline memory reorganization between sessions).

### Rationale
- Anthropic prompt cache (5-minute TTL) saves ~90% on cached tokens for stable preamble
- `/compact` reduces 100K+ tokens to ~5K at session boundaries
- Long-running sessions accumulate context drift; Dreaming would offline-restructure
- Without Layer 4, every session re-reads stable files, paying full token cost

### Sound reasoning
- Anthropic official guidance: cache stable preamble (CLAUDE.md, memory_protocol.md, edition profile) for ~90% cost savings
- Community research: /compact mechanics + pre-compact checklist are the user-facing tools that actually matter
- Anthropic Dreaming beta: scheduled async memory reorganization (Tier C, not yet GA but tracked)
- Without caching: 5K-token stable preamble × N sessions = N × 5K. With caching: 5K once + ~500 per cached read.

### Scope — CAN
- Prompt cache stable preamble (CLAUDE.md, memory_protocol.md, edition profile, decisions.md if stable)
- `/compact` at user-controlled intervals (~95% community-derived threshold)
- Pre-compact checklist (heartbeat session_state.md BEFORE compacting; surface dangling tasks; verify mirror parity)
- Post-compact reset (verify Tier 1 + Tier 2 still loaded; smoke-test recall)
- (T4) Dreaming: scheduled offline memory reorganization
- (T3) Code-Exec-backed compaction jobs for log rotation, dead-link sweeps

### Scope — CANNOT
- Cache live conversation (Anthropic prompt cache is preamble-only, not turn-by-turn)
- Force `/compact` autonomously (auto-compact threshold is heuristic, not deterministic; user must decide)
- Replace human curation (Dreaming reorganizes structure; humans decide what's worth keeping)
- Survive a cache miss faster than a fresh read

### Active features in the current release
- Prompt caching strategy guidance (T0, always-applicable)
- `/compact` workflow + pre-compact checklist (T0, user-driven; documented in USER_CHEAT_SHEET_core.md)
- **C1 Auto-Dream sleep-time consolidation** (designed-in T4): Anthropic `dreaming-2026-04-21` beta — offline async memory reorganization between sessions
- **C6 LLMLingua/LongLLMLingua prompt compression** (designed-in T3): ~40× compound discount on hot prefixes (4× compression × 10× cache savings); requires Python ML libs via Code Exec

### Deployment tier
- **T0** base (caching strategy + `/compact` workflow)
- **T3** enhanced (Code Exec for LLMLingua compression — C6)
- **T4** Auto-Dream (Anthropic beta required — C1)

### Cross-references
- `USER_CHEAT_SHEET_core.md` §When-to-Compact
- C1 (Auto-Dream designed-in) · C6 (LLMLingua compression designed-in)

---

## 9. Layer 5 — Graph Backends (Graphiti + Kuzu)

### Purpose
**Temporal-fact knowledge graph** of memory entries. Entities (decisions, facts, sessions, projects), relationships (`supersedes`, `references`, `derived_from`), and **bi-temporal validity windows** (`valid_at` / `invalid_at` per SCHEMA_A18 B5). Markdown vault remains source of truth; graph is the derived structural + temporal index.

### Rationale
- Markdown wiki-links work but require parser traversal — slow for deep queries ("show full decision chain leading to Y")
- Graph DBs optimized for traversal — milliseconds vs seconds
- **Bi-temporal fact model** (Graphiti pattern) enables point-in-time queries: *"What did we believe on date X?"* — load-bearing for regulatory/audit forensics
- At T0, wiki-links work as fallback; graph adds speed AND temporal query capability
- **Kuzu embedded backend** = in-process graph DB, comparable to SQLite for graphs. **Zero infrastructure overhead.** No separate server, no admin privilege. Critical for single-workstation deployments.
  - ⚠️ **Kuzu upstream is ARCHIVED** (read-only since 2025-10-10; Kùzu Inc. acquired by Apple). 0.11.3 is final and still ships Windows wheels, and it remains our default because no maintained embedded alternative covers Windows — FalkorDB Lite cannot even build there. This is a *frozen* dependency, deliberately accepted; see `recommended-addons/graphiti-installer/requirements.txt` for the full position. *(Verified 2026-08-20.)*

### Sound reasoning
- Research synthesis (graph-augmented memory, 14 sources): hybrid pattern (markdown source-of-truth + graph index) is convergent across 5+ production systems
- **Graphiti** is the actively-developed open-source layer since Zep Community Edition deprecation (Feb 2026); Apache 2.0 license; **30.1k stars**, latest 0.29.3 (2026-07-27), pushed daily — healthy, not winding down. The architecture paper is **`arXiv:2501.13956`, *"Zep: A Temporal Knowledge Graph Architecture for Agent Memory"*, Rasmussen et al.** — it describes Zep, of which Graphiti is the open-source engine. *(Verified 2026-08-20. This previously read "Chalef et al."; Daniel Chalef is the LAST of five authors, not the first — the citation was misattributed.)*
- Graphiti supports multiple backends (Neo4j 5.26+, FalkorDB 1.1.2+, FalkorDB Lite, Kuzu 0.11.2+ embedded, **Amazon Neptune**). **Kuzu embedded remains the most plausible target for single-workstation, no-admin environments** — *"comparable to SQLite for graphs"* — and is the ONLY embedded option that installs on Windows, which is why an archived upstream has not displaced it.
- **As of Graphiti v0.29.0 (April 2026):**
  - **MCP Server included** — Graphiti now ships an MCP (Model Context Protocol) server. Direct integration with Claude Code, Cursor, and other MCP-compatible assistants. **Changes the activation path: instead of a custom Python bridge, wire Graphiti via MCP.**
  - **REST Service** — FastAPI-based server in `server/` directory for multi-process deployments
  - **Ollama support** — local LLM via OpenAI-compatible endpoint. **Implication: Graphiti can activate at T1 (Ollama present) instead of T3 (Anthropic API via Code Execution)** if the deployment shouldn't depend on a cloud LLM for graph ingestion. Tier reduction.
  - **Google Gemini, Groq, Azure OpenAI** added as LLM providers
  - **Custom database name configuration** for Neo4j/FalkorDB (v0.17.0+)
- Retrieval is hybrid: semantic embeddings + BM25 keyword + graph traversal — Zep claims sub-200ms latency. Crucially, retrieval does NOT depend on LLM-generated summaries at query time.
- **Vendor benchmark numbers** (94.8% / +18.5% improvements on LongMemEval / DMR) are vendor-published preprints, not peer-reviewed. **Borrow the design, not the numbers** (see §13).

### Scope — CAN
- Build graph index from SCHEMA_A18 frontmatter (`related`, `supersedes`, `cross_references`) + inline `[[wiki-links]]`
- **Point-in-time queries**: `valid_at ≤ X AND (invalid_at IS NULL OR invalid_at > X)` — answer "what did we know on date X?"
- Traverse: "what depends on X" / "what references DEC-###" / "full lineage from this decision back to source episodes"
- **Fact-supersession with history preservation** — when contradicting fact arrives, set old fact's `invalid_at` rather than deleting (B5 bi-temporal model)
- Refresh index on file change (file-watcher at T2)
- Hybrid retrieval (semantic + lexical + graph traversal, weighted)
- Cache traversal results within session
- Surface graph-derived context to Tier 2/3 loads ("loading this project → also load related decisions")
- Provide forensic/audit-control reconstruction at any historical date

### Scope — CANNOT
- Replace markdown vault — graph is derived index, not store. Wipe and rebuild from Layer 1 anytime.
- Operate without Code Execution (T3 minimum gate — Kuzu Python driver required even though Kuzu itself is embedded)
- Persist across deployments — graph rebuilds on demand from markdown source
- Provide semantic similarity alone (Layer 3 does that; Graphiti pairs them — graph for structure/temporal, vectors for similarity)
- Hold the only copy of any data — if graph DB is wiped, rebuild from Layer 1

### Active features in the current release
- **DESIGNED-IN, DORMANT at T0.** Architecture, schema, integration patterns specified.
- **C2 Graphiti temporal-fact graph (Kuzu embedded)** — activates with Code Execution (T3). Research verdict: *"strongest single storage upgrade on the future roadmap."*
- **B5 bi-temporal annotations** (`valid_at` / `invalid_at` in SCHEMA_A18) — already adoptable at **T0 in pure markdown**. The graph backend just makes the queries fast later. Codifying the pattern NOW (in YAML) primes Layer 5 activation without re-migration.

### Deployment tier
- **T0–T1**: bi-temporal annotations in YAML; queries answered by grep + manual reasoning
- **T1+** (Ollama present): Graphiti can activate using Ollama as the LLM for ingestion (per v0.29.0 Ollama support); zero cloud LLM dependency for the graph layer
- **T3** (Code Execution): full feature set including Anthropic/OpenAI/Gemini LLM ingestion options
- **T3+** recommended (file-watcher daemon for automatic index refresh + MCP server for Claude Code integration)
- **Install:** the add-on's hash-pinned lock — `pip install --require-hashes -r <path-to-install-graphiti-skill>/locks/requirements-py<VER>.lock`. ⛔ **Not** `pip install graphiti-core[kuzu]`: that extra is deprecated upstream, and pip installs a package *silently and successfully* — exit 0, no warning — without an extra it no longer provides. For Claude API ingestion, uncomment the `anthropic` line in the add-on's `requirements.txt` and regenerate the lock — which requires a clone of the **source package**, since the regenerator is a maintainer tool and is not copied into an installed skill (see `TIER_C_ACTIVATION.md` §C2). Ollama needs nothing extra (it is OpenAI-compatible — set `OPENAI_BASE_URL`).

### Implementation choice — closed
This resolves Open Question #2 from the initial draft (*"Memgraph vs Neo4j vs lightweight in-memory"*). Selected: **Graphiti + Kuzu embedded backend** at T3. Reasoning:
- Kuzu = zero admin overhead (the deciding factor for single-workstation environments)
- Graphiti = actively developed (Apache 2.0); Zep CE is abandonware
- Bi-temporal model is the highest single capability gain we can adopt
- Falls back gracefully: at T0–T2, bi-temporal YAML still works; only the FAST queries require T3

### Cross-references
- B5 (bi-temporal annotations) · C2 (Graphiti+Kuzu designed-in) · §13 D3 (vendor benchmark caveat)
- `SCHEMA_A18` §Bi-temporal-fields (the schema-side B5 implementation)

---

## 10. Layer 6 — Cryptographic Signatures

### Purpose
Tamper-evidence for memory entries. Detect when entries have been modified outside expected write flow (memory poisoning, accidental edit, filesystem corruption, malicious tampering). **Signing, not encryption** — content remains plaintext markdown; signatures attest to authenticity.

### Rationale
- A real memory-poisoning incident during development demonstrated need beyond Layer 2 validation-on-read
- Validation-on-read catches format/structure issues; signatures catch content tampering after the write
- Intended signing scheme: HMAC with session-derived secret (symmetric, sufficient for single-user single-deployment). ⚠️ NOT IMPLEMENTED — no signing or verification code exists; only secret generation ships.
- Ed25519 with offline key (asymmetric verification, higher integrity assurance) is not implemented in this edition

### Sound reasoning
- Production memory systems with audit trails commonly use HMAC at minimum
- Ed25519 is the modern standard for offline-key + asymmetric verification (RFC 8032)
- HMAC-SHA256 is sufficient for tamper detection within a single deployment with shared secret
- Both require crypto libraries not in Claude Code default toolkit at T0 (hence T3 gate via Code Exec)
- Ideal-first design philosophy: design-in NOW with T3 gate, activate when Code Exec unblocks — no re-architecture later

### Scope — CAN
- Sign every memory entry on write (entry body + frontmatter `content_sha256`)
- Verify signature on every read (intended; Layer 6 is NOT IMPLEMENTED, so no verification occurs)
- Detect tampering and route to Layer 2 quarantine (failed verification = automatic quarantine)
- Rotate signing keys without invalidating old entries (signature scheme includes key-id; verify-only with old keys retained)
- Attach signatures to audit log entries (chain-of-custody for B1)
- Operate with an in-memory secret (HMAC) — designed, NOT implemented; offline private-key signing (Ed25519) is likewise not implemented

### Scope — CANNOT
- Encrypt content (this is signing, not encryption)
- Provide non-repudiation in a meaningful sense (single-user deployment; no third party to repudiate to)
- Operate without Code Execution (T3 gate)
- Replace OS-level disk encryption
- Detect tampering BEFORE the entry is read (only on read; quarantine catches it)

### Active features in the current release
- **DESIGNED-IN, DORMANT at T0.** Schemes specified; activation gated by Code Exec (T3).
- Intended default signing scheme: HMAC-SHA256 with session-derived secret (NOT IMPLEMENTED)
- Ed25519 with offline key (RFC 8032) is not implemented in this edition
- Both schemes would integrate with `SCHEMA_A18` (`signature` field is RESERVED; nothing writes it)

### Deployment tier
- **T3** minimum (Code Exec for crypto libraries)

### Cross-references
- C4 (cryptographic signatures designed-in)
- `SCHEMA_A18` §content_sha256 (integrity check; complementary to Layer 6 signature which is authenticity check)
- `SCHEMA_audit_log.md` (signatures chain audit entries)

---

## 11. Cross-Layer Concerns

### 11.1 Sub-Agent Architecture (reference example)

Out-of-scope for memory stack design (orchestration is a separate layer of the broader agent architecture), but referenced here for completeness — the reference 4-agent example:

- **Warden** (security) — pre-vetting context, posture reports, incident response
- **Sentinel** (vetting) — pre-installation tool/skill review
- **Vault** (memory) — read/write to Layer 1 memory artifacts
- **Clerk** (PM) — kanban + daily activity log

**Memory stack interaction:** Sub-agents read/write through Layer 1 (vault) and Layer 2 (audit). Each entry's `source_agent` field (SCHEMA_A18) records attribution. Audit log captures sub-agent activity.

**Cross-reference:** the consuming architecture's orchestration rules (a sibling layer; out of memory stack scope).

### 11.2 Edition Profiles

The same Layer 0–6 architecture applies to any edition; `PROFILE.md` selects per-deployment configuration:

| Layer Concern | Default |
|---------------|---------|
| Compliance preset (B7) | `none` (overridable to enterprise/custom) |
| Audit log (B1) | OPT-IN (configurable) |
| Delete semantics | Hard delete |
| Quarantine UX | One-line approval toast at session start |
| Pattern-key recurrence (B6) | ≥5 |
| Cryptographic signatures (C4) | NOT IMPLEMENTED (HMAC intended) |

Override-file mechanism: edition-specific overrides at `<edition>/overrides/X.override.md` REPLACE sections of `common-specs/X.md` of the same name.

### 11.3 Deployment-Tier Markers

Every feature carries a tier marker. Features auto-activate when tier unblocks — no re-installation needed.

| Tier | Infrastructure | Features Activated |
|------|----------------|--------------------|
| **T0** | None (Claude Code default) | All Tier A (20) + most Tier B (~10) = ~30 features |
| **T1** | + Ollama (local embeddings) | + Hybrid search (B9), pattern-key embeddings ≈ 32 features |
| **T2** | + Node.js | + Hook automation (B12), file-watcher, C9 Transformers.js embeddings ≈ 34 features |
| **T3** | + Code Execution unblocked | + Python analytics, sandboxed jobs (crypto signatures C4 are NOT IMPLEMENTED) |
| **T4** | + Skills + Anthropic Dreaming beta | + Dreaming (C1), skill-packaged artifacts (C10) ≈ 42 features (full ideal state) |


### 11.4 Single-Source Storage (Layer 1 authority)

**Inviolable rule:** Layer 1 (markdown vault) is the only source of truth. Any data that doesn't exist in Layer 1 doesn't exist in the system.

- Layer 3 (hybrid search) — index, not store. Rebuild from Layer 1.
- Layer 5 (graph backend) — index, not store. Rebuild from Layer 1.
- Layer 6 (signatures) — attestation, not store. Would sign Layer 1 entries; NOT IMPLEMENTED.
- Layer 4 (caching) — accelerator, not store. Cache misses fall back to Layer 1.

If any higher layer is wiped, the system reconstructs from Layer 1. **Layer 1 loss is unrecoverable; everything else is rebuildable.** This is what makes the architecture portable.

### 11.5 Adjacent Tools — Designed-In, Outside the 7-Layer Architecture Proper

Two Tier C items are **designed-in but NOT part of the 7-layer memory architecture**. They are adjacent tools that produce artifacts the memory stack can ingest, but they operate on a different domain (code, not memory entries):

#### C3 — Graphify (codebase structural knowledge graph)

**What it is:** Tree-sitter (**31 languages** as of v0.8.13 / May 18, 2026) AST extraction + NetworkX graph + Leiden community detection (via graspologic) + vis.js for visualization. Three-pass process: AST extraction (local, no LLM) → optional Claude subagents for docs/papers/images/videos (LLM API) → Leiden community detection (local). Produces `graph.html` (interactive visualization), `GRAPH_REPORT.md` (key concepts, surprising connections, suggested queries), `graph.json` (queryable, persistent). Optional exports: `.svg`, `.graphml` (Gephi/yEd), Obsidian vault, markdown wiki, Neo4j Cypher. **49.6k stars, MIT license** . **Multi-modal:** code + SQL + R + shell + docs + papers + images + videos (faster-whisper for audio/video transcription, audio never leaves machine). Operates on **codebase files**, not memory entries.

**Why adjacent and not a Layer:** Graphify analyzes **codebase structure**; our memory stack stores **agent memory facts**. Different scope. Graphify's output can be **ingested by Layer 1** as a source artifact (e.g., `memory/references/codebase_graph_2026-05-14.md`) — but Graphify is not a memory backend.

**Useful for:** bioinformatics codebases, NGS pipelines, and other large polyglot projects. Provides a code-knowledge-graph alongside the memory stack. Optional adjacent integration.

**Important nuance** (see §13): The TOOL is Tier C designed-in. The **marketing claim** ("71.5× / 499× fewer tokens" from LucasRosati's ClaudeCodeMemorySetup repo, also echoed in PyShine + GoPenAI articles) is a strawman benchmark — debunked, NOTHING borrowed from the number. We adopt Graphify the tool, not the inflated benchmark.

**Activation paths**:
- **Manual install (T3 — Code Execution / Python on local machine):** `uv tool install graphifyy` (PyPI package name: `graphifyy` with double-y) → `graphify install`. Python 3.10+ required. No Node.js needed.
- **Skill install (T4 — Skills enabled):** `graphify install` registers `~/.claude/skills/graphify/SKILL.md` with `/graphify` slash command. on deployments with Skills enabled, activation is one line; otherwise use the manual install path.
- **MCP server option (optional):** `python -m graphify.serve graphify-out/graph.json` runs as MCP stdio server for Claude Code MCP wiring. Complements Skill install.

**Supported AI assistants** (via Skill install): Claude Code, Codex, OpenCode, Cursor, Gemini CLI, GitHub Copilot CLI, VS Code Copilot Chat, Aider, OpenClaw, Factory Droid, Trae, Hermes, Kiro, Google Antigravity.

**Code privacy:** Code files processed locally via tree-sitter AST — file contents do not leave the machine for the code pass. Docs/papers/images/videos sent to the AI assistant's chosen model API (Claude/GPT/Gemini/Kimi/DeepSeek/Ollama/Bedrock — your choice). Audio/video transcribed locally with faster-whisper.

**Forks:** Active fork at `krshna-ai/graphify-codebase` (v6 branch) — same functionality, fork of safishamsi/graphify upstream.

**Source repo:** https://github.com/safishamsi/graphify (latest v8 branch, v0.8.13 PyPI tag).

#### C7 — Aider repo-map primitive

**What it is:** Tree-sitter + PageRank to surface the most "interesting" symbols in a codebase. The only deterministic always-fresh structural primitive in the surveyed cohort (no LLM dependency for the ranking).

**Why adjacent and not a Layer:** Same reasoning as Graphify — operates on code, not memory entries. Its output (a ranked list of code symbols) can be ingested as a Layer 1 reference artifact but doesn't structurally belong to the 7-layer memory architecture.

**Activation:** Code Execution + Aider integration (T3).

#### How adjacent tools interact with the memory stack

```
Codebase ──[C3 Graphify]──→ GRAPH_REPORT.md ──[Layer 1 ingestion]──→ memory/references/
Codebase ──[C7 Aider]────→ repo-map output ──[Layer 1 ingestion]──→ memory/references/
                                                       │
                                              (then Layer 3 + Layer 5
                                               can index normally)
```

The memory stack treats their outputs as ordinary source artifacts. No special integration needed — Layer 1 ingests anything you put in `memory/references/`.

### 11.6 Architecture Plug-In Modularity

The Ultimate Memory Stack is a **branded module**; the consuming Claude architecture (sub-agent topology) is **modular and pluggable**.

**Brand-protected (canonical):** stack name, layer structure (Layers 0–6), schemas, protocols, compliance preset system, deployment-tier markers, bi-temporal model, documentation discipline, detection patterns, edition profiles.

**Modular (consumer-pluggable):** `source_agent` attribution slots (standard + consumer-defined per SCHEMA_A18), sub-agent template structure (consuming architecture supplies templates), sub-agent coordination protocols (an orchestration concern).

**Reference example:** the reference Claude Code deployment uses 4 sub-agents (Warden, Sentinel, Vault, Clerk). This is the canonical *example*, not the canonical *enum*. Other deployments may use different agent topologies — the memory stack accepts whatever the consuming architecture registers at bootstrap.

**See dedicated doc:** `MODULARITY.md` for full plug-in pattern + reference architecture + variations + brand-protection mechanism.

---

## 12. Tier C Inventory — Designed-In, Dormant at T0

10 features present in the spec but require infrastructure to activate. All designed ideal-first (build for the ideal state); activate on tier unblock.

| ID | Feature | Min Tier | Layer | Activation gate |
|----|---------|----------|-------|------------------|
| **C1** | **Auto-Dream sleep-time consolidation** (Anthropic `dreaming-2026-04-21` beta) — offline async memory reorganization between sessions; replaces Letta sleep-time framing | T4 | 4 | Code Exec + Anthropic beta access |
| **C2** | **Graphiti temporal-fact graph (Kuzu embedded)** — bi-temporal facts, point-in-time queries, fact lineage. *Strongest single storage upgrade on the future roadmap.* | T3 | 5 | Code Execution |
| **C3** | **Graphify structural code graph** — Tree-sitter AST + NetworkX + Leiden community detection. Codebase-adjacent, optional. (See §11.5 — adjacent tool, not a layer.) | T2–T3 | adjacent | Code Exec + likely Node.js |
| **C4** | **Cryptographic memory signatures** — ⚠️ NOT IMPLEMENTED. HMAC with a session-derived secret is the intended default and Ed25519 offline-key signing the intended upgrade; neither exists in code. Only secret generation ships. | T3 | 6 | Code Execution |
| **C5** | **DGM-H self-improvement loop** | T4 | — | **DEFERRED to a future evolution layer (see §14)** |
| **C6** | **LLMLingua / LongLLMLingua prompt compression** on cached prefixes — ~40× compound discount (4× compression × 10× cache savings) | T3 | 4 | Code Exec + Python ML libs |
| **C7** | **Aider repo-map primitive** (Tree-sitter + PageRank) — only deterministic always-fresh structural primitive in the surveyed cohort. (See §11.5 — adjacent tool, not a layer.) | T3 | adjacent | Code Exec + Aider integration |
| **C8** | **LLM-as-judge auto-grading evals** — extends the manual eval harness with automated quality checks | T3 | cross-cutting | LLM-callable infrastructure |
| **C9** | **Transformers.js embeddings** — alternative semantic-search backend if Ollama (B9) isn't viable on a deployment | T2 | 3 | Node.js 18+ |
| **C10** | **Skill / template extraction pipeline** (`extract_skill.py`-style) — closes the promotion ladder: inline → decisions → standing rule → reusable skill | T3–T4 | cross-cutting | Code Exec; Skills unblock for full pipeline |

**Activation tier distribution:**
- **7 items unblock with Code Execution** (C1 partial, C2, C4, C6, C7, C8, C10)
- **2 items unblock with Node.js** (C3 partial, C9)
- **1 item unblock with Anthropic beta** (C1 full)
- **1 item unblock with Skills** (C10 full)

**C5 special note:** DGM-H (Darwin-Gödel Machine, Hawkins variant) self-improvement loop is **NOT** part of v4.0.0. It is a future evolution-layer initiative. The memory stack ships without it; it can be added later without re-architecture.

**Important: tools vs vendor benchmark claims.** Several Tier C items have peer-reviewed-or-not status. We adopt the **patterns and tools** that fit; we **do not cite vendor-published benchmark numbers** as authoritative (see §13 Tier D for the debunked-claims inventory). The standing rule: *"borrow ideas, not numbers."*

All Tier C features have schemas, layer assignments (or adjacent-tool callouts), and activation criteria specified. Activation = "tier unblocks + edition profile enables." No re-installation needed.

---

## 13. Tier D Exclusions — Documented Rationale

12 features evaluated and EXCLUDED from the current release + general distribution. Full rationale below.

### Critical framing: "Borrow ideas, not numbers"

**The most important distinction:** Several Tier D exclusions are **vendor benchmark numbers**, not the tools or patterns themselves. The standing rule:
- ✅ **Adopt the design** if it's sound and useful
- ❌ **Do NOT cite the vendor-published benchmark** as authoritative evidence

This is why some tools appear simultaneously in **Tier C (included)** and **Tier D (claims debunked)**:

| Item | Tool / pattern | Vendor benchmark claim |
|------|----------------|------------------------|
| **Graphiti** | C2 INCLUDED (Kuzu embedded backend, bi-temporal model) | D3 DEBUNKED: 94.8% / +18.5% improvements on LongMemEval / DMR — Zep vendor preprint, no peer review |
| **Graphify** | C3 INCLUDED (Tree-sitter + Leiden code-graph tool) | D5 DEBUNKED: "71.5× / 499× fewer tokens" from LucasRosati's ClaudeCodeMemorySetup — strawman baseline (compares against re-reading 126 source files per query, which Claude Code doesn't do) |
| **GraphRAG** (community-summary pattern) | C-equivalent INCLUDED (pattern captured) | D2 DEBUNKED: 9–43× cost reduction — Microsoft preprint v2 still "under review" on arXiv, no peer-review venue |
| **mem0** (3-modality concept, ADD/UPDATE/DELETE/NOOP) | B11 INCLUDED (hybrid retrieval pattern) | D1 DEBUNKED: 91.6 / 93.4 scores — vendor self-reported only |
| **Letta sleep-time** (replaced by C1 Auto-Dream framing) | C1 INCLUDED (Auto-Dream framing) | D4 DEBUNKED: 5× speedup — preprint + not designed for interactive sessions |

**The Awrshift critique** is on a DIFFERENT axis from Tier D — it documents OVER-ENGINEERED IMPLEMENTATIONS failing (300-line auto-pipeline lost context in ~50% of sessions due to laptop-lid kills, transcript parser issues, background subprocess failures). That critique applies to **how you wrap a tool**, not the tool itself. Stay simple and use tools appropriately.

### Tier D inventory summary

| Category | Count | What's excluded |
|----------|-------|------------------|
| **Vendor benchmark debunks (claims, not tools)** | 5 (D1–D5) | The NUMBERS — not the tools/patterns, which are individually in Tier A/B/C |
| **Already parked elsewhere in the 7-layer architecture** | 3 (D6–D8) | KV-cache compression papers, inference engines, RMT papers — belong to other layers of the broader agent architecture |
| **Wholesale-inappropriate (borrow patterns only)** | 3 (D9–D11) | ChatGPT consumer memory wholesale (UX patterns borrowed only); Cursor's removed Memories (LESSON borrowed → A19); Zep Community Edition (deprecated, replaced by Graphiti) |
| **Unverified claim** | 1 (D12) | "87% downstream contamination in 4 hours" — primary source not located. Do NOT cite. |

**These exclusions are NOT silent.** Each has a documented rationale. Future contributors can re-evaluate if circumstances change (e.g., vendor publishes peer-reviewed reproduction; an unverified claim gets confirmed by independent measurement).

**For adopters defending design choices:** D1–D12 are the "what we evaluated and chose not to include" record — answering the "why didn't you use mem0/GraphRAG/etc.?" question with evidence of careful curation.

---

## 14. Future — Evolution Layer (Out of Scope for the Current Release)

**DGM-H self-improvement loop** is a separate future initiative.

**What it would do:** A 6-script self-modifying memory system that improves itself between sessions — learning which memory patterns work, which conflict-resolution rules fire, which load-order tiers are too aggressive, etc.

**Why not now:** DGM-H scope is large enough to warrant its own roadmap. Including it in v4.0.0 would:
1. Block release on an unstable dependency (self-modifying systems require extensive testing)
2. Conflict with the "documentation discipline" mandate (self-modifying code is hard to document)
3. Introduce alignment + safety concerns (self-improving systems need robust guardrails)

**When picked up:** After the current release stabilizes. It becomes its own roadmap.


---

## 15. Status + Open Questions

**This architecture is stable.** The companion specs (`MEMORY_PROTOCOL.md`, `MEMORY_PROTOCOL_EXTENDED.md`, `SCHEMA_*.md`) and templates all ship alongside it. Remaining open questions are tracked here for future versions:

1. **Layer 4 caching scope** — should explicit Anthropic prompt-cache integration be designed-in (vs leaving to user discipline)? Likely yes.
2. ~~**Layer 5 graph backend choice** — Memgraph vs Neo4j vs lightweight in-memory~~ **CLOSED: Graphiti + Kuzu embedded** (zero infra overhead, bi-temporal model is audit/regulatory load-bearing). Graphiti is actively developed; **Kuzu is not — it is archived and frozen at 0.11.3**, retained because it is the only embedded backend that installs on every platform we support. Re-opened only if graphiti-core withdraws the driver. See §9.
3. **Layer 6 signature scheme defaults** — HMAC is the intended default and Ed25519 the intended upgrade; NEITHER is implemented (no signing or verification code exists). Key management UX is unresolved.
4. **Cross-layer sub-agent integration** — formal "Layer 7" or stay as cross-cutting concern? Currently cross-cutting (memory ≠ orchestration); revisit if real deployments surface integration friction.
5. ~~**C10 placeholder** — "Anthropic beta features TBD"~~ **CLOSED: C10 is the Skill / template extraction pipeline (extract_skill.py-style).** See §12.
6. **Wiki-link parser automation** — at T0–T1, inline `[[ID]]` ↔ YAML `related` sync is manual. At T2+ (Node.js), automated parser. Should the parser be a hard requirement at T2, or remain opt-in?
7. **Bi-temporal default behavior** — B5 is "available, not required". Should `valid_at` default to `created_at` automatically, or be omitted unless explicitly set? Lean: auto-default to `created_at` (zero friction).
