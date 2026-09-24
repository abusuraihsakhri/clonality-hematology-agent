import csv

import pytest

from clonality_hematology_agent.agents import ClonoCoordinator
from clonality_hematology_agent.cli import main
from clonality_hematology_agent.models import ClinicalCasePayload


def test_canonical_engine_rejects_non_finite_values():
    case = ClinicalCasePayload(
        case_id="CASE-NAN",
        patient_synthetic_id="SYNTHETIC",
        primary_metric=float("nan"),
        secondary_metric=1.0,
        status_flag="NORMAL",
    )
    with pytest.raises(ValueError):
        ClonoCoordinator().process_case(case)


def test_batch_false_string_is_not_truthy(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "case_id,patient_synthetic_id,metric_primary,metric_secondary,is_stat,status_flag\n"
        "CASE-1,SYNTH-1,10,2,False,NORMAL\n",
        encoding="utf-8",
    )
    assert main(["batch", "-i", str(source), "-o", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["stat_critical_alerts"] == "0"
    assert row["overall_status"] == "CONCORDANT_NORMAL"


def test_primary_rule_is_explicitly_demonstration_only():
    case = ClinicalCasePayload(
        case_id="CASE-1",
        patient_synthetic_id="SYNTH-1",
        primary_metric=30.0,
        secondary_metric=2.0,
        status_flag="NORMAL",
    )
    dossier = ClonoCoordinator().process_case(case)
    assert dossier["warning_alerts"] == 1
    assert "demonstration" in dossier["guideline_standard"].lower()
