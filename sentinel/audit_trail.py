"""
Sentinel — Module M2: Immutable Audit Trail
Legal basis: EU AI Act Art.12, GDPR Art.25, NIST AI RMF MG-2.2
"""

import hashlib
import json
import datetime
import re
from typing import List, Optional


_PII = re.compile(r'_(email|ssn|dob|phone|name|address|ip)$', re.IGNORECASE)


class AuditEntry:
    """Plain class — avoids dataclass asdict issues in Python 3.14."""
    def __init__(self, event_type, actor, payload,
                 timestamp, prev_hash, entry_hash=""):
        self.event_type = event_type
        self.actor      = actor
        self.payload    = payload
        self.timestamp  = timestamp
        self.prev_hash  = prev_hash
        self.entry_hash = entry_hash


class AuditTrail:
    GENESIS = "0" * 64

    def __init__(self):
        self._log: List[AuditEntry] = []
        self._last_hash: str = self.GENESIS

    def _scrub(self, payload: dict) -> dict:
        return {k: v for k, v in payload.items()
                if not _PII.search(k)}

    def _serialize(self, entry: AuditEntry) -> str:
        """Convert entry to deterministic JSON string."""
        data = {
            "event_type": entry.event_type,
            "actor":      entry.actor,
            "payload":    entry.payload,
            "timestamp":  entry.timestamp,
            "prev_hash":  entry.prev_hash,
            "entry_hash": entry.entry_hash,
        }
        return json.dumps(data, sort_keys=True, default=str)

    def _hash(self, entry: AuditEntry) -> str:
        raw = self._serialize(entry)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record(self, event_type: str, actor: str,
               payload: dict) -> AuditEntry:
        clean = self._scrub(payload)
        # Freeze payload as sorted JSON string to prevent mutation
        frozen_payload = json.loads(
            json.dumps(clean, sort_keys=True, default=str)
        )
        entry = AuditEntry(
            event_type = event_type,
            actor      = actor,
            payload    = frozen_payload,
            timestamp  = datetime.datetime.now(datetime.timezone.utc).isoformat(),
            prev_hash  = self._last_hash,
            entry_hash = "",
        )
        entry.entry_hash = self._hash(entry)
        self._last_hash  = entry.entry_hash
        self._log.append(entry)
        return entry

    def verify(self) -> bool:
        prev = self.GENESIS
        for entry in self._log:
            if entry.prev_hash != prev:
                return False
            saved_hash   = entry.entry_hash
            entry.entry_hash = ""
            recomputed   = self._hash(entry)
            entry.entry_hash = saved_hash
            if recomputed != saved_hash:
                return False
            prev = saved_hash
        return True

    def query(self, event_type: Optional[str] = None,
              actor: Optional[str] = None) -> List[AuditEntry]:
        return [
            e for e in self._log
            if (event_type is None or e.event_type == event_type)
            and (actor is None or e.actor == actor)
        ]

    @property
    def entry_count(self) -> int:
        return len(self._log)

    @property
    def terminal_hash(self) -> str:
        return self._last_hash


if __name__ == "__main__":
    trail = AuditTrail()

    trail.record("APPROVAL", "sarah.chen@bank.com", {
        "model_id": "loan-ai-v3",
        "action": "approved_for_production",
        "applicant_email": "john.smith@email.com",
    })

    trail.record("DECISION", "loan-ai-v3", {
        "app_id": "APP-7821",
        "decision": "DENY",
        "confidence": 0.91,
        "top_feature": "zip_code",
        "applicant_ssn": "123-45-6789",
    })

    trail.record("DRIFT_ALERT", "monitor-svc", {
        "model_id": "loan-ai-v3",
        "psi": 0.21,
        "threshold": 0.15,
    })

    print("\nSentinel Audit Trail")
    print("=" * 40)
    print(f"Entries:  {trail.entry_count}")
    print(f"Verified: {trail.verify()}")
    print(f"Terminal: {trail.terminal_hash[:20]}...")
    print()

    for i, e in enumerate(trail._log):
        print(f"Entry {i+1}: {e.event_type} by {e.actor}")
        print(f"  payload:  {e.payload}")
        print(f"  hash:     {e.entry_hash[:20]}...")

    print()
    print("Tamper test — modifying entry 2...")
    trail._log[1].payload["decision"] = "APPROVE"
    print(f"Verified after tamper: {trail.verify()}")
    print("=" * 40)