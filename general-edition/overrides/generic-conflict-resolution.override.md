# Override — Generic Conflict Resolution (General-Edition)

> **File:** `general-edition/overrides/generic-conflict-resolution.override.md`
> **Version:** 1.0 — 2026-05-15
> **Overrides:** `common-specs/MEMORY_PROTOCOL.md` §3 (Conflict Resolution Hierarchy)
> **Override mechanism:** Per B4 — preset-dependent compliance rank for general-edition
> **Status:** stable
> **Design basis:** B7 (3-preset hybrid); modular consumer architecture

---

## §3 Conflict Resolution Hierarchy (General-Edition Implementation)

This section REPLACES `common-specs/MEMORY_PROTOCOL.md` §3.

When memory files contradict each other, resolve in this order. General-edition's key difference from biotech-edition: **compliance rank is PRESET-DEPENDENT** — `none` preset allows more user flexibility; `enterprise` is moderately strict; `custom` is user-defined.

### Resolution order (highest authority wins)

The hierarchy structure is identical to common-spec, but the strictness of rank 1 varies by active preset:

1. **Compliance rules — preset-dependent**
   - `compliance: none` → Standing rules only (no secrets, no PII/PHI universal block) ranked here; user-instruction can override most other compliance behavior
   - `compliance: enterprise` → GDPR + SOC2 baseline ranked here; user-instruction CANNOT override consent + audit requirements
   - `compliance: custom` → User-defined enforcement level; see `compliance.override.md`

2. **Live security decisions**
   - Vetting verdicts, access restrictions, quarantine routing (same as common-spec)

3. **User's live instruction**
   - What user just told you this session
   - For `none` preset: can override most non-standing-rule behaviors
   - For `enterprise` preset: cannot override compliance rule 1

4. **`feedback.md`** (explicit corrections)
5. **`decisions.md` — FINAL**
6. **`session_state.md`**
7. **`decisions.md` — TENTATIVE**
8. **`project_context.md` / project memory-bank**
9. **`user_profile.md`**

### Bi-temporal precedence (B5)

Same as common-spec — entries with `invalid_at` set deprioritize unless point-in-time queries explicitly request that time.

### Preset-driven compliance behavior comparison

| Aspect | `none` | `enterprise` | `custom` |
|--------|--------|--------------|----------|
| Standing rules enforcement | Strict (always-on) | Strict | Strict |
| Preset-specific detection enforcement | OFF (no detection) | Moderate (PII warning) | Configured |
| User instruction override of detection | N/A | NO (for consent + audit) | Configured |
| Friction level | LOW | MEDIUM | Configured |

### Practical examples by preset

#### `none` preset

**Example:** User says "store this email address as a contact reference"
**Response:** Allowed. `none` preset doesn't detect emails. Memory entry written.

**Example:** User adds an SSN to a note ("My test SSN is 123-45-6789")
**Response:** REFUSE — even at `none`, the universal standing rule (no secrets / no PII) blocks SSN format. This is the universal floor; not preset-dependent.

> A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

#### `enterprise` preset

**Example:** User says "log this contractor name — we have explicit consent"
**Response:** Allow IF entry includes `consent_at` and `consent_basis` frontmatter fields. REFUSE if consent fields missing.

**Example:** User says "log this customer email; consent is implicit from our terms-of-service"
**Response:** Warn — implicit consent isn't sufficient for enterprise preset. Require explicit `consent_basis: tos-acceptance` annotation.

#### `custom` preset

Behavior depends on user-defined override; preset-specific examples documented in `overrides/compliance.override.md`.

### When user is frustrated by enforcement

For non-`none` presets:
1. Acknowledge friction
2. Explain preset rationale (you chose this; here's why it's enforcing)
3. Offer to switch to lighter preset (`setup.sh --change-preset=none`)
4. Note: switching to lighter preset re-validates existing entries with new patterns

For `none` preset:
1. Standing rule violations are non-negotiable (secrets, basic PII)
2. If user genuinely needs to store sensitive data, the memory stack is the wrong tool — they need a different storage system

### Differences from biotech-edition conflict-resolution.override.md

| Aspect | Biotech-edition | General-edition |
|--------|------------------|-----------------|
| Compliance rank 1 strictness | ABSOLUTE (no exceptions) | PRESET-DEPENDENT (strict for enterprise; lighter for none) |
| User can change preset | NO (locked to healthcare) | YES (via setup.sh or PROFILE.md edit) |
| BAA-coverage user reasoning | Never honored | Never honored (same rule, different reason — preset framework doesn't model BAA) |
| Quarantine UX on detection | Blocking workflow | Non-blocking toast |
| Standing rules (universal) | Same | Same |

---

## §Cross-References

- Parent: `../../common-specs/MEMORY_PROTOCOL.md` §3 (overridden by this file)
- `./compliance-presets.override.md` (preset implementation details)
- `../PROFILE.md` (user-selectable defaults)
- `../../common-specs/SCHEMA_compliance_profile.md` §5 (preset definitions)
- The institutional edition applies a stricter conflict-resolution posture (planned for a future release; not shipped publicly)
- Design notes: B7 3-preset hybrid; modular consumer architecture
