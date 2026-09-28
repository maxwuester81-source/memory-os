# MAX OS Memory Upgrade Gate

Status: ANALYZED / NO UPSTREAM MERGE PERFORMED

## Verified baseline

Fork head: a4ca094a7b07eb4592b7f9183ff33efc7da06a18 (2026-06-01)
Upstream head inspected: e03db1f1c83e94fdb2007c90d232c6c852c0f274 (2026-06-10)
Distance: 46 upstream commits.

The earlier assumption that upstream code had advanced through September was incorrect. Repository metadata changed later, but the inspected upstream main head is June 10.

## Classification

### ADOPT / high value
- provider-agnostic Icarus endpoint/model configuration
- configurable embedding backend
- embedding dimension validation
- setup smoke tests and ingestion tests
- Qdrant injection/import-path fix
- per-session injection dedup
- parsing/sanitization hardening
- path-containment tests
- CI and reproducible setup improvements

### ADAPT / do not copy verbatim
- Ground Truth hierarchy: upstream ranks injected memory as ground truth for documented knowledge. MAX OS instead uses provenance + freshness and keeps Drive/CANON authoritative.
- Mandatory Pre-Action Protocol: useful verification principle, but its universal multi-tool "plan then wait" rule is unsuitable for autonomous residents. MAX OS uses risk-tiered approvals instead.
- Hermes-specific SOUL/rulebook changes: translate into resident contracts and bridge policy.
- OpenRouter defaults: local-first MAX OS should prefer explicit local endpoints where appropriate.

### HOLD / benchmark first
- collapse pipeline
- reflection automation
- semantic dedup/decay changes
- wiki continuous ingestion changes
- automatic learning extraction

These can mutate or reinterpret memory and therefore require corpus-level regression tests before adoption.

## Merge policy

Do NOT merge upstream into main yet.

After the LM Studio/Paperclip G1-G3 gates:
1. create a separate memory-upgrade branch from main;
2. replay high-value infrastructure changes in small groups;
3. run baseline retrieval tests after every group;
4. require provenance/freshness invariants;
5. merge only after readback.

## Critical invariant

No upstream feature may turn retrieved/injected memory into a higher authority than MAX_AI_SYNC / Drive canon.
