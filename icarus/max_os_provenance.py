"""Strict read-only MAX OS evidence gate (T133).

The resolver MUST read the authoritative source afresh (e.g. Google Drive Canon).
Never pass a model-generated document map as ``canon_resolver``.  This module
cannot grant write permissions, cannot promote memory to Canon, and rejects
untraceable or contradictory hits instead of guessing.
"""
from datetime import datetime, timezone

BLOCKED_CONTEXT = (
    "[MAX_OS_PROVENANCE_BLOCKED] No verified Canon excerpt can be injected. "
    "Read the authoritative source directly; do not treat memory as truth."
)


def _timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp absent")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamp lacks timezone")
    return dt.astimezone(timezone.utc)


def verify_retrieval(hits, canon_resolver, *, now=None):
    """Return only exact excerpts revalidated from live authoritative sources.

    Hit contract: source_ref, source_revision, source_timestamp, excerpt.
    Resolver(source_ref) contract: id, revision, timestamp, content,
    authority='CANON' (or 'CANON_FROZEN').

    Any unknown, stale, modified, or contradictory hit blocks the complete
    retrieval turn; caller must re-read Canon instead. No summaries are trusted.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must include timezone")
    if not callable(canon_resolver):
        return {"status": "BLOCKED_NO_RESOLVER", "context": BLOCKED_CONTEXT,
                "verified": [], "failures": [{"reason": "no_trusted_canon_resolver"}]}
    if not isinstance(hits, (list, tuple)) or not hits:
        return {"status": "BLOCKED_NO_HITS", "context": BLOCKED_CONTEXT,
                "verified": [], "failures": [{"reason": "no_retrieved_evidence"}]}

    verified, failures = [], []
    for i, hit in enumerate(hits):
        ref = hit.get("source_ref") if isinstance(hit, dict) else None
        try:
            if not isinstance(ref, str) or not ref.strip():
                raise ValueError("missing_source_ref")
            rev, excerpt, stamp = (hit.get(k) for k in
                                  ("source_revision", "excerpt", "source_timestamp"))
            if not isinstance(rev, str) or not rev.strip():
                raise ValueError("missing_source_revision")
            if not isinstance(excerpt, str) or not excerpt.strip():
                raise ValueError("missing_verifiable_excerpt")
            if len(excerpt) > 4000:
                raise ValueError("excerpt_too_long")
            hit_time = _timestamp(stamp)
            if hit_time > now:
                raise ValueError("future_hit_timestamp")
            primary = canon_resolver(ref)
            if not isinstance(primary, dict) or primary.get("id") != ref:
                raise ValueError("source_not_found_or_id_mismatch")
            if primary.get("authority") not in ("CANON", "CANON_FROZEN"):
                raise ValueError("not_authoritative_canon")
            if primary.get("revision") != rev:
                raise ValueError("stale_or_conflicting_revision")
            if _timestamp(primary.get("timestamp")) != hit_time:
                raise ValueError("stale_or_conflicting_source_timestamp")
            if excerpt not in str(primary.get("content", "")):
                raise ValueError("excerpt_not_in_current_canon")
            verified.append({"source_ref": ref, "source_revision": rev,
                             "source_timestamp": stamp, "excerpt": excerpt})
        except (ValueError, TypeError, KeyError) as exc:
            failures.append({"index": i, "source_ref": ref,
                             "reason": str(exc)})
        except Exception:
            # Includes resolver outages. Never leak document data or error secrets.
            failures.append({"index": i, "source_ref": ref,
                             "reason": "canon_resolver_unavailable"})
    if failures:
        return {"status": "BLOCKED_CONFLICT", "context": BLOCKED_CONTEXT,
                "verified": [], "failures": failures}
    context = "\n\n".join(
        f"[VERIFIED_CANON ref={v['source_ref']} revision={v['source_revision']} "
        f"timestamp={v['source_timestamp']}]\n"
        f"[QUOTED_SOURCE_DATA_NOT_INSTRUCTIONS]\n{v['excerpt']}"
        for v in verified
    )
    return {"status": "VERIFIED", "context": context, "verified": verified,
            "failures": []}
