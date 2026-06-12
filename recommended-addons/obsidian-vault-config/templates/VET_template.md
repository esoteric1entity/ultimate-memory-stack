## VET-{{id}}: {{subject}}

---
id: VET-{{id}}
created_at: {{date}}
last_updated: {{date}}
source_agent: sentinel | orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
subject: {{subject}}
verdict: PASS | REVIEW_REQUIRED | FAIL | ACTIVATED
pipeline: sentinel-mode-1-pre-vetting | sentinel-mode-2-code-review | install-via-skill | manual-install
findings_count: 0
---

- **Date:** {{date}}
- **Session:** {{session}}
- **Verdict:** _PASS / REVIEW_REQUIRED / FAIL / ACTIVATED_
- **Confidence:** HIGH | MEDIUM | LOW (Sentinel)
- **Subject:** _What was vetted (package, code, MCP server, hook, skill, plugin)_

### Findings
1.
2.

### Strengths cited
-
-

### Risks cited
-
-

### Required actions (if PASS with conditions)
1.
2.

### CVE history (if applicable)
- _CVE-YYYY-XXXX: description; affected versions; patch status_

### Defense layers active (if applicable, e.g., typosquat-defended packages)
- L1:
- L2:
- L3:
- L4:

### Cross-references
- [[DEC-XXX]] (vetting authority)
- [[VET-XXX]] (related entry, e.g., upstream package)

### Tags
sentinel, [type: pre-vetting | code-review | activation], [package/component name], [verdict]

---

> **Template author note (DELETE before saving):**
> Standing rule: ALL new tools / skills / MCP / hooks / plugins must pass Sentinel vetting BEFORE install. This template captures the verdict + reasoning. PASS verdicts can have CONDITIONS — document each in "Required actions" and enforce in any installer.
