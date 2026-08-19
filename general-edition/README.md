# Ultimate Memory Stack — General Edition

> The public, general-purpose edition of the Ultimate Memory Stack — the edition this repository ships.
> Field-agnostic by default; compliance features are opt-in.
>
> **Status:** stable — ships with UMS v4.0.0
> **Parent:** [`../README.md`](../README.md) (Ultimate Memory Stack overview)

---

## What this edition is

The general edition takes the common Ultimate Memory Stack spec and **applies a generic profile**: nothing domain-specific is active by default, all compliance features are toggleable, and examples are field-agnostic. It is the edition delivered by every install door (script / agent / marketplace / manual).

**Target audience:**
- Solo developers using any capable agent harness — Claude Code, OpenClaw, or any 9-root-file agent
- Researchers in any field (software dev, writing, science, education, law, finance, etc.)
- Open-source users wanting persistent agent memory
- Anyone whose first encounter with this work is via the public GitHub release

## Compliance posture

The general edition ships three selectable compliance presets — **`none` / `enterprise` / `custom`** — plus optional `gdpr` / `soc2` / `pci-dss` extensions (see `overrides/compliance-presets.override.md`). Concretely, the general profile:

1. Has **no PHI/HIPAA profile active or selectable** — the setup wizard refuses a `healthcare` preset, which is a reserved value. HIPAA/PHI is out of scope for this edition.
2. Uses **generic PII detection** (SSN, credit card, email) rather than PHI patterns.
3. Treats compliance rules as **configurable** (`gdpr` / `soc2` / `pci-dss` / `none` — user picks).
4. Runs the self-test PII check (T7) **only when** a compliance profile is active.
5. Ships **field-agnostic examples** (project state, technical decisions, preferences, references).

## Contents

```
general-edition/
├── README.md                       ← You are here
├── PROFILE.md                      ← Declares which common-spec sections are active + generic defaults
├── DEPLOYMENT.md                   ← Install + deployment guide (any harness)
├── setup.sh / setup.py / setup.ps1 ← Edition installers (invoked by the top-level setup-memory-stack.*)
├── MIGRATION_v2_to_v3.md           ← v2.0 → v3.x upgrade procedure
├── MIGRATION_v3.6_to_v4.0.md       ← v3.6.x → v4.0.0 upgrade procedure (current)
├── USER_CHEAT_SHEET_general_addendum.md  ← General-edition best-practices addendum
├── overrides/                      ← Edition-specific overrides on top of common-specs/
│   ├── generic-conflict-resolution.override.md
│   ├── compliance-presets.override.md   ← Selectable presets + how to activate
│   └── generic-examples.override.md     ← Software dev, research, writing examples
├── EXTENSIONS/                     ← Optional compliance profiles
│   ├── gdpr-profile.md             ← EU jurisdiction + consent tracking
│   ├── soc2-profile.md             ← SOC2 Trust Services Criteria
│   ├── pci-dss-profile.md          ← Payment-card data context
│   └── healthcare-profile.md       ← reserved value (not selectable)
└── PRIVACY_REVIEW.md               ← Public-release readiness check
```

## License

[Apache-2.0](../LICENSE) — locked. Attribution to **esoteric1entity** (sole author) preserved per [`../AUTHORS.md`](../AUTHORS.md).

---

> Version history lives in [`../CHANGELOG.md`](../CHANGELOG.md).
