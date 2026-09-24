"""Compact compatibility layer for the original enrichment module.

The original file duplicated the same threshold logic across eight classes and
used clinical-sounding recommendations unsupported by the implemented math.
This module preserves the public class names while centralizing the rule.
"""

import datetime
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuleEvaluationResult:
    feature_name: str
    status: str = "OPTIMAL"
    score: float = 0.0
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class _ThresholdEngine:
    FEATURE_NAME = "Rule Evaluation"

    def __init__(self, threshold: float = 1.0, config: Optional[Dict[str, Any]] = None):
        threshold = float(threshold)
        if not math.isfinite(threshold) or threshold <= 0:
            raise ValueError("threshold must be a finite number greater than zero")
        self.threshold = threshold
        self.config = config or {}
        self.history: List[RuleEvaluationResult] = []

    def evaluate(self, primary_value: float, secondary_value: float = 0.0, **kwargs) -> RuleEvaluationResult:
        primary_value = float(primary_value)
        secondary_value = float(secondary_value)
        if not math.isfinite(primary_value) or not math.isfinite(secondary_value):
            raise ValueError("input values must be finite")

        alerts: List[str] = []
        recommendations: List[str] = []
        if primary_value > self.threshold * 2:
            status = "CRITICAL_ALERT"
            alerts.append(
                f"{self.FEATURE_NAME}: value {primary_value:.2f} exceeded the "
                f"configured high threshold ({self.threshold * 2:.2f})."
            )
            recommendations.append("Review the configured threshold and source measurement before use.")
        elif primary_value > self.threshold:
            status = "WARNING"
            alerts.append(
                f"{self.FEATURE_NAME}: value {primary_value:.2f} exceeded the "
                f"configured threshold ({self.threshold:.2f})."
            )
            recommendations.append("Review the source measurement against the intended validated workflow.")
        else:
            status = "OPTIMAL"
            recommendations.append("Value is within the configured demonstration bounds.")

        result = RuleEvaluationResult(
            feature_name=self.FEATURE_NAME,
            status=status,
            score=round(primary_value, 3),
            metrics={"primary": primary_value, "secondary": secondary_value, **kwargs},
            alerts=alerts,
            recommendations=recommendations,
        )
        self.history.append(result)
        return result


class EnrichmentIdeasImplementationPlansEngine(_ThresholdEngine):
    FEATURE_NAME = "Enrichment Ideas & Implementation Plans"


class RealtimeClonalityDashboardEngine(_ThresholdEngine):
    FEATURE_NAME = "Real-Time Clonality Dashboard"


class AutomatedMrdMonitoringProtocolEngine(_ThresholdEngine):
    FEATURE_NAME = "Automated MRD Monitoring Protocol"


class MultilabAssayHarmonizationPipelineEngine(_ThresholdEngine):
    FEATURE_NAME = "Multilab Assay Harmonization Pipeline"


class IntegratedLymphomaSubtypeClassifierEngine(_ThresholdEngine):
    FEATURE_NAME = "Integrated Lymphoma Subtype Classifier"


class ClonalEvolutionTracker(_ThresholdEngine):
    FEATURE_NAME = "Clonal Evolution Tracker"


class QualityControlAnomalyDetectorEngine(_ThresholdEngine):
    FEATURE_NAME = "Quality Control Anomaly Detector"


class TamperevidentMolecularAuditTrailEngine(_ThresholdEngine):
    FEATURE_NAME = "Tamper-Evident Molecular Audit Trail"


EnrichmentIdeasImplementationPlansEngineResult = RuleEvaluationResult
RealtimeClonalityDashboardEngineResult = RuleEvaluationResult
AutomatedMrdMonitoringProtocolEngineResult = RuleEvaluationResult
MultilabAssayHarmonizationPipelineEngineResult = RuleEvaluationResult
IntegratedLymphomaSubtypeClassifierEngineResult = RuleEvaluationResult
ClonalEvolutionTrackerResult = RuleEvaluationResult
QualityControlAnomalyDetectorEngineResult = RuleEvaluationResult
TamperevidentMolecularAuditTrailEngineResult = RuleEvaluationResult


class ClonalityhematologyagentEnrichmentSuite:
    def __init__(self):
        self.enrichmentideasimple = EnrichmentIdeasImplementationPlansEngine()
        self.realtimeclonalitydas = RealtimeClonalityDashboardEngine()
        self.automatedmrdmonitori = AutomatedMrdMonitoringProtocolEngine()
        self.multilabassayharmoni = MultilabAssayHarmonizationPipelineEngine()
        self.integratedlymphomasu = IntegratedLymphomaSubtypeClassifierEngine()
        self.clonalevolutiontrack = ClonalEvolutionTracker()
        self.qualitycontrolanomal = QualityControlAnomalyDetectorEngine()
        self.tamperevidentmolecul = TamperevidentMolecularAuditTrailEngine()

    def execute_all(self, primary_val: float = 1.5, secondary_val: float = 0.5) -> Dict[str, RuleEvaluationResult]:
        return {
            "EnrichmentIdeasImplementationPlansEngine": self.enrichmentideasimple.evaluate(primary_val, secondary_val),
            "RealtimeClonalityDashboardEngine": self.realtimeclonalitydas.evaluate(primary_val, secondary_val),
            "AutomatedMrdMonitoringProtocolEngine": self.automatedmrdmonitori.evaluate(primary_val, secondary_val),
            "MultilabAssayHarmonizationPipelineEngine": self.multilabassayharmoni.evaluate(primary_val, secondary_val),
            "IntegratedLymphomaSubtypeClassifierEngine": self.integratedlymphomasu.evaluate(primary_val, secondary_val),
            "ClonalEvolutionTracker": self.clonalevolutiontrack.evaluate(primary_val, secondary_val),
            "QualityControlAnomalyDetectorEngine": self.qualitycontrolanomal.evaluate(primary_val, secondary_val),
            "TamperevidentMolecularAuditTrailEngine": self.tamperevidentmolecul.evaluate(primary_val, secondary_val),
        }


enrichment_suite = ClonalityhematologyagentEnrichmentSuite()
