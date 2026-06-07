"""
Sentinel — Module M7: EU AI Act Compliance Checker
Legal basis: EU AI Act 2024/1689 Articles 9-15, 43
Answers: Can we prove compliance to auditors?
         What controls are missing before deployment?
"""

from typing import List, Dict


RISK_TIERS = ["UNACCEPTABLE", "HIGH", "LIMITED", "MINIMAL"]

REQUIREMENTS = {
    "data_governance":       {"article": "Art.10", "effort": "High"},
    "transparency":          {"article": "Art.13", "effort": "Low"},
    "human_oversight":       {"article": "Art.14", "effort": "Medium"},
    "accuracy_testing":      {"article": "Art.15", "effort": "Medium"},
    "robustness_testing":    {"article": "Art.15", "effort": "High"},
    "cybersecurity":         {"article": "Art.15", "effort": "Medium"},
    "audit_logging":         {"article": "Art.12", "effort": "Low"},
    "conformity_assessment": {"article": "Art.43", "effort": "High"},
}

EFFORT_ORDER = {"Low": 0, "Medium": 1, "High": 2}


class AISystem:
    def __init__(self, system_id, name, risk_tier,
                 controls_implemented=None,
                 approved_by="",
                 training_data_source=""):
        self.system_id              = system_id
        self.name                   = name
        self.risk_tier              = risk_tier
        self.controls_implemented   = controls_implemented or []
        self.approved_by            = approved_by
        self.training_data_source   = training_data_source


class ComplianceChecker:

    def gap_report(self, system: AISystem) -> Dict:
        """Generate EU AI Act compliance gap report."""

        if system.risk_tier == "UNACCEPTABLE":
            return {
                "system":  system.name,
                "tier":    "UNACCEPTABLE",
                "status":  "BANNED",
                "action":  "Decommission immediately — EU AI Act Art.5",
                "gaps":    [],
                "roadmap": [],
            }

        if system.risk_tier in ("LIMITED", "MINIMAL"):
            return {
                "system":  system.name,
                "tier":    system.risk_tier,
                "status":  "COMPLIANT",
                "action":  (
                    "Transparency disclosure required"
                    if system.risk_tier == "LIMITED"
                    else "No mandatory requirements"
                ),
                "gaps":    [],
                "roadmap": [],
            }

        # HIGH risk — check all 8 mandatory requirements
        implemented = set(system.controls_implemented)
        all_reqs    = set(REQUIREMENTS.keys())
        gaps        = all_reqs - implemented

        roadmap = sorted(
            [
                {
                    "control": g,
                    "article": REQUIREMENTS[g]["article"],
                    "effort":  REQUIREMENTS[g]["effort"],
                    "task":    f"Implement {g.replace('_', ' ')}",
                }
                for g in gaps
            ],
            key=lambda x: EFFORT_ORDER[x["effort"]]
        )

        score = round(100 * (1 - len(gaps) / len(all_reqs)), 1)
        status = "COMPLIANT" if not gaps else "NON_COMPLIANT"

        return {
            "system":       system.name,
            "tier":         "HIGH",
            "status":       status,
            "score_pct":    score,
            "gaps_count":   len(gaps),
            "gaps":         list(gaps),
            "roadmap":      roadmap,
            "approved_by":  system.approved_by,
            "data_source":  system.training_data_source,
        }


if __name__ == "__main__":
    checker = ComplianceChecker()

    system = AISystem(
        system_id  = "loan-ai-v3",
        name       = "LoanApproval-AI",
        risk_tier  = "HIGH",
        controls_implemented = [
            "data_governance",
            "human_oversight",
            "cybersecurity",
            "audit_logging",
        ],
        approved_by           = "Dr. James Wilson",
        training_data_source  = "FDIC loan history 2005-2023",
    )

    result = checker.gap_report(system)

    print("\nSentinel EU AI Act Compliance Report")
    print("=" * 45)
    print(f"System:  {result['system']}")
    print(f"Tier:    {result['tier']}")
    print(f"Status:  {result['status']}")
    print(f"Score:   {result['score_pct']}%")
    print(f"Gaps:    {result['gaps_count']} missing controls")
    print()
    print("Remediation roadmap (ordered by effort):")
    for item in result["roadmap"]:
        print(f"  [{item['effort']:<6}] {item['task']} ({item['article']})")
    print("=" * 45)
