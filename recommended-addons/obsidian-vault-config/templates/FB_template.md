## FB-{{id}}: {{topic}}

---
id: FB-{{id}}
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
pattern_key: {{stable.dotted.identifier}}
recurrence_count: 1
last_seen: {{date}}
---

- **Date:** {{date}}
- **Session:** {{session}}
- **Trigger:** _What did the user correct, ask for, or prefer?_
- **Correction / preference:**
  _User's exact instruction (quote where possible)_

### Why this matters
_The principle behind the correction — what general rule is being instilled?_

### Application going forward
_How will this change Claude's behavior in future sessions?_

### Pattern-key promotion path (per MEMORY_PROTOCOL §4)

- **Biotech edition:** auto-promote to standing rule when `recurrence_count >= 3`
- **General edition:** suggest promotion when `recurrence_count >= 5`
- **This entry's recurrence_count:** 1 (initial observation)

### Cross-references
- [[DEC-XXX]] (if this feedback challenges or refines a prior decision)
- [[FB-XXX]] (if this is a related earlier feedback)

### Tags
feedback, [topic], [user-preference | correction | standing-rule-candidate]

---

> **Template author note (DELETE before saving):**
> Per MEMORY_PROTOCOL §4 pattern-key promotion: assign a STABLE dotted identifier as `pattern_key`. When the same pattern_key is observed again (next session, different context), increment `recurrence_count` and update `last_seen`. At promotion threshold, this entry promotes to a standing rule in `.claude/rules/`.
>
> Examples of pattern_keys:
> - `tooling.always-prefer-conda-envs`
> - `documentation.purpose-rationale-mandatory`
> - `security.sentinel-vetting-required`
