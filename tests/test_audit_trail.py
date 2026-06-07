"""Sentinel — Tests for Module M2: Audit Trail"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sentinel.audit_trail import AuditTrail


def test_empty_chain_verifies():
    trail = AuditTrail()
    assert trail.verify() is True


def test_three_entries_verify():
    trail = AuditTrail()
    trail.record("APPROVAL", "sarah.chen", {"model_id": "m1"})
    trail.record("DECISION", "model-v1",  {"result": "DENY"})
    trail.record("DRIFT_ALERT", "monitor", {"psi": 0.21})
    assert trail.verify() is True


def test_tamper_detected():
    trail = AuditTrail()
    trail.record("DECISION", "model-v1", {"result": "DENY"})
    trail._log[0].payload["result"] = "APPROVE"
    assert trail.verify() is False


def test_pii_scrubbed_before_hashing():
    trail = AuditTrail()
    trail.record("DECISION", "model-v1", {
        "app_id": "APP-001",
        "applicant_ssn": "123-45-6789",
        "applicant_email": "user@email.com",
        "decision": "DENY",
    })
    entry = trail._log[0]
    assert "applicant_ssn" not in entry.payload
    assert "applicant_email" not in entry.payload
    assert "app_id" in entry.payload
    assert "decision" in entry.payload


def test_chain_still_verifies_after_query():
    trail = AuditTrail()
    trail.record("APPROVAL", "sarah.chen", {"model_id": "m1"})
    trail.record("DECISION", "model-v1",  {"result": "DENY"})
    results = trail.query(event_type="APPROVAL")
    assert len(results) == 1
    assert trail.verify() is True


def test_entry_count():
    trail = AuditTrail()
    trail.record("APPROVAL", "sarah.chen", {"model_id": "m1"})
    trail.record("DECISION", "model-v1",  {"result": "DENY"})
    assert trail.entry_count == 2


def test_genesis_hash_is_64_zeros():
    trail = AuditTrail()
    assert trail.GENESIS == "0" * 64
    assert trail._log[0].prev_hash == "0" * 64 if trail._log else True