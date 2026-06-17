# Graphify Installer — Recommended Addon

> **Status:** stable — ships with UMS v3.6.2 (security-reviewed: PASS)
> **Tier:** C (opt-in; not loaded by default per the C3 designation)
> **Last updated:** 2026-06-16
> **Authority:** C3 (Tier C adjacent tool) · Sentinel vetting PASS

---

## ⚠️ TYPOSQUAT WARNING — READ FIRST

**The package name is `graphifyy` (DOUBLE-y).** The single-y `graphify` on PyPI is an UNRELATED package and a typosquat risk.

| Command | Result |
|---|---|
| ✅ `pip install graphifyy==0.8.21` | Installs the vetted Tree-sitter symbol graph tool |
| ❌ `pip install graphify` | Installs an UNRELATED package — DO NOT USE |
| ❌ `pip install graphifyy` (no pin) | Installs latest version (uncalibrated; needs fresh Sentinel vetting) |

**This installer enforces the correct name at 4 defense layers (L1-L4, per the Sentinel vetting conditions).**

---

## What This Addon Does

**Graphify** (PyPI: `graphifyy`) is a Tree-sitter-based codebase symbol graph tool from Safi Shamsi (MSc Data Science, University of Birmingham). It extracts definitions, references, and call sites across 31 programming languages and produces a queryable graph.

**Why install it on the Ultimate Memory Stack:**
- Layer 1 reference artifact for code-context-aware memory
- 31-language support (Python, JS, TS, Rust, Go, Java, C++, more)
- Designed-in adjacent tool (C3)
- Skill registration is validated — already battle-tested in the deployment chain

**Why it's Tier C (opt-in):**
- Most projects don't need codebase-graph-aware memory
- C3 designation as adjacent tool (not core)
- Active upstream means pins need periodic re-vetting

---

## Defense Layers (L1-L4)

| Layer | What it is | Where it lives | Enforced by |
|---|---|---|---|
| **L1** | bash-guard typosquat pattern blocking `pip install graphify` (single-y) | `.claude/hooks/bash-guard.sh` | User (Skill recommends + presents patch) |
| **L2** | Installer manifest with double-y exact pin | `requirements.txt` (this folder) | This installer |
| **L3** | README user-facing warning | `README.md` (this file) | Documentation |
| **L4** | Exact version pin `==0.8.21` (not floor) | `requirements.txt` | This installer |
| L5 (optional) | Sigstore signature verification | Future enhancement | Not yet implemented |

**Defense in depth.** Each layer independently catches the typosquat at a different point in the install flow:
- L1 catches direct CLI typos (`pip install graphify`) at the OS level
- L2 catches manifest tampering (`requirements.txt` edited to use single-y)
- L3 alerts the user before invoking the Skill
- L4 prevents inadvertent version drift via floor pin

---

## Sentinel Vetting Summary (2026-05-27)

**Verdict:** PASS with conditions
**Confidence:** HIGH (Sentinel)

**Strengths cited:**
- Excellent published `SECURITY.md` (URL allowlist, path-traversal guards, XSS-safe labels)
- 48-hour security response SLA committed by maintainer
- MIT license — permissive
- Active maintenance (116 releases in ~8 weeks at vetting time)

**Risks cited:**
- **Typosquat surface (#1 concern):** single-y `graphify` on PyPI is unrelated and dangerous
- Active upstream means version churn — pins need periodic re-vetting

**Required actions enforced by this installer:**
1. ✅ Pin EXACT version `graphifyy==0.8.21` (requirements.txt; L4 defense)
2. ✅ Explicit name check in installer Skill (SKILL.md Step 7; L2 defense)
3. ✅ bash-guard.sh typosquat pattern recommended (SKILL.md Step 1; L1 defense)
4. ✅ Monthly review cadence (SKILL.md Step 12; calendar reminder)
5. ✅ Document in README (this file; L3 defense)

---

## Installation

### Recommended: via Skill

```
/install-graphify
```

The Skill walks through the 12-step workflow defined in `SKILL.md`:
intent + typosquat warning → L1 bash-guard check → L2 manifest check → L3 README acknowledged → L4 exact pin → pip-audit → install → identity verification → smoke test → optional integration → security subscription → activation logging → operational briefing

### Fallback: manual install (with all 4 defense layers asserted by user)

Per `INSTALL_GRAPHIFY.md`:

```bash
# In your conda env or venv:
pip install pip-audit
pip-audit --requirement requirements.txt   # MUST PASS

pip install -r requirements.txt            # uses graphifyy==0.8.21
pip show graphifyy                         # verify package identity (NOT 'graphify')
python smoke_test.py                       # verify install works
```

---

## Documentation Discipline

### Purpose

Provide codebase symbol-graph capability to the Ultimate Memory Stack via Graphify (Tree-sitter, 31 languages), as an opt-in Tier C adjacent tool with full L1-L4 typosquat defense per the Sentinel vetting conditions.

### Rationale

- Graphify is the most institutionally-secured of the 4 packages vetted (excellent SECURITY.md, 48h response SLA, published threat model)
- Sentinel vetting confirmed PASS with conditions; all conditions are enforced by this installer
- The C3 capability was designed-in to v3.0 as an adjacent tool
- The Skill registration pattern is validated
- This addon is one of 3 PASS-verdict addons proceeding in v3.5
- Typosquat defense at 4 independent layers — defense in depth — is appropriate for active upstream + similar-name-on-PyPI conditions

### Sound reasoning

1. Per the security-first standing rule: Graphify PASSED Sentinel vetting; installer enforces all 5 conditions
2. Per the ideal-first design principle: 4-layer typosquat defense is the cleanest topology for active-upstream + similar-name conditions
3. Per the documentation discipline: this README + SKILL.md capture purpose/rationale/scope (CAN/CANNOT) + typosquat warning surfaces in 3 distinct places (frontmatter, Step 0, this README)
4. Per the C3 Tier C designation: capability is opt-in (not auto-loaded); installer enforces opt-in via Step 9 user prompt
5. The registration pattern is battle-tested; this Skill formalizes it
6. Graphify proceeds with its Sentinel-specified guardrails (one of the 3 PASS-verdict addons)

### Scope — CAN

- Install Graphify at exact pin `graphifyy==0.8.21` into a user-chosen Python environment
- Recommend L1 bash-guard pattern (user applies manually)
- Verify L2 manifest integrity at install time
- Surface L3 README warning at Skill invocation
- Enforce L4 exact pin (not floor)
- Run `pip-audit` pre-install and block on HIGH/CRITICAL CVEs
- Verify installed package identity via `pip show` (catches L2 bypass)
- Smoke-test the install via `smoke_test.py`
- Register the addon in `<edition>/PROFILE.md` if user opts to wire into memory protocol
- Subscribe to upstream security advisories
- Log activation per the security-first and documentation-discipline standing rules

### Scope — CANNOT

- Mutate `.claude/hooks/bash-guard.sh` (security boundary — user must apply L1 manually)
- Prevent typosquat if user invokes `pip install graphify` directly outside the Skill (L1 bash-guard is the only catch)
- Auto-bump pin beyond `==0.8.21` without fresh Sentinel vetting + DEC override
- Manage Tree-sitter language pack installs beyond defaults (user runs `graphifyy install <lang>`)
- Auto-subscribe to security advisories without `gh` CLI or browser access
- Validate Sigstore signatures (L5 not yet implemented; future enhancement)
- Catch typosquat if the L2 manifest itself is tampered (other defense layers must catch)

---

## Files in This Folder

| File | Purpose |
|---|---|
| `SKILL.md` | Claude-executable installer manifest (12-step workflow with L1-L4 defense) |
| `README.md` | This file — addon README with typosquat warning + vetting summary |
| `requirements.txt` | Pinned manifest (L2 defense layer) |
| `INSTALL_GRAPHIFY.md` | Companion manual install guide |
| `smoke_test.py` | Post-install verification (includes L2 package identity check) |

---

## Cross-References

- `common-specs/TIER_C_ACTIVATION.md` §C3 (Graphify activation guide)
