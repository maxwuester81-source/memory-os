"""MAX OS T133: isolated, read-only provenance and contradiction acceptance gate.

This is a deterministic validator, NOT a live memory-os/Paperclip adapter and
NOT a replacement for Drive Canon. It has no network or canonical write path.

Usage:
  python provenance_gate.py --self-test
  python provenance_gate.py --cases private_cases.json

Each case contains: id, canonical {source_ref, updated_at, text}, memory
{source_ref, source_sha256, source_updated_at, content}, claim, expect.
The canonical snapshot MUST be loaded from the real authority by the caller.
A real T133 PASS requires three real memory-os retrievals plus one contradiction;
synthetic self-tests alone do not establish that acceptance.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

VERIFIED = "VERIFIED"
CONFLICT = "CONFLICT"
INSUFFICIENT = "INSUFFICIENT"
_HEX256 = re.compile(r"^[a-f0-9]{64}$")


def _date(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo is not None and dt.utcoffset() is not None else None


def _norm(text):
    return " ".join(text.split()) if isinstance(text, str) else ""


def _result(verdict, reason, source_ref="", digest=""):
    return {"verdict": verdict, "reason": reason,
            "source_ref": source_ref, "canonical_sha256": digest}


def from_fabric_entry(entry):
    """Lossless adapter only: never guess source identifiers/hashes from prose.

    Current Icarus entries may have evidence/source_tool but no source_sha256.
    Those entries intentionally fail provenance verification until a trusted
    ingestion path records all required metadata.
    """
    return {"source_ref": entry.get("source_ref"),
            "source_sha256": entry.get("source_sha256"),
            "source_updated_at": entry.get("source_updated_at"),
            "content": entry.get("content") or entry.get("_body") or ""}


def verify_case(case):
    canon = case.get("canonical") or {}
    memory = case.get("memory")
    if memory is None and "fabric_entry" in case:
        memory = from_fabric_entry(case["fabric_entry"])
    memory = memory or {}
    ref = canon.get("source_ref")
    content = canon.get("text")
    claim = _norm(case.get("claim"))
    if not isinstance(ref, str) or not ref.strip() or not isinstance(content, str) or not content:
        return _result(INSUFFICIENT, "CANON_SNAPSHOT_MISSING")
    current_time = _date(canon.get("updated_at"))
    if current_time is None or not claim:
        return _result(INSUFFICIENT, "CANON_DATE_OR_CLAIM_MISSING", ref)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if claim not in _norm(content):
        return _result(CONFLICT, "CLAIM_NOT_IN_CANON", ref, digest)
    fields = ("source_ref", "source_sha256", "source_updated_at", "content")
    if any(not isinstance(memory.get(k), str) or not memory[k].strip() for k in fields):
        return _result(INSUFFICIENT, "MEMORY_PROVENANCE_MISSING", ref, digest)
    if memory["source_ref"] != ref:
        return _result(CONFLICT, "SOURCE_REF_MISMATCH", ref, digest)
    supplied = memory["source_sha256"].lower()
    if not _HEX256.fullmatch(supplied):
        return _result(INSUFFICIENT, "MEMORY_HASH_INVALID", ref, digest)
    if supplied != digest:
        return _result(CONFLICT, "STALE_OR_FOREIGN_SOURCE_HASH", ref, digest)
    memory_time = _date(memory["source_updated_at"])
    if memory_time is None:
        return _result(INSUFFICIENT, "MEMORY_TIMESTAMP_INVALID", ref, digest)
    if memory_time < current_time:
        return _result(CONFLICT, "STALE_SOURCE_TIMESTAMP", ref, digest)
    if claim not in _norm(memory["content"]):
        return _result(INSUFFICIENT, "CLAIM_NOT_IN_RETRIEVED_EVIDENCE", ref, digest)
    return _result(VERIFIED, "EXACT_CANON_SOURCE_AND_QUOTE", ref, digest)


def validate_suite(cases, *, require_acceptance=True):
    if not isinstance(cases, list):
        raise ValueError("cases must be a JSON list")
    rows = []
    for n, case in enumerate(cases):
        result = verify_case(case)
        expected = case.get("expect", "")
        rows.append({"id": str(case.get("id", n)), "verdict": result["verdict"],
                     "reason": result["reason"], "as_expected": result["verdict"] == expected})
    pass_count = sum(r["verdict"] == VERIFIED and r["as_expected"] for r in rows)
    contradiction_count = sum(r["verdict"] == CONFLICT and r["as_expected"] for r in rows)
    ok = bool(rows) and all(r["as_expected"] for r in rows)
    if require_acceptance:
        ok = ok and pass_count >= 3 and contradiction_count >= 1
    return {"unit_suite_pass": ok, "verified_cases": pass_count,
            "conflict_cases": contradiction_count, "results": rows,
            "real_memory_os_runtime_verified": False}


def _self_test():
    cases = []
    for i in range(3):
        text = f"Synthetic project P{i}: CANON_VALUE_{i} is authoritative."
        t = "2026-10-17T12:00:00+02:00"
        cases.append({"id": f"synthetic-pass-{i}", "canonical": {
            "source_ref": f"test://source/{i}", "updated_at": t, "text": text},
            "memory": {"source_ref": f"test://source/{i}",
                       "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                       "source_updated_at": t, "content": text},
            "claim": f"CANON_VALUE_{i}", "expect": VERIFIED})
    stale = json.loads(json.dumps(cases[0]))
    stale["id"] = "synthetic-stale-timestamp"
    stale["expect"] = CONFLICT
    stale["memory"]["source_updated_at"] = "2026-10-16T12:00:00+02:00"
    cases.append(stale)
    missing = json.loads(json.dumps(cases[1]))
    missing["id"] = "synthetic-missing-provenance"
    missing["expect"] = INSUFFICIENT
    del missing["memory"]["source_sha256"]
    cases.append(missing)
    changed = json.loads(json.dumps(cases[2]))
    changed["id"] = "synthetic-changed-source"
    changed["expect"] = CONFLICT
    changed["memory"]["source_sha256"] = "a" * 64
    cases.append(changed)
    return cases


def main():
    p = argparse.ArgumentParser()
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--cases", type=Path)
    args = p.parse_args()
    cases = _self_test() if args.self_test else json.loads(args.cases.read_text(encoding="utf-8"))
    report = validate_suite(cases)
    # No private source bodies or retrieved text are emitted.
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["unit_suite_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
