<!--
Thank you for contributing to Ultimate Memory Stack!

Before submitting:
- Read CONTRIBUTING.md if you have not yet
- Confirm the CLA (a maintainer will ask on your first PR)
- Make sure your commits follow Conventional Commits + are DCO-signed (`git commit -s`)
-->

## Summary

<!-- One paragraph: what does this PR do and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] New addon (in `recommended-addons/`)
- [ ] Documentation only
- [ ] Schema change (requires DEC entry)
- [ ] Refactor (no functional change)
- [ ] Test infrastructure
- [ ] Other:

## Component affected

- [ ] `common-specs/` (schemas, MEMORY_PROTOCOL, ARCHITECTURE, MODULARITY)
- [ ] `general-edition/` (setup scripts, PROFILE, overrides, EXTENSIONS)
- [ ] `core/` (audit-quarantine-skill, openclaw-adapter)
- [ ] `recommended-addons/` (graphify / graphiti / llmlingua / obsidian-vault-config)
- [ ] `skills/install-ultimate-memory-stack`
- [ ] Top-level entry-points (`setup-memory-stack.{sh,ps1}` + `verify.sh`)
- [ ] Documentation (README, CHANGELOG, USER_GUIDE, INSTALL, QUICKSTART)
- [ ] CI/CD (`.github/workflows/`)

## Test plan

- [ ] `./setup-memory-stack.sh --skip-wizard --compliance=none` runs to completion in a clean directory
- [ ] `./verify.sh` reports all checks PASS
- [ ] If touching Skills: invoked the relevant `/install-X` and confirmed end-to-end behavior in a real Claude Code (or OpenClaw) session
- [ ] If touching schemas: existing entries still validate under the changed schema (or migration path documented)
- [ ] No regression — `general-edition/setup.sh` still works against fresh + migration scenarios

## Compatibility

- [ ] No breaking change
- [ ] Breaking change (describe migration path in CHANGELOG)
- [ ] Affects only `--minimal` install
- [ ] Affects only specific addon(s):

## Checklist

- [ ] My changes follow the coding style described in `CONTRIBUTING.md`
- [ ] If schemas changed, I added a DEC entry (or updated an existing one) in the package's R&D tree
- [ ] I have added or updated tests covering my changes
- [ ] I have updated documentation (README, CHANGELOG, relevant SCHEMA docs)
- [ ] I have signed my commits (`git commit -s`)
- [ ] I have signed the CLA

## Related issues / DEC entries

<!-- Closes #N, related to #N, refs DEC-### -->
