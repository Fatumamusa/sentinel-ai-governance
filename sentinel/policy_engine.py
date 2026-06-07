"""
Sentinel — Module M3: Policy Enforcement Engine
Legal basis: EU AI Act Art.14 (human oversight)
             CCPA §1798.100 (PII action blocking)
Answers: Who approved this AI system?
         Can the model be manipulated at runtime?
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Optional
from enum import Enum


class Verdict(Enum):
    ALLOW            = "ALLOW"
    DENY             = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


@dataclass
class Policy:
    name:      str
    condition: Callable[[Dict], bool]
    verdict:   Verdict
    reason:    str
    priority:  int = 0


class PolicyEngine:
    """
    Single choke point for all AI actions.
    Default-deny: unmatched actions are blocked.
    """

    def __init__(self, default_deny: bool = True):
        self._policies: List[Policy] = []
        self._default_deny = default_deny

    def register(self, policy: Policy) -> None:
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority)

    def evaluate(self, action: Dict[str, Any]) -> Dict:
        for policy in self._policies:
            try:
                fired = policy.condition(action)
            except Exception:
                fired = False
            if fired:
                return {
                    "verdict": policy.verdict.value,
                    "policy":  policy.name,
                    "reason":  policy.reason,
                    "action":  action,
                    "matched": True,
                }
        return {
            "verdict": "DENY" if self._default_deny else "ALLOW",
            "policy":  "default",
            "reason":  (
                "No matching policy — default-deny active"
                if self._default_deny
                else "No matching policy — default-allow active"
            ),
            "action":  action,
            "matched": False,
        }

    def list_policies(self) -> List[Dict]:
        return [
            {
                "priority": p.priority,
                "name":     p.name,
                "verdict":  p.verdict.value,
                "reason":   p.reason,
            }
            for p in self._policies
        ]

    @property
    def policy_count(self) -> int:
        return len(self._policies)


def build_sentinel_engine() -> PolicyEngine:
    """Default Sentinel policy set for loan AI governance."""
    engine = PolicyEngine(default_deny=True)

    engine.register(Policy(
        name      = "block-pii-in-prompt",
        priority  = 0,
        condition = lambda a: "ssn" in a.get("prompt", "").lower(),
        verdict   = Verdict.DENY,
        reason    = "SSN detected in prompt (CCPA §1798.100)",
    ))

    engine.register(Policy(
        name      = "block-high-risk-deployment",
        priority  = 0,
        condition = lambda a: (
            a.get("action_type") == "deploy"
            and a.get("risk_tier") == "HIGH"
        ),
        verdict   = Verdict.DENY,
        reason    = "HIGH-risk model blocked (EU AI Act Art.9)",
    ))

    engine.register(Policy(
        name      = "high-value-require-approval",
        priority  = 1,
        condition = lambda a: a.get("amount", 0) > 10_000,
        verdict   = Verdict.REQUIRE_APPROVAL,
        reason    = "Amount >$10k — human oversight required (EU AI Act Art.14)",
    ))

    engine.register(Policy(
        name      = "medium-risk-deployment-review",
        priority  = 1,
        condition = lambda a: (
            a.get("action_type") == "deploy"
            and a.get("risk_tier") == "MEDIUM"
        ),
        verdict   = Verdict.REQUIRE_APPROVAL,
        reason    = "MEDIUM-risk model — named reviewer required",
    ))

    engine.register(Policy(
        name      = "allow-standard-inference",
        priority  = 10,
        condition = lambda a: (
            a.get("action_type") == "infer"
            and a.get("risk_tier") == "LOW"
        ),
        verdict   = Verdict.ALLOW,
        reason    = "Standard low-risk inference — approved",
    ))

    return engine


if __name__ == "__main__":
    engine = build_sentinel_engine()

    test_actions = [
        {"action_type": "infer",  "risk_tier": "LOW",  "amount": 500},
        {"action_type": "deploy", "risk_tier": "HIGH", "amount": 0},
        {"action_type": "deploy", "risk_tier": "MEDIUM"},
        {"amount": 50_000, "action_type": "wire"},
        {"prompt": "my ssn is 123-45-6789"},
        {"action_type": "export", "model_id": "m1"},
    ]

    print("\nSentinel Policy Engine")
    print("=" * 50)
    print(f"Policies registered: {engine.policy_count}")
    print()

    for action in test_actions:
        result = engine.evaluate(action)
        verdict = result["verdict"]
        symbol  = "OK" if verdict == "ALLOW" else "!!" if verdict == "REQUIRE_APPROVAL" else "XX"
        print(f"  [{symbol}] {verdict:<20} {result['policy']}")
        print(f"       action: {action}")
        print(f"       reason: {result['reason']}")
        print()
    print("=" * 50)