"""Deterministic demonstration rules used by the package.

These thresholds are compatibility defaults from the original project. They
are not EuroClonality/BIOMED-2 diagnostic cutoffs and must not be treated as
validated clinical decision limits.
"""

import math
from typing import Any, Dict, Optional

from .models import ClinicalCasePayload


class ClinicalDomainEngine:
    PRIMARY_BASELINE_LIMIT = 20.0
    SECONDARY_ALERT_LIMIT = 10.0
    REFERENCE_NOTE = (
        "EuroClonality interpretation is pattern-based and laboratory-validated; "
        "the numeric defaults in this project are demonstration thresholds."
    )

    @staticmethod
    def _validate_metric(name: str, value: float) -> float:
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{name} must be a finite number")
        return numeric

    @classmethod
    def validate_case(cls, case: ClinicalCasePayload) -> None:
        if not str(case.case_id).strip():
            raise ValueError("case_id must not be empty")
        if not str(case.patient_synthetic_id).strip():
            raise ValueError("patient_synthetic_id must not be empty")
        cls._validate_metric("primary_metric", case.primary_metric)
        cls._validate_metric("secondary_metric", case.secondary_metric)

    @classmethod
    def evaluate_primary_index(cls, value: float) -> Optional[Dict[str, Any]]:
        value = cls._validate_metric("primary_metric", value)
        if value > cls.PRIMARY_BASELINE_LIMIT:
            return {
                "title": "Configured Primary Threshold Exceeded",
                "finding": (
                    f"Observed value ({value:.2f}) exceeds the project demonstration "
                    f"threshold ({cls.PRIMARY_BASELINE_LIMIT:.1f})."
                ),
                "recommendation": (
                    "Review the source measurement and interpret it only against a "
                    "locally validated assay workflow."
                ),
            }
        return None

    @classmethod
    def evaluate_secondary_kinetics(cls, value: float, is_stat: bool) -> Optional[Dict[str, Any]]:
        value = cls._validate_metric("secondary_metric", value)
        if value > cls.SECONDARY_ALERT_LIMIT or is_stat:
            return {
                "title": "Configured Secondary Review Flag",
                "finding": (
                    f"Secondary value ({value:.2f}) or explicit priority flag "
                    f"(is_stat={bool(is_stat)}) triggered the demonstration rule."
                ),
                "recommendation": (
                    "Review the record in the intended local workflow; this flag does "
                    "not establish clinical urgency."
                ),
            }
        return None

    @classmethod
    def evaluate_biomarker_concordance(cls, status_flag: str, biomarkers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        del biomarkers
        status_upper = str(status_flag).upper()
        if any(token in status_upper for token in ("DISCORDANT", "EQUIVOCAL", "MUTANT")):
            return {
                "title": "Descriptor Review Flag",
                "finding": f"Status descriptor '{status_flag}' matched a configured review keyword.",
                "recommendation": (
                    "Correlate the descriptor with validated laboratory results, morphology, "
                    "immunophenotype, and the relevant clinical context."
                ),
            }
        return None
