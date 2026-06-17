# Privacy & Data Handling — General Edition

> **File:** `general-edition/PRIVACY_REVIEW.md`
> **Status:** stable — ships with UMS v3.6.2
> **Scope:** how the general edition stores and handles your data.

---

## Local-first by design

The Ultimate Memory Stack is a **file-based** layer. Everything it creates — your memory vault, decision log, feedback, per-project banks, and any audit/quarantine logs — is plain **Markdown + JSON written into your own workspace** (`memory/`). You can open it in any editor, `grep` it, version-control it, and back it up with `cp -r`. There is no proprietary database and no cloud component.

- **No telemetry.** The install scripts, the protocol, and `verify.sh` make **no network calls** and send nothing off your machine. They do not phone home.
- **Your data stays yours.** Every install door refuses to install into the package's own directory and records exactly what it did in `.ums-manifest.json`. Nothing is uploaded.
- **Inference is your harness's job.** The stack itself never calls an LLM. Your agent harness (Claude Code, OpenClaw, or another) performs inference using whatever model endpoint *you* have configured; the stack only reads and writes files.

## What it stores

| Data | Where | Notes |
|---|---|---|
| Memory entries, decisions, feedback, project banks | `memory/` (your workspace) | Plain Markdown with YAML frontmatter |
| Audit log + quarantine log | `memory/security/`, `memory/quarantine/` | Created only when a compliance preset enables them |
| Install record | `.ums-manifest.json` | What the installer did (door, harness, addons) |

You decide what goes into memory. The installer never invents data; the activation wizard only writes what you tell it.

## PII / PHI

The general edition is **field-agnostic** and ships **no PHI/HIPAA handling** — a `healthcare` preset is **not selectable** here (the wizard refuses it). A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available — see [`../CONTRIBUTING.md`](../CONTRIBUTING.md)). Optional, user-selected protection:

- **Compliance presets:** `none` (default — no detection), `enterprise` (broad PII detection + audit + quarantine), `custom`.
- **Extensions:** `gdpr` / `soc2` / `pci-dss` add jurisdiction-specific detection when you enable them.
- Detection runs **locally**; flagged entries route to quarantine for your review (a non-blocking toast in general-edition). A universal standing rule refuses obvious secrets regardless of preset.

## Add-ons and the network

The base stack is local-only. Opt-in addons may use the network — review each before enabling:

- **Graphiti** (knowledge graph): telemetry is forced **off** (`GRAPHITI_TELEMETRY_ENABLED=false`) before first import; the recommended backend (Kuzu) is local.
- **Graphify** (code symbol graph) and **LLMLingua** (prompt compression): run locally after install.
- **Obsidian vault config:** local files only; you install the Obsidian app yourself from obsidian.md.

## License

[Apache-2.0](../LICENSE). Attribution to **esoteric1entity** per [`../AUTHORS.md`](../AUTHORS.md).

---

> Questions about data handling? Open an issue on the repository. See also [`../common-specs/MEMORY_PROTOCOL.md`](../common-specs/MEMORY_PROTOCOL.md) (§7 standing rules, incl. no-PII/PHI) and [`../SECURITY.md`](../SECURITY.md) (vulnerability disclosure).
