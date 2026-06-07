"""Sentinel — Tests for Module M1: Risk Assessor"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sentinel.risk_assessor import RiskAssessor, ModelRiskReport


def make_report(**kwargs):
    defaults = dict(
        model_id="test-model",
        model_name="Test Model",
        version="1.0",
        bias_score=20.0,
        drift_score=20.0,
        data_quality=20.0,
        fairness_score=20.0,
        approved_by="tester@sentinel.ai",
        training_data_source="test-data",
        bias_tested=True,
        explainability_method="SHAP",
    )
    defaults.update(kwargs)
    return ModelRiskReport(**defaults)


def test_low_tier():
    assessor = RiskAssessor()
    result = assessor.assess(make_report())
    assert result["tier"] == "LOW"
    assert result["action"] == "APPROVE_WITH_MONITORING"


def test_medium_tier():
    assessor = RiskAssessor()
    result = assessor.assess(make_report(bias_score=60, drift_score=50))
    assert result["tier"] == "MEDIUM"
    assert result["action"] == "REQUIRE_HUMAN_REVIEW"


def test_high_tier_blocks_deployment():
    assessor = RiskAssessor()
    result = assessor.assess(make_report(
        bias_score=90,
        drift_score=90,
        data_quality=90,
        fairness_score=90,
    ))
    assert result["tier"] == "HIGH"
    assert result["action"] == "BLOCK_DEPLOYMENT"


def test_bias_not_tested_generates_warning():
    assessor = RiskAssessor()
    result = assessor.assess(make_report(bias_tested=False))
    assert any("ECOA" in w for w in result["warnings"])


def test_weights_sum_to_one():
    assessor = RiskAssessor()
    total = sum(assessor.WEIGHTS.values())
    assert abs(total - 1.0) < 0.001


def test_score_matches_manual_calculation():
    assessor = RiskAssessor()
    report = make_report(
        bias_score=72.0,
        drift_score=28.0,
        data_quality=15.0,
        fairness_score=55.0,
    )
    result = assessor.assess(report)
    assert result["score"] == 46.2