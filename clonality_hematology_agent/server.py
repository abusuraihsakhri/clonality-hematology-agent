"""Optional FastAPI application for the research utility."""

from typing import Any, Dict

from .agents import ClonoCoordinator
from .models import ClinicalCasePayload

coordinator = ClonoCoordinator()


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    app = FastAPI(
        title="Clonality Hematology Rule Review API",
        description=(
            "Research/demo API for deterministic rule checks. "
            "Not a validated diagnostic interpretation service."
        ),
        version="2.1.0",
    )

    class AuditRequest(BaseModel):
        case_id: str = "CASE-2026-001"
        patient_synthetic_id: str = "SYNTHETIC"
        primary_metric: float = 15.0
        secondary_metric: float = 5.0
        status_flag: str = "NORMAL"
        is_stat: bool = False
        clinical_notes: str = ""
        biomarkers: Dict[str, Any] = Field(default_factory=dict)

    class ChatRequest(BaseModel):
        query: str

    @app.get("/health")
    def health():
        return {
            "status": "HEALTHY",
            "system": "clonality-hematology-agent",
            "domain": "Hematopathology research utility",
            "version": "2.1.0",
        }

    @app.post("/api/audit")
    def api_audit(req: AuditRequest):
        payload = ClinicalCasePayload(
            case_id=req.case_id,
            patient_synthetic_id=req.patient_synthetic_id,
            primary_metric=req.primary_metric,
            secondary_metric=req.secondary_metric,
            status_flag=req.status_flag,
            is_stat=req.is_stat,
            clinical_notes=req.clinical_notes,
            biomarkers=req.biomarkers,
        )
        return coordinator.process_case(payload)

    @app.post("/api/chat")
    def api_chat(req: ChatRequest):
        return {"response": coordinator.query_supervisory_chat(req.query)}

    return app
