"""Legacy compatibility workers using deterministic demonstration thresholds."""

import uuid
from typing import List

from .models import AgentAlert, SystemTaskPayload, UrgencyLevel


class InvariantQCWorker:
    PRIMARY_THRESHOLD = 25.0

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        if payload.primary_metric <= cls.PRIMARY_THRESHOLD:
            return []
        return [AgentAlert(
            alert_id=f"QC-{uuid.uuid4().hex[:6]}",
            origin_worker="InvariantQCWorker",
            urgency=UrgencyLevel.ELEVATED,
            summary="Configured Primary Threshold Exceeded",
            technical_details=(
                f"Primary measurement ({payload.primary_metric:.2f}) exceeds the "
                f"project demonstration threshold ({cls.PRIMARY_THRESHOLD:.2f})."
            ),
            actionable_remediation="Review the source measurement against locally validated assay criteria.",
        )]


class SafetyEscalationWorker:
    SECONDARY_THRESHOLD = 12.0

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        if not payload.is_critical_flag and payload.secondary_metric <= cls.SECONDARY_THRESHOLD:
            return []
        return [AgentAlert(
            alert_id=f"SAFE-{uuid.uuid4().hex[:6]}",
            origin_worker="SafetyEscalationWorker",
            urgency=UrgencyLevel.CRITICAL_STAT if payload.is_critical_flag else UrgencyLevel.ELEVATED,
            summary="Configured Secondary Review Flag",
            technical_details=(
                f"PriorityFlag={payload.is_critical_flag}; secondary value "
                f"{payload.secondary_metric:.2f}."
            ),
            actionable_remediation=(
                "Review the record in the intended local workflow; this rule does "
                "not establish clinical urgency."
            ),
        )]


class ProtocolConformanceWorker:
    TOKENS = ("DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT")

    @classmethod
    def evaluate(cls, payload: SystemTaskPayload) -> List[AgentAlert]:
        descriptor = str(payload.status_descriptor).upper()
        if not any(token in descriptor for token in cls.TOKENS):
            return []
        return [AgentAlert(
            alert_id=f"CONF-{uuid.uuid4().hex[:6]}",
            origin_worker="ProtocolConformanceWorker",
            urgency=UrgencyLevel.ELEVATED,
            summary="Descriptor Review Flag",
            technical_details=(
                f"Descriptor '{payload.status_descriptor}' matched a configured review keyword."
            ),
            actionable_remediation=(
                "Correlate the descriptor with validated laboratory and pathology data."
            ),
        )]
