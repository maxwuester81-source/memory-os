# Gate contract

Status: PREPARED / NOT YET EXECUTED ON MAX HOST

## G0 Isolation
PASS when no canonical systems are writable from the harness.

## G1 LM Studio
PASS when /v1/models and /v1/chat/completions respond locally.

## G2 Multi-tool
PASS only when Qwen calls get_alpha, consumes its tool result, then calls multiply, consumes that result, and returns GATE_PASS=51.

## G3 Resume
Not implemented in the stateless harness. Must be tested through the selected persistent Paperclip adapter/bridge before residents exist.

## G4 Paperclip
After G2 PASS, connect the same deterministic task to Paperclip. The generic process adapter alone is not sufficient evidence for G3 because its documented runs do not preserve conversational session state.

## Stop conditions
Any malformed tool arguments, premature final answer, missing second tool call, context loss, or canonical write capability => FAIL CLOSED.

## T133 provenance gate (17 Oct 2026)

Implemented in `provenance_gate.py` on the isolated `paperclip-max-os` branch.
This is a **read-only validation harness**, not an installed memory-os runtime adapter.

Run the deterministic unit checks:

```powershell
cd experiments/paperclip-max-os
python provenance_gate.py --self-test
```

Local unit result (17 Oct): 3 positive cases VERIFIED and 3 negative cases correctly rejected (2 CONFLICT, 1 INSUFFICIENT); byte-identical GitHub blob verified. The self-test uses synthetic data and is **not T133 acceptance PASS**.

For **real T133 acceptance**, obtain a canonical snapshot directly from the authoritative Drive source and an *independently retrieved* memory-os result for each of three source-bound claims. Include `source_ref`, `source_sha256` (SHA-256 of the exact source text bytes), `source_updated_at` (timezone-aware ISO-8601), original memory `content`, exact source `claim`, and `expect`. Keep the input JSON on the owner PC, outside Git. Run:

```powershell
python provenance_gate.py --cases PATH_TO_PRIVATE_CASES.json
```

Use at least three real Canon source/retrieval pairs and one deliberate stale/contradictory memory hit. No self-generated memory matches count as genuine retrieval evidence. If existing Icarus/Fabric entries lack `source_sha256` or `source_updated_at`, their result is INSUFFICIENT; do not forge fields, infer hashes from snippets, or promote memory to truth. The authoritative snapshot must be independently fetched before comparison.

**Blocker:** MAX OS bridge/live adapter not yet executed or proven; real 3+1 tests pending. T129 (Paperclip loop) and T105 (end-to-end) remain blocked until T133 proves actual retrieval/provenance. No automatic Drive Canon write, trade, approval, publishing or merge to main.
