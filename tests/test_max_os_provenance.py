import unittest
from datetime import datetime, timezone
from icarus.max_os_provenance import verify_retrieval

NOW = datetime(2026, 10, 15, 18, 0, tzinfo=timezone.utc)
SOURCES = {
    "CANON-001": {"id": "CANON-001", "authority": "CANON_FROZEN", "revision": "r3", "timestamp": "2026-10-10T12:00:00Z", "content": "A horse does not speak. Scene one."},
    "CANON-002": {"id": "CANON-002", "authority": "CANON", "revision": "r7", "timestamp": "2026-10-11T12:00:00Z", "content": "Three gates precede an order. Scene two."},
    "CANON-003": {"id": "CANON-003", "authority": "CANON", "revision": "r9", "timestamp": "2026-10-12T12:00:00Z", "content": "A verified completion needs a readback. Scene three."},
}


def hit(key, excerpt):
    s = SOURCES[key]
    return {"source_ref": key, "source_revision": s["revision"],
            "source_timestamp": s["timestamp"], "excerpt": excerpt}


class ProvenanceTests(unittest.TestCase):
    def test_three_independent_canon_retrievals(self):
        for ref, excerpt in (("CANON-001", "A horse does not speak."),
                             ("CANON-002", "Three gates precede an order."),
                             ("CANON-003", "A verified completion needs a readback.")):
            with self.subTest(ref=ref):
                got = verify_retrieval([hit(ref, excerpt)], SOURCES.get, now=NOW)
                self.assertEqual(got["status"], "VERIFIED")
                self.assertIn(f"ref={ref}", got["context"])
                self.assertIn(excerpt, got["context"])

    def test_deliberately_stale_contradiction_blocks(self):
        bad = hit("CANON-001", "A horse does not speak.")
        bad["source_revision"] = "r0"
        got = verify_retrieval([bad], SOURCES.get, now=NOW)
        self.assertEqual(got["status"], "BLOCKED_CONFLICT")
        self.assertEqual(got["verified"], [])
        self.assertNotIn("A horse does not speak.", got["context"])

    def test_fail_closed_missing_metadata_no_resolver(self):
        self.assertEqual(verify_retrieval([{"summary": "looks right"}], SOURCES.get, now=NOW)["status"], "BLOCKED_CONFLICT")
        self.assertEqual(verify_retrieval([hit("CANON-001", "Scene one.")], None, now=NOW)["status"], "BLOCKED_NO_RESOLVER")

    def test_fabric_and_qdrant_claims_are_not_auto_promoted(self):
        for fake in ({"source": "wiki.md", "content_preview": "Scene one."},
                     {"id": "fabric4", "timestamp": "2026-10-12", "summary": "Scene one."}):
            self.assertEqual(verify_retrieval([fake], SOURCES.get, now=NOW)["verified"], [])

    def test_modified_or_noncanonical_excerpt_is_blocked(self):
        bad = hit("CANON-002", "Three gates precede an order.")
        bad["excerpt"] = "Orders are unrestricted."
        self.assertEqual(verify_retrieval([bad], SOURCES.get, now=NOW)["status"], "BLOCKED_CONFLICT")
        SOURCES["CANON-002"]["authority"] = "DRAFT"
        try:
            self.assertEqual(verify_retrieval([hit("CANON-002", "Scene two.")], SOURCES.get, now=NOW)["status"], "BLOCKED_CONFLICT")
        finally:
            SOURCES["CANON-002"]["authority"] = "CANON"

    def test_mixed_good_and_bad_blocks_everything(self):
        bad = hit("CANON-002", "Scene two.")
        bad["source_revision"] = "outdated"
        got = verify_retrieval([hit("CANON-001", "Scene one."), bad], SOURCES.get, now=NOW)
        self.assertEqual(got["status"], "BLOCKED_CONFLICT")
        self.assertEqual(got["verified"], [])


if __name__ == "__main__":
    unittest.main()
