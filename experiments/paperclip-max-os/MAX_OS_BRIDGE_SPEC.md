# MAX OS Bridge — Interface Contract V0.1

The bridge is an anti-corruption layer between orchestration/runtime agents and authoritative knowledge systems.

## Read interfaces

### memory.query(query, scope, top_k)
Returns retrieval candidates with provenance, timestamp, freshness, confidence and source authority.

### canon.read(resource_id | query)
Reads authoritative/derived MAX OS state. Read-only for residents.

### source.verify(claim, source_refs)
Returns VERIFIED / CONFLICT / INSUFFICIENT with evidence references.

## Proposal interfaces

### proposal.create(payload)
Creates a non-canonical proposed delta. Required fields:
- proposal_id
- actor
- task_id
- target
- before_hash when target exists
- proposed_change
- evidence_refs
- created_at
- risk_class

### provenance.log(event)
Append-only execution/evidence ledger.

## Restricted interface

### canon.commit(proposal_id, approval)
Unavailable to ordinary residents. Requires:
- verified proposal
- valid approval for risk tier
- current target hash equals proposal before_hash
- no unresolved conflict
- readback after write

## Failure semantics

memory unavailable -> BLOCKED_MEMORY_UNAVAILABLE
canon unavailable -> BLOCKED_CANON_UNAVAILABLE
source conflict -> BLOCKED_EVIDENCE_CONFLICT
stale before_hash -> BLOCKED_STALE_WRITE
missing approval -> BLOCKED_APPROVAL_REQUIRED

Never silently downgrade these conditions to best-effort execution.
