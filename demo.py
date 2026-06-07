import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sentinel.orchestrator import GovernanceOrchestrator
from sentinel.bias_auditor import GroupStats

orchestrator = GovernanceOrchestrator()

# Scenario 1 - clean low risk model
clean_groups = [
    GroupStats("group_a", 1000, 800, 770, 30, 850),
    GroupStats("group_b", 1000, 790, 760, 30, 840),
]

result = orchestrator.run_pipeline(
    model_id             = "fraud-detector-v2",
    model_name           = "FraudDetector",
    version              = "2.0",
    approved_by          = "sarah.chen@bank.com",
    training_data_source = "transaction-history-2023",
    bias_groups          = clean_groups,
    drift_score          = 12.0,
    data_quality         = 8.0,
    explainability       = "SHAP",
    controls_implemented = [
        "data_governance", "transparency", "human_oversight",
        "accuracy_testing", "robustness_testing", "cybersecurity",
        "audit_logging", "conformity_assessment",
    ],
)

print("\nSentinel Governance Pipeline")
print("=" * 50)
print("Scenario 1: Clean LOW-risk model")
print(f"Verdict:     {result.verdict}")
print(f"Blocked at:  {result.blocking_gate}")
print(f"Gates run:   {len(result.gate_results)}")
print(f"Audit hash:  {result.audit_chain_hash[:20]}...")

# Scenario 2 - biased model
orchestrator2 = GovernanceOrchestrator()
biased_groups = [
    GroupStats("group_a", 5000, 3900, 3700, 200, 4100),
    GroupStats("group_b", 2800, 1708, 1560, 148, 1900),
]

result2 = orchestrator2.run_pipeline(
    model_id             = "loan-ai-v3",
    model_name           = "LoanApproval-AI",
    version              = "3.0.1",
    approved_by          = "james.wilson@bank.com",
    training_data_source = "FDIC-2005-2023",
    bias_groups          = biased_groups,
    drift_score          = 28.0,
    data_quality         = 15.0,
    explainability       = "SHAP",
    controls_implemented = [
        "data_governance", "human_oversight",
        "cybersecurity", "audit_logging",
    ],
)

print()
print("Scenario 2: Biased model")
print(f"Verdict:     {result2.verdict}")
print(f"Blocked at:  {result2.blocking_gate}")
print(f"Reason:      {result2.blocking_reason}")
print("=" * 50)
