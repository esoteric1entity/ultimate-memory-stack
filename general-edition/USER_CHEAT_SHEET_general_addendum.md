# Ultimate Memory Stack — General-Edition Addendum

> **Version:** 1.1 — stable
> **Read this AFTER:** `common-specs/USER_CHEAT_SHEET_core.md`
> **Audience:** Solo developers, software dev, research, writing, education, B2B SaaS, enterprise users
> **Approximate read time:** 4 minutes (skim) · 7 minutes (with the general-edition section)

---

## General-Edition Quickstart

**General-edition specifics:**

| Aspect | General behavior | Cross-ref |
|---|---|---|
| **Compliance preset** | `none` (default), `enterprise`, or `custom` | `<edition>/PROFILE.md` |
| **Audit log (EXTENDED §E3.2)** | OPT-IN (default OFF) — set `audit_log: true` in PROFILE.md to enable | B1 |
| **Quarantine UX (EXTENDED §E3.3)** | Toast at session start: "X entries quarantined — review?"; full workflow Skill available | Skill at `core/audit-quarantine-skill/` |
| **Pattern-key recurrence (§4)** | Threshold = 5 | B6 |
| **Cryptographic signatures (C4)** | HMAC available (T3+, opt-in) | C4 |
| **Lint findings (EXTENDED §E7)** | Surface as suggestions; non-blocking | EXTENDED §E7 |
| **Doc completeness check (Lint #10)** | MEDIUM severity | EXTENDED §E7 |

**General-edition components (all 6 supported):**

| Component | When to install | Tier |
|---|---|---|
| Obsidian vault config | Visual editor preferred | B (recommended) |
| LLMLingua | Token-budget pressure | C (opt-in) |
| Graphiti | Knowledge-graph queries | C (opt-in) |
| Graphify | Codebase memory | C (opt-in) |
| Audit Quarantine Skill | Auto-available; use when needed | A (core) |
| OpenClaw General Edition Adapter | Deploying to an OpenClaw harness | A (core for OpenClaw target) |

**Validation chain:**

| Stage | Target | What |
|---|---|---|
| Stage 1 | A test machine | Dry-run all 6 components |
| Stage 2 | Your production target | Production OpenClaw adapter deployment |
| Stage 3 | Cross-machine | Entry round-trip between two machines |

---

---

## What's Different About General-Edition

You're using general-edition. Three things matter:

1. **YOU choose the compliance preset.** None / enterprise / custom. Pick at install; can change later.
2. **Audit log is OPT-IN.** Default OFF for `none` preset; ON for `enterprise`. Enable manually if you want it on for `none`.
3. **Quarantine is NON-BLOCKING.** Suspicious entries surface as a toast at session start; you review at your pace. No queue blocking.

General-edition is the lighter-touch, general-purpose edition. Most users start with `compliance: none` — that's fine.

---

## Picking Your Preset (5-second guide)

| Your context | Pick |
|--------------|------|
| Personal projects, hobby code, learning | `none` |
| HIPAA / PHI work | Not in general-edition — A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md. |
| You handle business customer PII or you're prepping for SOC2 | `enterprise` |
| Multiple regulatory regimes simultaneously OR very specific needs | `custom` (advanced) |

**Don't overthink it.** Picking `none` and changing later is fine — preset change is a single command.

---

## Compose Extensions for Specific Regimes

If `enterprise` base preset isn't enough, add extensions:

- **`gdpr-profile.md`** — EU jurisdiction; consent tracking; right-to-be-forgotten
- **`soc2-profile.md`** — SOC2 audit prep; change management discipline; access controls
- **`pci-dss-profile.md`** — Payment card data context; aggressive PAN detection

For HIPAA/PHI: A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

Activate at install:
```bash
bash setup.sh --compliance=enterprise --extensions=soc2,gdpr
```

Or after install via PROFILE.md edit.

---

## Toast UX (General-Edition Specific)

When quarantined entries exist:

```
At session start:
  3 entries quarantined since last session. Review? [A]pprove all / [R]eview / [D]efer

If you pick [R]eview:
  Entry 1 of 3: ...
    Quick action: [R]elease / [D]iscard / [DE]fer
    Justification (optional): _
```

General-edition is intentionally lighter — you can defer indefinitely; the queue won't block new writes.

**Tip:** Don't let queue grow past 20. Detection patterns may be misconfigured if many false positives accumulate.

---

## Changing Presets Mid-Deployment

Common scenario: started with `none` for a side project; now you're considering open-sourcing it and want SOC2 audit prep.

```bash
bash setup.sh --change-preset=enterprise
```

What happens:
1. Backup of current PROFILE.md created
2. New preset applied
3. Existing memory entries re-validated against new patterns
4. Any failing entries route to quarantine for review

**Re-validation is non-destructive.** No data lost; just flagged for review.

If you change presets often (more than once a month), reconsider — preset is meant to be relatively stable. Use extensions for nuanced multi-regime needs instead.

---

## When to Choose `custom`

The 3 base presets cover ~95% of deployments. `custom` is for the 5% with sophisticated needs:

- Multiple compliance regimes that need fine-grained composition
- Industry-specific requirements not covered by extensions (FERPA, ITAR, FedRAMP — extensions for these aren't yet built)
- You need to override specific behaviors in ways extensions don't reach

**`custom` requires explicit configuration.** Bootstrap rejects bare `compliance: custom` — you must provide `overrides/compliance.override.md` with at least 1 override. This prevents the "I picked custom but didn't configure anything" footgun.

If you're considering `custom`, read `overrides/compliance-presets.override.md` §5.4 for the full pattern. Most users should pick a base + extensions instead.

---

## HMAC Signatures (T3+ only)

General-edition uses HMAC by default for cryptographic signatures:

- Generate secret at install: `python3 setup.py --generate-hmac-secret`
- Secret derives from your session OR stored in `~/.config/keys/`
- Signatures activate at T3 (when Code Execution is available)
- Without Code Execution: signatures are dormant; you're protected by validation-on-read

Stronger cryptographic guarantees (e.g. Ed25519) are part of the planned institutional edition. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

---

## Common General-Edition Use Cases

### Software development (solo dev)
- Preset: `none`
- Memory entries: architecture decisions, tool choices, framework patterns, debugging insights
- Audit log: usually off
- Best feature: pattern-key promotion (your coding pet peeves become standing rules)

### Research project (R&D non-PHI)
- Preset: `none` or `enterprise` (if business R&D)
- Memory entries: methodology, hypothesis evolution, literature citations
- Audit log: optional
- Best feature: bi-temporal model (hypothesis evolution preserved)

### Writing project (book/article)
- Preset: `none`
- Memory entries: outline state, character/concept tracking, stylistic decisions
- Audit log: usually off
- Best feature: wiki-links + Obsidian compat (visual graph of concepts)

### B2B SaaS (preparing for SOC2)
- Preset: `enterprise`
- Extensions: `soc2`, possibly `gdpr`
- Memory entries: design decisions with change_approver discipline
- Audit log: REQUIRED
- Best feature: SOC2-ready evidence patterns

### Education (teacher or learner)
- Preset: `none` (unless touching student grades — then `enterprise`)
- Memory entries: lesson plans, concept progression, pedagogical decisions
- Audit log: optional unless institution requires
- Best feature: per-project memory bank for course tracking

---

## HIPAA / PHI Work — Institutional Edition

If your work involves PHI or HIPAA-grade enforcement — for example:

- Work that is PRIMARILY in healthcare/regulated R&D (not occasional)
- An institution with strict HIPAA enforcement requirements

then note: A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

General-edition does not ship PHI/HIPAA compliance; its presets are `none`, `enterprise`, and `custom`.

---

## Things You Don't Need to Worry About

- **Sub-agent topology:** General-edition doesn't assume any specific sub-agents. Most users have none. Standard slots (`user`, `orchestrator`, `webfetch`, `external-tool-output`) cover everything.
- **Mirror parity:** Only relevant if you mirror your memory dir to a second location. Most users have a single working directory.
- **Institutional IP review:** That's the institutional edition's concern. General-edition is the public edition and carries no institution-specific content.
- **Multi-machine sync:** Out of scope for v4.0.0. Each deployment is independent.

---

## Cross-references

- `common-specs/USER_CHEAT_SHEET_core.md` (read first)
- `PROFILE.md` (general-edition defaults)
- `DEPLOYMENT.md` (install instructions)
- `PRIVACY_REVIEW.md` (public-release readiness)
- `overrides/compliance-presets.override.md` (preset details)
- `overrides/generic-examples.override.md` (worked examples per use case)
- `EXTENSIONS/` (4 optional regulatory extensions)
