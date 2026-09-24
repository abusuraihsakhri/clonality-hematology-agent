#!/usr/bin/env python3
"""Legacy compatibility entry point for clonality-hematology-agent.

The implementation delegates to the canonical package so rule behavior is not
maintained in multiple independent code paths.
"""

import argparse
import csv
import datetime
import sys
from typing import Any, Dict

from clonality_hematology_agent import __version__
from clonality_hematology_agent.agents import (
    BMRDMarkerFinderAgent as _BMRDMarkerFinderAgent,
    ClonoCoordinator as _ClonoCoordinator,
    PeakRatioCalculatorAgent as _PeakRatioCalculatorAgent,
    PolyClonalityFilterAgent as _PolyClonalityFilterAgent,
)
from clonality_hematology_agent.cli import _parse_bool
from clonality_hematology_agent.models import ClinicalCasePayload


class Severity(str):
    INFO = "INFO"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL_ACTION_REQUIRED"


class DomainKnowledgeRegistry:
    SYSTEM_VERSION = __version__
    ZERO_PHI_COMPLIANCE = False
    HIPAA_SAFE_HARBOR = "NOT_CLAIMED"

    @staticmethod
    def audit_security_and_integrity(payload: Dict[str, Any]):
        warnings = []
        for key in payload:
            if any(marker in key.lower() for marker in ("patient_name", "ssn", "mrn_raw", "dob_raw")):
                warnings.append(f"IDENTIFIER_REVIEW: direct-identifier-like field '{key}' detected.")
        return warnings


def _to_case(payload: Dict[str, Any]) -> ClinicalCasePayload:
    return ClinicalCasePayload(
        case_id=str(payload.get("case_id", "CASE-01")),
        patient_synthetic_id=str(
            payload.get("patient_synthetic_id", payload.get("target_identifier", "SYNTHETIC"))
        ),
        primary_metric=float(payload.get("metric_primary", payload.get("primary_metric", 15.0))),
        secondary_metric=float(payload.get("metric_secondary", payload.get("secondary_metric", 5.0))),
        status_flag=str(
            payload.get(
                "status_text",
                payload.get("status_flag", payload.get("status_descriptor", "NORMAL")),
            )
        ),
        is_stat=_parse_bool(
            payload.get(
                "critical_flag",
                payload.get("is_stat", payload.get("is_critical_flag", False)),
            )
        ),
    )


class PeakRatioCalculatorAgent:
    def __init__(self):
        self._impl = _PeakRatioCalculatorAgent()

    def evaluate(self, payload: Dict[str, Any]):
        return self._impl.audit(_to_case(payload))


class PolyClonalityFilterAgent:
    def __init__(self):
        self._impl = _PolyClonalityFilterAgent()

    def evaluate(self, payload: Dict[str, Any]):
        return self._impl.audit(_to_case(payload))


class BMRDMarkerFinderAgent:
    def __init__(self):
        self._impl = _BMRDMarkerFinderAgent()

    def evaluate(self, payload: Dict[str, Any]):
        return self._impl.audit(_to_case(payload))


class ClonoCoordinator:
    def __init__(self):
        self._impl = _ClonoCoordinator()

    def audit_case(self, case_payload: Dict[str, Any]) -> Dict[str, Any]:
        dossier = self._impl.process_case(_to_case(case_payload))
        alerts = [
            {
                "alert_id": alert["alert_id"],
                "agent": alert["sub_agent"],
                "severity": alert["urgency"],
                "title": alert["title"],
                "details": alert["clinical_finding"],
                "recommendation": alert["actionable_recommendation"],
                "timestamp": alert["timestamp"],
            }
            for alert in dossier["alerts"]
        ]
        return {
            "system": dossier["system"],
            "domain": dossier["domain"],
            "case_id": dossier["case_id"],
            "overall_status": dossier["overall_status"],
            "total_alerts": dossier["total_alerts"],
            "critical_count": dossier["stat_critical_alerts"],
            "warning_count": dossier["warning_alerts"],
            "alerts": alerts,
            "consensus_summary": dossier["consensus_summary"],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def query_assistant(self, user_query: str) -> str:
        return self._impl.query_supervisory_chat(user_query)


coordinator = ClonoCoordinator()


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError:
        return None

    app = FastAPI(
        title="Clonality Hematology Rule Review API",
        description="Legacy-compatible research/demo interface.",
        version=__version__,
    )

    class AuditRequest(BaseModel):
        case_id: str = "CASE-TEST-001"
        metric_primary: float = 15.0
        metric_secondary: float = 5.0
        critical_flag: bool = False
        status_text: str = "NORMAL"

    class ChatRequest(BaseModel):
        query: str

    @app.get("/health")
    def health():
        return {
            "status": "HEALTHY",
            "system": "clonality-hematology-agent",
            "version": __version__,
        }

    @app.post("/api/audit")
    def api_audit(req: AuditRequest):
        return coordinator.audit_case(req.model_dump())

    @app.post("/api/chat")
    def api_chat(req: ChatRequest):
        return {"response": coordinator.query_assistant(req.query)}

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clono-mind",
        description="Legacy clonality hematology rule-review interface",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--case-id", default="CASE-TEST-001")
    audit_parser.add_argument("--primary", type=float, default=15.0)
    audit_parser.add_argument("--secondary", type=float, default=5.0)
    audit_parser.add_argument("--critical", action="store_true")
    audit_parser.add_argument("--status", default="NORMAL")

    batch_parser = subparsers.add_parser("batch")
    batch_parser.add_argument("-i", "--input", required=True)
    batch_parser.add_argument("-o", "--output", default="results.csv")

    chat_parser = subparsers.add_parser("chat")
    chat_parser.add_argument("query", nargs="+")

    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        dossier = coordinator.audit_case(
            {
                "case_id": args.case_id,
                "metric_primary": args.primary,
                "metric_secondary": args.secondary,
                "critical_flag": args.critical,
                "status_text": args.status,
            }
        )
        print(f"{dossier['case_id']}: {dossier['overall_status']} ({dossier['total_alerts']} alert(s))")
        return 0

    if args.command == "chat":
        print(coordinator.query_assistant(" ".join(args.query)))
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = fieldnames + [
            name
            for name in ("overall_status", "total_alerts", "critical_count", "consensus_summary")
            if name not in fieldnames
        ]
        output_rows = []
        for row in rows:
            dossier = coordinator.audit_case(dict(row))
            result = dict(row)
            result["overall_status"] = dossier["overall_status"]
            result["total_alerts"] = dossier["total_alerts"]
            result["critical_count"] = dossier["critical_count"]
            result["consensus_summary"] = dossier["consensus_summary"]
            output_rows.append(result)

        with open(args.output, mode="w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(output_rows)
        print(f"Processed {len(output_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
        except ImportError:
            print("Install the server extra: pip install -e '.[server]'", file=sys.stderr)
            return 1
        app = create_app()
        if app is None:
            return 1
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
