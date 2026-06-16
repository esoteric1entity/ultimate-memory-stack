# Ultimate Memory Stack — General Edition

> The generic, public-safe edition of the Ultimate Memory Stack.
> Compliance features available but opt-in. Intended for any field, any user, any project.
>
> **Status:** STUB — design pending (begins after the research phase completes)
> **Parent:** `../README.md` (Ultimate Memory Stack overview)

---

## What This Edition Is

The general edition takes the common Ultimate Memory Stack spec and **applies a generic profile**: nothing healthcare-specific is active by default, all compliance features are toggleable, and examples are field-agnostic.

Target audience:
- Solo developers using Claude Code on personal projects
- Researchers in any field (software dev, writing, science, education, law, finance, etc.)
- Open-source community wanting persistent Claude Code memory
- Anyone whose first encounter with this work is via the maintainer's public GitHub release

## How It Differs From the Biotech Edition

The general edition is the common spec with **a profile applied** that:

1. **Section 11 (Healthcare Compliance Profile) — NOT active and NOT selectable in general-edition.** The PHI/HIPAA profile is reserved for the institutional biotech-edition. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.
2. **PHI detection patterns** — REPLACED with generic PII only (SSN, credit card, email in non-profile files)
3. **Conflict resolution hierarchy rank 1** — "Compliance rules (configurable: GDPR / SOC2 / PCI-DSS / none — user picks; PHI/HIPAA is biotech-edition-reserved and not selectable in general-edition)"
4. **Self-test T7** — runs only when user activates a compliance profile
5. **Default examples** — generic (project state, technical decisions, preferences, references) instead of healthcare-flavored
6. **Audit trail emphasis** — present but not central; just normal change tracking

## How It Differs From the Maintainer's Original Personal Memory Stack

That's the original PERSONAL operational stack with healthcare defaults baked in. General edition is the public variant with the healthcare specifics genericized.

| Aspect | Original personal memory stack | general-edition |
|--------|------------------------------|------------------|
| Audience | <your-name> (healthcare R&D) | The whole world |
| Compliance default | Healthcare/HIPAA always-on | Compliance opt-in, no defaults |
| Examples | Healthcare-flavored | Field-agnostic |
| Author/affiliation | (see `/AUTHORS.md`) | Author names only — no affiliation by default |
| Distribution | Personal use | Public GitHub |

## Contents (planned)

```
general-edition/
├── README.md                       ← You are here
├── PROFILE.md                      ← Declares which common-spec sections are active + generic defaults
├── DEPLOYMENT.md                   ← How to install on any Claude Code project
├── overrides/                      ← Edition-specific overrides on top of common-specs/
│   ├── generic-conflict-resolution.override.md
│   ├── compliance-presets.override.md   ← Available compliance presets + how to activate
│   └── generic-examples.override.md     ← Software dev, research, writing examples
├── EXTENSIONS/                     ← Optional compliance profiles users can apply
│   ├── gdpr-profile.md             ← (for European users)
│   ├── soc2-profile.md             ← (for SaaS contexts)
│   └── pci-dss-profile.md          ← (for fintech)
└── PRIVACY_REVIEW.md               ← Public-release readiness check
```

## License Status

Intended to be public open-source. Likely candidates:
- **MIT** — most permissive, broad adoption
- **Apache-2.0** — adds patent grant + mandatory attribution
- **CC-BY-SA-4.0** — share-alike for derivative works

Decision deferred to Phase 4 (deployable iteration phase). Attribution to author (esoteric1entity, sole author) preserved regardless of license choice.

---

> **Status:** STUB | **Design begins:** after the research phase completes
