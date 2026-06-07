import datetime
from typing import List, Dict, Optional

from .risk_assessor      import RiskAssessor, ModelRiskReport
from .audit_trail        import AuditTrail
from .policy_engine      import PolicyEngine, Policy, Verdict, build_sentinel_engine
from .anomaly_detector   import AnomalyDetector
from .bias_auditor       import BiasAuditor, GroupStats
from .compliance_checker import ComplianceChecker, AISystem


class PipelineResult:
    def __init__(self, model_id, verdict, gate_results,
                 blocking_gate, blocking_reason,
                 audit_chain_hash, evidence_package):
        self.model_id         = model_id
        self.verdict          = verdict
        self.gate_results     = gate_results
        self.blocking_gate    = blocking_gate
        self.blocking_reason  = blocking_reason
        self.audit_chain_hash = audit_chain_hash
        self.evidence_package = evidence_package
        self.completed_at     = datetime.datetime.now(
            datetime.timezone.utc).isoformat()


class GovernanceOrchestrator:

    def __init__(self):
        self.risk_assessor      = RiskAssessor()
        self.audit_trail        = AuditTrail()
        self.policy_engine      = build_sentinel_engine()
        self.anomaly_detector   = AnomalyDetector()
        self.bias_auditor       = BiasAuditor()
        self.compliance_checker = ComplianceChecker()

    def run_pipeline(
        self,
        model_id,
        model_name,
        version,
        approved_by,
        training_data_source,
        bias_groups,
        drift_score,
        data_quality,
        explainability,
        controls_implemented,
        risk_tier="HIGH",
    ):
        gate_results = []

        # Gate 1: Bias audit
        bias_result = self.bias_auditor.audit(bias_groups)
        gate_results.append({"gate": "bias", "result": bias_result})
        self.audit_trail.record("BIAS_AUDIT", "orchestrator", {
            "model_id":   model_id,
            "dir":        bias_result["dir"],
            "dir_flag":   bias_result["dir_flag"],
            "legal_risk": bias_result["legal_risk"],
        })

        # Block immediately on DIR violation
        if bias_result["dir_flag"]:
            return self._blocked(
                model_id, gate_results, "bias",
                f"DIR={bias_result['dir']:.3f} violates EEOC 4/5ths rule (ECOA)"
            )

        bias_score     = 20.0
        fairness_score = 75.0 if bias_result["eog_flag"] else 15.0

        # Gate 2: Risk assessment
        risk_report = ModelRiskReport(
            model_id             = model_id,
            model_name           = model_name,
            version              = version,
            bias_score           = bias_score,
            drift_score          = drift_score,
            data_quality         = data_quality,
            fairness_score       = fairness_score,
            approved_by          = approved_by,
            training_data_source = training_data_source,
            bias_tested          = True,
            explainability_method= explainability,
        )
        risk_result = self.risk_assessor.assess(risk_report)
        gate_results.append({"gate": "risk", "result": risk_result})
        self.audit_trail.record("RISK_ASSESSMENT", "orchestrator", {
            "model_id": model_id,
            "score":    risk_result["score"],
            "tier":     risk_result["tier"],
            "action":   risk_result["action"],
        })

        if risk_result["tier"] == "HIGH":
            return self._blocked(
                model_id, gate_results, "risk",
                f"Risk score {risk_result['score']} >= 70 blocked"
            )

        # Gate 3: Compliance check
        ai_system = AISystem(
            system_id            = model_id,
            name                 = model_name,
            risk_tier            = risk_tier,
            controls_implemented = controls_implemented,
            approved_by          = approved_by,
            training_data_source = training_data_source,
        )
        compliance_result = self.compliance_checker.gap_report(ai_system)
        gate_results.append({"gate": "compliance", "result": compliance_result})
        self.audit_trail.record("COMPLIANCE_CHECK", "orchestrator", {
            "model_id":   model_id,
            "status":     compliance_result["status"],
            "score_pct":  compliance_result.get("score_pct", 100),
            "gaps_count": compliance_result.get("gaps_count", 0),
        })

        # Gate 4: Policy evaluation
        policy_action = {
            "action_type":  "deploy",
            "model_id":     model_id,
            "risk_tier":    risk_result["tier"],
            "bias_flagged": bias_result["dir_flag"],
        }
        policy_result = self.policy_engine.evaluate(policy_action)
        gate_results.append({"gate": "policy", "result": policy_result})
        self.audit_trail.record("POLICY_DECISION", "orchestrator", {
            "model_id": model_id,
            "verdict":  policy_result["verdict"],
            "policy":   policy_result["policy"],
            "reason":   policy_result["reason"],
        })

        if policy_result["verdict"] == "DENY":
            return self._blocked(
                model_id, gate_results, "policy",
                policy_result["reason"]
            )

        # Gate 5: Record approval
        self.audit_trail.record("APPROVAL", approved_by, {
            "model_id":   model_id,
            "verdict":    policy_result["verdict"],
            "risk_tier":  risk_result["tier"],
            "bias_flags": bias_result["flags"],
        })

        final_verdict = (
            "REQUIRES_REVIEW"
            if policy_result["verdict"] == "REQUIRE_APPROVAL"
            else "APPROVED"
        )

        return PipelineResult(
            model_id         = model_id,
            verdict          = final_verdict,
            gate_results     = gate_results,
            blocking_gate    = None,
            blocking_reason  = None,
            audit_chain_hash = self.audit_trail.terminal_hash,
            evidence_package = {
                "bias":       bias_result,
                "risk":       risk_result,
                "compliance": compliance_result,
                "policy":     policy_result,
                "audit_hash": self.audit_trail.terminal_hash,
            },
        )

    def _blocked(self, model_id, gates, gate, reason):
        self.audit_trail.record("PIPELINE_BLOCKED", "orchestrator", {
            "model_id": model_id,
            "gate":     gate,
            "reason":   reason,
        })
        return PipelineResult(
            model_id         = model_id,
            verdict          = "BLOCKED",
            gate_results     = gates,
            blocking_gate    = gate,
            blocking_reason  = reason,
            audit_chain_hash = self.audit_trail.terminal_hash,
            evidence_package = {"blocked_at": gate, "reason": reason},
        )
