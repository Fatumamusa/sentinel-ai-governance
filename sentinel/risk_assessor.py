"""
Sentinel — Module M1: Model Risk Assessment
Legal basis: EU AI Act Art.15, NIST AI RMF MEASURE
Answers: Is the model safe to deploy?
         Who approved it? Where did data come from?
"""

from dataclasses import dataclass, field
from typing import Dict, List
import datetime


@dataclass
class ModelRiskReport:
    # Identity
    model_id:   str
    model_name: str
    version:    str

    # Four risk dimensions — 0 (best) to 100 (worst)
    bias_score:     float
    drift_score:    float
    data_quality:   float
    fairness_score: float

    # Accountability — answers regulators top two questions
    approved_by:          str
    training_data_source: str

    # Governance completeness flags
    bias_tested:           bool = False
    explainability_method: str  = ""

    # Auto-stamped
    assessed_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


class RiskAssessor:
    WEIGHTS: Dict[str, float] = {
        "bias":     0.35,
        "drift":    0.25,
        "data":     0.20,
        "fairness": 0.20,
    }
    HIGH_RISK_THRESHOLD   = 70
    MEDIUM_RISK_THRESHOLD = 40

    def __init__(self):
        total = sum(self.WEIGHTS.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")

    def compute_score(self, r: ModelRiskReport) -> float:
        return (
            r.bias_score     * self.WEIGHTS["bias"]     +
            r.drift_score    * self.WEIGHTS["drift"]    +
            r.data_quality   * self.WEIGHTS["data"]     +
            r.fairness_score * self.WEIGHTS["fairness"]
        )

    def assess(self, r: ModelRiskReport) -> Dict:
        score = self.compute_score(r)

        if score >= self.HIGH_RISK_THRESHOLD:
            tier, action = "HIGH", "BLOCK_DEPLOYMENT"
        elif score >= self.MEDIUM_RISK_THRESHOLD:
            tier, action = "MEDIUM", "REQUIRE_HUMAN_REVIEW"
        else:
            tier, action = "LOW", "APPROVE_WITH_MONITORING"

        warnings: List[str] = []
        if not r.bias_tested:
            warnings.append("No disparate impact analysis performed (ECOA risk)")
        if not r.explainability_method:
            warnings.append("No explainability method specified (GDPR Art.22 risk)")
        if not r.approved_by:
            warnings.append("No named approver (EU AI Act Art.14 violation)")

        return {
            "model_id":      r.model_id,
            "model_name":    r.model_name,
            "version":       r.version,
            "score":         round(score, 2),
            "tier":          tier,
            "action":        action,
            "approved_by":   r.approved_by,
            "data_source":   r.training_data_source,
            "bias_tested":   r.bias_tested,
            "explainability": r.explainability_method,
            "warnings":      warnings,
            "assessed_at":   r.assessed_at,
        }


# Quick test — run this file directly to verify it works
if __name__ == "__main__":
    assessor = RiskAssessor()

    report = ModelRiskReport(
        model_id             = "loan-ai-v3",
        model_name           = "LoanApproval-AI",
        version              = "3.0.1",
        bias_score           = 72.0,
        drift_score          = 28.0,
        data_quality         = 15.0,
        fairness_score       = 55.0,
        approved_by          = "sarah.chen@bank.com",
        training_data_source = "FDIC loan history 2005-2023",
        bias_tested          = True,
        explainability_method= "SHAP TreeExplainer",
    )

    result = assessor.assess(report)
    print("\nSentinel Risk Assessment")
    print("=" * 40)
    print(f"Model:   {result['model_name']} v{result['version']}")
    print(f"Score:   {result['score']}")
    print(f"Tier:    {result['tier']}")
    print(f"Action:  {result['action']}")
    print(f"Approver:{result['approved_by']}")
    if result['warnings']:
        print("Warnings:")
        for w in result['warnings']:
            print(f"  - {w}")
    print("=" * 40)