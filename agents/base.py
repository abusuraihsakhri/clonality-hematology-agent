"""Identifier screening and an in-memory HMAC-SHA256 audit trail.

The identifier screen is a heuristic safeguard, not a complete de-identification
or HIPAA Safe Harbor implementation.
"""

import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI_PATTERNS = [
    re.compile(r"\b(?:MRN)[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Raised when the heuristic identifier screen detects a configured pattern."""


class ResourceLimitExceededException(Exception):
    """Raised when computational parameters exceed configured bounds."""


def assert_no_phi(text: str) -> None:
    if not text:
        return
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text)):
            raise SecurityException(f"Sensitive identifier pattern detected: {pattern.pattern}")


class PHIGuard:
    @staticmethod
    def assert_no_phi(text: str) -> None:
        assert_no_phi(text)

    @staticmethod
    def redact_phi(text: str) -> str:
        result = str(text)
        for pattern in PHI_PATTERNS:
            result = pattern.sub("[REDACTED_IDENTIFIER]", result)
        return result


class AuditTrail:
    """Process-local chained HMAC-SHA256 audit entries."""

    def __init__(self, secret_key: Optional[str] = None):
        configured = secret_key or os.getenv("AUDIT_SECRET_KEY")
        self.secret_key = configured.encode("utf-8") if configured else secrets.token_bytes(32)
        self.logs: List[Dict[str, Any]] = []

    def _signature_for(self, entry: Dict[str, Any]) -> str:
        sign_string = (
            f"{entry['audit_id']}|{entry['timestamp']}|{entry['actor']}|"
            f"{entry['actor_tier']}|{entry['event_type']}|{entry['payload_hash']}|"
            f"{entry['prev_hash']}"
        )
        return hmac.new(self.secret_key, sign_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        payload_str = json.dumps(details, sort_keys=True)
        assert_no_phi(payload_str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        audit_id = f"AUDIT-{int(time.time() * 1000)}-{len(self.logs) + 1}"
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_hash = self.logs[-1]["current_hash"] if self.logs else "GENESIS_BLOCK_0000000000000000"
        entry = {
            "audit_id": audit_id,
            "timestamp": timestamp,
            "actor": actor,
            "actor_tier": actor_tier,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "prev_hash": prev_hash,
        }
        entry["current_hash"] = self._signature_for(entry)
        self.logs.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        for index, entry in enumerate(self.logs):
            expected_prev = (
                self.logs[index - 1]["current_hash"]
                if index > 0
                else "GENESIS_BLOCK_0000000000000000"
            )
            if entry.get("prev_hash") != expected_prev:
                return False
            expected_signature = self._signature_for(entry)
            if not hmac.compare_digest(str(entry.get("current_hash", "")), expected_signature):
                return False
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        return self.logs


GLOBAL_AUDIT = AuditTrail()


class AuditLogger:
    @staticmethod
    def log(actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        return GLOBAL_AUDIT.log(actor, actor_tier, event_type, details)

    @staticmethod
    def get_trail() -> List[Dict[str, Any]]:
        return GLOBAL_AUDIT.get_trail()

    @staticmethod
    def verify_integrity() -> bool:
        return GLOBAL_AUDIT.verify_integrity()


class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return result
