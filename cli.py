"""Legacy command-line interface for clonality-hematology-agent."""

import argparse
import csv
import sys

from agents.base import AuditLogger
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="clonality-hematology-agent",
        description="Legacy deterministic rule-review interface",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_audit = subparsers.add_parser("audit", help="Run single task rule review")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=float, default=15.0)
    p_audit.add_argument("--secondary", type=float, default=5.0)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="NOMINAL")

    p_chat = subparsers.add_parser("chat", help="Query utility configuration")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    subparsers.add_parser("verify-audit", help="Verify the process-local HMAC audit trail")

    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 72)
        print("CLONALITY HEMATOLOGY RULE REVIEW")
        print("Research/demo compatibility rules; not a diagnostic interpretation.")
        print(
            f"Dossier: {dossier.dossier_id} | "
            f"Rule status: [{dossier.overall_urgency.value}]"
        )
        print("=" * 72)
        for alert in dossier.alerts:
            print(f"\n[{alert.urgency.value}] from {alert.origin_worker}:")
            print(f"Summary: {alert.summary}")
            print(f"Details: {alert.technical_details}")
            print(f"Review:  {alert.actionable_remediation}")
        print(f"\nHMAC-SHA256 audit hash: {dossier.audit_hash}")
        print("=" * 72)
        return 0

    if args.command == "chat":
        answer = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Rule Review Utility]:\n{answer}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit trail blocks: {len(trail)} | HMAC integrity verified: {valid}")
        return 0

    if args.command == "batch":
        try:
            with open(args.input, mode="r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
        except OSError as exc:
            print(f"Could not read input CSV: {exc}", file=sys.stderr)
            return 2

        if not fieldnames:
            print("Input CSV must contain a header row.", file=sys.stderr)
            return 2

        extras = ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]
        out_fields = fieldnames + [name for name in extras if name not in fieldnames]
        out_rows = []

        for row_number, row in enumerate(rows, start=2):
            try:
                primary_val = float(
                    row.get("primary_metric", row.get("metric_primary", 15.0))
                )
                secondary_val = float(
                    row.get("secondary_metric", row.get("metric_secondary", 5.0))
                )
                status_val = row.get(
                    "status_descriptor",
                    row.get("status_flag", row.get("status_text", "NOMINAL")),
                )
                crit_val = row.get(
                    "is_critical_flag",
                    row.get("is_stat", row.get("critical_flag", False)),
                )
                if isinstance(crit_val, str):
                    normalized = crit_val.strip().lower()
                    if normalized in ("true", "1", "yes", "y", "t"):
                        crit_val = True
                    elif normalized in ("false", "0", "no", "n", "f", ""):
                        crit_val = False
                    else:
                        raise ValueError(f"invalid boolean value: {crit_val!r}")
                else:
                    crit_val = bool(crit_val)

                payload = SystemTaskPayload(
                    task_id=row.get("task_id", row.get("case_id", "TASK-01")),
                    target_identifier=row.get(
                        "target_identifier",
                        row.get("patient_synthetic_id", "TARGET-01"),
                    ),
                    primary_metric=primary_val,
                    secondary_metric=secondary_val,
                    status_descriptor=status_val,
                    is_critical_flag=crit_val,
                )
                dossier = supervisor.process_task(payload)
            except (TypeError, ValueError) as exc:
                print(f"Row {row_number}: {exc}", file=sys.stderr)
                return 2

            row_dict = dict(row)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
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
            from agents.api import app
        except ImportError:
            print(
                "Server dependencies are not installed. "
                "Run 'pip install -e .[server]'.",
                file=sys.stderr,
            )
            return 1
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
