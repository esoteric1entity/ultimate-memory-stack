#!/usr/bin/env python3
"""
LLMLingua Installer — Post-Install Smoke Test
================================================

Verifies the LLMLingua install works end-to-end:
  1. Import check
  2. Model load check                  (skipped if --quick)
  3. Compression round-trip            (skipped if --quick)
  4. Output validation                 (skipped if --quick)

Authority: SKILL.md Step 4 + INSTALL_LLMLINGUA.md Step 5
Vetting: Sentinel security vetting PASS
Pin contract: llmlingua==0.2.2 + bounded transformers/torch/sentencepiece

Usage:
  python smoke_test.py              # Full smoke (all 4 steps; first-run downloads ~500 MB model — can exceed 5 min)
  python smoke_test.py --quick      # Quick smoke (step 1 only; skips model load + compression)

Note: First-run model download can exceed a 300s wrapping-timeout. Use
--quick to validate env/install without triggering the download; run full smoke after model is cached.
The full smoke test does NOT internally enforce a timeout (it relies on HuggingFace's own download
mechanism); if a parent wrapper enforces a timeout, raise that to ≥900s for first-run installs.

Exit codes:
  0 = all checks passed (or --quick step 1 passed)
  1 = import failure (install incomplete or wrong env active)
  2 = model load failure (dependency conflict or missing weights)
  3 = compression failure (runtime / API mismatch)
  4 = output validation failure (compression returned empty or identical output)
"""

from __future__ import annotations

import sys
import time


SAMPLE_PROMPT = (
    "The Ultimate Memory Stack v3.6.0 release bundles three security-vetted, opt-in "
    "addons (LLMLingua, Graphiti, Graphify) alongside five surface-only Lint checks "
    "added to MEMORY_PROTOCOL.md §10.5. Automated self-modification remains deferred "
    "by design: memory-hygiene scanners surface findings for human review and never "
    "auto-mutate content, which preserves auditability and prevents feedback-loop "
    "reward hacking. Knowledge-graph and prompt-compression addons install "
    "independently and each records a manifest so updates and uninstalls stay "
    "deterministic. This sample prompt exists purely as input "
    "to verify the LLMLingua compression pipeline produces non-empty, distinct output."
)

TARGET_TOKEN_LIMIT = 60


def check_import() -> None:
    """Step 1: Import llmlingua and report version."""
    try:
        import llmlingua  # noqa: F401
    except ImportError as exc:
        print(f"[smoke_test] LLMLingua import:    FAIL ({exc})")
        print("[smoke_test] Hint: confirm `pip list | grep llmlingua` shows 0.2.2 in active env")
        sys.exit(1)
    version = getattr(llmlingua, "__version__", "<unknown>")
    print(f"[smoke_test] LLMLingua import:    OK (version reported: {version})")
    if version not in ("<unknown>", "0.2.2"):
        print(f"[smoke_test] WARNING:             version drift from pinned 0.2.2 — re-audit recommended")


def load_compressor():
    """Step 2: Construct PromptCompressor (triggers model download/load)."""
    try:
        from llmlingua import PromptCompressor
    except ImportError as exc:
        print(f"[smoke_test] PromptCompressor:    FAIL import ({exc})")
        sys.exit(2)

    print("[smoke_test] PromptCompressor:    loading (first run downloads ~500 MB)...")
    t0 = time.time()
    try:
        # Force CPU mode for portability (works in CPU-only environments without a GPU)
        compressor = PromptCompressor(device_map="cpu")
    except TypeError:
        # Older LLMLingua signature variant
        try:
            compressor = PromptCompressor()
        except Exception as exc:
            print(f"[smoke_test] PromptCompressor:    FAIL construct ({exc})")
            sys.exit(2)
    except Exception as exc:
        print(f"[smoke_test] PromptCompressor:    FAIL construct ({exc})")
        sys.exit(2)

    elapsed = time.time() - t0
    print(f"[smoke_test] PromptCompressor:    OK (load: {elapsed:.1f}s)")
    return compressor


def compression_roundtrip(compressor) -> tuple[str, float]:
    """Step 3+4: Compress the sample prompt; validate non-empty + distinct output."""
    t0 = time.time()
    try:
        result = compressor.compress_prompt(SAMPLE_PROMPT, target_token=TARGET_TOKEN_LIMIT)
    except Exception as exc:
        print(f"[smoke_test] Compression test:    FAIL ({exc})")
        sys.exit(3)
    elapsed = time.time() - t0

    # Normalize the result shape (llmlingua returns a dict or string depending on version)
    if isinstance(result, dict):
        compressed = result.get("compressed_prompt") or result.get("compressed") or ""
    else:
        compressed = str(result)

    if not compressed or compressed.strip() == "":
        print("[smoke_test] Output validation:   FAIL (compressed output is empty)")
        sys.exit(4)

    if compressed.strip() == SAMPLE_PROMPT.strip():
        print("[smoke_test] Output validation:   FAIL (compressed output identical to input)")
        sys.exit(4)

    input_tokens = len(SAMPLE_PROMPT.split())
    output_tokens = len(compressed.split())
    ratio = input_tokens / max(output_tokens, 1)

    print(f"[smoke_test] Compression test:    OK (ratio: {ratio:.1f}x, latency: {elapsed:.1f}s)")
    print(f"[smoke_test] Round-trip:          OK (input: {input_tokens} tokens → output: {output_tokens} tokens)")
    return compressed, ratio


def main() -> int:
    # --quick flag skips model load (which can take >300s on first run)
    quick_mode = "--quick" in sys.argv or "-q" in sys.argv

    print("=" * 60)
    print("LLMLingua Installer — Post-Install Smoke Test")
    print("Authority: SKILL.md Step 4")
    if quick_mode:
        print("Mode: --quick (env/install validation only; skips model load + compression)")
    else:
        print("Mode: full smoke (will download ~500 MB model on first run; can exceed 5 min)")
    print("=" * 60)

    check_import()

    if quick_mode:
        print("=" * 60)
        print("[smoke_test] --quick checks PASSED (import only)")
        print("[smoke_test] Run without --quick to validate full compression round-trip")
        print("=" * 60)
        print()
        return 0

    compressor = load_compressor()
    compressed, ratio = compression_roundtrip(compressor)

    print("=" * 60)
    print("[smoke_test] All checks PASSED")
    print(f"[smoke_test] Compression ratio achieved: {ratio:.1f}x (target: 5-20x typical)")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  - Log activation to memory/security/vetting_log.md (VET-### entry)")
    print("  - Log activation to memory/decisions/decisions.md (DEC-### entry)")
    print("  - Optionally register addon in <edition>/PROFILE.md to wire into memory protocol")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
