"""Sentinel — Tests for Module M3: Policy Engine"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sentinel.policy_engine import (
    PolicyEngine, Policy, Verdict, build_sentinel_engine
)


def test_allow_low_risk_inference():
    engine = build_sentinel_engine()
    result = engine.evaluate({
        "action_type": "infer",
        "risk_tier": "LOW",
        "amount": 500,
    })
    assert result["verdict"] == "ALLOW"
    assert result["matched"] is True


def test_deny_high_risk_deployment():
    engine = build_sentinel_engine()
    result = engine.evaluate({
        "action_type": "deploy",
        "risk_tier": "HIGH",
    })
    assert result["verdict"] == "DENY"
    assert result["policy"] == "block-high-risk-deployment"


def test_require_approval_medium_risk():
    engine = build_sentinel_engine()
    result = engine.evaluate({
        "action_type": "deploy",
        "risk_tier": "MEDIUM",
    })
    assert result["verdict"] == "REQUIRE_APPROVAL"


def test_deny_pii_in_prompt():
    engine = build_sentinel_engine()
    result = engine.evaluate({"prompt": "my ssn is 123-45-6789"})
    assert result["verdict"] == "DENY"
    assert result["policy"] == "block-pii-in-prompt"


def test_require_approval_high_value():
    engine = build_sentinel_engine()
    result = engine.evaluate({"amount": 50_000, "action_type": "wire"})
    assert result["verdict"] == "REQUIRE_APPROVAL"
    assert result["policy"] == "high-value-require-approval"


def test_default_deny_unknown_action():
    engine = build_sentinel_engine()
    result = engine.evaluate({"action_type": "export", "model_id": "m1"})
    assert result["verdict"] == "DENY"
    assert result["policy"] == "default"
    assert result["matched"] is False


def test_default_allow_mode():
    engine = PolicyEngine(default_deny=False)
    result = engine.evaluate({"action_type": "unknown"})
    assert result["verdict"] == "ALLOW"


def test_broken_condition_does_not_crash():
    engine = PolicyEngine(default_deny=True)
    engine.register(Policy(
        name      = "broken-policy",
        priority  = 0,
        condition = lambda a: a["missing_key"],
        verdict   = Verdict.ALLOW,
        reason    = "This condition always raises KeyError",
    ))
    result = engine.evaluate({"action_type": "infer"})
    assert result["verdict"] == "DENY"


def test_priority_order_lower_fires_first():
    engine = PolicyEngine(default_deny=False)
    engine.register(Policy(
        name="low-priority", priority=10,
        condition=lambda a: True,
        verdict=Verdict.ALLOW, reason="low",
    ))
    engine.register(Policy(
        name="high-priority", priority=0,
        condition=lambda a: True,
        verdict=Verdict.DENY, reason="high",
    ))
    result = engine.evaluate({"action_type": "anything"})
    assert result["verdict"] == "DENY"
    assert result["policy"] == "high-priority"


def test_policy_count():
    engine = build_sentinel_engine()
    assert engine.policy_count == 5