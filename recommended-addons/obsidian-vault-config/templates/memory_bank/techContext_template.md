---
project: {{project_slug}}
file: techContext
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
schema: A3
purpose: "Tech stack — languages, frameworks, dependencies, environment setup"
---

# Tech Context — {{project_name}}

> **Schema:** A3 #5 of 6
> **Purpose:** Concrete tech stack details. The TOOLS that implement what `systemPatterns.md` describes.
> **Updated:** {{date}} ({{session_label}})

---

## Language(s)

| Language | Version | Why |
|---|---|---|
| | | |

## Runtime / Environment

| Component | Version | Notes |
|---|---|---|
| | | |

## Conda / venv environment

```bash
# Activation command:
conda activate <env-name>
# or
source /path/to/venv/bin/activate
```

| Env name | Python version | Purpose |
|---|---|---|
| | | |

## Key Dependencies (with version pins)

| Package | Version pin | Why this pin | Vetting |
|---|---|---|---|
| | | | VET-XXX |

Standing rule — all dependencies must pass Sentinel vetting before install.

## Build / Run Commands

```bash
# Build:

# Run:

# Test:
```

## External Services / APIs

| Service | Purpose | Auth | Cost concern |
|---|---|---|---|
| | | | |

## Development Tools

| Tool | Version | Purpose |
|---|---|---|
| | | |

## Known Issues / Workarounds

| Issue | Workaround | Tracked in |
|---|---|---|
| | | |

## Migration Paths

_Where pins need to advance, what alternatives exist, etc._

| Current | Target | Trigger to migrate |
|---|---|---|
| | | |

## Cross-References

- `systemPatterns.md` — how these tools fit into the architecture
- `progress.md` — what's been built with this stack
- `projects/<other-slug>/memory-bank/techContext.md` — cross-project stack alignment
- `recommended-addons/*/requirements.txt` — vetted dependency manifests

---

> **Template author note (DELETE before saving):**
> Per SCHEMA_A3 #5: this is the FACTUAL tech inventory. Update when dependencies change, versions advance (after vetting), or environments are added.
> Security-first standing rule: any new dependency MUST pass Sentinel vetting before install. Capture VET-### in the "Vetting" column.
