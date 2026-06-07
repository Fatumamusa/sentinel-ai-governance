# Sentinel — AI Governance Security Engineering System

Production-grade AI governance pipeline built in Python. Implements NIST AI RMF,
EU AI Act Articles 9-15, ECOA, Fair Housing Act, and GDPR Art.22/25 as executable code.

## What Sentinel does

Every AI model must pass 8 sequential governance gates before deployment:

1. **Bias Audit** — Disparate Impact Ratio, Equalized Odds Gap, Demographic Parity Gap
2. **Risk Assessment** — Weighted composite score across bias, drift, data quality, fairness
3. **Compliance Check** — EU AI Act gap report with remediation roadmap
4. **Policy Evaluation** — Default-deny runtime gate (ALLOW / REQUIRE_APPROVAL / DENY)
5. **Audit Trail** — SHA-256 hash-chained tamper-evident logging with PII scrubbing
6. **Model Card** — EU AI Act Art.13 transparency documentation
7. **Anomaly Detection** — Three-layer runtime protection against prompt injection and abuse
8. **Orchestrator** — Wires all modules into one deployment pipeline

## Legal basis

| Module | Legal basis |
|---|---|
| Risk Assessor | EU AI Act Art.15, NIST AI RMF MEASURE |
| Audit Trail | EU AI Act Art.12, GDPR Art.25 |
| Policy Engine | EU AI Act Art.14 (human oversight) |
| Anomaly Detector | EU AI Act Art.15 (robustness + cybersecurity) |
| Bias Auditor | ECOA, Fair Housing Act, Title VII, EU AI Act Art.10 |
| Model Card | EU AI Act Art.13, GDPR Art.22 |
| Compliance Checker | EU AI Act Art.9-15, Art.43 |
| Orchestrator | NIST AI RMF MANAGE, EU AI Act Art.9 |

## Quick start

```bash
git clone https://github.com/Fatumamusa/sentinel-ai-governance.git
cd sentinel-ai-governance
pip install pydantic pandas scikit-learn shap fairlearn evidently pytest fastapi uvicorn
python demo.py
```

## Run the governance pipeline

```python
from sentinel.orchestrator import GovernanceOrchestrator
from sentinel.bias_auditor import GroupStats

orchestrator = GovernanceOrchestrator()

result = orchestrator.run_pipeline(
    model_id             = "loan-ai-v3",
    model_name           = "LoanApproval-AI",
    version              = "3.0.1",
    approved_by          = "sarah.chen@bank.com",
    training_data_source = "FDIC-loan-history-2023",
    bias_groups          = [...],
    drift_score          = 12.0,
    data_quality         = 8.0,
    explainability       = "SHAP",
    controls_implemented = ["data_governance", "human_oversight", ...],
)

print(result.verdict)         # APPROVED / BLOCKED / REQUIRES_REVIEW
print(result.blocking_reason) # Why it was blocked
print(result.audit_chain_hash) # SHA-256 evidence fingerprint
```

## Test suite

```bash
python -m pytest tests/ -v
```

73 tests. Zero failures. Eight modules.

## Governance questions Sentinel answers

- Is the AI making accurate decisions? (M1 Risk Assessor)
- Can we prove compliance to auditors? (M2 Audit Trail)
- Who approved this AI system? (M3 Policy Engine)
- Can attackers manipulate the model? (M4 Anomaly Detector)
- Is the AI biased against certain groups? (M5 Bias Auditor)
- Can we explain AI decisions? (M6 Model Card)
- What EU AI Act controls are missing? (M7 Compliance Checker)
- Is it safe to deploy end-to-end? (M8 Orchestrator)

## Stack

Python 3.11+ | pydantic | pandas | scikit-learn | shap | fairlearn | fastapi | pytest

## Author

Built as part of an AI Governance Security Engineering curriculum covering
NIST AI RMF, EU AI Act, ISO 42001, and production governance engineering.
