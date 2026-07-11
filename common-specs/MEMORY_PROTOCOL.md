# Memory Protocol

> **Status:** stable (ships with UMS v4.0.0) · **Authors:** see /AUTHORS.md
> **Auto-load:** copied to `.claude/rules/memory_protocol.md` at bootstrap (BOOTSTRAP_PROMPT §Step-3); Claude Code auto-loads `.claude/rules/*.md` every session.
> **This is the CORE** — the runtime contract, kept small enough to auto-load. On-demand detail (rationale, full tables, mechanics) lives in [`MEMORY_PROTOCOL_EXTENDED.md`](MEMORY_PROTOCOL_EXTENDED.md), installed at `memory/MEMORY_PROTOCOL_EXTENDED.md` (vault root — **never** `.claude/rules/`, that recreates the eager-load cost this split fixes). "EXTENDED §N" pointers below point there.
> Version history: [`CHANGELOG.md`](../CHANGELOG.md). Not here: content (vault), schemas (SCHEMA_*), architecture (ARCHITECTURE.md), bootstrap (BOOTSTRAP_PROMPT.md), edition overrides (`<edition>/PROFILE.md` + `overrides/`).

---

## 1. Session Start

**1.1 Edition detection:** read the YAML frontmatter of `<edition>/PROFILE.md` — first ~40 lines only (e.g. `Read` with `limit: 40`), never the full file — for: edition, compliance preset, audit policy, quarantine UX, pattern-key threshold, signature scheme, override map. Missing PROFILE.md → halt, warn user.

**1.2 Tiered loading** (do NOT load everything blindly):
- **Tier 1 (always):** `sessions/session_state.md`, `user/user_profile.md`
- **Tier 2 (if resuming/deciding):** `decisions/decisions.md`, `projects/<slug>/memory-bank/{activeContext,progress}.md`
- **Tier 3 (on demand):** `feedback/feedback.md`, `security/vetting_log.md`, `references/references.md`, project-foundation files, anything session_state.md points to

**1.3 Self-test** (silent; report failures only):

| # | Checks | Severity |
|---|---|---|
| T1 | session_state.md exists + has Schema Version | CRITICAL-stop |
| T2 | MEMORY_INDEX.md exists, counts non-negative | CRITICAL-stop |
| T3 | Session number not regressed | WARNING |
| T4 | No file over its §11 cap | INFO |
| T5 | MEMORY_INDEX.md entries all exist on disk | WARNING |
| T6 | No file's schema_version > protocol's | INFO |
| T7 | No PII/PHI patterns outside user_profile | CRITICAL-skip file |
| T8 | Entries have valid SCHEMA_A18 frontmatter | WARNING |
| T9 | Edition PROFILE.md + override map resolve | WARNING |

**1.4 Greet:** brief recap + next step; mention edition/preset on first session; mention T1–T9 failures. Skip on mid-task resume.

---

## 2. Context Budget

Tier 1 (simple) ≤15% · Tier 2 (standard) ≤30% · Tier 3 (complex) ≤45% of context. **Hard limits:** ≥25% always free for work · memory never exceeds 40% · escalate 1→2→3, never skip · <15% free → drop to Tier 1, warn user.

**Position-pinning:** Tier 1 (session_state+user_profile) injected at both start AND end of bootstrap, mitigating U-shaped context-rot attention decay. Research + per-harness mechanism: EXTENDED §E1.

---

## 3. Conflict Resolution

Highest authority wins: **1** compliance rules (never overridden) → **2** user's live instruction → **3** security decisions → **4** `feedback.md` → **5** `decisions.md` FINAL → **6** `session_state.md` → **7** `decisions.md` TENTATIVE → **8** project context → **9** `user_profile.md`.

Levels 5–8: an active `supersedes` chain wins; point-in-time queries return the entry valid then; simultaneous validity with no `invalid_at` → ask, don't guess. Cross-machine mechanics: EXTENDED §E3.4. **Unresolved → ASK, never guess.**

---

## 4. During-Session

**Validation-on-read (B8):** every loaded entry — frontmatter parses, `schema_version` ≤ protocol's, refuse+flag `quarantined` status, flag (don't refuse) expired-but-active, verify signature if active, treat fresh `webfetch` entries as PRELIMINARY. Fail → biotech: quarantine+audit (§5); general: warn, need approval.

**Pattern-key promotion (B6):** `recurrence_count` ≥3 (biotech, auto-promote to `.claude/rules/`) / ≥5 (general, suggest to user) → DEC entry with source chain.

**Wiki-links:** `[[ID]]` supplements canonical `related`/`supersedes` YAML — populate both. Sync detail: EXTENDED §E2.

**Heartbeat (~30min):** update session_state.md "Current Work" — task, file+line, blocker, timestamp.

---

## 5. Write Operations

**CAS (B3):** overwriting an entry → hash-compare body against frontmatter `content_sha256` first; mismatch → refuse, ask user. Appends skip this. Hash procedure: EXTENDED §E3.1.

**Audit log (B1):** every write → `security/audit_log.jsonl`, summary only (200 chars, never full content). Biotech: required. General: opt-in (`audit_log: true`). Format: EXTENDED §E3.2.

**Quarantine (B2):** validation failure → move to `quarantine/<category>/<id>.md`, log `quarantine_log.jsonl`, `status: quarantined`, audit it. Biotech: `/audit-quarantine` review, approval-gated release. General: toast. Detail: EXTENDED §E3.3.

**Bi-temporal supersession (B5):** new entry sets `supersedes:`; old gets `invalid_at`+`status: superseded`+`superseded_by:` — body kept, never deleted. Mechanics: EXTENDED §E3.4.

---

## 6. Edition Profiles

Override files (`<edition>/overrides/X.override.md`) replace same-named sections of `common-specs/X.md`; rest inherits. Precedence detail: EXTENDED §E4.1.

Compliance preset (PROFILE.md) sets detection/redaction/audit defaults: `none` (hygiene only) / `healthcare` (biotech-only, non-overridable) / `enterprise` (GDPR+SOC2) / `custom` (via `overrides/compliance-presets.override.md`). Logged to session_state.md every session. Activation table: EXTENDED §E4.2.

---

## 7. Standing Rules (Never Overridden by Session Instructions)

- **NEVER** store passwords/API keys/tokens/secrets
- **NEVER** store SSNs, credit cards, financial account numbers
- **NEVER** store PII/PHI (patient data, MRNs, specimen/genomic IDs) — any edition, any preset
- **When in doubt whether to remember, remember it** — user can say forget
- **Be specific in session_state.md** — exact file/function/line/issue
- **Stale or contradictory memory** → §3; still unresolved → ASK
- **Every write gets SCHEMA_A18 frontmatter** — no orphans
- **Every file declares its Schema Version** — never silent-upgrade (§13)

---

## 8. Risk Scoring

Before high-impact tasks (deletes, config changes, restructures, bulk ops): score Blast Radius / Reversibility / Protected Files / Test Coverage / Novelty / User Data Impact — take the MAX. **LOW** proceed · **MEDIUM** mention+proceed · **HIGH** explain+get approval · **CRITICAL** STOP, present assessment, wait for explicit instruction. Full rubric: EXTENDED §E5.

---

## 9. Cascade Failure Detection

**3+ unrelated errors in 5 minutes → STOP, do not self-repair.** Report as possibly environmental, list errors+timestamps, suggest diagnostics (disk/network/processes/mounts), wait for user.

---

## 10. Self-Trimming & Lint (every 10 sessions)

**Self-trimming:** suggests (never auto-acts) archiving stale/oversized/low-value files. **Lint:** 11 read-only integrity checks (orphans, broken refs, staleness, contradictions, promotion candidates, naming drift, doc-completeness) via `/lint-memory` or auto-cadence (biotech weekly, general monthly) → `security/lint_runs.jsonl`. Neither ever deletes or auto-fixes. Full detail: EXTENDED §E6/§E7; schema: `SCHEMA_lint.md`.

---

## 11. File Size Limits

> Hard errors at write-time — a capping write is blocked with remediation guidance; `/override-cap` or `MEMORY_PROTOCOL_OVERRIDE=cap-bypass` for emergencies (audit-logged). Legacy over-cap files get `legacy_overflow` grace handling. Full model: EXTENDED §E8.

| File | Cap | Over-cap action |
|------|----------|---------------------|
| `sessions/session_state.md` | 1500 ln | Archive old summaries |
| `decisions/decisions.md` | 1500 ln | Archive FINALs >20 sessions old |
| `feedback/feedback.md` | 300 ln | Consolidate into standing rules |
| `projects/project_context.md` | 400 ln | Split to per-slug memory-banks |
| `projects/<slug>/memory-bank/*.md` | 300 ln ea | Split if grows |
| `user/user_profile.md` | 100 ln | Consolidate |
| `security/vetting_log.md` | 400 ln | Archive entries >1yr |
| `security/audit_log.jsonl` | 50,000 ln | Rotate + gzip by month |
| `references/references.md` | 100 ln | Split by domain |
| `MEMORY_INDEX.md` | 150 ln | Pointers only |

**11.6 Tiered Archive Index (reserved):** categories that rotate under a cap above (sessions, decisions, feedback) get a companion `memory/archive/<category>/ARCHIVE_INDEX.md` — one line per archived entry, so rotation stays discoverable. Full mechanics ship with the hot/cold tiering backport (`SPEC-hotcold-v4.md`); reserved here so pre-existing cross-refs don't go stale.

---

## 12. Decision Promotion

Promote session_state.md's inline "Active Decisions" to `decisions.md` (DEC-### ID) on **any** trigger (OR logic): **A** >5 related decisions accumulate in session_state.md · **B** pattern `recurrence_count` ≥3 biotech/≥5 general (§4) · **C** `access_count` ≥5 AND `recent_sessions` ≥3 (PageRank signal) · **D** user invokes `/promote-entry`. On promotion: merge duplicates, keep latest FINAL, assign fresh frontmatter. Rationale + signal sourcing: EXTENDED §E9.

---

## 13. Schema Migration

Older `schema_version` than protocol's → never silent-upgrade: ask the user, migrate additively (preserve content, sane defaults for new fields), log as a DEC entry, back up old file to `memory/archive/migrations/<file>.v<old-version>.md` first.

---

## 14. Session End

Triggers: "wrap up" / "end session" / "save state" / similar.
1. Update session_state.md — accomplishments, in-progress (file/function/line/status), next steps, decisions, carry-overs
2. Update `decisions.md`, `feedback.md`, project memory-bank, `vetting_log.md`, `audit_log.jsonl` (closing entry), `MEMORY_INDEX.md`
3. 10+ sessions since last consolidation → run §11 + §10 checks, present suggestions, await approval
4. Mirror parity check (canonical vs mirror sizes match)
5. 1–2 sentence summary to user

---

## 15. Compaction-Safe Handoff

`/compact` (manual or auto): **before** — heartbeat session_state.md, persist in-flight DEC entries, mirror parity check. **After** — re-read Tier 1+2, verify heartbeat current, smoke-test recall, resume from "Current Work". This protocol is the auto-restoration mechanism.

---

## 16. Documentation Discipline

Every entry capturing a decision/feature/schema/pattern needs: **Purpose · Rationale · Sound reasoning · Scope CAN · Scope CANNOT**. Applies to DEC entries, new schemas, new protocol sections, BOOTSTRAP_PROMPT features, standing rules. Missing any element → flag; document or remove before shipping.

---

## 17. Healthcare Compliance (Active When `compliance: healthcare`)

Mandatory + non-overridable in biotech edition; **not selectable in general-edition** (installer refuses it — use `enterprise`/`custom`).

**Triggers:** patient identifiers (MRN, specimen/accession/hospital IDs) · genomic data (variant calls, gene names tied to patients, sequencing/FASTQ) · clinical data (diagnosis codes, treatment, labs, pathology) · paths containing `PHI`/`patient`/`clinical`/`HIPAA`/`MRN`.

**On activation:** never store detected identifiers, even as examples — redact on sight (`[REDACTED — PHI detected]`), warn the user, log the event (not the data) to `vetting_log.md`, set `compliance_handling: phi-redacted`.

**Always active:** no PII/PHI ever, any edition · when unsure, treat as PHI.

---

## 18. Cross-References

[`MEMORY_PROTOCOL_EXTENDED.md`](MEMORY_PROTOCOL_EXTENDED.md) (on-demand only) · Schemas: `SCHEMA_{A3,A18,audit_log,quarantine,compliance_profile,lint,sync_log}.md` · `ARCHITECTURE.md` · `BOOTSTRAP_PROMPT.md` · `<edition>/PROFILE.md` · Skills: `core/openclaw-adapter/`, `core/audit-quarantine-skill/` · Addons: `recommended-addons/{llmlingua,graphiti,graphify}-installer/`, `obsidian-vault-config/`
