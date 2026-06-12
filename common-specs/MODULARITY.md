# Modularity — Architecture Plug-In Pattern

> **File:** `common-specs/MODULARITY.md`
> **Version:** 1.0 — 2026-05-15
> **Status:** APPROVED
> **Authors:** see `/AUTHORS.md`
> **Design decision:** Memory stack as branded module; consumer architecture pluggable

---

## 1. Purpose

Define what's **brand-protected** (canonical to the Ultimate Memory Stack) versus what's **modular** (pluggable by consuming Claude architectures). This is the load-bearing distinction that allows the memory stack to be deployed in **any Claude architecture** while preserving its identity as a coherent product.

The analogy that resolves this cleanly: **SQL is branded; applications consuming SQL vary.** The memory stack is the SQL of agent memory — its name, schemas, protocols, and architecture are canonical. The consuming agent topology is the application — different Claude setups consume the stack with different sub-agent layouts.

---

## 2. What's Brand-Protected (Canonical)

These elements ARE the Ultimate Memory Stack. They are not user-changeable. They define the product:

### Brand identity
- **Stack name:** "Ultimate Memory Stack" (working title; final-name decision still deferred)
- **Authors:** see `/AUTHORS.md`
- **License:** Apache-2.0

### Architecture (Layers 0–6)
- Layer 0 — Protocol & Budget
- Layer 1 — Markdown Vault
- Layer 2 — Compliance & Audit
- Layer 3 — Hybrid Search
- Layer 4 — Caching & Compression
- Layer 5 — Graph Backends
- Layer 6 — Cryptographic Signatures

See `ARCHITECTURE.md`.

### Schemas
- `SCHEMA_A3_per_project_memory_bank.md` — per-project Memory Bank (Cline 6-file convention adopted)
- `SCHEMA_A18_per_entry_metadata.md` — per-entry YAML frontmatter (the universal entry shape)
- `SCHEMA_audit_log.md` — JSONL audit log format
- `SCHEMA_quarantine.md` — quarantine workflow + reason codes
- `SCHEMA_compliance_profile.md` — 3-preset hybrid + custom (B7)

### Operational protocols
- `MEMORY_PROTOCOL.md` — 19 sections defining session start, context budget, conflict resolution, validation-on-read, write operations, edition profile application, standing rules, risk scoring, self-test, self-trimming, decision promotion, schema migration, session end, compaction-safe handoff, documentation discipline, healthcare compliance profile
- `BOOTSTRAP_PROMPT.md` — deployment activation prompt

### Design system
- 9-level conflict resolution hierarchy with bi-temporal precedence (B5)
- Tiered context budget (15/30/45% with 25% reserved + 40% ceiling)
- Deployment-tier markers (T0–T4)
- Documentation discipline (every feature has purpose/rationale/sound reasoning/scope CAN/CANNOT)
- Bi-temporal model (`valid_at` / `invalid_at` per B5)
- 3-preset compliance hybrid + custom (B7)
- Wiki-link inline syntax (`[[ID]]`) as supplemental cross-reference form

### Detection patterns + edition profiles
- `detection_patterns_none.md`, `detection_patterns_healthcare.md`, `detection_patterns_enterprise.md`
- `biotech-edition/` and `general-edition/` directory structures + override conventions (B4)

**Brand-protected = "the product." Users adopting the stack get these as-is. Consistency across adopters is a feature, not a constraint.**

---

## 3. What's Modular (Pluggable by Consuming Claude Architectures)

These elements are intentionally pluggable. They reflect the consuming agent topology, not the memory stack:

### `source_agent` attribution (SCHEMA_A18 v1.2)

The `source_agent` field on every memory entry attributes it to whichever agent created it. The memory stack provides **standard slots** and accepts **consumer-defined slots**:

#### Standard slots (always available)
- `user` — manually entered by the human operator
- `orchestrator` — the main agent instance
- `webfetch` — sourced from WebFetch (HIGH-RISK)
- `external-tool-output` — sourced from any other tool
- `migration-script` — one-time migration or bootstrap

#### Consumer-defined slots
Any string matching `[a-z][a-z0-9-]*`. The consuming architecture registers its sub-agent names at bootstrap (BOOTSTRAP_PROMPT.md Step 7 setup wizard).

### Sub-agent template structure

The memory stack does NOT define sub-agent templates. Consuming architectures supply their own at `<working-dir>/agents/<agent-name>.md` (or wherever their orchestration layer expects them). The memory stack only requires that consumer-defined `source_agent` slots match registered agents.

### Sub-agent coordination protocols

Cross-agent coordination (spawning rules, parallel-safe pairs, dependency ordering) is an orchestration concern, NOT a memory stack concern. By design, orchestration is a separate layer of the consuming agent architecture; the memory stack doesn't dictate it.

---

## 4. Reference Architecture — Example Claude Code Deployment

This reference Claude Code deployment is an **example** of how a consuming architecture plugs into the memory stack. It is NOT canonical — other deployments may differ.

### The reference sub-agents (4-agent flat hierarchy)

- `warden` — security agent (Warden — pre-vetting context, posture reports, incident response)
- `sentinel` — vetting / code review agent (Sentinel — pre-installation tool/skill review)
- `vault` — memory operations agent (Vault — read/write to Layer 1 memory artifacts)
- `clerk` — PM agent (Clerk — kanban + daily activity log)

These are registered as consumer-defined `source_agent` slots in the reference deployment. Other deployments may register different agents (or none).

### Sub-agent templates location

In the author's deployment, templates live at `<YOUR_WORKSPACE>\agents\` (not part of the memory stack package). Templates define what each agent does, its tool permissions, and how the orchestrator spawns it.

### Sub-agent coordination

The reference orchestration rules live at `.claude/rules/agent_orchestration.md` (separate from `.claude/rules/memory_protocol.md` which IS part of the memory stack). The orchestration rules define spawning protocols, parallel-safe pairs, and dependency chains — concerns OUTSIDE the memory stack's scope.

---

## 5. Example Variations — How Different Deployments Plug In

### Variation A: a second machine (same 4 sub-agent roles, maybe different names)

Setup wizard registers: `warden`, `sentinel`, `vault`, `clerk`. Same roles as the reference setup. Memory stack accepts identical attribution. No changes to memory stack itself.

### Variation B: a coworker (different agent topology)

Setup wizard registers: `researcher`, `code-reviewer`. The memory stack accepts these as valid `source_agent` values for the coworker's deployment. The coworker's memory entries carry `source_agent: researcher` or `source_agent: code-reviewer`. The memory stack does not care about the semantic meaning — it just enforces the naming convention + registered-slot rule.

### Variation C: Personal hobby project (no sub-agents)

Setup wizard prompts for sub-agent topology; user replies "none." The memory stack uses ONLY standard slots (`user`, `orchestrator`, `webfetch`, `external-tool-output`). Every memory entry attributes to one of these. Works perfectly fine — many users won't have sub-agents.

### Variation D: Power user with custom additions

Setup wizard accepts initial 4 (`warden`, `sentinel`, `vault`, `clerk`) but user later adds `data-analyst`. The user updates `user_profile.md` to include the new slot. Subsequent memory entries can use `source_agent: data-analyst`. Memory stack accepts this without protest.

---

## 6. What's Explicitly Out of Scope for v3.0 Modularity

Per the design directive:

- **Other harnesses (OpenClaw, custom non-Claude agents):** Deferred to future iteration. v3.0 is Claude-only.
- **Cross-architecture migration tools:** If a deployment changes its sub-agent topology mid-flight (e.g., adds new agents), the memory stack DOES NOT auto-migrate prior entries. Old entries retain their original `source_agent` values; new entries use new slots. This is intentional — historical attribution preserves provenance.
- **Memory stack INTERNAL features being user-changeable:** No. The 7-layer architecture, schemas, protocols are FIXED for a given v3.0 deployment. Only the `source_agent` registration is pluggable.

---

## 7. Brand Protection Mechanism

How does the memory stack PREVENT consumers from "modifying the brand"?

It doesn't have a hard enforcement mechanism (it's markdown, not a runtime). Instead, the protection is by **convention + documentation**:

1. **Schema files declare canonical structure** — overrides to canonical schemas are explicitly out of scope (no `SCHEMA_A18.override.md` allowed for renaming standard slots, for example)
2. **MODULARITY.md (this file) names what's brand-protected** — consumer architectures that modify these are no longer "deploying the Ultimate Memory Stack"; they're deploying a fork
3. **Forks are allowed but must rename** — per the Apache-2.0 license + the brand-protected boundary in this document, forks of the memory stack would need a different name. Same way SQL forks rename (MySQL, PostgreSQL — different products)

In practice: most users have no reason to modify brand-protected elements. The compliance preset system (B7) handles regulatory variation. The override-file convention (B4) handles edition variation. Modularity handles agent topology variation. These cover the vast majority of customization needs without touching the brand.

---

## 8. How This Maps to Existing Decisions

| Element | Decision | Status |
|---------|----------|--------|
| Stack name brand-protected | Working title; brand-protected boundary set in this document | FINAL |
| Layer structure brand-protected | Core layer design (Layers 0–6) | FINAL |
| Schemas brand-protected | Canonical schema set | FINAL |
| Compliance preset system brand-protected | B7 (⭐) preset design | FINAL |
| `source_agent` modular | This document (new) | FINAL |
| Sub-agent templates modular | Memory ≠ orchestration layer split | FINAL |
| Sub-agent coordination modular | Memory ≠ orchestration layer split | FINAL |
| Other-harness portability | Deferred to future iteration per the design directive | DEFERRED |
| Public release / license | Apache-2.0 | ✅ Locked |

---

## 9. Cross-References

- `SCHEMA_A18_per_entry_metadata.md` v1.2 (modular `source_agent` definition)
- `ARCHITECTURE.md` §11.6 (modularity reference)
- `BOOTSTRAP_PROMPT.md` Step 7 (consumer agent registration at bootstrap)
- Author's reference agents at `<YOUR_WORKSPACE>\agents\` (Warden/Sentinel/Vault/Clerk — example deployment)
