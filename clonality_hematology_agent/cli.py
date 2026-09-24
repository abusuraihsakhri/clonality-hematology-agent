"""Command-line interface for the clonality hematology research utility."""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Iterable, List

from .agents import ClonoCoordinator
from .models import ClinicalCasePayload

coordinator = ClonoCoordinator()
_TRUE_VALUES = {"1", "true", "yes", "y", "t"}
_FALSE_VALUES = {"0", "false", "no", "n", "f", ""}


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _append_missing(fieldnames: Iterable[str], extras: Iterable[str]) -> List[str]:
    result = list(fieldnames)
    for name in extras:
        if name not in result:
            result.append(name)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clonality-hematology-agent",
        description="Deterministic clonality-assay rule review utility",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit", help="Run a single rule review")
    p_audit.add_argument("--case-id", default="CASE-2026-001")
    p_audit.add_argument("--primary", type=float, default=15.0)
    p_audit.add_argument("--secondary", type=float, default=5.0)
    p_audit.add_argument("--stat", action="store_true")
    p_audit.add_argument("--status", default="NORMAL")

    p_chat = subparsers.add_parser("chat", help="Query utility configuration")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    p_serve = subparsers.add_parser("serve", help="Launch optional FastAPI server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        case = ClinicalCasePayload(
            case_id=args.case_id,
            patient_synthetic_id="SYNTHETIC",
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_flag=args.status,
            is_stat=args.stat,
        )
        try:
            dossier = coordinator.process_case(case)
        except ValueError as exc:
            print(f"Input error: {exc}", file=sys.stderr)
            return 2

        print("=" * 72)
        print("CLONALITY HEMATOLOGY RULE REVIEW")
        print(
            f"Case: {dossier['case_id']} | Status: [{dossier['overall_status']}] "
            f"| Alerts: {dossier['total_alerts']}"
        )
        print("=" * 72)
        for alert in dossier["alerts"]:
            print(f"\n[{alert['urgency']}] {alert['title']}")
            print(f"Finding: {alert['clinical_finding']}")
            print(f"Review:  {alert['actionable_recommendation']}")
        print("\nDemonstration rules only; not a validated diagnostic interpretation.")
        return 0

    if args.command == "chat":
        print(coordinator.query_supervisory_chat(" ".join(args.query)))
        return 0

    if args.command == "batch":
        input_path = Path(args.input)
        try:
            with input_path.open(mode="r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except OSError as exc:
            print(f"Could not read input CSV: {exc}", file=sys.stderr)
            return 2

        if not fieldnames:
            print("Input CSV must contain a header row.", file=sys.stderr)
            return 2

        out_fields = _append_missing(
            fieldnames,
            ["overall_status", "total_alerts", "stat_critical_alerts", "consensus_summary"],
        )
        out_rows = []
        for row_number, row in enumerate(rows, start=2):
            try:
                case = ClinicalCasePayload(
                    case_id=row.get("case_id", "CASE-01"),
                    patient_synthetic_id=row.get("patient_synthetic_id", "SYNTHETIC"),
                    primary_metric=float(row.get("metric_primary", row.get("primary_metric", 15.0))),
                    secondary_metric=float(row.get("metric_secondary", row.get("secondary_metric", 5.0))),
                    status_flag=row.get("status_flag", row.get("status_text", "NORMAL")),
                    is_stat=_parse_bool(row.get("is_stat", row.get("critical_flag", False))),
                )
                dossier = coordinator.process_case(case)
            except (TypeError, ValueError) as exc:
                print(f"Row {row_number}: {exc}", file=sys.stderr)
                return 2

            row_dict = dict(row)
            row_dict["overall_status"] = dossier["overall_status"]
            row_dict["total_alerts"] = dossier["total_alerts"]
            row_dict["stat_critical_alerts"] = dossier["stat_critical_alerts"]
            row_dict["consensus_summary"] = dossier["consensus_summary"]
            out_rows.append(row_dict)

        try:
            with open(args.output, mode="w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=out_fields)
                writer.writeheader()
                writer.writerows(out_rows)
        except OSError as exc:
            print(f"Could not write output CSV: {exc}", file=sys.stderr)
            return 2

        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from .server import create_app
        except ImportError:
            print("Server dependencies are not installed. Run 'pip install -e .[server]'.", file=sys.stderr)
            return 1

        app = create_app()
        if app is None:
            print("FastAPI is not available.", file=sys.stderr)
            return 1
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
