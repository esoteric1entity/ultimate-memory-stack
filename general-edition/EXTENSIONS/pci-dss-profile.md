# EXTENSION — PCI-DSS Profile (for General-Edition)

> **File:** `general-edition/EXTENSIONS/pci-dss-profile.md`
> **Version:** 1.0 — 2026-05-15
> **Compose with:** `enterprise` + `soc2` base most commonly; can compose with `none` for solo developers
> **Activates:** PCI-DSS payment card industry data security standards — cardholder data detection + tokenization patterns
> **Status:** stable — ships with UMS v4.0.0

---

## Purpose

PCI-DSS-specific compliance for general-edition deployments handling payment card data. Adds aggressive cardholder data detection, tokenization patterns, and key management awareness.

**Important:** The memory stack is NOT designed to store cardholder data (CHD) itself — it's designed to handle the SOFTWARE development context that touches payment systems. Use this extension if you're building payment apps, doing PCI-DSS audits, or handling vendor evidence for payment-card-touching systems.

Common use cases:
- Software developers building payment integrations (Stripe, Adyen, Braintree)
- B2B SaaS handling card data on behalf of clients
- Organizations preparing for PCI-DSS audits

---

## What This Extension Adds

### Detection patterns activated (aggressive)

- All `detection_patterns_none.md` Luhn-valid PAN detection — but escalated to CRITICAL severity (always REDACT)
- ADD card industry-specific patterns:
  - Issuer Identification Numbers (IINs / first 6 digits)
  - Card expiration date patterns
  - Card verification values (CVV / CVC) — refuse outright
  - Track 1 / Track 2 magnetic stripe data — refuse outright
  - PIN block patterns — refuse outright

### Behavior changes

| Aspect | Base preset | + pci-dss-profile EXTENSION |
|--------|-------------|----------------------------|
| Cardholder data (CHD) detection | Off or warn | **CRITICAL — REDACT + REFUSE + QUARANTINE** |
| Sensitive Authentication Data (SAD: CVV, PIN, full track) | Off | **ABSOLUTE REFUSAL — never store, never even in redacted form** |
| Audit log | Per base | MANDATORY for security-tagged entries + minimum 1 year retention |
| Tokenization awareness | N/A | Flag entries with `tokenization_pointer` (NOT the token itself) |
| Cryptographic signatures | Per base | STRONGLY RECOMMEND at T3 for entries with `pci_relevant: true` |

### Frontmatter fields added

```yaml
compliance_extension: pci-dss
pci_relevant: true | false                       # whether this entry touches PCI scope
tokenization_pointer: <external-token-vault-ref> # pointer to where tokens live, NOT the tokens themselves
pci_dss_requirement_ref: <e.g., Req 3, Req 4, Req 10>  # which PCI-DSS requirement this entry relates to
cardholder_data_present: false                   # MUST be false for active entries (true entries are quarantined)
```

### Detection rules

**Pattern: PAN (Primary Account Number) — Luhn-valid**
```regex
# 13-19 digit strings with optional spacing
\b(?:\d[ -]?){13,19}\b
```
Apply Luhn checksum. If valid → CRITICAL → REDACT + REFUSE + QUARANTINE.

**Pattern: CVV / CVC**
```regex
# 3-4 digit "verification" context
\b(CVV|CVC|CVN|CID|CSC)[:\s]+\d{3,4}\b
```
ABSOLUTE REFUSAL — even redacted form not allowed. Refuse the write entirely.

**Pattern: PIN block / Track data**
```regex
# Track 1 (formatted with sentinels)
%[A-Z]\d{1,19}\^[\s\S]+\?

# Track 2
;\d{1,19}=[\s\S]+\?
```
ABSOLUTE REFUSAL.

**Pattern: Expiration date in payment context**
```regex
\b(0[1-9]|1[0-2])\/\d{2,4}\b[\s\S]{0,30}(expir|exp|valid)
```
Warn + log + suggest sanitization. Lower severity if not co-located with PAN.

### Standing rules (universal floor + PCI-DSS-specific)

- Universal: no secrets, no full credit card numbers (this extension makes detection AGGRESSIVE)
- PCI-DSS-specific: NEVER store CVV/CVC/PIN/track data — not even in redacted form. The memory stack must reject the write entirely.

## Activation

```bash
# At bootstrap:
setup.sh --compliance=enterprise --extensions=pci-dss

# Or combined:
setup.sh --compliance=enterprise --extensions=soc2,pci-dss
```

## Composition Examples

| Composition | Common scenario |
|-------------|------------------|
| `enterprise` + `pci-dss` | Most common — payment-touching SaaS |
| `enterprise` + `soc2` + `pci-dss` | SOC2 + PCI-DSS together |
| `enterprise` + `gdpr` + `pci-dss` | EU payment processing |
| `none` + `pci-dss` | Solo dev building payment integration (lightweight) |

## What Goes in Memory (Allowed) vs What Doesn't (Forbidden)

### Allowed (non-CHD)
- Tokenization architecture decisions: "Using Stripe tokens; never store raw PAN"
- API integration patterns: "POST /v1/charges with token, not PAN"
- PCI-DSS requirement mapping: "Req 3 (storage) → use Stripe Vault; Req 4 (transmission) → TLS 1.2+ enforced"
- Test data patterns: "Use 4242 4242 4242 4242 for Stripe test transactions" (test PANs are NOT real cardholder data)
- Vendor evidence pointers: "PCI compliance report Q1 2026 stored at external-vault-ref-12345"

### Forbidden (CHD or SAD)
- Real cardholder numbers (Luhn-valid PANs of actual cards)
- Customer card numbers in any form
- CVV / CVC / PIN values
- Magnetic stripe track data
- Full unmasked card numbers anywhere

## Risks + Mitigations

| Risk | Mitigation |
|------|------------|
| Developer pastes real card number for debugging | Aggressive detection catches Luhn-valid PANs; redacts + refuses |
| Test card numbers (4242...) trigger detection | Pattern detects + applies LOW severity for known test ranges; logs but doesn't refuse |
| Tokenization pointer accidentally captures real token | Documentation emphasizes "pointer to vault, NOT the token"; review on quarantine |
| Audit log entry summary leaks redacted PAN context | Summary truncated at 200 chars; PAN itself redacted before summary computed |

## Cross-References

- `../../common-specs/detection_patterns_none.md` (Luhn-valid PAN base pattern)
- `../../common-specs/SCHEMA_compliance_profile.md` §5.3 (enterprise preset base)
- `../../common-specs/MEMORY_PROTOCOL.md` §7 (standing rules — no credit cards universal)
- B7 compliance preset design
- PCI-DSS v4.0 Standard (current at writing)
- PCI-DSS Requirements 3 (storage), 4 (transmission), 10 (logging)
