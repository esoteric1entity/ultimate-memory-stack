# Ultimate Memory Stack — Bootstrap Prompt

> **File:** `common-specs/BOOTSTRAP_PROMPT.md`
> **Status:** stable — ships with UMS v4.0.0, alongside the companion files (MEMORY_PROTOCOL.md + MEMORY_PROTOCOL_EXTENDED.md + schemas)
> **Authors:** see /AUTHORS.md
>
> Version history lives in [`CHANGELOG.md`](../CHANGELOG.md).

---

## Design Model — Referencing Bootstrap

> The activation prompt is short by design; capabilities live in companion files in `common-specs/`, with edition-specific overrides applied via the active edition's profile. (This replaced an earlier single-paste monolith: the feature surface — audit log, quarantine, signatures, per-project memory banks, edition profiles, tier gates — is too large for one prompt, and the referencing model lets schemas evolve independently.)

### Feature inventory by tier (54 reviewed: 32 active, 10 designed-in, 12 excluded)

**Tier A — Foundation (20 features, all active at T0+):**
- Per-entry YAML frontmatter (SCHEMA_A18) — replaces v2.0 inline confidence tags
- Per-project memory bank (SCHEMA_A3) — Cline 6-file convention under `memory/projects/<slug>/memory-bank/`
- Layered architecture (Layer 0–6 with deployment-tier markers T0–T4)
- Documentation discipline — every feature carries purpose + rationale + reasoning + scope (CAN/CANNOT)
- Pattern-key promotion (Letta-style recurrence counter)
- Validation-on-read with quarantine fallback
- Content-addressable concurrency (CAS via `content_sha256` for replace-class operations)
- **Obsidian-vault compatibility by design** — open `memory/` in Obsidian; wiki-links, frontmatter, graph view all work
- 13 more — see ARCHITECTURE.md for the full Layer 0–6 inventory

**Tier B — Conditional / per-edition (12 features):**
- **B1 Audit log** — OPT-IN by default; required under strict compliance presets (JSONL append-only)
- **B2 Quarantine workflow** — `/audit-quarantine` review, surfaced via one-line toast
- **B3 CAS concurrency** — scoped to replace-class operations (str_replace, insert)
- **B4 Override-file convention** — `.override.md` shadow-files (engine behind edition profiles)
- **B5 Bi-temporal annotations** — `valid_at` / `invalid_at` in SCHEMA_A18. Available (may be enforced by compliance preset). Enables point-in-time queries ("what did we believe on date X?"). Markdown-now, Graphiti-backed-later.
- **B6 Pattern-key recurrence** — ≥5 (suggest to user)
- **B7 Compliance preset hybrid ⭐** — presets: `none` / `enterprise` + `custom` override (GDPR/SOC2/PCI-DSS). HIPAA/PHI is out of scope for this edition.
- **B8 Memory poisoning defenses** — provenance, validation-on-read, quarantine, optional signatures
- **B9 Local semantic search via Ollama** — opt-in; privacy-friendly; T1+
- **B10 Embedding-cache as derived index** — required architecture (`memory/.index/`, gitignored, regenerable)
- **B11 Hybrid retrieval** — semantic + BM25 + entity (mem0 pattern); v2.2 opt-in; depends on B9 + B10
- **B12 Error-detector hook** — PostToolUse hook; designed-in now, activates when Node.js (T2) unblocks

**Tier C — Designed-in for ideal state (10 features, activate with deployment-tier unblocks):**
- **C1 Auto-Dream sleep-time consolidation** — Anthropic `dreaming-2026-04-21` beta. Offline async memory reorganization. Activates: Code Exec + Anthropic beta (T4).
- **C2 Graphiti temporal-fact graph (Kuzu embedded) ⭐** — bi-temporal facts, point-in-time queries, fact lineage. Apache 2.0, zero-infra Kuzu backend; the strongest single storage upgrade, especially for regulatory/provenance use cases. Activates: Code Exec (T3).
- **C3 Graphify structural code graph** — Tree-sitter AST + Leiden community detection for **codebase** structure (not memory entries; adjacent tool, see ARCHITECTURE.md §11.5). Optional. Activates: Code Exec + Node.js (T2–T3).
- **C4 Cryptographic memory signatures** — ⚠️ NOT IMPLEMENTED. HMAC with a session-derived secret is the intended scheme; no signing or verification code exists. Do not report this layer as active.
- **C5 Self-improvement loop — deferred to a future evolution layer** (not in this release)
- **C6 LLMLingua / LongLLMLingua prompt compression** — ~40× compound discount on hot cached prefixes. Activates: Code Exec + Python ML libs (T3).
- **C7 Aider repo-map primitive** (Tree-sitter + PageRank) — deterministic always-fresh code-structure ranking; adjacent tool (see §11.5). Activates: Code Exec + Aider integration (T3).
- **C8 LLM-as-judge auto-grading evals** — extends the manual eval harness with automated quality checks. Activates: LLM-callable infrastructure.
- **C9 Transformers.js embeddings** — alternative semantic-search backend if Ollama (B9) isn't viable. Activates: Node.js 18+ (T2).
- **C10 Skill / template extraction pipeline** (`extract_skill.py`-style) — closes promotion ladder: inline → decisions → standing rule → reusable skill. Activates: Code Exec; full pipeline needs Skills.

**Tier D — Explicitly excluded (12 items):**

**Critical:** Several Tier D items debunk **vendor benchmark NUMBERS**, not the tools/patterns themselves. The standing rule: *"borrow ideas, not numbers."* Tools like Graphiti (C2), Graphify (C3), and mem0's 3-modality concept (B11) are INCLUDED; their vendor-published benchmark claims are NOT cited as authoritative. See ARCHITECTURE.md §13 for the tool-vs-claims distinction.

### Core operational features (carried forward from the original stack)
- session_state.md as lifeline
- Adaptive context loading (Tier 1/2/3)
- Tiered context budget (≤15% / ≤30% / ≤45%, ≥25% reserved, 40% ceiling)
- 9-level conflict resolution hierarchy
- Risk scoring rubric (6-factor MAX-score)
- Cascade failure detection (3 errors / 5 min → STOP)
- Self-test suite (T1–T7 in v2.0; expanded to T1–T9 in v3.0 per MEMORY_PROTOCOL.md §1.3)
- Self-trimming protocol (every 10 sessions, suggestions-only)
- Decision promotion pattern (inline → decisions.md at >5)
- Heartbeat checkpoint (~30 min)
- Compliance preset system (B7: `none` / `enterprise` / `custom`) — HIPAA/PHI is out of scope for this edition
- Schema versioning

---

## Deployment Instructions

### Prerequisites
- A capable agent harness — Claude Code is the reference example; OpenClaw and any 9-root-file harness also work (see `INSTALL_AGENT.md`). The script and manual doors need no agent at all.
- Working directory selected (where the memory system will live)
- This package ships the **general-edition**. HIPAA/PHI is out of scope for this edition.

### Steps
1. **Copy the stack package** into your working directory as `ultimate-memory-stack/`, containing:
   - `common-specs/` — universal files (this is the shared 95%)
   - `general-edition/` — the edition shipped in this package. HIPAA/PHI is out of scope for this edition.
2. **Open your agent harness** in your working directory (e.g. Claude Code, OpenClaw, or any 9-root-file agent)
3. **Paste the activation prompt** below
4. **Answer the setup-wizard questions** (general-edition confirmation, user profile, project list, compliance preset)
5. **Verify**: your agent runs the self-test suite and reports any failures
6. **At end of every session**: tell your agent "update session state" or "wrap up"
7. **At start of every session**: your agent auto-loads memory and resumes (no prompt needed) — on Claude Code via `.claude/rules/memory_protocol.md`; other harnesses load it per their rules mechanism (see `INSTALL_AGENT.md`)

> **First-time users:** Read `USER_CHEAT_SHEET_core.md` first. It walks through the universal best practices for working with persistent-memory AI systems (slash commands, /compact timing, anti-patterns). Then read `general-edition/USER_CHEAT_SHEET_general_addendum.md` for edition specifics.

---

## The Activation Prompt

```
You are deploying the Ultimate Memory Stack v4.0.1 in this working directory.

The complete spec lives in `ultimate-memory-stack/common-specs/` plus the general-edition profile in `ultimate-memory-stack/general-edition/`. Read those files for full detail. This prompt is the activation entry point — it doesn't duplicate the schemas, it activates them.

---

### Step 1 — Confirm Edition

This package ships the **general-edition**. Confirm with me: "Deploying the general-edition in this directory — confirm?"

Wait for my answer. Then load `ultimate-memory-stack/general-edition/PROFILE.md` to determine which common-spec sections are active, which overrides apply, and which compliance preset is in effect.

Ask "Which compliance preset — none, enterprise, or custom?" Save the answer to my user profile.

If `custom`: ask which regulations apply — GDPR, SOC2, PCI-DSS. HIPAA/PHI is out of scope for this edition.

---

### Step 2 — Verify Directory Structure

Confirm or create the following structure (this is the common spec; edition profiles may add subdirectories):

```
.claude/
  rules/
    memory_protocol.md           ← Auto-loaded each session (copy from ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md)
memory/
  MEMORY_PROTOCOL_EXTENDED.md    ← On-demand reference (never auto-loaded — see .claude/rules/ above)
  MEMORY_INDEX.md                ← Master registry (per ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md §Index)
  sessions/
    session_state.md             ← Lifeline file (per SCHEMA_A18 entry format)
  user/
    user_profile.md              ← Who you're working with
  decisions/
    decisions.md                 ← Settled choices with confidence levels
  projects/                      ← One subdir per project (SCHEMA_A3)
    <slug>/
      memory-bank/               ← Cline 6-file convention
        projectbrief.md
        productContext.md
        systemPatterns.md
        techContext.md
        activeContext.md
        progress.md
  feedback/
    feedback.md                  ← User corrections that should change my behavior
  security/
    vetting_log.md               ← Audit trail
    audit_log.jsonl              ← If audit log enabled (B1)
  references/
    references.md                ← File location pointers
  archive/                       ← Superseded content
  quarantine/
    quarantine_log.jsonl         ← If quarantine enabled (B2)
ultimate-memory-stack/           ← The spec itself, read-mostly during operation
  common-specs/                  ← Universal schemas + protocol + architecture
  general-edition/               ← The active edition shipped in this package
```

---

### Step 3 — Apply the Memory Protocol

Read `ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md`. It contains the operational rules: when to load files (Tier 1/2/3), context budget, conflict resolution hierarchy, file size limits, standing rules, risk scoring, cascade failure detection, self-test suite. Do not duplicate that file's content here — load it and follow it.

Copy `MEMORY_PROTOCOL.md` to `.claude/rules/memory_protocol.md` so Claude Code auto-loads it each session. Also copy `MEMORY_PROTOCOL_EXTENDED.md` to `memory/MEMORY_PROTOCOL_EXTENDED.md` — on-demand reference detail, **never** `.claude/rules/` (that would auto-load it every session and recreate the eager-load cost the CORE/EXTENDED split fixes). (OpenClaw and other harnesses register the protocol via their own rules/bootstrap mechanism — see `INSTALL_AGENT.md` and `core/openclaw-adapter/`.)

---

### Step 4 — Apply Edition Profile + Overrides

Read `ultimate-memory-stack/general-edition/PROFILE.md`. It declares:
- Which common-spec features are active (e.g., audit log: required vs opt-in)
- Compliance preset (`none` / `enterprise` / `custom`; HIPAA/PHI is out of scope for this edition)
- Override-file map — each line says "override file X applies override Y" (the B4 override-file convention)
- Pattern-key recurrence threshold (general ≥5)
- Cryptographic signature scheme (HMAC intended — NOT IMPLEMENTED)
- Audit log retention policy
- Quarantine UX pattern (one-line toast)

Apply each `.override.md` file listed in PROFILE.md. The override pattern: if `ultimate-memory-stack/common-specs/X.md` and `ultimate-memory-stack/general-edition/overrides/X.override.md` both exist, the override's sections REPLACE the common-spec's sections of the same name (other sections inherit).

---

### Step 5 — Apply Schemas

Read all schema files in `ultimate-memory-stack/common-specs/`:
- `SCHEMA_A3_per_project_memory_bank.md` — per-project memory bank structure
- `SCHEMA_A18_per_entry_metadata.md` — YAML frontmatter for every memory entry
- `SCHEMA_audit_log.md` — JSONL audit log format (B1)
- `SCHEMA_quarantine.md` — quarantine queue + release workflow (B2)
- `SCHEMA_compliance_profile.md` — 3-preset compliance hybrid + custom (B7)

Every new memory entry MUST carry SCHEMA_A18 frontmatter (id, created_at, source_agent, pattern_key, recurrence_count, confidence, status, content_sha256, etc.). Use the schema's worked example as a template.

---

### Step 6 — Initialize Memory Vault

If `memory/` is empty (first deployment):
1. Create directory structure (Step 2)
2. Initialize `memory/sessions/session_state.md` with Session 1 — Initial Setup (include Schema Version: 3.0)
3. Initialize `memory/MEMORY_INDEX.md` with empty counts
4. Run the setup wizard (Step 7) to populate `user_profile.md` and `project_context.md`

If `memory/` exists (upgrading from v2.0):
1. Detect schema version of existing files
2. Migrate per `ultimate-memory-stack/general-edition/MIGRATION_v2_to_v3.md` (separate file) — adds YAML frontmatter to existing entries, restructures projects into per-project subdirs
3. Preserve all FINAL decisions, security entries, user profile, standing rules — these survive any migration
4. Tell me the migration plan BEFORE executing. Wait for approval.

---

### Step 7 — Setup Wizard (first deployment only)

Ask me these questions in order. Save my answers to the indicated files:

1. **Identity** (→ `user/user_profile.md`)
   - Name + role + organization
   - Primary tech stack / languages / frameworks
   - Domain (biotech R&D? data science? web dev? other?)
   - How do I prefer responses (brief vs detailed, technical level)?

2. **Active Projects** (→ `projects/<slug>/memory-bank/projectbrief.md` per project)
   - List active projects (1 per line, brief description each)
   - For each: high-level goal + current status

3. **Compliance** (→ `user/user_profile.md` + active compliance profile)
   - Compliance preset: none / enterprise / custom
   - If `custom`: which regulations apply (GDPR, SOC2, PCI-DSS)?
   - HIPAA/PHI is out of scope for this edition.

4. **Pet Peeves** (→ `feedback/feedback.md` as initial entries — the canonical location)
   - Anything you should NEVER do
   - Anything you should ALWAYS do
   - Common AI behaviors you find annoying

   These become FB-NNN entries with pattern_key. Do NOT also place them in `user/user_profile.md` — feedback.md is the single source of truth.

5. **Consumer Agent Topology** (→ `user/user_profile.md`)
   - What sub-agent names will be using this memory stack? (e.g., warden / sentinel / vault / clerk for orchestrated setups; or "none" if no sub-agents)
   - These names register as valid `source_agent` slots in SCHEMA_A18 frontmatter. Standard slots (`user`, `orchestrator`, etc.) always available.

6. **Deployment Tier** (→ saved internally for tier-gate decisions)
   - Code Execution: enabled or blocked?
   - Node.js available: yes or no?
   - Skills: enabled or blocked?
   - Anthropic beta access: enabled or none?

   Some Tier C features auto-activate based on these answers; others stay designed-in but dormant.

---

### Step 8 — Run Self-Test

Per `MEMORY_PROTOCOL.md §Self-Test`, run T1–T9 silently. Only report failures.

If T1 fails (no session_state.md): CRITICAL — stop.
If T7 fails (PII/PHI detected): CRITICAL — refuse to load the affected file.
If T8 fails (invalid SCHEMA_A18 frontmatter on any entry): WARNING — flag affected entries.
If T9 fails (edition profile / override map doesn't resolve): WARNING — fall back to common-specs defaults.
Other failures: warn but proceed.

---

### Step 9 — Greet and Orient

Brief greeting:
- Confirm edition deployed
- Confirm compliance preset active
- Summary of what was scaffolded (X files created / verified)
- "Where would you like to start? Try `/help` or ask me about your projects."

If migrating from v2.0: also list what changed (new frontmatter, new per-project memory bank, new audit/quarantine/signature options).

---

### Ongoing Operation

After bootstrap, the system runs on `MEMORY_PROTOCOL.md` rules (auto-loaded every session). Bootstrap is one-time. You don't paste this prompt again.

When I say "update session state" / "wrap up" / "save state" / "end session" — execute the Session End protocol in MEMORY_PROTOCOL.md.

When I ask about a project, load its memory-bank (Tier 2).
When I correct you, append to feedback.md and apply immediately.
When we make a technical decision, append to decisions.md with confidence level + DEC-### id if it's significant enough to track.
When 30 min passes during active work, heartbeat to session_state.md.
When errors cascade (3 unrelated in 5 min), STOP and report.

That's the contract. Everything else is in the protocol + schemas.
```

---

## What's in the Box — Feature Inventory

Full inventory in `ARCHITECTURE.md` (Layer 0–6, with tier markers). Quick summary:

| Tier | Count | Status | Where Documented |
|------|-------|-----------------|-------------------|
| **A — Definite include** | 20 | All active at T0 (no infra needed) | ARCHITECTURE.md |
| **B — Conditional include** | 12 | Per-edition configuration via PROFILE.md | ARCHITECTURE.md + SCHEMA files |
| **C — Designed-in, tier-gated** | 10 | Schema present, activates at tier unblock | ARCHITECTURE.md (T-markers) |
| **D — Excluded / borrow-only** | 12 | NOT present (with rationale) | documented exclusion rationale (ARCHITECTURE.md §13) |
| **Future evolution layer** | 1 (C5) | NOT in this release — separate future initiative | roadmap |

**Total feature surface: 42 active or designed-in (Tier A 20 + Tier B 12 + Tier C 10).**

---

## Deployment Tier Compatibility

The stack is designed for the **ideal state**. Features are tagged with the deployment tier they require:

| Tier | What's Available | Features Active at This Tier |
|------|-------------------|------------------------------|
| **T0** | Anywhere (current Claude Code default) | All Tier A (20) + most Tier B (~10) — ~30 features |
| **T1** | + Ollama (local embedding model) | + Hybrid search (B9), pattern-key embeddings — ~32 features |
| **T2** | + Node.js | + Hook-based automation (B12), file-watcher patterns — ~34 features |
| **T3** | + Code Execution unblocked | + Python-backed indexing, sandboxed analytics (cryptographic signatures C4 are NOT IMPLEMENTED) |
| **T4** | + Skills + Anthropic Dreaming beta | + Dreaming (C1), skill-based memory artifacts — ~42 features (full ideal state) |

**Worked example:** a locked-down workstation with Code Execution / Skills / Node.js all blocked lands at T0 — and still runs ~30 features.

> **Important:** Tier C features designed-in but dormant. They become active automatically when the deployment tier unblocks — no re-installation needed. This is the value of "build for ideal state, gate by tier."

---

## Documentation Discipline (Standing Rule)

Every feature carries explicit documentation:

- **Purpose** — what this feature is for (the user-facing goal)
- **Rationale** — why we chose this approach over alternatives (the design argument)
- **Sound reasoning** — the chain of evidence + research findings backing the design
- **Scope (CAN / CANNOT)** — explicit boundaries: what this feature does AND does not do

This applies to every common-spec section, every schema, every edition override, every tier-C designed-in component. **No undocumented features ship.**

If someone asks "why does the memory stack do X?" or "why doesn't it do Y?" — the answer is in writing, traceable to a recorded design decision and research source.

See `ARCHITECTURE.md` for the template + worked examples.

---

## Migration from v2.0 → v3.0

> Detailed migration steps live in the edition's `MIGRATION_v2_to_v3.md`. Brief summary:

1. **Pre-flight check**: backup `memory/` directory before starting
2. **Add YAML frontmatter** to existing entries (A18 schema) — automation-script available at T2+ (Node.js)
3. **Restructure projects** — move per-project content into `memory/projects/<slug>/memory-bank/` (A3 schema)
4. **Add new directories**: `audit_log.jsonl` (if enabling B1), `quarantine/` (if enabling B2)
5. **Update protocol**: copy `ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md` v3.0 over `.claude/rules/memory_protocol.md`
6. **Re-run self-test**: verify migration succeeded

**Backward compatibility:** v2.0 memory files without YAML frontmatter are treated as legacy entries with implicit `confidence: FINAL`, `status: active`, `created_at: <file-mtime>`. They continue to work; new entries get the full frontmatter.

**Migration is non-destructive.** All v2.0 content survives. Schema upgrade is purely additive.

---

## Open Questions

Tracked for future refinement, not resolved in this bootstrap:

1. **MIGRATION_v2_to_v3.md** — automation script vs manual procedure for adding frontmatter; do we need a one-time migration agent?
2. **Override-file precedence** — what if multiple edition override files exist (multi-edition deployment)? Edge case, but spec needs to handle it.
3. **First-run vs upgrade detection** — bootstrap currently asks the user. Could auto-detect from presence of `memory/MEMORY_INDEX.md` with Schema Version header. Tradeoff: less prompting vs less explicit.
4. **Compliance preset selection UX** — for `general`, should it default to `none` or prompt-on-first-use? Currently prompts at Step 7.
5. **Tier-detection auto-discovery** — Step 7 question 5 is manual. Could probe (e.g., try `node --version`, try Code Execution call). Deferred.

---

## Status

**Stable — ships with UMS v4.0.0.** The companion files carry the detail this bootstrap references:
- ARCHITECTURE.md — Layer 0–6 details + tier markers
- MEMORY_PROTOCOL.md — Tier 1/2/3 loading + conflict resolution + self-test (CORE, auto-loaded)
- MEMORY_PROTOCOL_EXTENDED.md — full rationale, tables, and mechanics behind the CORE rules (on-demand, never auto-loaded)
- The runtime schemas — entry formats, audit log, quarantine, compliance profiles
- templates/ — instantiation examples

This bootstrap is a living document: it gets refined whenever a companion file exposes a gap. Version history lives in `CHANGELOG.md`.

