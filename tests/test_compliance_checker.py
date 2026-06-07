import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sentinel.compliance_checker import ComplianceChecker, AISystem


def make_system(tier="HIGH", controls=None):
    return AISystem(
        system_id="test-001",
        name="Test AI System",
        risk_tier=tier,
        controls_implemented=controls or [],
        approved_by="jane.smith@org.com",
        training_data_source="test-dataset-v1",
    )


def test_unacceptable_returns_banned():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="UNACCEPTABLE"))
    assert result["status"] == "BANNED"
    assert "Decommission" in result["action"]


def test_minimal_returns_compliant():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="MINIMAL"))
    assert result["status"] == "COMPLIANT"
    assert len(result["gaps"]) == 0


def test_limited_requires_transparency():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="LIMITED"))
    assert result["status"] == "COMPLIANT"
    assert "Transparency" in result["action"]


def test_high_no_controls_is_noncompliant():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="HIGH", controls=[]))
    assert result["status"] == "NON_COMPLIANT"
    assert result["score_pct"] == 0.0
    assert result["gaps_count"] == 8


def test_high_all_controls_is_compliant():
    checker = ComplianceChecker()
    all_controls = [
        "data_governance", "transparency", "human_oversight",
        "accuracy_testing", "robustness_testing", "cybersecurity",
        "audit_logging", "conformity_assessment",
    ]
    result = checker.gap_report(make_system(tier="HIGH", controls=all_controls))
    assert result["status"] == "COMPLIANT"
    assert result["score_pct"] == 100.0
    assert result["gaps_count"] == 0


def test_partial_compliance_score():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="HIGH", controls=[
        "data_governance", "human_oversight",
        "cybersecurity", "audit_logging",
    ]))
    assert result["score_pct"] == 50.0
    assert result["gaps_count"] == 4


def test_roadmap_ordered_by_effort():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="HIGH", controls=[]))
    efforts = [item["effort"] for item in result["roadmap"]]
    order = {"Low": 0, "Medium": 1, "High": 2}
    ordered = sorted(efforts, key=lambda e: order[e])
    assert efforts == ordered


def test_roadmap_contains_article_citations():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="HIGH", controls=[]))
    articles = [item["article"] for item in result["roadmap"]]
    assert "Art.12" in articles
    assert "Art.13" in articles
    assert "Art.14" in articles


def test_approved_by_in_result():
    checker = ComplianceChecker()
    result = checker.gap_report(make_system(tier="HIGH"))
    assert result["approved_by"] == "jane.smith@org.com"


def test_audit_logging_gap_identified():
    checker = ComplianceChecker()
    all_except_audit = [
        "data_governance", "transparency", "human_oversight",
        "accuracy_testing", "robustness_testing", "cybersecurity",
        "conformity_assessment",
    ]
    result = checker.gap_report(make_system(
        tier="HIGH", controls=all_except_audit))
    assert "audit_logging" in result["gaps"]
    assert result["score_pct"] == round(100 * 7/8, 1)
