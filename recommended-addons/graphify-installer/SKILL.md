---
name: install-graphify
description: Installer for Graphify codebase symbol graph addon (Tier C C3, adjacent tool). Installs graphifyy==0.8.21 EXACTLY (note double-y — single-y "graphify" is an UNRELATED package and a typosquat risk; this Skill enforces the correct package). Includes L1-L5 typosquat defense (security-vetting conditions plus hash-pinned install). Use when the user asks to install, deploy, activate, or enable Graphify / Tree-sitter symbol graph for their memory stack deployment.
version: "1.0"
authors: ["esoteric1entity"]
decision_authority: ["security-first vetting", "ideal-first design", "documentation discipline", "Tier C adjacent tool", "PASS-verdict addon batch"]
vetting_reference: pre-release security vetting (2026-05-27, verdict PASS with conditions)
edition: any
tier: C (opt-in; not loaded by default)
license: MIT (Graphify AT THE PINNED 0.8.21 — upstream relicensed to Apache-2.0 by 0.9.48; verified 2026-08-22); installer license: Apache-2.0
upstream_status: active (last release 2026-05-27 v0.8.21 — 116 releases in ~8 weeks)
maintainer: PyPI account `captainturbo` / GitHub account `safishamsi` (Safi Shamsi, MSc Data Science, University of Birmingham — same human; two account names)
key_risk: TYPOSQUAT — `pip install graphify` (single-y) installs UNRELATED package; correct is `graphifyy` (double-y)
defense_layers: L1 bash-guard typosquat pattern + L2 installer name verification + L3 README warning + L4 exact version pin + L5 hash-pinned install (--require-hashes)
---

# Install Graphify Codebase Symbol Graph — Skill Workflow

When this Skill is invoked (typically via `/install-graphify` slash command or when the user asks Claude to install/deploy/activate Graphify), execute the workflow below **IN ORDER**.

⚠️ **CRITICAL: This installer ONLY uses `graphifyy` (DOUBLE-y) on PyPI.** Single-y `graphify` is an UNRELATED package and a typosquat risk. The Skill enforces this at multiple layers (L1-L5 defense per security-vetting conditions plus hash pinning).

---

## Step 0 — Confirm Install Intent + Typosquat Warning

```
👋 You're about to install Graphify (codebase symbol graph addon).

What Graphify does:
  - Tree-sitter-based symbol extraction across 31 programming languages
  - Builds queryable graph of definitions, references, and call sites
  - Outputs ingested as Layer 1 reference artifact in the memory stack
  - Tier C C3: adjacent tool (Skill registration validated on a live deployment)

⚠️  TYPOSQUAT WARNING — PACKAGE NAME IS DOUBLE-Y:
  - CORRECT:    pip install graphifyy==0.8.21    ← DOUBLE-y
  - INCORRECT:  pip install graphify             ← SINGLE-y (UNRELATED package, typosquat risk)
  - This Skill enforces the correct name at 5 defense layers (L1-L5)

Vetting: pre-release security review 2026-05-27 (verdict PASS with conditions)
License: MIT (permissive)
Upstream: active (116 releases in ~8 weeks; SECURITY.md with 48h response SLA)
Tier: C (opt-in, not loaded by default)

Continue with install? [Y/n]:
```

---

## Step 1 — L1 Defense: bash-guard Typosquat Pattern (Document Required Hook)

**Per security-vetting condition #3:** the deployment's bash-guard.sh hook should block `pip install graphify` (single-y) at OS level.

Check whether the user's deployment has the typosquat pattern in `.claude/hooks/bash-guard.sh`:

```bash
# Pattern to check for:
grep -n "pip install graphify[^y]" "<working-dir>/.claude/hooks/bash-guard.sh" 2>/dev/null
```

If pattern is NOT present, surface the recommendation to the user:

```
ℹ️  L1 Defense — bash-guard pattern NOT detected.

Recommended addition to <working-dir>/.claude/hooks/bash-guard.sh:

  # Graphify typosquat defense (security-vetting condition)
  # Block single-y "graphify" (UNRELATED package); allow double-y "graphifyy"
  if echo "$COMMAND" | grep -qE '\bpip install graphify(\s|$|=)'; then
    if ! echo "$COMMAND" | grep -qE '\bpip install graphifyy'; then
      echo "BLOCKED: 'pip install graphify' (single-y) — typosquat risk."
      echo "Use the install-graphify Skill (pinned to graphifyy==0.8.21, double-y)."
      exit 1
    fi
  fi

Add this pattern? [Y/n]:
```

If yes: present the patch and ask user to apply manually (this Skill does NOT mutate hooks — security boundary).
If no: log the warning to `audit_log.jsonl` and proceed.

---

## Step 2 — L2 Defense: Installer Name Verification (Already Active)

This Skill's `requirements.txt` ONLY contains `graphifyy==0.8.21` (double-y exact pin). Any drift would require editing this file, which is the L2 defense layer.

Verify the manifest is intact:

```bash
grep -E '^graphifyy==0\.8\.21$' <path-to-this-skill>/requirements.txt
```

If grep returns no match, STOP. The installer's manifest has been tampered with; do not proceed.

---

## Step 3 — L3 Defense: User-Facing Warning in README (Already Present)

`README.md` in this folder contains an explicit "DOUBLE-Y" warning section. No action needed in workflow; warning is part of the documentation surface.

---

## Step 4 — L4 Defense: Exact Pin (Not Floor) in requirements.txt

The pin is `graphifyy==0.8.21` (EXACT), not `>=0.8.21`. Active upstream (~116 releases in 8 weeks) means new versions need fresh Sentinel vetting before this pin can advance.

**Do NOT relax to floor pin** without a fresh VET-### entry + DEC override.

---

## Step 5 — Pre-Install Security Audit

```bash
# In INSTALL_ENV:
pip install pip-audit
pip-audit --requirement <path-to-this-skill>/requirements.txt
```

### Dependency freshness check (informational)

Before installing, see what upstream looks like today versus what this add-on pins:

```bash
python <path-to-this-skill>/preflight.py
```

It prints, per dependency, the constraint this package ships against the latest
version on PyPI and when that version was published — so an abandoned
dependency is visible BEFORE you install rather than months later. It never
blocks the install and never edits anything; being offline is not a finding.
Advancing a pin is a security-vetting decision, not a mechanical refresh.


**Outcomes:**
- **No vulnerabilities** → proceed to Step 6
- **HIGH or CRITICAL CVE** → STOP. Surface CVE. Capture DEC entry before any override.
- **LOW or MEDIUM CVE** → proceed with disclosure in activation log.

Log to `audit_log.jsonl` per LLMLingua/Graphiti pattern.

---

## Step 6 — Install Graphify with Exact Pin

```bash
# In INSTALL_ENV (Conda or venv activated). Check your version first:
python --version

# Then install from the lock matching it (3.10 / 3.11 / 3.12 / 3.13):
pip install --require-hashes -r <path-to-this-skill>/locks/requirements-py3.12.lock
```

`requirements.txt` states what versions are ACCEPTABLE; the lock states exactly
what you GET, verified by hash. For a package whose headline risk is a
**typosquat**, this matters more than usual: `--require-hashes` makes pip refuse
any artifact whose hash is not listed, so a substituted distribution fails
closed. That is an L5 defense on top of the exact pin (L4). The locks are
universal — one file per Python version covers every platform.

Top-level requirements (`requirements.txt`):
- `graphifyy==0.8.21` (EXACT — typosquat defense)
- `tree-sitter>=0.23.0,<0.26` (parser engine; floor is graphifyy 0.8.21's own
  declared minimum, ceiling is ours — 0.8.21 sets no upper bound, so an
  upstream tree-sitter release could otherwise break a pinned graphifyy)

**Fall back to the manifest only if no lock matches your Python version (locks ship for 3.10 / 3.11 / 3.12 / 3.13):**

```bash
pip install -r <path-to-this-skill>/requirements.txt
```

**Do NOT use `pip install graphify`** — that installs an UNRELATED single-y package.
**Do NOT use a bare `pip install graphifyy`** — that pins nothing and allows version drift.

---

## Step 7 — Verify Installed Package Identity

After install, verify the package metadata to confirm L2 defense held:

```bash
pip show graphifyy
```

Expected output should include:
- `Name: graphifyy`
- `Author: Safi Shamsi` (or `captainturbo`)
- `License: MIT`
- `Version: 0.8.21`

If `Name` is `graphify` (single-y) OR the maintainer is unexpected, the install failed L2 defense. STOP and surface the issue.

---

## Step 8 — Smoke Test

```bash
python <path-to-this-skill>/smoke_test.py
```

Verifies:
1. Module `graphify` imports (single-y — the module name the `graphifyy` distribution ships by upstream design)
2. L2 identity check: installed **distribution** is `graphifyy` (double-y), version 0.8.21, via package metadata — this is the typosquat defense
3. Tree-sitter language pack loads
4. Parses a test code snippet + extracts symbols; symbol count is non-zero (round-trip works)

**On failure:** uninstall and surface error. No half-installed state.

---

## Step 9 — Register with Memory Stack (Optional Integration)

```
Wire Graphify output into the memory stack as Layer 1 reference artifact?
  (a) Yes — graph output stored at memory/references/graphify/ and indexed
  (b) No — install only; user runs Graphify ad-hoc on demand
```

If yes, add to `<working-dir>/memory/user/USER_OVERRIDES.md`:
```yaml
addons:
  graphify:
    enabled: true
    version: "0.8.21"           # EXACT — typosquat defense + pin contract
    package_name: "graphifyy"   # NEVER omit — defense layer reinforcement
    output_path: ./memory/references/graphify/
    language_packs:
      - python
      - javascript
      - typescript
      # (others on demand)
```

---

## Step 10 — Subscribe to Security Advisories (L6 Optional)

**Per security-vetting condition #4 (monthly review cadence) + optional L6 Sigstore monitoring:**

```bash
# Watch the repo for security advisories:
gh api -X PUT /repos/safishamsi/graphify/subscription -f subscribed=true
```

OR via browser: github.com/safishamsi/graphify → Watch → Custom → check "Security advisories"

Document subscription in vetting log entry.

---

## Step 11 — Log Activation

Append VET-### entry to `<working-dir>/memory/security/vetting_log.md`:

```markdown
### VET-###: Graphify activated (`pip install graphifyy==0.8.21`)

---
id: VET-###
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: orchestrator
source_session: <N>
status: active
schema_version: "3.0"
subject: graphifyy==0.8.21 (NOTE: double-y; typosquat defense in place)
verdict: ACTIVATED
pipeline: install-graphify Skill v1.0
defense_layers_active: [L1, L2, L3, L4]   # append L5 ONLY if the lock path was used
---

- **Date:** <today>
- **Verdict:** ACTIVATED (Tier C — adjacent tool)
- **Package:** graphifyy (DOUBLE-y; verified via pip show in Step 7)
- **Version:** 0.8.21 (EXACT pin)
- **L1 bash-guard:** [added | not added — user choice]
- **L2 installer manifest:** intact (verified Step 2)
- **L3 README warning:** present
- **L4 pin discipline:** enforced (==, not >=)
- **L5 hash-pinned install:** [enforced via `locks/` | NOT applied — manifest fallback used]
- **L6 security subscription:** [enabled | skipped]
- **Tags:** tier-c, activation, graphify, addon, typosquat-defended
```

Append corresponding DEC-### entry per the documentation discipline.

---

## Step 12 — Brief User on Operational Notes

```
✅ Graphify installed (graphifyy==0.8.21 in <INSTALL_ENV>)
✅ Defense layers active: L1 (bash-guard) · L2 (manifest) · L3 (README) · L4 (exact pin)
   L5 (hash pin): report ONLY if the lock path was used, not the manifest fallback

Operational notes:
  - Active upstream (116 releases in 8 weeks) — re-run Sentinel vetting monthly
  - Pin update path: new VET-### entry + DEC override required before bumping
  - Per the monthly review cadence vetting condition: set a calendar reminder for 30 days out
  - Run Graphify: graphifyy --help to see CLI options
```

---

## Compliance Cross-References

| Step | Action | Decision authority |
|---|---|---|
| 0 | Intent + typosquat warning | documentation discipline + vetting condition #5 |
| 1 | L1 bash-guard pattern | vetting condition #3 + security-first vetting |
| 2 | L2 manifest verification | defense in depth |
| 3 | L3 README warning | documentation discipline |
| 4 | L4 exact pin | vetting condition #1 |
| 5 | L5 hash-pinned closure (`--require-hashes`) | supply-chain integrity |
| 5 | pip-audit | security-first vetting |
| 6 | Install with exact pin | vetting condition #1 |
| 7 | Verify package identity | vetting condition #2 |
| 8 | Smoke test | ideal-first design |
| 9 | Register with stack (opt) | Tier C C3 adjacent tool |
| 10 | Security subscription | vetting condition #4 |
| 11 | Log activation | security-first vetting + documentation discipline |
| 12 | Hand-off | ideal-first design |

---

## What This Skill CANNOT Do

- **Cannot mutate `.claude/hooks/bash-guard.sh`** — security boundary; user must add L1 pattern manually
- **Cannot guarantee L1 defense if user skips it** — strongly recommended but advisory
- **Cannot prevent user from running `pip install graphify` directly** outside this Skill (L1 bash-guard is the only catch for direct CLI use)
- **Cannot upgrade beyond `==0.8.21`** without fresh Sentinel vetting + DEC override (defense layer #4)
- **Cannot install language packs for Tree-sitter** beyond defaults — user must run `graphifyy install <lang>` per upstream docs
- **Cannot auto-subscribe to security advisories** without `gh` CLI or browser access
