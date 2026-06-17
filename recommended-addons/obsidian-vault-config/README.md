# Obsidian Vault Config — Recommended Addon

> **Status:** stable — ships with UMS v3.6.2 (config-only — no executable code, no vetting required)
> **Tier:** B (recommended; not auto-installed but lightweight to set up)
> **Last updated:** 2026-05-28
> **Design basis:** ideal-first design + documentation discipline + addon tier framework + OpenClaw research + independent convergence on Obsidian patterns by a peer OpenClaw deployment
> **Upstream:** https://obsidian.md/ (desktop app, user-installed)

---

## What This Addon Does

Configures an [Obsidian](https://obsidian.md/) vault to work with the Ultimate Memory Stack. Drops SCHEMA_A18-compliant templates, recommends community plugins, and optionally registers the vault as the canonical memory-stack view.

**Why install it on the Ultimate Memory Stack:**
- Bi-directional wiki-links: `[[DEC-046]]` resolves in Obsidian's graph AND matches MEMORY_PROTOCOL §4.3
- Frontmatter is canonical SCHEMA_A18 — Dataview can query memory entries directly
- Graph view visualizes decision lineage + supersession chains
- Live preview makes editing dense memory files less painful than raw markdown
- Peer OpenClaw deployments already use Obsidian-style conventions — installing here brings v3.0/v3.5 deployments into alignment

**Why it's Tier B (recommended), not Tier C (opt-in):**
- Pure markdown — no proprietary lock-in
- No executable code installed — config-only
- Lightweight (~10 template files + 2 JSON config files)
- Cross-platform (Obsidian runs on Windows, Mac, Linux, iOS, Android)
- Already proven in a peer OpenClaw deployment, so this works as the canonical view across machines

**Why it's NOT Tier A (designed-in):**
- Obsidian app is user-installed (desktop app, not Python library)
- Skill cannot install community plugins programmatically — needs Obsidian UI
- User discipline required to actually USE the templates

---

## How This Skill Differs from the 3 Vetted Installers

| Property | LLMLingua / Graphiti / Graphify | Obsidian (this Skill) |
|---|---|---|
| Pip install | Yes (with pin contract) | NO |
| pip-audit pre-install | Required | Not applicable |
| Sentinel vetting | Required (PASS-vetted) | Not required (config-only) |
| smoke_test.py | Verifies executable | Not applicable (no executable) |
| User must install separately | No | YES — Obsidian app from obsidian.md |
| Risk profile | Supply-chain (Python deps) | Negligible (markdown + JSON only) |

---

## What's Included

```
obsidian-vault-config/
├── SKILL.md                                    # 9-step workflow
├── README.md                                   # This file
├── INSTALL_OBSIDIAN_VAULT.md                   # Manual fallback guide
├── templates/                                  # SCHEMA_A18-compliant templates
│   ├── DEC_template.md                         # Decision entry per documentation discipline
│   ├── VET_template.md                         # Vetting log entry
│   ├── FB_template.md                          # Feedback entry
│   ├── session_heartbeat_template.md            # Heartbeat per §4.4
│   └── memory_bank/                            # SCHEMA_A3 6-file set
│       ├── projectbrief_template.md
│       ├── productContext_template.md
│       ├── activeContext_template.md
│       ├── systemPatterns_template.md
│       ├── techContext_template.md
│       └── progress_template.md
└── obsidian_config/
    ├── community-plugins.json                 # 4 plugin recommendations
    ├── hotkeys.json                            # Memory-workflow hotkeys
    └── README.md                               # Plugin + hotkey reference docs
```

---

## Documentation Discipline

### Purpose

Bring v3.0/v3.5 deployments into Obsidian-canonical alignment by providing a one-shot Skill that configures the vault with SCHEMA_A18 templates, plugin recommendations, and memory-workflow hotkeys.

### Rationale

- OpenClaw research identified Obsidian as a recommended addon for the memory stack
- A peer OpenClaw deployment's independent convergence on Obsidian-style frontmatter + wiki-links is a validation signal
- MEMORY_PROTOCOL §4.3 already mandates wiki-link sync (`[[ID]]`); Obsidian is the canonical viewer for this convention
- Templates pre-populated with SCHEMA_A18 frontmatter prevent the "blank cursor → free-form entry" antipattern that produces orphan entries
- Dataview queries are powerful enough to replicate basic MEMORY_INDEX.md views, reducing index-staleness pressure
- This is one of the v3.5 recommended addons (alongside the 3 PASS-vetted Python installers)

### Sound reasoning

1. Per the ideal-first design principle: bi-directional links + frontmatter queries are the cleanest topology for memory exploration
2. Per the documentation discipline: templates carry the 5 required elements (purpose / rationale / sound reasoning / scope CAN / CANNOT) pre-populated, eliminating "I forgot to include purpose" errors
3. Per the Tier B (recommended) designation: appropriate tier because no executable risk, but user discipline required
4. Obsidian is validated as memory-stack-aligned PKM (research + independent convergence)
5. Within v3.5 scope: this is the 4th of 4 recommended addons (LLMLingua + Graphiti + Graphify + Obsidian)

### Scope — CAN

- Drop 10 SCHEMA_A18-compliant templates into `<vault>/.templates/`
- Drop community plugin recommendations (`.obsidian/community-plugins.json`)
- Drop hotkey configuration (`.obsidian/hotkeys.json`) if user wants
- Register vault in `<edition>/PROFILE.md` if user opts to
- Verify post-config setup via manual ls checks
- Log activation to vetting_log.md + decisions.md

### Scope — CANNOT

- Install the Obsidian desktop app (user installs from obsidian.md)
- Install community plugins programmatically (Obsidian UI required)
- Modify existing memory entries (templates only — for NEW entries)
- Enforce template usage at write-time (no Obsidian "must use template" mode)
- Validate wiki-link resolution without opening Obsidian
- Replace MEMORY_PROTOCOL §4.3 wiki-link sync requirements (Obsidian augments, doesn't replace)
- Sync vault state across machines (that's Multi-Machine Sync work — Phase 4+ candidate)

---

## Installation

### Recommended: via Skill

```
/config-obsidian-vault
```

The Skill walks through the 9-step workflow defined in `SKILL.md`.

### Fallback: manual config

Per `INSTALL_OBSIDIAN_VAULT.md`:

```bash
# Assuming Obsidian is installed and vault path chosen as <VAULT_PATH>
mkdir -p "<VAULT_PATH>/.templates"
cp -r templates/* "<VAULT_PATH>/.templates/"

mkdir -p "<VAULT_PATH>/.obsidian"
cp obsidian_config/community-plugins.json "<VAULT_PATH>/.obsidian/community-plugins.json"
cp obsidian_config/hotkeys.json "<VAULT_PATH>/.obsidian/hotkeys.json"

# Open Obsidian → File → Open Vault → select <VAULT_PATH>
# Settings → Community Plugins → enable → install 4 recommended
```

---

## Cross-References

- Design principles: ideal-first design; documentation discipline; Tier B/C addon framework
- OpenClaw research — Obsidian PKM patterns
- Independent convergence: peer OpenClaw deployments use Obsidian-style wiki-links + frontmatter
- v3.5 release trajectory (recommended addons batch)
- MEMORY_PROTOCOL §4.3 (wiki-link sync — Obsidian is canonical viewer)
- SCHEMA_A18 (per-entry frontmatter — templates carry this)
- SCHEMA_A3 (6-file memory bank — `memory_bank/` templates carry this)
- Upstream: https://obsidian.md/ — Obsidian desktop app
