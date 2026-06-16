# Override — Generic Examples (General-Edition Use Cases)

> **File:** `general-edition/overrides/generic-examples.override.md`
> **Version:** 1.0 — 2026-05-15
> **Overrides:** `common-specs/BOOTSTRAP_PROMPT.md` Step 7 (Setup Wizard examples)
> **Override mechanism:** Per B4 — provides general-edition-specific worked examples for setup wizard
> **Status:** stable
> **Design basis:** B7 (3-preset hybrid); modular consumer architecture

---

## Purpose

Provide worked examples of general-edition deployments across 4 common contexts:
1. **Software development** — building applications, libraries, services
2. **Research projects** — academic / industrial R&D not touching PHI
3. **Writing projects** — books, articles, documentation, content creation
4. **Education** — teaching, learning, course materials

Each example walks through the bootstrap wizard, expected outcomes, and common memory entries.

---

## Example 1: Software Development (Personal Project)

**Context:** Developer building a web app side project (no PHI, no compliance concerns).

### Bootstrap wizard answers

```
Q: Edition selection
> general

Q: Compliance preset
> none (recommended)

Q: Identity
  Name: <developer name>
  Role: Software developer
  Org: (personal)
  Domain: Web development (React + Node.js + Postgres)

Q: Active projects
  - "my-side-app" — Real-time chat app with WebSocket backend. Active.

Q: Compliance extensions
> (none)

Q: Consumer agent topology
> none (just user + orchestrator)

Q: Deployment tier
  Code Execution: enabled
  Node.js: yes
  Skills: enabled (testing)
  Web Search: enabled
  → Current effective tier: T3+ (close to T4)

Q: Pet peeves
  - Don't add comments to code unless explaining "why"
  - Don't suggest premature optimizations
  - Don't refactor working code I didn't ask about
```

### Expected memory entries

- Architecture decisions: "Chose WebSocket over Server-Sent Events for bidirectional"
- Tool choices: "Pinned PostgreSQL 16 for jsonb improvements"
- Coding conventions: "ES2023 modules; no CommonJS"
- Domain knowledge: project-specific concepts, business logic
- Performance notes: "ChatRoom render hot path — memoize MessageList"

### What memory stack provides

- **Tier 1 fast loading:** session_state + user_profile every session
- **Decisions promoted at >5:** auto-organize architectural choices
- **Pattern-key promotion (≥5 for general):** developer pet peeves become standing rules
- **Bi-temporal:** decisions evolve over project lifecycle ("WebSocket was good in 2026-05; switched to gRPC in 2026-08 — both decisions preserved")
- **Wiki-links inline:** `[[DEC-024]]` cross-references render in Obsidian for visual graph

---

## Example 2: Research Project (R&D, No PHI)

**Context:** Industrial R&D scientist working on materials science (or any non-PHI domain).

### Bootstrap wizard answers

```
Q: Edition selection
> general

Q: Compliance preset
> none (recommended) — no PHI, no PII handling

Q: Identity
  Name: <researcher name>
  Role: Research scientist
  Org: <company>
  Domain: Materials science — polymer composites

Q: Active projects
  - "comp-001" — Carbon fiber composite tensile strength characterization
  - "comp-002" — Polymer matrix optimization for high-temp applications

Q: Compliance extensions
> (none — research data is non-regulated)

Q: Consumer agent topology
  - researcher (lit-review agent)
  - analyst (data analysis agent)

Q: Deployment tier
  All features enabled → T4

Q: Pet peeves
  - Don't make up references; cite real papers only
  - Always note data provenance
  - Don't oversimplify domain concepts
```

### Expected memory entries

- Methodology: "Use ASTM D638 for tensile testing"
- Tool decisions: "Switching from Origin to Python + pandas for data analysis"
- Literature: "Smith et al. (2024) showed X for similar composites"
- Hypotheses: "Working hypothesis: cross-linking density affects T_g linearly under 200°C"
- Domain knowledge: process parameters, material specifications

### What general-edition adds

- **Source-agent attribution:** `researcher` agent's lit-review entries vs `analyst` agent's data analysis entries cleanly separated
- **Pattern-key promotion:** "always cite real papers" promoted to standing rule after 5+ feedback instances
- **Bi-temporal:** experimental hypotheses evolve; preserved history shows reasoning chain
- **Per-project memory bank:** comp-001 and comp-002 each get 6-file Cline-convention structure

---

## Example 3: Writing Project (Book / Article)

**Context:** Author writing a non-fiction book on a topic of expertise.

### Bootstrap wizard answers

```
Q: Edition selection
> general

Q: Compliance preset
> none

Q: Identity
  Name: <author name>
  Role: Author
  Org: (independent)
  Domain: Non-fiction writing — <topic>

Q: Active projects
  - "book-draft-v3" — Working title and 12-chapter outline; chapters 1-3 drafted

Q: Compliance extensions
> (none)

Q: Consumer agent topology
> none (just user + orchestrator)

Q: Deployment tier
  Code Execution: blocked
  Node.js: not installed
  Skills: blocked
  → T0 (manual operation; lower friction acceptable for writing context)

Q: Pet peeves
  - Don't suggest changes I didn't ask about
  - Don't paraphrase me — I have a voice
  - Don't pad with filler text
```

### Expected memory entries

- Outline state: chapter-by-chapter progression
- Character/concept tracking (for narrative non-fiction)
- Research citations: "Source A says X; Source B disagrees because Y"
- Stylistic decisions: "Use second-person voice in Chapter 4 only"
- Editorial feedback: "Editor wants Chapter 7 expansion on point Z"

### What general-edition provides

- **Pattern-key promotion:** "preserve my voice" promoted after recurring feedback
- **Cross-references:** wiki-links between concepts ("[[Chapter 4 voice decision]] applies here")
- **Memory bank per-project:** book-draft-v3/memory-bank/ holds chapter status, character notes, citation tracking
- **No automation friction:** T0 manual flow fits writing's reflective pace

---

## Example 4: Education (Teacher / Learner)

**Context:** Teacher preparing course materials OR student tracking learning across multiple subjects.

### Bootstrap wizard answers (teacher)

```
Q: Edition selection
> general

Q: Compliance preset
> none (or `enterprise` if institution requires audit trails for grade-related entries)

Q: Identity
  Name: <teacher name>
  Role: Educator
  Org: <institution>
  Domain: <subject area>

Q: Active projects
  - "course-101" — Intro Algorithms — Spring 2026 semester
  - "course-201" — Data Structures — Spring 2026 semester

Q: Compliance extensions
> (FERPA-style profile not yet built — would be a custom override; placeholder for future EXTENSIONS work)

Q: Consumer agent topology
> none

Q: Deployment tier
  Variable; depends on institution
```

### Expected memory entries (teacher)

- Lesson plans per topic
- Question banks (separate from student responses)
- Pedagogy decisions: "Use peer instruction for difficult topics"
- Student-aggregate analytics (NOT individual grades; aggregated patterns OK)

### Cautions for educational context

- **Student PII:** If memory stack touches grades, names, attendance — this is FERPA territory in US. Use `compliance: enterprise` with EXTENSIONS for FERPA (when available) OR avoid these entries entirely.
- **Aggregated patterns OK:** "70% of students struggled with recursion" is non-PII; safe.
- **Individual student data NOT OK:** "Student A scored 65 on midterm" violates FERPA.

### Bootstrap wizard answers (learner)

```
Q: Edition selection
> general

Q: Compliance preset
> none

Q: Identity
  Name: <learner name>
  Role: Student
  Org: <school>
  Domain: <field of study>

Q: Active projects
  - "ml-class" — Machine Learning course
  - "thesis-prep" — Senior thesis research

Q: Pet peeves
  - Don't just give me the answer; help me work through it
  - Cite real papers and concepts, not made-up references
```

### What learners get

- **Concept progression tracking:** "Today learned backprop; struggled with chain rule application"
- **Cross-subject linking:** ML concepts cross-link to math concepts via wiki-links
- **Self-directed pattern-key:** "always work through derivations by hand" becomes a learning standing rule

---

## Common Patterns Across All 4 Use Cases

| Pattern | Software dev | Research | Writing | Education |
|---------|--------------|----------|---------|------------|
| Decision tracking | ✅ Architecture | ✅ Methodology | ✅ Stylistic | ✅ Pedagogical |
| Domain knowledge | ✅ Tech stack | ✅ Field-specific | ✅ Subject expertise | ✅ Subject expertise |
| Feedback compounding | ✅ | ✅ | ✅ | ✅ |
| Per-project memory banks | ✅ | ✅ | ✅ | ✅ |
| Bi-temporal | ✅ Architecture evolution | ✅ Hypothesis evolution | ✅ Editorial revisions | ✅ Curriculum evolution |
| Wiki-link cross-references | ✅ DEC-XXX | ✅ Lit refs | ✅ Concept links | ✅ Subject cross-links |
| Compliance burden | LOW | LOW–MEDIUM | LOW | LOW–MEDIUM (if FERPA) |

---

## What General-Edition Excludes (PHI / HIPAA)

General-edition does not ship PHI/HIPAA compliance. Its presets are `none`, `enterprise`, and `custom`. If your context involves:
- HIPAA-covered PHI (patient data, specimens, genomic linking)
- Strict regulatory enforcement (no user override possible)
- Healthcare provider operations

then note: A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

---

## Cross-References

- Parent: `../../common-specs/BOOTSTRAP_PROMPT.md` Step 7 (overridden examples)
- `./compliance-presets.override.md` (preset details)
- `./generic-conflict-resolution.override.md` (preset-dependent enforcement)
- `../PROFILE.md` (defaults + user choices)
- `../EXTENSIONS/` (optional regulatory profile add-ons)
