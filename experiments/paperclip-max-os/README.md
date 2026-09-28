# Paperclip × MAX OS — V0.1 Gate

Purpose: isolate and test the local inference path before implementing MIRA/VECTOR/LUMEN/FORGE.

## Authority boundary

This experiment MUST NOT write to MAX_AI_SYNC, Google Drive canon, financial systems, calendars, email, or main.

Paperclip state is operational state only. memory-os remains retrieval/memory infrastructure; authoritative knowledge remains outside Paperclip.

## Gate order

1. LM Studio health/model discovery
2. Qwen multi-tool loop (two sequential tool calls in one task)
3. Deterministic tool-result continuation
4. Session/resume test
5. Paperclip process-adapter smoke test
6. Only after PASS: evaluate a persistent adapter path and resident implementation

## Required local environment

- LM Studio server enabled
- Qwen3.5-35B-A3B loaded
- Python 3.11+
- `LM_STUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`)
- optional `LM_STUDIO_MODEL` override

## Run

```powershell
cd experiments/paperclip-max-os
python lmstudio_multitool_gate.py
```

Exit 0 = gate pass. Non-zero = fail; do not proceed to residents.

## PASS criteria

- OpenAI-compatible models endpoint reachable
- target model resolved
- model requests tool #1
- result is returned to model
- model requests tool #2
- result is returned to model
- model emits final answer containing the deterministic expected value
- transcript is written locally to `artifacts/` (gitignored)

## Current limitation

The Paperclip `process` adapter is suitable for a smoke test but Paperclip documents it as non-persistent across runs. A production resident must therefore use an adapter/runtime with explicit session persistence or implement persistence in the MAX OS bridge. Do not infer production readiness from a successful process-adapter run.
