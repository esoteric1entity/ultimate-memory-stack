# Deployment — General-Edition

> **File:** `general-edition/DEPLOYMENT.md`
> **Version:** 1.1 — 2026-06-16
> **Status:** Stable — ships with UMS v3.6.2
> **Audience:** Solo developers, software dev, research, writing, education, B2B SaaS, enterprise contexts

---

## Quick Reference

| Deployment scenario | What you need |
|---------------------|---------------|
| **T0 first deployment** | Manual copy + paste activation prompt — 5 min |
| **T2+ first deployment** | Run `setup.sh` / `setup.ps1` / `setup.py` — 30 sec |
| **Upgrade from v2.0 → v3.0** | Run `MIGRATION_v2_to_v3.md` procedure first |
| **Personal/hobby project** | T0 manual is great fit (no infrastructure needed) |
| **B2B SaaS preparing for SOC2** | T2+ recommended; add `soc2` extension |

---

## Prerequisites

### Minimum (T0)
- A capable agent harness — Claude Code, OpenClaw, or any 9-root-file agent (the manual-paste path works on any of them; the script door needs no agent at all)
- Writable filesystem directory (~30 MB for memory)
- User account that can write to the workspace (and to `.claude/rules/` on Claude Code)

### Recommended (T2+)
- Node.js 18+ for setup script + B11 hybrid retrieval + C6 graph
- Ollama (B9) OR Transformers.js (C9) for semantic search
- More disk if audit log enabled (depends on preset + retention policy)

### Optional (T3+)
- Code Execution for crypto signatures (HMAC default; Ed25519 available for stronger-signature contexts)
- LLMLingua for prompt compression (C6)
- Aider integration for repo-map (C7)

### Optional (T4)
- Skills + Anthropic Dreaming beta for full Tier C activation

---

## Installation Path A — T0 Manual

### Step 1: Copy the directory

Copy `common-specs/` AND `general-edition/` into your working directory.

### Step 2: Open your agent harness

```bash
cd <working-dir>
# then open your agent here — Claude Code: run `claude`; OpenClaw: open your
# workspace at this path; any 9-root-file agent: use its working-dir selector
```

### Step 3: Paste activation prompt

From `common-specs/BOOTSTRAP_PROMPT.md` "The Activation Prompt" section.

### Step 4: Answer setup wizard

7 questions:
1. **Edition confirmation** (auto: `general`)
2. **Identity** (name, role, org, domain)
3. **Active projects** (with goals + status)
4. **Compliance preset selection** ⭐ — pick from 3 options (none / enterprise / custom)
5. **Compliance extensions** (optional) — none / gdpr / soc2 / pci-dss / multiple
6. **Consumer agent topology** (register sub-agent names if any, or "none")
7. **Deployment tier** (auto-detect when possible)

**Most users pick `compliance: none`** at Q4 unless they have explicit regulatory needs.

### Step 5: Verify

T1–T9 self-test runs automatically. All-pass means deployment is operational.

### Step 6: Begin work

Standard memory protocol now active. Memory entries write to `memory/` per SCHEMA_A18 frontmatter.

**Expected total time:** ~5 minutes.

---

## Installation Path B — T2+ Automated

### Step 1: Run setup script

```bash
# Linux / Mac / WSL
bash <path-to-stack>/general-edition/setup.sh

# Windows PowerShell
.<path-to-stack>\general-edition\setup.ps1

# Python (cross-platform)
python <path-to-stack>/general-edition/setup.py

# With pre-selected preset (skip prompt)
bash setup.sh --compliance=none
bash setup.sh --compliance=enterprise --extensions=soc2,gdpr
```

### What the setup script does

1. Validates prerequisites (Node.js available, OS detection)
2. Copies common-specs + general-edition into working dir
3. Initializes `memory/` directory structure
4. Registers the protocol for auto-load — `.claude/rules/memory_protocol.md` on Claude Code; per the harness's own rules/bootstrap convention on OpenClaw and others (the installer detects your harness)
5. Setup wizard (or accepts CLI args for unattended install)
6. Initializes audit log + quarantine ONLY IF user enables them (audit is OPT-IN for general)
7. Generates HMAC secret if Code Execution available (T3+) — stored encrypted
8. Self-test
9. Status report

---

## Tier-Aware Feature Activation

```
Ultimate Memory Stack — general-edition status
============================================
Edition: general
Compliance: none (user-selectable; can change via PROFILE.md or setup.sh --change-preset)
Extensions: (none)
Effective tier: T3 (Code Exec available)

Active features:
  ✓ Tier A — All 20
  ✓ Tier B — B3 CAS, B4 overrides, B5 bi-temporal (available; default `valid_at = created_at`),
             B6 pattern-key (≥5; SUGGEST not auto-promote),
             B8 poisoning defenses (always-on)
  ⏸️ Tier B opt-in — B1 audit log (currently OFF), B2 quarantine workflow,
                     B9 semantic search, B11 hybrid retrieval
  ✓ Tier C at this tier — C4 HMAC signatures (optional), C6 LLMLingua compression

Inactive (preset = none, so don't fire):
  ⏸️ Enterprise PII detection (would activate if preset changes to enterprise)

Quarantine queue: 0 entries (and quarantine is non-blocking anyway for general-edition)
Audit log: disabled (OPT-IN; enable via PROFILE.md edit if needed)
```

---

## Preset Selection Guidance

Choose preset based on your context:

### `none` — Solo Dev / Personal Projects (recommended for most)
- Your work doesn't touch PHI, PII, payment data, or regulated info
- You want lowest friction
- Memory entries are dev decisions, methodology, domain knowledge, project state
- → Pick this

> **PHI / HIPAA context?** A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

### `enterprise` — Business / Regulated
- You handle business-customer PII (names, emails, business identifiers)
- You need explicit consent tracking
- You're working toward SOC2 audit
- → Pick this; add extensions for specific regimes

### `custom` — Advanced (sophisticated needs)
- You need MULTIPLE compliance regimes simultaneously
- The 3 preset options don't cover your context
- You're prepared to write `overrides/compliance.override.md`
- → Pick this; bootstrap requires ≥1 explicit override

---

## Compliance Extensions

Optional add-ons that compose with base preset:

| Extension | When to add | Compose with |
|-----------|-------------|--------------|
| `gdpr-profile.md` | EU jurisdiction OR serving EU subjects | Most common: enterprise |
| `soc2-profile.md` | SOC2 audit prep | Most common: enterprise |
| `pci-dss-profile.md` | Payment card data context | Most common: enterprise + soc2 |

Activate via setup.sh:
```bash
bash setup.sh --compliance=enterprise --extensions=gdpr,soc2
```

---

## Multi-Machine Deployment

Same as biotech-edition multi-machine pattern (independent deployments per machine; no auto-sync).

---

## Edition-Specific Verification (General)

After install, exercise the standing rules + preset detection by asking your agent
(any harness) to remember test values — judge by its response, not via any CLI flag:

- **Universal standing rule fires.** Tell your agent: *"Remember that my fake SSN is 123-45-6789 (testing only)."*
  Expected: ⚠️ the SSN format is flagged and refused/quarantined regardless of preset.
- **Preset `none` — no PHI detection.** Tell your agent: *"Remember the specimen id ABC-12345."*
  Expected: no detection fires (the `none` preset ships no PHI patterns).
- **Preset `enterprise` — PII detection.** Tell your agent: *"Remember customer jane@acme.com."*
  Expected: ⚠️ enterprise PII flagged (consent-tracking required).

---

## Troubleshooting

### "I picked the wrong preset; how do I change it?"
```bash
bash setup.sh --change-preset=<new>
```
Or edit PROFILE.md directly. On preset change, system re-validates existing entries against new patterns; quarantines any that fail.

### "Quarantine queue is growing; can I disable it?"
- Quarantine is always-on by design (B2); cannot disable.
- BUT general-edition is non-blocking — you can defer indefinitely (queue won't block new writes).
- If queue grows >20 entries, consider tightening detection patterns OR reviewing batch via toast.

### "Audit log is empty; should I enable it?"
- Audit log is OPT-IN for general-edition with `none` preset (default OFF).
- Enable via PROFILE.md edit: `audit_log: true`.
- Recommended ON if you handle anything sensitive, even occasionally.

### "Setup script asks for sub-agent topology; I don't have any."
- That's fine. Answer "none" or just press Enter at the topology prompt.
- Standard slots (`user`, `orchestrator`, `webfetch`, `external-tool-output`) cover most use cases.

### "Can I deploy general-edition alongside biotech-edition on the same machine?"
- Not recommended. Pick one edition per working directory.
- If you have multi-context needs, deploy in separate working directories (different memory/ for each).

---

## Post-Installation Checklist

- [ ] Self-test passes
- [ ] Compliance preset confirmed (matches your context)
- [ ] Extensions enabled if needed
- [ ] Consumer agent topology registered (or "none")
- [ ] First session_state.md heartbeat written
- [ ] Mirror parity verified (if applicable)

---

## Cross-References

- `BOOTSTRAP_PROMPT.md`
- `PROFILE.md`
- `MIGRATION_v2_to_v3.md`
- `PRIVACY_REVIEW.md`
- `overrides/compliance-presets.override.md` (preset selection details)
- `overrides/generic-examples.override.md` (use case examples)
- `EXTENSIONS/` (3 selectable regulatory profiles: gdpr / soc2 / pci-dss)
- `../common-specs/MEMORY_PROTOCOL.md`
