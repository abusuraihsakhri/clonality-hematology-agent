from clono_mind import (
    BMRDMarkerFinderAgent,
    ClonoCoordinator,
    DomainKnowledgeRegistry,
    PeakRatioCalculatorAgent,
    PolyClonalityFilterAgent,
    main,
)


def test_sub_agents():
    assert len(PeakRatioCalculatorAgent().evaluate({"metric_primary": 35.0})) == 1
    assert len(PolyClonalityFilterAgent().evaluate({"critical_flag": True})) == 1
    assert len(BMRDMarkerFinderAgent().evaluate({"status_text": "DISCORDANT_FINDING"})) == 1


def test_coordinator():
    coord = ClonoCoordinator()
    dossier = coord.audit_case(
        {"case_id": "TEST-100", "metric_primary": 10.0, "metric_secondary": 2.0}
    )
    assert dossier["overall_status"] == "CONCORDANT_NORMAL"
    assert dossier["total_alerts"] == 0

    answer = coord.query_assistant("What are the guidelines?")
    assert "pattern-based" in answer.lower()


def test_cli():
    assert main(["audit", "--case-id", "CLI-01"]) == 0
    assert main(["chat", "What", "is", "the", "system", "status?"]) == 0


def test_domain_registry_does_not_claim_compliance():
    assert DomainKnowledgeRegistry.ZERO_PHI_COMPLIANCE is False
    assert DomainKnowledgeRegistry.HIPAA_SAFE_HARBOR == "NOT_CLAIMED"
