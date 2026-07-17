---
name: install-openclaw-adapter
description: Install the Ultimate Memory Stack General Edition adapter onto an OpenClaw harness deployment. Generates 9 root auto-load files (MEMORY/AGENTS/SOUL/TOOLS/IDENTITY/USER/HEARTBEAT/BOOTSTRAP/DREAMS) mapped to v3.0/v3.5 semantics, configures heartbeat-driven Lint compaction via cron, sets up tier mapping (HOT/WARM/COLD/DETAIL/DAILY ↔ Tier 1/2/3), and inherits the 3 PASS-vetted addons (LLMLingua, Graphiti, Graphify) plus the config-only Obsidian vault addon. Use when the user asks to install, deploy, port, or adapt the memory stack to an OpenClaw harness (or an OpenClaw-family / compatible 9-root-file harness such as NVIDIA NemoClaw or NanoClaw).
version: "1.0"
authors: ["esoteric1entity"]
decision_authority: ["ideal-first design", "documentation discipline", "modular consumer architecture", "Other-harness compatibility", "cross-harness convergence validation", "Option C extension"]
target_harness: openclaw (general-edition; biotech deferred pending B7 compliance review)
edition: general-edition only (v3.5 scope)
tier: A (core deliverable — NOT opt-in; required for OpenClaw deployment)
license: Apache-2.0
bootstrap_budget: 60000 (OpenClaw default; some deployments raise the individual-file cap to 16000)
heartbeat_cadence: 30min active / 6h idle (reference cron schedule)
foundation_design: MAPPING.md
---

# Install OpenClaw General Edition Adapter — Skill Workflow

When this Skill is invoked (typically via `/install-openclaw-adapter` or when the user asks Claude to deploy the memory stack onto an OpenClaw harness), execute the workflow below **IN ORDER**.

**The OpenClaw adapter validates the modular consumer architecture** by porting the memory stack to a non-Claude-Code harness for the first time. Foundation design at `MAPPING.md`.

---

## Step 0 — Confirm Install Intent + Pre-Install Check

```
👋 You're about to install the Ultimate Memory Stack General Edition Adapter onto OpenClaw.

What this does:
  - Creates 9 root auto-load files (MEMORY/AGENTS/SOUL/TOOLS/IDENTITY/USER/HEARTBEAT/BOOTSTRAP/DREAMS)
  - Maps v3.0/v3.5 tier semantics (Tier 1/2/3) to OpenClaw tiers (HOT/WARM/COLD/DETAIL/DAILY)
  - Sets up heartbeat-driven Lint compaction (cron-triggered, surface-only by design)
  - Inherits 3 PASS-vetted addons (LLMLingua, Graphiti, Graphify) + Obsidian vault config (config-only, no vetting required) — installable separately
  - Bootstrap budget: 60K chars total (validated against a real OpenClaw deployment)

What this does NOT do (explicit out-of-scope for v3.5):
  - Install DGM-H (deferred to a future evolution layer)
  - Install Auto-Dream (v4.0 candidate, Anthropic beta gated)
  - Multi-machine sync (Phase 4+ candidate)
  - Biotech-edition overrides (B7 compliance review required)
  - Ports to other OpenClaw-family harnesses (e.g. NVIDIA NemoClaw, NanoClaw) + ClawHub distribution (deferred to a later phase)

Edition: general-edition (compliance: none / enterprise — NOT healthcare)
Target machines: your OpenClaw host (primary), plus an optional validation cross-check machine

Prerequisites:
  - OpenClaw harness installed at <openclaw-root>/
  - Python 3.10+ available (for heartbeat_compactor.py + setup-openclaw.py)
  - Bash 4+ available (for setup-openclaw.sh)
  - Optional: cron for heartbeat compactor (Step 9)
  - Optional: USB or network share for cross-machine sync (Phase 4+ scope)

Continue? [Y/n]:
```

---

## Step 1 — Detect OpenClaw Installation

```bash
# Check for OpenClaw harness:
test -d <openclaw-root>/.openclaw && echo "OpenClaw detected" || echo "OpenClaw not found"
```

If OpenClaw not found:
- Surface error: "OpenClaw harness not detected at <openclaw-root>. Install OpenClaw first per https://openclaw.dev (or equivalent) before invoking this adapter Skill."
- Halt gracefully.

If detected:
- Read `<openclaw-root>/.openclaw/config.json` (or equivalent) to identify:
  - OpenClaw version
  - Bootstrap budget (`bootstrapMaxChars`, `totalBudget`)
  - Existing root files (some may already be present; backup before overwrite)
- Save as `OPENCLAW_CONFIG` for subsequent steps

---

## Step 2 — Backup Existing Root Files (Idempotency Safety)

Before writing any new root files, back up any that exist:

```bash
mkdir -p <openclaw-root>/.openclaw/backup/pre-adapter-install-<YYYY-MM-DD>/
for f in MEMORY.md AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md BOOTSTRAP.md DREAMS.md; do
  if [ -f "<openclaw-root>/$f" ]; then
    cp "<openclaw-root>/$f" "<openclaw-root>/.openclaw/backup/pre-adapter-install-<YYYY-MM-DD>/$f"
  fi
done
```

Idempotency requirement — re-running this Skill on a partial install MUST be safe (no data loss, no corruption).

---

## Step 3 — Source Adapter Templates

Locate the adapter templates (this Skill's `templates/` directory):

```bash
ADAPTER_TEMPLATES=<path-to-this-skill>/templates/
ls -la "$ADAPTER_TEMPLATES"
```

Expected to find 9 template files (one per root file). If any are missing, halt — the adapter source is incomplete.

---

## Step 4 — Generate 9 Root Files (Templated)

For each of the 9 root files, instantiate the template into `<openclaw-root>/`:

```bash
# Bash (or call setup-openclaw.sh / setup-openclaw.py for full automation):
for f in MEMORY AGENTS SOUL TOOLS IDENTITY USER HEARTBEAT BOOTSTRAP DREAMS; do
  template="$ADAPTER_TEMPLATES/${f}.md.template"
  output="<openclaw-root>/${f}.md"
  cp "$template" "$output"
  # Templater-style variable expansion happens at first OpenClaw bootstrap, not here
done
```

Per §1 of `MAPPING.md`, the 9 files map to v3.0/v3.5 concepts:

| OpenClaw file | v3.0/v3.5 equivalent | Bootstrap budget |
|---|---|---|
| `MEMORY.md` | `MEMORY_INDEX.md` | ~5K |
| `AGENTS.md` | `.claude/rules/agent_orchestration.md` | ~6K |
| `SOUL.md` | NEW — distilled FINAL principles from `decisions.md` | ~5K |
| `TOOLS.md` | Tier C activation guide + recommended-addons/ pointers | ~5K |
| `IDENTITY.md` | `memory/user/user_profile.md` (PII-redacted) | ~3K |
| `USER.md` | `memory/feedback/feedback.md` (recent + standing) | ~5K |
| `HEARTBEAT.md` | `memory/sessions/session_state.md` (rolling 3-deep) | ~5K |
| `BOOTSTRAP.md` | `memory/sessions/session_state.md` (next-actions section) | ~4K |
| `DREAMS.md` | v4.0 placeholder (Auto-Dream Anthropic beta gated) | ~2K |

**Total bootstrap = ~40K chars; 60K cap leaves ~20K headroom per MEMORY_PROTOCOL §2 Tier 1.**

---

## Step 5 — Generate Subdirectories (memory/ tree + heartbeat archive)

```bash
mkdir -p <openclaw-root>/memory/decisions/
mkdir -p <openclaw-root>/memory/sessions/
mkdir -p <openclaw-root>/memory/feedback/
mkdir -p <openclaw-root>/memory/security/
mkdir -p <openclaw-root>/memory/references/
mkdir -p <openclaw-root>/memory/user/
mkdir -p <openclaw-root>/memory/projects/
mkdir -p <openclaw-root>/memory/archive/heartbeats/
mkdir -p <openclaw-root>/memory/archive/daily_logs/
mkdir -p <openclaw-root>/memory/quarantine/
```

Mirrors the v3.0/v3.5 memory directory structure. Per MEMORY_PROTOCOL §1.2 tier loading.

---

## Step 6 — Initialize Empty Audit + Quarantine Logs

```bash
# Audit log (general-edition: opt-in per B1; create empty file as placeholder)
touch <openclaw-root>/memory/security/audit_log.jsonl

# Quarantine log
touch <openclaw-root>/memory/quarantine/quarantine_log.jsonl

# Daily log (rotates every 14 days, then archives)
touch "<openclaw-root>/memory/archive/daily_logs/DAILY_LOG_$(date +%Y-%m-%d).md"
```

---

## Step 7 — Configure Edition Profile

```
Edition: general-edition (locked for v3.5)
Compliance preset:
  (a) none — default
  (b) enterprise — GDPR/SOC2 baseline; provenance + audit + consent tracking
```

Write `<openclaw-root>/ultimate-memory-stack/general-edition/PROFILE.md` with chosen preset. Per MEMORY_PROTOCOL §6.

If user later wants `healthcare` preset, that requires biotech-edition adapter (separate work).

---

## Step 8 — Install MEMORY_PROTOCOL_EXTENDED §E7 Lint Checks (Option C)

Per Option C, 5 new self-improvement Lint checks ship by default in v3.5. The adapter installs the Lint runner at `<openclaw-root>/.openclaw/lint/`:

```bash
mkdir -p <openclaw-root>/.openclaw/lint/
# lint_runner.py moved to core/shared-tools/ in v4.0.0 (shared cross-harness
# tooling, not adapter-specific) — copy from there, not scripts/.
cp <path-to-this-skill>/../shared-tools/lint_runner.py <openclaw-root>/.openclaw/lint/lint_runner.py
```

Lint runs surface-only by design. NEVER auto-mutates.

---

## Step 9 — Configure Heartbeat Compactor (Optional Cron)

Per `MAPPING.md` §4 (memory-directory mapping — heartbeat archive):

```bash
cp <path-to-this-skill>/scripts/heartbeat_compactor.py <openclaw-root>/.openclaw/heartbeat_compactor.py
```

```
Wire heartbeat compactor to cron?
  (a) Yes — runs every 30 min (active hours) / 6h (idle hours); auto-archives HEARTBEAT.md when size exceeds threshold
  (b) Skip — install only; user runs manually via `python heartbeat_compactor.py` or wires cron later
```

If yes, present the cron entry:

```cron
# Heartbeat compactor — runs every 30 min during active hours (08-22), every 6h overnight
*/30 8-22 * * * cd <openclaw-root> && python3 .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
0 0,6 * * * cd <openclaw-root> && python3 .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
```

**This Skill does NOT mutate crontab automatically** (security boundary). Present the cron entry to the user; they run `crontab -e` and paste it manually.

---

## Step 10 — Optional: Wire Recommended Addons

```
Install any recommended addons now?
  (a) Obsidian vault config — point at <openclaw-root>/memory/ for canonical view
  (b) LLMLingua — for compression on the 60K bootstrap budget
  (c) Graphiti — for Layer 5 knowledge graph (Kuzu backend recommended)
  (d) Graphify — for codebase symbol graph (with L1-L4 typosquat defense)
  (e) None — install adapter only; addons later
```

For each chosen addon, hand off to its respective installer Skill (`/install-llmlingua`, `/install-graphiti`, `/install-graphify`, `/config-obsidian-vault`). Each runs independently with its own Sentinel-vetted guardrails.

---

## Step 11 — Run T1-T9 Self-Test

```bash
python <path-to-this-skill>/scripts/self_test.py <openclaw-root>/
```

Validates per MEMORY_PROTOCOL §1.3:
- T1: HEARTBEAT.md exists + has Schema Version header
- T2: MEMORY.md exists; entry counts non-negative
- T3: Session number ≥ previous (no regression)
- T4: No root file exceeds its size limit
- T5: All MEMORY.md references resolve to existing files
- T6: Schema versions consistent
- T7: No PII/PHI in root files (sanity check on IDENTITY.md sanitization)
- T8: All entries have valid SCHEMA_A18 frontmatter
- T9: Edition profile + compliance preset loaded correctly

Surface failures to user; CRITICAL failures halt.

---

## Step 12 — Log Activation

Append `DEC-### Adapter Installed` to `<openclaw-root>/memory/decisions/decisions.md`:

```markdown
## DEC-###: OpenClaw General Edition Adapter Installed

- **Status:** FINAL
- **Confidence:** 1.0
- **Session:** <N>
- **Date:** <today>
- **Decision:** Installed Ultimate Memory Stack General Edition Adapter v1.0 on this OpenClaw deployment
- **Rationale:** [user-supplied — e.g., a NAS deployment]
- **Components installed:** 9 root files + memory/ tree + Option C Lint + edition profile + [list addons]
- **Heartbeat compactor:** [enabled-cron | manual | not-installed]
- **Cross-references:** [related DEC-### entries in this deployment's log], MAPPING.md
- **Tags:** adapter-installed, openclaw, general-edition, v3-5
```

Also append `VET-### Adapter Activated` to `<openclaw-root>/memory/security/vetting_log.md` (standard security-first vetting-log pattern).

---

## Step 13 — Brief User on Operational Notes

```
✅ OpenClaw General Edition Adapter installed at <openclaw-root>/

Root files (9):           MEMORY · AGENTS · SOUL · TOOLS · IDENTITY · USER · HEARTBEAT · BOOTSTRAP · DREAMS
Tier mapping:             HOT/WARM (Tier 1) · COLD (Tier 2) · DETAIL/DAILY (Tier 3)
Bootstrap budget:         60K chars total · ~40K used by 9 root files · 20K headroom
Edition:                  general-edition / compliance: <preset>
Option C Lint:            installed at .openclaw/lint/
Heartbeat compactor:      <cron-status>
Addons:                   <installed-addons-list>

Next steps for you:
  1. Open OpenClaw on this machine — it should auto-load the 9 root files
  2. Verify the bootstrap doesn't exceed 60K (check OpenClaw startup log)
  3. Try a heartbeat: edit HEARTBEAT.md mid-session; verify it persists
  4. Try the heartbeat compactor manually: python3 .openclaw/heartbeat_compactor.py
  5. If cron wired up, watch .openclaw/lint/compactor.log for ~30 min

Cross-machine validation:
  - Write a test DEC entry on the OpenClaw host
  - Mount a share / use removable media to bring the entry to the target machine
  - Verify Claude Code reads the entry with matching SCHEMA_A18 frontmatter

For Sentinel-vetted addon installs:
  - /install-llmlingua  (token compression; vetted PASS)
  - /install-graphiti   (knowledge graph; vetted PASS; Kuzu backend recommended)
  - /install-graphify   (codebase symbol graph; vetted PASS; L1-L4 typosquat defense)
  - /config-obsidian-vault  (Obsidian vault config; no vetting required — config-only)
```

---

## Compliance Cross-References

| Step | Action | Decision authority |
|---|---|---|
| 0 | Intent + pre-install check | documentation discipline |
| 1 | OpenClaw detection | precondition check |
| 2 | Backup existing root files | idempotency |
| 3 | Source templates | validate before write |
| 4 | Generate 9 root files | modular consumer architecture validation |
| 5 | Generate memory/ tree | MEMORY_PROTOCOL §1.2 |
| 6 | Empty audit + quarantine | MEMORY_PROTOCOL_EXTENDED §E3.2 + §E3.3 |
| 7 | Edition profile | MEMORY_PROTOCOL §6 + B7 compliance preset |
| 8 | Option C Lint install | Option C extension |
| 9 | Heartbeat compactor cron | cross-harness convergence |
| 10 | Optional addon wiring | Tier C addon policy + Option C extension |
| 11 | T1-T9 self-test | MEMORY_PROTOCOL §1.3 |
| 12 | Log activation | security-first + documentation discipline |
| 13 | Hand-off | ideal-first design |

---

## What This Skill CANNOT Do

- **Cannot install the OpenClaw harness itself** — user installs OpenClaw separately
- **Cannot mutate user's crontab** (security boundary) — presents cron entry; user pastes via `crontab -e`
- **Cannot install DGM-H** — deferred; reverts to Phase 4+ candidate
- **Cannot install Auto-Dream** — v4.0 candidate, Anthropic Dreaming beta gated
- **Cannot activate biotech-edition** — separate work; B7 compliance review required
- **Cannot sync entries across machines** — Multi-Machine Sync is a Phase 4+ candidate; this adapter prepares the schema (sync_log.jsonl scope) but doesn't implement
- **Cannot guarantee bootstrap stays under 60K** if user adds large content to root files — heartbeat compactor surfaces violations; user must act
- **Cannot install addons it doesn't recognize** — only the 4 PASS-vetted ones (LLMLingua / Graphiti / Graphify / Obsidian) have known Skills; new addons require fresh VET-### entries
- **Cannot port Warden / Sentinel / Vault / Clerk to OpenClaw runtime** — AGENTS.md ships the SPEC but agents are advisory until OpenClaw supports peer-agent spawning (deferred to Phase 4+ research)
