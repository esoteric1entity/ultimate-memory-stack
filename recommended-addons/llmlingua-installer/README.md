# LLMLingua Installer — Recommended Addon

> **Status:** stable — ships with UMS v3.6.2 (security-reviewed: PASS)
> **Tier:** C (opt-in, not loaded by default — C6 designation)
> **Last updated:** 2026-06-16
> **Authority:** Tier C6 designation + Sentinel vetting verdict (PASS with conditions, all enforced by this installer)

---

## What This Addon Does

**LLMLingua** is a token-level prompt compression library from Microsoft Research (MIT licensed). It uses small-language-model perplexity scoring to identify and remove low-information tokens from long prompts, achieving 5-20× compression with minimal quality loss.

**Why install it on the Ultimate Memory Stack:**
- Token-budget pressure (large memory loads + long working sessions)
- API cost reduction (compounds with prompt caching)
- Compatible with bi-temporal memory entries (compression preserves frontmatter)

**Why it's Tier C (opt-in):**
- Adds runtime overhead (first-use download + per-compression latency)
- Pinned dependencies accumulate CVEs over time
- Upstream is stale — Microsoft Research moved to SecurityLingua

---

## ⚠️ Upstream Status — READ BEFORE INSTALLING

| Property | Value |
|---|---|
| Last upstream release | **2024-04-09 (v0.2.2)** — ~2 years stale |
| GitHub repo | github.com/microsoft/LLMLingua |
| License | MIT |
| Microsoft's successor project | **SecurityLingua** (arXiv:2506.12707, June 2025) |
| CVE history (LLMLingua itself) | None published on GitHub Security Advisories |
| CVE risk (transitive deps) | **Accumulates over time** — pinned `transformers`/`torch` versions don't get security patches automatically |

**Recommendation:** Use LLMLingua if you need prompt compression today, but plan a v3.6+ migration evaluation of SecurityLingua before this pinning becomes unsupported.

---

## Sentinel Vetting Summary

**Verdict:** PASS with conditions
**Confidence:** HIGH (Sentinel)

**Strengths cited by Sentinel:**
- Strongest institutional backing of the 4 packages reviewed (Microsoft Research, CLA-gated contributions)
- No dangerous patterns in code
- MIT license — permissive and compatible
- No published CVEs against the package itself

**Risks cited by Sentinel:**
- Dependency staleness (#1 concern) — pinned `transformers`/`torch` accumulate CVEs over time
- Low/no active development — upstream is in maintenance mode at best
- Microsoft moved on (SecurityLingua) — implies LLMLingua is not the long-term path

**Required actions enforced by this installer:**
1. ✅ Pin `llmlingua==0.2.2` exactly (installer's `requirements.txt`)
2. ✅ Pin compatible `transformers` + `torch` version range (bounded)
3. ✅ Document unmaintained status (this README + SKILL.md Step 0 disclosure)
4. ✅ Plan v3.6+ migration path (this README + DEC-### at activation time)
5. ✅ `pip-audit` pre-install on transitive tree (SKILL.md Step 2)

---

## Installation

### Recommended: via Skill

If your environment supports Claude Code Skills, invoke the installer Skill:

```
/install-llmlingua
```

The Skill walks through the 8-step workflow defined in `SKILL.md`:
1. Confirm intent + disclose upstream status
2. Detect deployment environment
3. pip-audit pre-install
4. Install with exact pin (`requirements.txt`)
5. Smoke test
6. Optional integration with memory protocol
7. Log to vetting log + decision log
8. Hand-off briefing

### Fallback: manual install

Per `INSTALL_LLMLINGUA.md`, run:

```bash
# In your conda env or venv:
pip install pip-audit
pip-audit --requirement requirements.txt   # MUST PASS before next step
pip install -r requirements.txt
python smoke_test.py                       # Verify install
```

If `pip-audit` surfaces HIGH or CRITICAL CVE: STOP. Do not proceed without explicit override + DEC entry.

---

## Documentation Discipline

### Purpose

Provide token-level prompt compression to the Ultimate Memory Stack as an opt-in Tier C capability, enabling cost-conscious operation under token-budget pressure without requiring users to script LLMLingua integration themselves.

### Rationale

- LLMLingua is the most institutionally-backed compression option vetted (Microsoft Research, MIT license, no dangerous patterns)
- Sentinel vetting confirmed PASS with conditions; all conditions are now enforced by this installer
- Per the Tier C6 designation the capability was already designed-in to v3.0; the Tier C opt-in installer was the missing implementation
- This addon is one of 3 PASS-verdict addons proceeding in v3.5 (alongside Graphiti + Graphify)
- A standardized installer prevents user-by-user drift in pin choices, which is the most common source of supply-chain divergence in dependency-heavy ML libraries

### Sound reasoning

1. Per the standing rule: "ALL tools must pass Sentinel vetting" — LLMLingua PASSED with conditions, this installer enforces those conditions
2. Per the ideal-first design principle: "design for the cleanest topology before compromising" — exact pin + bounded transitive range is the cleanest reproducible install
3. Per the documentation discipline: this README + SKILL.md frontmatter capture purpose/rationale/scope (CAN/CANNOT)
4. Per the Tier C (C6) designation: capability is opt-in (not auto-loaded), installer enforces opt-in via Step 5 user prompt
5. Per the PASS verdict: LLMLingua proceeds with its Sentinel-specified guardrails (all enforced here)

### Scope — CAN

- Install LLMLingua at exact pin `==0.2.2` into a user-chosen Python environment
- Pin compatible `transformers` + `torch` + `sentencepiece` versions
- Run `pip-audit` pre-install and block on HIGH/CRITICAL CVEs
- Smoke-test the install via `smoke_test.py`
- Register the addon in `<edition>/PROFILE.md` if user opts to wire it into memory protocol
- Log activation to `vetting_log.md` + `decisions.md` per the vetting and documentation disciplines

### Scope — CANNOT

- Auto-enable LLMLingua without explicit user opt-in (Tier C designation enforced)
- Upgrade beyond `==0.2.2` (would invalidate the Sentinel vetting; requires fresh VET- entry + DEC override)
- Patch transitive CVEs that emerge after install (user must periodically re-audit)
- Install if base Ultimate Memory Stack isn't deployed (Step 1 precondition check)
- Substitute for SecurityLingua-based future approach (v3.6+ migration path documented; not implemented here)
- Operate in offline environments without pre-cached compression model

---

## Files in This Folder

| File | Purpose |
|---|---|
| `SKILL.md` | Claude-executable installer manifest (8-step workflow) |
| `README.md` | This file — addon README with upstream status + vetting summary |
| `requirements.txt` | Pinned dependency manifest (used by Step 2 pip-audit + Step 3 install) |
| `INSTALL_LLMLINGUA.md` | Companion manual install guide (for environments without Skill support) |
| `smoke_test.py` | Post-install verification script (used by Step 4) |

---

## Migration Path to v3.6+

When evaluating SecurityLingua (arXiv:2506.12707) as a successor:

1. **Read the paper** + check the GitHub repo (likely github.com/microsoft/SecurityLingua) for current state
2. **Sentinel vet SecurityLingua** as VET-### entry (full Mode 1 pre-vetting)
3. **Compare deltas:** API compatibility, dependency burden, license, active maintenance
4. **If migration warranted:** capture as DEC-### with full 5-element documentation discipline, create `securitylingua-installer/` mirroring this Skill's pattern
5. **Don't deprecate LLMLingua installer immediately** — keep both available for v3.5 → v3.6 transition window

---

## Cross-References

- Tier C6 designation (LLMLingua/LongLLMLingua compression — designed-in, opt-in)
- Standing rule: all tools must pass Sentinel vetting
- Design principle: ideal-first design
- Documentation discipline (Purpose / Rationale / Sound reasoning / Scope CAN / Scope CANNOT)
- Sentinel vetting verdict for LLMLingua (PASS with conditions)
- `common-specs/TIER_C_ACTIVATION.md` §C6 (now points here)
