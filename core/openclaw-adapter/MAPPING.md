# v3.0/v3.5 ↔ OpenClaw Convention Mapping

> **Doc:** `core/openclaw-adapter/MAPPING.md`
> **Purpose:** Codify the exact mapping between Ultimate Memory Stack v3.6.0/v3.5 conventions and OpenClaw harness conventions. This is the reference doc for `SKILL.md` Step 4 + `setup-openclaw.sh/py`.
> **Foundation:** the OpenClaw general-edition design notes (internal R&D) + the cross-harness convergence contract
> **Last updated:** 2026-05-28

---

## §1 — File Mapping (9 Root Auto-Load Files)

OpenClaw expects 9 root files at `<openclaw-root>/`. The adapter generates each, mapped to a v3.0/v3.5 concept:

### 1. MEMORY.md ← MEMORY_INDEX.md

**Purpose:** Master pointer index. Browseable summary of all memory categories with pointers to detail files.

**v3.0/v3.5 source:** `<working-dir>/memory/MEMORY_INDEX.md`

**OpenClaw expectations:**
- Loaded into Tier 1 / HOT context every session
- Should fit ~5K characters
- Pointers (not full content) — actual entries live in detail files

**Adapter behavior:**
- Generates a fresh MEMORY.md skeleton with category headers
- User (or auto-populator) fills in pointer entries as memory grows
- Heartbeat compactor (`scripts/heartbeat_compactor.py`) updates MEMORY.md when entries are archived

**Frontmatter (file-level scope per SCHEMA_A18 v1.3):**
```yaml
---
scope: file
file_type: master_index
purpose: "Master pointer index for all memory entries"
loaded_when: bootstrap
schema_version: "3.0"
edition: general
adapter_version: "1.0"
---
```

---

### 2. AGENTS.md ← .claude/rules/agent_orchestration.md

**Purpose:** Agent topology + spawning rules + parallel/sequential constraints.

**v3.0/v3.5 source:** `.claude/rules/agent_orchestration.md` (Warden/Sentinel/Vault/Clerk flat hierarchy)

**OpenClaw expectations:**
- Loaded into Tier 1 / WARM context every session
- ~6K characters
- Describes agent topology that the harness can act on

**Adapter behavior:**
- Ports the 4-peer hierarchy SPEC verbatim
- Marks Warden/Sentinel/Vault/Clerk as **advisory** in OpenClaw runtime (until OpenClaw supports peer-agent spawning — Phase 4+ research)
- Reserves space for OpenClaw-native agent equivalents (Meta Hyperagents lineage) that user may add

**Note:** This is a known limitation of v3.5 — full agent topology execution requires Claude Code. OpenClaw users get the protocol spec but execute the agents manually or via OpenClaw's own subagent equivalents.

---

### 3. SOUL.md (NEW) — distilled FINAL principles from decisions.md

**Purpose:** Identity-stable standing principles that don't change session-to-session. Replaces the "agent self-image" pattern from a peer OpenClaw deployment with a v3.5-native convention.

**v3.0/v3.5 source:** synthesized from `memory/decisions/decisions.md` FINAL entries with `confidence: 1.0` and tag `standing-principle`

**OpenClaw expectations:**
- Loaded into Tier 1 / HOT context every session
- ~5K characters
- Concise principles, not detailed reasoning (reasoning lives in DEC entries)

**Adapter behavior:**
- Initial SOUL.md ships with 6-10 candidate principles distilled from v3.0/v3.5 FINAL DECs:
  - **DEC-001:** Security-first tool installation
  - **DEC-020:** Mirror discipline (canonical copy ↔ mirror copy kept in parity)
  - **DEC-021:** Ideal-first design (cleanest topology before compromise)
  - **DEC-023:** Documentation discipline (purpose/rationale/scope CAN/CANNOT mandatory)
  - **DEC-030:** Borrow ideas, not numbers
  - **DEC-032:** Karpathy Lint surface-only
  - **DEC-031:** Modular consumer architecture
  - **DEC-046:** Convergence is signal (independent agreement on patterns is the strongest validation)

**Content type:** principles, NOT rules-as-code. SOUL.md says "WHAT we believe"; AGENTS.md says "HOW we act on it."

---

### 4. TOOLS.md ← TIER_C_ACTIVATION.md + recommended-addons/ pointers

**Purpose:** Addon registry — lists installed addons, their activation status, and how to invoke them.

**v3.0/v3.5 source:** `common-specs/TIER_C_ACTIVATION.md` + per-addon installer Skills under `recommended-addons/`

**OpenClaw expectations:**
- Loaded into Tier 1 / WARM context every session
- ~5K characters
- Surfaces "what's installed" for the harness to make routing decisions

**Adapter behavior:**
- Generates TOOLS.md with addon table:
  ```markdown
  | Addon | Status | Installer Skill | Vetting |
  |---|---|---|---|
  | LLMLingua | [installed | not installed] | /install-llmlingua | VET-011 PASS |
  | Graphiti | [installed | not installed] | /install-graphiti | VET-010 PASS |
  | Graphify | [installed | not installed] | /install-graphify | VET-009 PASS |
  | Obsidian | [installed | not installed] | /config-obsidian-vault | n/a (config-only) |
  ```
- Status updated by each addon's installer Skill on completion (Step 6 of LLMLingua, etc.)

---

### 5. IDENTITY.md ← user_profile.md (PII-redacted for general-edition)

**Purpose:** User profile — who the harness is working with.

**v3.0/v3.5 source:** `memory/user/user_profile.md`

**OpenClaw expectations:**
- Loaded into Tier 1 / HOT context every session
- ~3K characters (compact, not the maintainer's full profile)
- General-edition: PII-redacted by default

**Adapter behavior:**
- General-edition `compliance: none` → ships the maintainer's basic identity (role, domains, machine inventory) with sensitive fields ([email], [phone]) redacted as placeholders user fills in
- General-edition `compliance: enterprise` → additional GDPR/SOC2-aligned redaction (e.g., no SSN, no financial account IDs)
- Healthcare preset → NOT activated for general-edition (would require biotech-edition adapter)

**Sanitization rule:** any field tagged `pii: true` in the source user_profile.md gets replaced with `[REDACTED — user-configurable]` in IDENTITY.md.

---

### 6. USER.md ← feedback.md (recent + standing rules)

**Purpose:** User corrections + preferences + standing rules promoted from recurring feedback.

**v3.0/v3.5 source:** `memory/feedback/feedback.md`

**OpenClaw expectations:**
- Loaded into Tier 1 / WARM context every session
- ~5K characters
- Shows recent corrections + promoted standing rules

**Adapter behavior:**
- Ships USER.md template with two sections:
  - **Recent feedback (last 5 sessions):** rolling window of FB entries
  - **Standing rules (promoted patterns):** patterns with `recurrence_count >= 5` per general-edition threshold (per MEMORY_PROTOCOL §4.2 + B6)
- Heartbeat compactor rotates feedback older than 5 sessions to `memory/feedback/archive/`

---

### 7. HEARTBEAT.md ← session_state.md (current heartbeat + rolling history)

**Purpose:** Active heartbeat per MEMORY_PROTOCOL §4.4 — captures current state for compaction-safe handoff.

**v3.0/v3.5 source:** `memory/sessions/session_state.md` current "Current Work" + last 3 heartbeats

**OpenClaw expectations:**
- Loaded into Tier 1 / HOT context every session
- ~5K characters
- Rolling 3-deep history (current + last 2)

**Adapter behavior:**
- HEARTBEAT.md starts with template heartbeat (this Skill's Step 4 instantiates)
- During session, user (or Claude) appends heartbeats every ~30 min per MEMORY_PROTOCOL §4.4
- Heartbeat compactor archives oldest heartbeat when 3-deep window exceeded
- Critical for `/compact`-safe handoff — per MEMORY_PROTOCOL §15

---

### 8. BOOTSTRAP.md ← session_state.md (next-actions section)

**Purpose:** Where to pick up + immediate next actions for next session.

**v3.0/v3.5 source:** `memory/sessions/session_state.md` "Next session entry-point" section

**OpenClaw expectations:**
- Loaded into Tier 1 / HOT context every session
- ~4K characters
- Concise: top 3-5 next actions + key context

**Adapter behavior:**
- Updated at session-end per MEMORY_PROTOCOL §14
- Heartbeat compactor doesn't touch BOOTSTRAP.md (updated only by session-end)

---

### 9. DREAMS.md (NEW for v4.0 — placeholder in v3.5)

**Purpose:** Auto-Dream offline consolidation output. Placeholder file ships empty in v3.5; populated when Anthropic Dreaming beta enables Phase 4+ candidate #2.

**v3.0/v3.5 source:** none yet (v4.0 candidate)

**OpenClaw expectations:**
- Loaded into Tier 1 / WARM context (lower priority than HOT)
- ~2K characters (empty placeholder in v3.5)
- File MUST exist (OpenClaw expects all 9 root files); content can be empty/placeholder

**Adapter behavior:**
- Ships DREAMS.md with placeholder content: "v3.5 placeholder — Auto-Dream not yet active. Activation is gated on Phase 4+ (Anthropic Dreaming beta)."

---

## §2 — Tier Mapping (Loading Semantics)

| v3.0/v3.5 Tier | OpenClaw Tier | Loading rule | Files involved |
|---|---|---|---|
| **Tier 1 (always)** | **HOT + WARM** | Bootstrap auto-load, unconditional | All 9 root files |
| **Tier 2 (on resume)** | **COLD** | Loaded when resuming a project or making a decision | `memory/projects/<slug>/memory-bank/*.md`, `decisions.md` |
| **Tier 3 (on demand)** | **DETAIL + DAILY** | Lazy-loaded only when relevant | `memory/feedback/`, `memory/security/`, `memory/references/`, daily logs |

**Convergent with peer OpenClaw deployments:** This mapping IS the cross-harness contract. Adapter MUST preserve.

**OpenClaw-specific:** HOT and WARM differ by priority within Tier 1 — HOT is the agent's working set, WARM is loaded but lower-priority. v3.0/v3.5 Tier 1 doesn't make this distinction, but the adapter's templates encode it via frontmatter `loaded_when: bootstrap` + an additional `priority: hot|warm` field for OpenClaw-aware loaders.

---

## §3 — Frontmatter Mapping

All 9 root files carry **file-level SCHEMA_A18 frontmatter** (file-level scope per SCHEMA_A18):

```yaml
---
scope: file
file_type: <one of: master_index | agent_topology | standing_principles | addon_registry | user_profile | feedback_log | heartbeat_active | bootstrap_handoff | dream_log_placeholder>
purpose: "<one-line purpose>"
loaded_when: bootstrap | on_resume | on_demand
priority: hot | warm | cold  # OpenClaw-specific extension
schema_version: "3.0"
edition: general
adapter_version: "1.0"
last_compacted: <YYYY-MM-DD>  # populated by heartbeat_compactor.py
content_sha256: <hex>          # populated at write time for CAS concurrency (MEMORY_PROTOCOL §5.1)
---
```

Per-entry frontmatter inside these files uses standard SCHEMA_A18 (`scope: entry`).

---

## §4 — Memory Directory Mapping

OpenClaw root layout vs v3.0/v3.5:

| v3.0/v3.5 path | OpenClaw equivalent | Notes |
|---|---|---|
| `memory/` | `<openclaw-root>/memory/` | Identical subdirectory structure |
| `memory/decisions/decisions.md` | (same) | Full DEC entries with SCHEMA_A18 frontmatter |
| `memory/sessions/session_state.md` | (synthesized into HEARTBEAT.md + BOOTSTRAP.md) | OpenClaw splits the v3.0 single-file into two |
| `memory/feedback/feedback.md` | (synthesized into USER.md) | OpenClaw promotes recent + standing into root |
| `memory/security/audit_log.jsonl` | (same) | Identical JSONL format |
| `memory/security/quarantine_log.jsonl` | (same) | Identical |
| `memory/security/vetting_log.md` | (same) | Identical |
| `memory/references/` | (same) | Identical |
| `memory/user/user_profile.md` | (synthesized into IDENTITY.md, PII-redacted) | OpenClaw root version is sanitized; full version stays in subdirectory |
| `memory/projects/<slug>/memory-bank/*.md` | (same — SCHEMA_A3) | Identical 6-file convention |
| `memory/archive/heartbeats/` | (same) | Heartbeat compactor archives here |
| `memory/archive/daily_logs/` | (same) | Daily logs rotate here after 14 days (OpenClaw deployment convention) |
| `memory/quarantine/` | (same) | Identical workflow |

---

## §5 — Compliance Mapping

| v3.0/v3.5 compliance preset | OpenClaw equivalent | Notes |
|---|---|---|
| `none` | (default) | Standard hygiene only; no regulatory detection |
| `enterprise` | (supported in general-edition adapter) | GDPR/SOC2 baseline; opt-in audit log; consent tracking |
| `healthcare` | **NOT ACTIVATED** for general-edition adapter | Requires biotech-edition adapter (B7 compliance review pending) |
| `custom` | (deferred) | Future enhancement |

Per B7: biotech-edition has non-overridable healthcare compliance. General-edition can opt-in to enterprise; healthcare requires biotech adapter.

---

## §6 — Bootstrap Budget Reconciliation

| v3.0/v3.5 default | OpenClaw |
|---|---|
| Tier 1 cap: ≤45% of context (per MEMORY_PROTOCOL §2 Tier 3 ceiling) | 60K total bootstrap budget |
| Per-file caps: see MEMORY_PROTOCOL §11 | `bootstrapMaxChars: 16000` per individual file (the maintainer's reference OpenClaw config) |
| Reserved for work: ≥25% of context | (implicit — Tier 1 fills 60K, conversation + tools get remainder) |

**Adapter behavior:**
- Templates sized so 9 root files total ~40K (well under 60K cap)
- ~20K headroom for conversation + tool output
- Heartbeat compactor enforces per-file caps; surfaces violations as Lint findings

---

## §7 — Edge Cases + Limitations

### Edge case 1: User wants OpenClaw-native agents (not the Claude-Code 4-peer)
**Resolution:** AGENTS.md ships the SPEC. Adapter doesn't override OpenClaw's runtime — if user has Meta Hyperagents (or similar) on OpenClaw, they keep using those; AGENTS.md is advisory.

### Edge case 2: User runs Obsidian on a different machine than OpenClaw
**Resolution:** Obsidian vault config can point to a network share / synced folder. Out of adapter's direct scope; user wires sync via OS or Multi-Machine Sync (Phase 4+).

### Edge case 3: User wants to migrate from v3.0 Claude Code to OpenClaw mid-project
**Resolution:** Memory directory is identical layout; just `cp -r` the `memory/` tree to OpenClaw root and run adapter to generate the 9 root files. No conversion needed.

### Edge case 4: User wants both Claude Code AND OpenClaw on the same machine
**Resolution:** Separate working directories. Each has its own `memory/` tree and root files. Multi-Machine Sync (Phase 4+) eventually unifies — for v3.5, treat as separate deployments.

### Limitation 1: DGM-H not included
Deferred by design decision. Adapter explicitly excludes DGM-H from v3.5 scope.

### Limitation 2: Auto-Dream not included
Auto-Dream (C1) is gated on a future Anthropic beta (v4.0 roadmap). DREAMS.md ships as empty placeholder.

### Limitation 3: Multi-Machine Sync not implemented
Multi-Machine Sync is a Phase 4+ feature. Adapter prepares `sync_log.jsonl` schema (separate v3.5 deliverable) but doesn't activate sync.

### Limitation 4: Biotech-edition not supported
Per B7 — compliance review required. General-edition only for v3.5.

---

## §8 — Cross-References

- `MAPPING.md` (foundation design — §4.1-§4.5 detailed here)
- `SKILL.md` (Claude-executable workflow using this mapping)
- `README.md` (addon-level README)
- `INSTALL_OPENCLAW_ADAPTER.md` (manual fallback)
- `templates/*.md.template` (9 root file templates — implement this mapping)
- `scripts/setup-openclaw.sh` + `setup-openclaw.py` (idempotent installers using this mapping)
- MEMORY_PROTOCOL §1.2 (tier loading)
- MEMORY_PROTOCOL §2 (Context Budget)
- MEMORY_PROTOCOL §6 (Edition Profile Application)
- MEMORY_PROTOCOL §11 (File Size Limits)
- SCHEMA_A18 v1.3 + v1.4 (file-level frontmatter + PageRank)
