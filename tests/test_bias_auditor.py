import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sentinel.bias_auditor import BiasAuditor, GroupStats


def make_groups(a_rate=0.78, b_rate=0.61):
    return [
        GroupStats("group_a", 5000,
                   int(5000 * a_rate), int(5000 * a_rate * 0.95),
                   int(5000 * a_rate * 0.05), int(5000 * 0.82)),
        GroupStats("group_b", 2800,
                   int(2800 * b_rate), int(2800 * b_rate * 0.92),
                   int(2800 * b_rate * 0.08), int(2800 * 0.68)),
    ]


def test_dir_violation_detected():
    auditor = BiasAuditor()
    result = auditor.audit(make_groups(a_rate=0.78, b_rate=0.61))
    assert result["dir_flag"] is True
    assert result["dir"] < 0.80
    assert result["legal_risk"] == "HIGH"


def test_dir_ok_when_rates_equal():
    auditor = BiasAuditor()
    result = auditor.audit(make_groups(a_rate=0.75, b_rate=0.72))
    assert result["dir_flag"] is False
    assert result["dir"] >= 0.80


def test_compliant_model():
    auditor = BiasAuditor()
    groups = [
        GroupStats("group_a", 1000, 750, 720, 30, 800),
        GroupStats("group_b", 1000, 740, 710, 30, 790),
    ]
    result = auditor.audit(groups)
    assert result["compliant"] is True
    assert result["legal_risk"] == "LOW"
    assert len(result["flags"]) == 0


def test_legal_risk_high_on_dir_violation():
    auditor = BiasAuditor()
    result = auditor.audit(make_groups(a_rate=0.80, b_rate=0.50))
    assert result["legal_risk"] == "HIGH"


def test_legal_risk_medium_on_eog_only():
    auditor = BiasAuditor()
    groups = [
        GroupStats("group_a", 1000, 750, 700, 50, 800),
        GroupStats("group_b", 1000, 720, 690, 30, 780),
    ]
    result = auditor.audit(groups)
    if not result["dir_flag"] and (result["eog_flag"] or result["dpg_flag"]):
        assert result["legal_risk"] == "MEDIUM"


def test_dir_formula_correct():
    auditor = BiasAuditor()
    groups = [
        GroupStats("majority", 1000, 800, 760, 40, 850),
        GroupStats("minority", 1000, 600, 570, 30, 650),
    ]
    result = auditor.audit(groups)
    expected_dir = round(0.6 / 0.8, 3)
    assert result["dir"] == expected_dir


def test_flags_contain_legal_citation():
    auditor = BiasAuditor()
    result = auditor.audit(make_groups(a_rate=0.78, b_rate=0.61))
    assert any("ECOA" in f for f in result["flags"])


def test_positive_rates_returned():
    auditor = BiasAuditor()
    result = auditor.audit(make_groups(a_rate=0.78, b_rate=0.61))
    assert "group_a" in result["positive_rates"]
    assert "group_b" in result["positive_rates"]


def test_two_groups_dir_calculation():
    auditor = BiasAuditor()
    groups = [
        GroupStats("a", 100, 90, 85, 5, 92),
        GroupStats("b", 100, 70, 65, 5, 75),
    ]
    result = auditor.audit(groups)
    assert result["dir"] == round(0.70 / 0.90, 3)
    assert result["dir_flag"] is True


def test_equal_groups_fully_compliant():
    auditor = BiasAuditor()
    groups = [
        GroupStats("a", 1000, 800, 770, 30, 850),
        GroupStats("b", 1000, 800, 770, 30, 850),
    ]
    result = auditor.audit(groups)
    assert result["dir"] == 1.0
    assert result["dir_flag"] is False
    assert result["dpg"] == 0.0
