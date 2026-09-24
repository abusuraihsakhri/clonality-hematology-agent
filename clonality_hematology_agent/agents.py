"""Rule coordinators for the clonality hematology research utility."""

import uuid
from typing import Any, Dict, List

from .engine import ClinicalDomainEngine
from .models import AgentAlert, ClinicalCasePayload, ClinicalIntegrityStatus, UrgencyLevel


class PeakRatioCalculatorAgent:
    """Compatibility worker for the configured primary numeric threshold."""

    def audit(self, case: ClinicalCasePayload) -> List[AgentAlert]:
        res = ClinicalDomainEngine.evaluate_primary_index(case.primary_metric)
        if not res:
            return []
        return [AgentAlert(
            alert_id=str(uuid.uuid4())[:8],
            sub_agent="PeakRatioCalculatorAgent",
            urgency=UrgencyLevel.WARNING,
            title=res["title"],
            clinical_finding=res["finding"],
            actionable_recommendation=res["recommendation"],
        )]


class PolyClonalityFilterAgent:
    """Compatibility worker for the configured secondary/priority rule."""

    def audit(self, case: ClinicalCasePayload) -> List[AgentAlert]:
        res = ClinicalDomainEngine.evaluate_secondary_kinetics(case.secondary_metric, case.is_stat)
        if not res:
            return []
        return [AgentAlert(
            alert_id=str(uuid.uuid4())[:8],
            sub_agent="PolyClonalityFilterAgent",
            urgency=UrgencyLevel.STAT_CRITICAL if case.is_stat else UrgencyLevel.WARNING,
            title=res["title"],
            clinical_finding=res["finding"],
            actionable_recommendation=res["recommendation"],
        )]


class BMRDMarkerFinderAgent:
    """Compatibility worker for lexical status-descriptor review flags."""

    def audit(self, case: ClinicalCasePayload) -> List[AgentAlert]:
        res = ClinicalDomainEngine.evaluate_biomarker_concordance(case.status_flag, case.biomarkers)
        if not res:
            return []
        return [AgentAlert(
            alert_id=str(uuid.uuid4())[:8],
            sub_agent="BMRDMarkerFinderAgent",
            urgency=UrgencyLevel.ADVISORY,
            title=res["title"],
            clinical_finding=res["finding"],
            actionable_recommendation=res["recommendation"],
        )]


class ClonoCoordinator:
    """Coordinates deterministic compatibility rules and returns a dossier."""

    def __init__(self):
        self.agent_1 = PeakRatioCalculatorAgent()
        self.agent_2 = PolyClonalityFilterAgent()
        self.agent_3 = BMRDMarkerFinderAgent()
        self.case_registry: Dict[str, Dict[str, Any]] = {}

    def process_case(self, case: ClinicalCasePayload) -> Dict[str, Any]:
        ClinicalDomainEngine.validate_case(case)
        all_alerts: List[AgentAlert] = []
        all_alerts.extend(self.agent_1.audit(case))
        all_alerts.extend(self.agent_2.audit(case))
        all_alerts.extend(self.agent_3.audit(case))

        stat_count = sum(1 for alert in all_alerts if alert.urgency == UrgencyLevel.STAT_CRITICAL)
        warn_count = sum(1 for alert in all_alerts if alert.urgency == UrgencyLevel.WARNING)

        if stat_count:
            status = ClinicalIntegrityStatus.CRITICAL_ACTION_REQUIRED
        elif warn_count or all_alerts:
            status = ClinicalIntegrityStatus.DISCORDANCE_DETECTED
        else:
            status = ClinicalIntegrityStatus.CONCORDANT_NORMAL

        dossier = {
            "system": "clonality-hematology-agent",
            "domain": "Hematopathology research utility",
            "case_id": case.case_id,
            "patient_synthetic_id": case.patient_synthetic_id,
            "overall_status": status.value,
            "total_alerts": len(all_alerts),
            "stat_critical_alerts": stat_count,
            "warning_alerts": warn_count,
            "alerts": [alert.to_dict() for alert in all_alerts],
            "guideline_standard": ClinicalDomainEngine.REFERENCE_NOTE,
            "consensus_summary": (
                f"Rule review completed across 3 deterministic checks with status [{status.value}]."
            ),
        }
        self.case_registry[case.case_id] = dossier
        return dossier

    def query_supervisory_chat(self, user_query: str) -> str:
        query = user_query.strip().lower()
        if "status" in query or "summary" in query:
            return (
                f"Clonality hematology research utility currently holds "
                f"{len(self.case_registry)} case result(s) in process memory."
            )
        if "guideline" in query or "standard" in query:
            return ClinicalDomainEngine.REFERENCE_NOTE
        return (
            "This utility runs deterministic demonstration rules only. "
            "Use validated laboratory criteria for diagnostic interpretation."
        )
