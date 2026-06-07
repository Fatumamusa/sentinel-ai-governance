import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sentinel.orchestrator import GovernanceOrchestrator
from sentinel.bias_auditor import GroupStats


def make_clean_groups():
    return [
        GroupStats("group_a", 1000, 800, 770, 30, 850),
        GroupStats("group_b", 1000, 790, 760, 30, 840),
    ]


def make_biased_groups():
    return [
        GroupStats("group_a", 5000, 3900, 3700, 200, 4100),
        GroupStats("group_b", 2800, 1708, 1560, 148, 1900),
    ]


def run_clean_pipeline(orchestrator):
    return orchestrator.run_pipeline(
        model_id             = "fraud-detector-v2",
        model_name           = "FraudDetector",
        version              = "2.0",
        approved_by          = "sarah.chen@bank.com",
        training_data_source = "transaction-history-2023",
        bias_groups          = make_clean_groups(),
        drift_score          = 12.0,
        data_quality         = 8.0,
        explainability       = "SHAP",
        controls_implemented = [
            "data_governance", "transparency", "human_oversight",
            "accuracy_testing", "robustness_testing", "cybersecurity",
            "audit_logging", "conformity_assessment",
        ],
    )


def run_biased_pipeline(orchestrator):
    return orchestrator.run_pipeline(
        model_id             = "loan-ai-v3",
        model_name           = "LoanApproval-AI",
        version              = "3.0.1",
        approved_by          = "james.wilson@bank.com",
        training_data_source = "FDIC-2005-2023",
        bias_groups          = make_biased_groups(),
        drift_score          = 28.0,
        data_quality         = 15.0,
        explainability       = "SHAP",
        controls_implemented = [
            "data_governance", "human_oversight",
            "cybersecurity", "audit_logging",
        ],
    )


def test_clean_model_approved():
    result = run_clean_pipeline(GovernanceOrchestrator())
    assert result.verdict == "APPROVED"
    assert result.blocking_gate is None


def test_biased_model_blocked():
    result = run_biased_pipeline(GovernanceOrchestrator())
    assert result.verdict == "BLOCKED"
    assert result.blocking_gate == "bias"


def test_biased_model_blocking_reason_contains_ecoa():
    result = run_biased_pipeline(GovernanceOrchestrator())
    assert "ECOA" in result.blocking_reason


def test_biased_model_blocking_reason_contains_dir():
    result = run_biased_pipeline(GovernanceOrchestrator())
    assert "DIR=" in result.blocking_reason


def test_clean_model_audit_chain_hash_exists():
    result = run_clean_pipeline(GovernanceOrchestrator())
    assert len(result.audit_chain_hash) == 64


def test_clean_model_evidence_package_complete():
    result = run_clean_pipeline(GovernanceOrchestrator())
    assert "bias"       in result.evidence_package
    assert "risk"       in result.evidence_package
    assert "compliance" in result.evidence_package
    assert "policy"     in result.evidence_package
    assert "audit_hash" in result.evidence_package


def test_clean_model_gates_all_run():
    result = run_clean_pipeline(GovernanceOrchestrator())
    gate_names = [g["gate"] for g in result.gate_results]
    assert "bias"       in gate_names
    assert "risk"       in gate_names
    assert "compliance" in gate_names
    assert "policy"     in gate_names


def test_blocked_model_has_fewer_gates():
    result = run_biased_pipeline(GovernanceOrchestrator())
    assert len(result.gate_results) < 4


def test_audit_trail_records_entries():
    o = GovernanceOrchestrator()
    run_clean_pipeline(o)
    assert o.audit_trail.entry_count >= 4


def test_audit_trail_verifies_after_pipeline():
    o = GovernanceOrchestrator()
    run_clean_pipeline(o)
    assert o.audit_trail.verify() is True
