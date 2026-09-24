"""Tests for the legacy compatibility interface and security primitives."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import AuditLogger, GLOBAL_AUDIT, PHIGuard, SecurityException
from agents.llm_factory import LLMFactory
from agents.models import SystemIntegrityStatus, SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor
from agents.workers import InvariantQCWorker, ProtocolConformanceWorker, SafetyEscalationWorker
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    p2 = SystemTaskPayload(
        task_id="T2",
        target_identifier="KEY-02",
        primary_metric=10.0,
        is_critical_flag=True,
    )
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    p3 = SystemTaskPayload(
        task_id="T3",
        target_identifier="KEY-03",
        primary_metric=10.0,
        status_descriptor="DISCORDANT_ANOMALY",
    )
    assert len(ProtocolConformanceWorker.evaluate(p3)) == 1


def test_supervisor_consensus_and_cli(tmp_path):
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL",
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash
    assert AuditLogger.verify_integrity() is True

    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0

    output = tmp_path / "out.csv"
    assert main(["batch", "-i", "sample.csv", "-o", str(output)]) == 0
    assert output.exists()
    assert output.stat().st_size > 0


def test_audit_detects_signature_tampering():
    entry = AuditLogger.log("tester", "test", "INTEGRITY_TEST", {"status": "SUCCESS"})
    original = entry["current_hash"]
    entry["current_hash"] = "0" * 64
    assert GLOBAL_AUDIT.verify_integrity() is False
    entry["current_hash"] = original
    assert GLOBAL_AUDIT.verify_integrity() is True


def test_unimplemented_llm_provider_fails_closed():
    with pytest.raises(ValueError):
        LLMFactory.create("openai")


def test_non_finite_payload_rejected():
    with pytest.raises(ValueError):
        SystemTaskPayload(task_id="T-NAN", target_identifier="KEY", primary_metric=float("nan"))
