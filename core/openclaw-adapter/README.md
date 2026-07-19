# OpenClaw General Edition Adapter

> **Status:** stable — ships with UMS v4.0.0 (design + Skill artifact complete; cross-machine deployment validated)
> **Tier:** A (CORE deliverable — required for OpenClaw deployment; not opt-in)
> **Edition:** general-edition (the public edition; a HIPAA/PHI institutional edition is planned for a future release)
> **Last updated:** 2026-07-11

---

## What This Adapter Does

The OpenClaw General Edition Adapter ports the Ultimate Memory Stack onto the **OpenClaw harness** — the first non-Claude-Code consumer of the memory stack. It generates the 9 root auto-load files OpenClaw expects, maps tier semantics across the two harnesses, and inherits the 3 PASS-vetted addons plus the config-only Obsidian vault addon.

**Why this matters:**
- Validates the modular consumer architecture in practice
- Validates independent convergence with an existing OpenClaw deployment (the cross-harness pattern is real)
- Unlocks NAS-class OpenClaw deployment targets
- Establishes the pattern for future ports to OpenClaw-family harnesses with compatible tool-surface contracts — e.g. [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw) (OpenShell-sandboxed OpenClaw) and [NanoClaw](https://github.com/nanocoai/nanoclaw) (container-isolated OpenClaw variant)

**What's included:**

```
core/openclaw-adapter/
├── SKILL.md                              # 13-step Claude-executable workflow
├── README.md                             # This file
├── INSTALL_OPENCLAW_ADAPTER.md            # Manual fallback guide
├── MAPPING.md                            # v3.0/v3.5 ↔ OpenClaw convention mapping
├── templates/                            # 9 root file templates
│   ├── MEMORY.md.template                # Master index
│   ├── AGENTS.md.template                # Agent topology
│   ├── SOUL.md.template                  # Distilled FINAL principles
│   ├── TOOLS.md.template                 # Addon registry
│   ├── IDENTITY.md.template              # User profile (PII-redacted)
│   ├── USER.md.template                  # Feedback + standing rules
│   ├── HEARTBEAT.md.template             # Active heartbeat + rolling history
│   ├── BOOTSTRAP.md.template             # Next-actions section
│   └── DREAMS.md.template                # v4.0 placeholder
└── scripts/
    ├── setup-openclaw.sh                 # Bash setup (one-shot install)
    ├── setup-openclaw.py                 # Python parity script
    ├── heartbeat_compactor.py             # Cron-triggered Lint runner
    ├── lint_runner.py                    # Compat shim (moved in v4.0.0 — see below)
    └── self_test.py                      # T1-T9 validation
```

**Moved in v4.0.0:** `lint_runner.py`'s real implementation now lives at `core/shared-tools/lint_runner.py` — it's cross-harness tooling used by every edition, not adapter-specific. The file at the path above is a deprecate-never-delete compat shim; existing installed vaults and old docs keep working unchanged.

---

## v3.0/v3.5 ↔ OpenClaw Mapping Quick Reference

(Full mapping in `MAPPING.md`.)

| v3.0/v3.5 | OpenClaw | Notes |
|---|---|---|
| `MEMORY_INDEX.md` | `MEMORY.md` | Master pointer index |
| `.claude/rules/agent_orchestration.md` | `AGENTS.md` | Topology + spawning rules |
| (NEW for v3.5) FINAL principles distilled | `SOUL.md` | Identity-stable rules |
| `TIER_C_ACTIVATION.md` + `recommended-addons/` | `TOOLS.md` | Addon registry |
| `memory/user/user_profile.md` (sanitized) | `IDENTITY.md` | PII-redacted |
| `memory/feedback/feedback.md` | `USER.md` | Corrections + preferences |
| `memory/sessions/session_state.md` (current) | `HEARTBEAT.md` | Rolling 3-deep heartbeat |
| `memory/sessions/session_state.md` (next-actions) | `BOOTSTRAP.md` | Where to pick up |
| (v4.0 placeholder) | `DREAMS.md` | Auto-Dream gated |
| Tier 1 (always) | HOT + WARM | Bootstrap auto-load |
| Tier 2 (on resume) | COLD | Conditional load |
| Tier 3 (on demand) | DETAIL + DAILY | Lazy load |

---

## Documentation Discipline

### Purpose

Port the Ultimate Memory Stack to the OpenClaw harness, enabling NAS-class OpenClaw deployments and validating the modular consumer architecture. Establishes the cross-harness pattern that future harness ports will inherit.

### Rationale

- **Convergence validation:** an independent OpenClaw deployment arrived at the same tier model + Obsidian conventions that v3.0 designed from first principles. This adapter codifies that convergence so future deployments inherit it cleanly.
- **Roadmap trajectory:** ships "other-harness compatibility" in PARTIAL form — OpenClaw only, design-validated, ready for cross-machine testing.
- **Modular consumer architecture:** Memory stack is the branded module; agent topology is pluggable. OpenClaw is the first real consumer beyond Claude Code — this adapter sits at the interface between the two pluggable layers.
- **OpenClaw ecosystem research:** prior ecosystem research identified the 6 convergent patterns. Adapter inherits all 6.
- **Option C:** DGM-H deferred from this adapter (was tentatively in scope for this release; reverted to Phase 4+); Option C Lint extensions ship by default.

### Sound reasoning

1. **Ideal-first design:** 9-root file mapping is the cleanest topology — each OpenClaw root file has exactly one v3.0/v3.5 equivalent. No mapping ambiguity.
2. **Documentation discipline:** This README + SKILL.md + MAPPING.md carry all 5 required elements (purpose/rationale/sound reasoning/scope CAN/CANNOT).
3. **Tier A designation:** Adapter is CORE (required for OpenClaw deployment), not Tier C opt-in.
4. **Modular consumer:** Adapter validates the architecture in practice.
5. **Surface-only Lint:** Heartbeat compactor + Option C extensions NEVER auto-mutate; surface only.
6. **Convergence:** Adapter design matches an independent OpenClaw deployment's tier model + frontmatter conventions; cross-harness pattern preserved.
7. **DGM-H deferred:** Adapter explicitly does NOT include DGM-H (deferred following security vetting review).

### Scope — CAN

- Generate 9 OpenClaw root auto-load files from templates
- Map v3.0/v3.5 tier semantics to OpenClaw HOT/WARM/COLD/DETAIL/DAILY
- Set up memory/ subdirectory tree mirroring v3.0/v3.5
- Initialize empty audit_log.jsonl + quarantine_log.jsonl
- Configure edition profile (general-edition; compliance: none / enterprise)
- Install MEMORY_PROTOCOL_EXTENDED §E7 Option C Lint extensions
- Install heartbeat_compactor.py + present cron entry to user
- Run T1-T9 self-test post-install
- Hand off to addon installer Skills (`/install-llmlingua` etc.)
- Be idempotent — re-run safely after partial install
- Log activation per the security-first + documentation discipline standing rules

### Scope — CANNOT

- Install the OpenClaw harness itself (user installs separately)
- Mutate user's crontab (security boundary — present entry, user pastes)
- Install DGM-H (deferred; Phase 4+ candidate)
- Install Auto-Dream (v4.0 candidate, Anthropic beta gated)
- Enable the `healthcare` compliance preset (not shipped in this edition)
- Sync entries across machines (Phase 4+ candidate)
- Port Warden/Sentinel/Vault/Clerk agents to OpenClaw runtime (advisory in AGENTS.md only until OpenClaw runtime supports peer-agent spawning)
- Install unrecognized addons (only the 4 PASS-vetted ones have known Skills)
- Guarantee bootstrap < 60K if user adds large content post-install (compactor surfaces violations; user acts)

---

## Cross-References

- MEMORY_PROTOCOL §1.2 (tier loading)
- MEMORY_PROTOCOL §2 (Context Budget — adapter scales to 60K profile)
- MEMORY_PROTOCOL §4.4 (heartbeat protocol — HEARTBEAT.md mapping)
- MEMORY_PROTOCOL_EXTENDED §E7 (Lint operation — Option C extensions ship by default)
- MEMORY_PROTOCOL §17 (healthcare compliance — NOT activated for general-edition adapter)
- SCHEMA_A18 v1.3 + v1.4 (file-level + PageRank fields)
