# Privacy Review — General-Edition

> **File:** `general-edition/PRIVACY_REVIEW.md`
> **Version:** 1.0 — 2026-05-15
> **Status:** active — public-distribution readiness checklist
> **Audience:** the author (see `/AUTHORS.md`) + future external reviewers

---

## Purpose

General-edition is intended as the **public-distribution candidate** of the Ultimate Memory Stack. This file documents what's been reviewed for public release, what's pending, and the checklist for future external review.

**Default posture:** General-edition is **public-release-pending** — almost-ready, with specific items to confirm before going live.

---

## What's Public-Safe (Already Reviewed)

### Universal Memory Stack Content
| Item | Public-safe? | Source / Verification |
|------|--------------|------------------------|
| Stack architecture (Layers 0-6) | ✅ YES | General design, not proprietary; Phase 2 research is public |
| Schemas (A3, A18, audit_log, quarantine, compliance_profile) | ✅ YES | General data structures; YAML frontmatter convention is public PKM standard |
| Memory Protocol v3.0 | ✅ YES | General operational rules; nothing institution-specific |
| Compliance preset framework | ✅ YES | 3-preset hybrid is a design choice; framework is public |
| Bootstrap prompt v3.0 | ✅ YES | Referencing model is public PKM convention |
| Detection patterns (none, healthcare Layer 1, enterprise) | ✅ YES | Based on HIPAA Safe Harbor / GDPR / standard PII patterns |

### General-Edition-Specific Content
| Item | Public-safe? | Source / Verification |
|------|--------------|------------------------|
| 4 preset definitions | ✅ YES | None of `none`/`healthcare`/`enterprise`/`custom` has institution-specific content |
| 3 overrides (compliance-presets, generic-conflict-resolution, generic-examples) | ✅ YES | Generic patterns for software dev / research / writing / education |
| 4 EXTENSIONS profiles | ✅ YES | All based on public standards (HIPAA, GDPR, SOC2, PCI-DSS) |
| DEPLOYMENT.md | ✅ YES | General install instructions |
| Setup scripts (setup.sh / setup.ps1 / setup.py) | ✅ YES | Open-source-ready code |
| Worked examples in `generic-examples.override.md` | ✅ YES | Solo dev / research / writing / education examples are generic |

---

## What Needs Specific Confirmation

### Authorship + Attribution
- ⏸️ Authorship model (sole author with acknowledgements per `/AUTHORS.md`) — confirm wording is accurate for public release
- ⏸️ Author's institutional affiliation — confirm whether to mention in public release
- ⏸️ Other contributors (research agents are AI-generated; the project owner is the orchestrator)

### License
- ✅ License: **Apache-2.0** (locked)
- General-edition is the public-distribution candidate; biotech-edition remains private
- Comparison reference: Letta (Apache 2.0), Graphiti (Apache 2.0), Cline Memory Bank (MIT-like)

### Phase 2 Research Sources
- ⏸️ All 210 cited sources in the research source master list — verify all citations are accurate
- ⏸️ Compliance with each source's license / terms (most are public papers / GitHub repos with permissive licenses)
- ⏸️ Attribution credits in public README

### No Institution-Specific Content
- ✅ General-edition does NOT reference biotech-edition's institution-specific patterns
- ✅ NGS workflow examples in `biotech-examples.override.md` are biotech-edition-only
- ✅ Common-specs files don't mention the institution (verified via grep)

### Universal Standing Rules
- ✅ No secrets in template files
- ✅ No customer / patient / employee data in worked examples
- ✅ No internal-only tool references

---

## Pre-Release Checklist

Before general-edition can be made public (e.g., GitHub release):

### Content cleanup
- [ ] Verify NO accidental institutional references in common-specs/ (grep check)
- [ ] Verify NO accidental PHI/PII in worked examples
- [ ] Verify NO accidental references to private infrastructure (private drive paths, machine-specific hostnames, etc.)
- [ ] Update README.md (general-edition root) for public audience
- [ ] Add CHANGELOG.md

### Authorship + Attribution
- [ ] Confirm the maintainer's preferred attribution (name, role, affiliation mention)
- [ ] Confirm the coworker's preferred attribution
- [ ] Decide on institutional acknowledgment language
- [ ] Add CONTRIBUTORS.md if multiple human contributors

### License
- [x] License decision: Apache-2.0 (locked)
- [x] LICENSE file present
- [ ] Add SPDX headers to source files (`setup.sh`, `setup.ps1`, `setup.py`)
- [ ] Verify license compatibility with cited Phase 2 sources

### Documentation
- [ ] Public README.md (top-level overview, installation, quick start)
- [ ] Public CONTRIBUTING.md if accepting contributions
- [ ] Public CODE_OF_CONDUCT.md
- [ ] Public SECURITY.md (vulnerability disclosure)
- [ ] Verify all internal-reference DEC-### links resolve OR convert to public references

### Quality
- [ ] Setup scripts tested on Linux + Mac + Windows
- [ ] Cheat sheets render correctly in both MD and PDF
- [ ] All schemas valid YAML
- [ ] All cross-references resolve

### Infrastructure
- [ ] GitHub repository created
- [ ] CI/CD for validation (optional but recommended)
- [ ] Issue templates
- [ ] PR templates

---

## Public-Release Status Tracking

| Item | Status | Date | Owner |
|------|--------|------|-------|
| Content cleanup pass | ⏸️ Pending | — | project owner |
| Authorship confirmation | ⏸️ Pending | — | project owner |
| License decision | ✅ Apache-2.0 | locked | project owner |
| Public README + docs | ⏸️ Pending | — | project owner |
| Setup script testing (multi-OS) | ⏸️ Pending | — | project owner |
| GitHub release | ⏸️ Pending | — | TBD post-clearance |

---

## What's Out of Scope for General-Edition Public Release

These items remain biotech-edition-private (per `biotech-edition/PRIVACY_REVIEW.md`):

- Institution-specific Layer 2 detection patterns
- Vendor-specific NGS assay workflow examples
- Institution-specific customer-account-ID / report-ID / specimen-ID formats
- Internal R&D process details

Users wanting biotech-grade PHI/HIPAA behavior should note: the `healthcare` preset and extension are biotech-edition-reserved — not selectable in general-edition (the installer refuses them). A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

---

## Comparison to Existing Public Memory Stacks

When general-edition goes public, it'll join a landscape that includes:

| Stack | License | Public scope |
|-------|---------|--------------|
| Letta (Zep) | Apache 2.0 | Cloud product + open-source agent framework |
| Graphiti | Apache 2.0 | Open-source temporal knowledge graph |
| Cline Memory Bank | MIT-like (convention, not formal license) | Open-source IDE integration |
| MemoryOS | Apache 2.0 | Research artifact |
| Karpathy LLM Wiki | Public domain (gist) | Idea / pattern |
| **Ultimate Memory Stack (general-edition)** | Apache-2.0 | ✅ Locked |

General-edition's differentiator: documentation discipline, tier-gated design philosophy, and the modularity pattern.

---

## Cross-References

- `PROFILE.md` (general-edition defaults)
- `DEPLOYMENT.md` (install instructions)
- `MIGRATION_v2_to_v3.md` (upgrade procedure)
- `../biotech-edition/PRIVACY_REVIEW.md` (companion — private-distribution focus)
