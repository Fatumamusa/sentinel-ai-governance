import streamlit as st
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(__file__))

from sentinel.policy_engine import build_sentinel_engine
from sentinel.bias_auditor import BiasAuditor, GroupStats
from sentinel.orchestrator import GovernanceOrchestrator
from sentinel.audit_trail import AuditTrail

st.set_page_config(
    page_title="Sentinel AI Governance",
    page_icon="shield",
    layout="wide",
)

st.sidebar.title("Sentinel")
st.sidebar.caption("AI Governance Security Engineering")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [
        "Policy Engine Tester",
        "Bias Audit Visualizer",
        "Full Pipeline Runner",
        "Audit Trail Viewer",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("73 tests | 8 modules | Zero failures")
st.sidebar.caption("EU AI Act | NIST AI RMF | ECOA")

# ── PAGE 1: POLICY ENGINE TESTER ──────────────────────────────
if page == "Policy Engine Tester":
    st.title("Policy Engine Tester")
    st.caption("EU AI Act Art.14 — Human Oversight | CCPA §1798.100")

    engine = build_sentinel_engine()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Registered Policies")
        policies = engine.list_policies()
        df = pd.DataFrame(policies)

        def color_verdict(val):
            if val == "ALLOW":            return "background-color: #d4edda"
            elif val == "DENY":           return "background-color: #f8d7da"
            elif val == "REQUIRE_APPROVAL": return "background-color: #fff3cd"
            return ""

        st.dataframe(
            df,
            use_container_width=True,
        )

    with col2:
        st.subheader("Test an Action")

        action_type = st.selectbox(
            "Action type",
            ["infer", "deploy", "export", "wire", "delete"],
        )
        risk_tier = st.selectbox("Risk tier", ["LOW", "MEDIUM", "HIGH"])
        amount    = st.number_input("Amount ($)", min_value=0, value=500, step=500)
        prompt    = st.text_input("Prompt snippet (optional)", value="")

        action = {
            "action_type": action_type,
            "risk_tier":   risk_tier,
            "amount":      amount,
        }
        if prompt:
            action["prompt"] = prompt

        if st.button("Evaluate Action", type="primary"):
            result = engine.evaluate(action)
            verdict = result["verdict"]

            if verdict == "ALLOW":
                st.success(f"Verdict: {verdict}")
            elif verdict == "DENY":
                st.error(f"Verdict: {verdict}")
            else:
                st.warning(f"Verdict: {verdict}")

            st.json({
                "verdict": result["verdict"],
                "policy":  result["policy"],
                "reason":  result["reason"],
                "matched": result["matched"],
            })

    st.markdown("---")
    st.subheader("Batch Test — All Scenarios")

    test_actions = [
        {"label": "Low-risk inference",     "action_type": "infer",  "risk_tier": "LOW",    "amount": 500},
        {"label": "High-risk deployment",   "action_type": "deploy", "risk_tier": "HIGH",   "amount": 0},
        {"label": "Medium-risk deployment", "action_type": "deploy", "risk_tier": "MEDIUM", "amount": 0},
        {"label": "High-value transaction", "action_type": "wire",   "risk_tier": "LOW",    "amount": 50000},
        {"label": "SSN in prompt",          "action_type": "infer",  "risk_tier": "LOW",    "amount": 0, "prompt": "my ssn is 123-45-6789"},
        {"label": "Unknown export",         "action_type": "export", "risk_tier": "LOW",    "amount": 0},
        {"label": "Low-risk deployment",    "action_type": "deploy", "risk_tier": "LOW",    "amount": 0},
    ]

    rows = []
    for t in test_actions:
        a = {k: v for k, v in t.items() if k != "label"}
        r = engine.evaluate(a)
        rows.append({
            "Scenario": t["label"],
            "Verdict":  r["verdict"],
            "Policy":   r["policy"],
            "Reason":   r["reason"][:60],
        })

    df_batch = pd.DataFrame(rows)
    st.dataframe(
        df_batch,
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Verdict Distribution")
    verdict_counts = df_batch["Verdict"].value_counts()
    colors = {"ALLOW": "#28a745", "DENY": "#dc3545", "REQUIRE_APPROVAL": "#ffc107"}
    bar_colors = [colors.get(v, "#6c757d") for v in verdict_counts.index]

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.bar(verdict_counts.index, verdict_counts.values,
                  color=bar_colors, edgecolor="white", linewidth=1.5)
    ax.set_title("Policy Engine — Verdict Distribution", fontweight="bold")
    ax.set_ylabel("Actions")
    for bar, count in zip(bars, verdict_counts.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                str(count), ha="center", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)


# ── PAGE 2: BIAS AUDIT VISUALIZER ─────────────────────────────
elif page == "Bias Audit Visualizer":
    st.title("Bias Audit Visualizer")
    st.caption("ECOA | Fair Housing Act | Title VII | EU AI Act Art.10")
    st.caption("EEOC 4/5ths rule: DIR < 0.80 = prima facie illegal discrimination")

    auditor = BiasAuditor()

    industry = st.selectbox(
        "Select industry",
        ["Loan Approval AI", "Hiring Screening AI", "Medical Triage AI"],
    )

    if industry == "Loan Approval AI":
        groups = [
            GroupStats("White",           5000, 3900, 3700, 200, 4100),
            GroupStats("Black",           2800, 1708, 1560, 148, 1900),
            GroupStats("Hispanic",        2200, 1276, 1150, 126, 1500),
            GroupStats("Asian",           1800, 1476, 1400,  76, 1600),
            GroupStats("Native American",  400,  196,  180,  16,  220),
        ]
    elif industry == "Hiring Screening AI":
        groups = [
            GroupStats("Male_Under40",   3000, 1980, 1900, 80, 2200),
            GroupStats("Male_Over40",    2000, 1160, 1100, 60, 1400),
            GroupStats("Female_Under40", 2800, 1624, 1550, 74, 1900),
            GroupStats("Female_Over40",  1800,  864,  810, 54, 1100),
        ]
    else:
        groups = [
            GroupStats("Private_Insurance", 4000, 3360, 3200, 160, 3600),
            GroupStats("Medicare",          3000, 2310, 2200, 110, 2700),
            GroupStats("Medicaid",          2500, 1750, 1650, 100, 2000),
            GroupStats("Uninsured",         1500,  855,  800,  55, 1050),
        ]

    result = auditor.audit(groups)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("DIR", f"{result['dir']:.3f}",
                delta="VIOLATION" if result["dir_flag"] else "OK",
                delta_color="inverse" if result["dir_flag"] else "normal")
    col2.metric("EOG", f"{result['eog']:.3f}",
                delta="VIOLATION" if result["eog_flag"] else "OK",
                delta_color="inverse" if result["eog_flag"] else "normal")
    col3.metric("DPG", f"{result['dpg']:.3f}",
                delta="VIOLATION" if result["dpg_flag"] else "OK",
                delta_color="inverse" if result["dpg_flag"] else "normal")
    col4.metric("Legal Risk", result["legal_risk"])

    if result["flags"]:
        for flag in result["flags"]:
            st.error(f"FLAG: {flag}")
    else:
        st.success("All fairness thresholds passed. Model is compliant.")

    st.markdown("---")

    group_names = list(result["positive_rates"].keys())
    rates       = list(result["positive_rates"].values())
    max_rate    = max(rates)
    threshold   = 0.80 * max_rate
    bar_colors  = ["#28a745" if r >= threshold else "#dc3545" for r in rates]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle(f"Bias Metrics — {industry}", fontsize=13, fontweight="bold")

    axes[0].barh(group_names, rates, color=bar_colors, edgecolor="white")
    axes[0].axvline(x=threshold, color="red", linestyle="--",
                    linewidth=2, label=f"4/5ths threshold ({threshold:.2f})")
    axes[0].set_title("Positive Outcome Rates", fontweight="bold")
    axes[0].set_xlabel("Rate")
    axes[0].legend(fontsize=7)
    for i, v in enumerate(rates):
        axes[0].text(v + 0.002, i, f"{v:.1%}", va="center", fontsize=8)

    fpr_names  = list(result["false_pos_rates"].keys())
    fpr_values = list(result["false_pos_rates"].values())
    fpr_colors = ["#28a745" if v <= 0.10 else "#dc3545" for v in fpr_values]
    axes[1].bar(fpr_names, fpr_values, color=fpr_colors, edgecolor="white")
    axes[1].axhline(y=0.05, color="red", linestyle="--", linewidth=2, label="EOG threshold")
    axes[1].set_title("False Positive Rates\n(EOG)", fontweight="bold")
    axes[1].set_ylabel("FPR")
    axes[1].legend(fontsize=7)
    plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=20, ha="right", fontsize=7)

    summary_labels = ["DIR", "EOG", "DPG"]
    summary_values = [result["dir"], result["eog"], result["dpg"]]
    thresholds     = [0.80, 0.05, 0.05]
    s_colors = []
    for i, (v, t) in enumerate(zip(summary_values, thresholds)):
        if i == 0:
            s_colors.append("#dc3545" if v < t else "#28a745")
        else:
            s_colors.append("#dc3545" if v > t else "#28a745")

    axes[2].bar(summary_labels, summary_values, color=s_colors, edgecolor="white")
    axes[2].set_title("All Three Metrics\nSummary", fontweight="bold")
    axes[2].set_ylabel("Value")
    for i, v in enumerate(summary_values):
        axes[2].text(i, v + 0.005, f"{v:.3f}", ha="center", fontweight="bold", fontsize=9)

    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)


# ── PAGE 3: FULL PIPELINE RUNNER ──────────────────────────────
elif page == "Full Pipeline Runner":
    st.title("Full Pipeline Runner")
    st.caption("All 8 governance gates — one pipeline")

    scenario = st.selectbox(
        "Select scenario",
        [
            "Fraud Detector — Clean LOW risk",
            "Loan AI — Biased (BLOCKED)",
            "Hiring AI — Medium risk (REQUIRES REVIEW)",
        ],
    )

    if st.button("Run Governance Pipeline", type="primary"):
        orchestrator = GovernanceOrchestrator()

        with st.spinner("Running governance pipeline..."):
            if scenario == "Fraud Detector — Clean LOW risk":
                groups = [
                    GroupStats("group_a", 1000, 800, 770, 30, 850),
                    GroupStats("group_b", 1000, 790, 760, 30, 840),
                ]
                result = orchestrator.run_pipeline(
                    model_id="fraud-v2", model_name="FraudDetector",
                    version="2.0", approved_by="sarah.chen@bank.com",
                    training_data_source="transaction-2023",
                    bias_groups=groups, drift_score=12.0,
                    data_quality=8.0, explainability="SHAP",
                    controls_implemented=[
                        "data_governance","transparency","human_oversight",
                        "accuracy_testing","robustness_testing","cybersecurity",
                        "audit_logging","conformity_assessment"
                    ],
                )

            elif scenario == "Loan AI — Biased (BLOCKED)":
                groups = [
                    GroupStats("White",    5000, 3900, 3700, 200, 4100),
                    GroupStats("Black",    2800, 1708, 1560, 148, 1900),
                    GroupStats("Hispanic", 2200, 1276, 1150, 126, 1500),
                ]
                result = orchestrator.run_pipeline(
                    model_id="loan-v3", model_name="LoanApproval-AI",
                    version="3.0.1", approved_by="james.wilson@bank.com",
                    training_data_source="FDIC-2023",
                    bias_groups=groups, drift_score=28.0,
                    data_quality=15.0, explainability="SHAP",
                    controls_implemented=[
                        "data_governance","human_oversight",
                        "cybersecurity","audit_logging"
                    ],
                )

            else:
                groups = [
                    GroupStats("Male_Under40",  3000, 1980, 1900, 80, 2200),
                    GroupStats("Female_Over40", 1800,  864,  810, 54, 1100),
                ]
                result = orchestrator.run_pipeline(
                    model_id="hiring-v1", model_name="HiringScreener",
                    version="1.0", approved_by="hr.review@company.com",
                    training_data_source="historical-hiring-2023",
                    bias_groups=groups, drift_score=22.0,
                    data_quality=18.0, explainability="LIME",
                    controls_implemented=[
                        "data_governance","transparency","human_oversight",
                        "accuracy_testing","audit_logging"
                    ],
                )

        if result.verdict == "APPROVED":
            st.success(f"VERDICT: {result.verdict}")
        elif result.verdict == "BLOCKED":
            st.error(f"VERDICT: {result.verdict}")
            st.error(f"Blocked at gate: {result.blocking_gate}")
            st.error(f"Reason: {result.blocking_reason}")
        else:
            st.warning(f"VERDICT: {result.verdict}")

        st.markdown("---")
        st.subheader("Gate-by-Gate Results")

        for g in result.gate_results:
            gate_name = g["gate"].upper()
            res = g["result"]

            with st.expander(f"Gate: {gate_name}", expanded=True):
                if gate_name == "BIAS":
                    col1, col2, col3 = st.columns(3)
                    col1.metric("DIR", f"{res['dir']:.3f}",
                                delta="VIOLATION" if res["dir_flag"] else "OK",
                                delta_color="inverse" if res["dir_flag"] else "normal")
                    col2.metric("EOG", f"{res['eog']:.3f}")
                    col3.metric("Legal Risk", res["legal_risk"])
                elif gate_name == "RISK":
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Score", res["score"])
                    col2.metric("Tier", res["tier"])
                    col3.metric("Action", res["action"])
                elif gate_name == "COMPLIANCE":
                    col1, col2 = st.columns(2)
                    col1.metric("Status", res["status"])
                    col2.metric("Score", f"{res.get('score_pct', 100)}%")
                    if res.get("gaps_count", 0) > 0:
                        st.warning(f"{res['gaps_count']} controls missing")
                elif gate_name == "POLICY":
                    col1, col2 = st.columns(2)
                    col1.metric("Verdict", res["verdict"])
                    col2.metric("Policy", res["policy"])
                    st.caption(res["reason"])

        st.markdown("---")
        st.subheader("Audit Chain")
        st.code(f"Terminal hash: {result.audit_chain_hash}")
        st.caption(f"Completed: {result.completed_at}")
        st.caption(f"Chain verified: {orchestrator.audit_trail.verify()}")


# ── PAGE 4: AUDIT TRAIL VIEWER ────────────────────────────────
elif page == "Audit Trail Viewer":
    st.title("Audit Trail Viewer")
    st.caption("EU AI Act Art.12 — Tamper-evident logging | GDPR Art.25 — PII scrubbing")

    if "trail" not in st.session_state:
        st.session_state.trail = AuditTrail()
        st.session_state.trail.record("APPROVAL", "sarah.chen@bank.com", {
            "model_id": "fraud-v2", "action": "approved_for_production",
            "applicant_email": "test@email.com",
        })
        st.session_state.trail.record("DECISION", "fraud-v2", {
            "app_id": "APP-001", "decision": "DENY",
            "confidence": 0.91, "top_feature": "velocity",
            "applicant_ssn": "123-45-6789",
        })
        st.session_state.trail.record("DRIFT_ALERT", "monitor-svc", {
            "model_id": "fraud-v2", "psi": 0.21, "threshold": 0.15,
        })

    trail = st.session_state.trail

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Entries", trail.entry_count)
    col2.metric("Chain Verified", str(trail.verify()))
    col3.metric("Genesis Hash", trail.GENESIS[:8] + "...")

    st.markdown("---")

    st.subheader("Add a New Entry")
    col1, col2 = st.columns(2)
    event_type = col1.selectbox("Event type",
        ["DECISION", "APPROVAL", "OVERRIDE", "DRIFT_ALERT"])
    actor = col2.text_input("Actor", value="governance-system")
    payload_text = st.text_input("Payload (key=value pairs)",
        value="model_id=fraud-v2, result=ALLOW, confidence=0.87")

    if st.button("Record Entry"):
        payload = {}
        for pair in payload_text.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                payload[k.strip()] = v.strip()
        trail.record(event_type, actor.strip(), payload)
        st.success(f"Entry recorded. Chain has {trail.entry_count} entries.")
        st.rerun()

    st.markdown("---")
    st.subheader("Audit Chain Entries")

    for i, entry in enumerate(trail._log):
        with st.expander(f"Entry {i+1} — {entry.event_type} by {entry.actor}"):
            col1, col2 = st.columns(2)
            col1.code(f"prev_hash:  {entry.prev_hash[:32]}...")
            col2.code(f"entry_hash: {entry.entry_hash[:32]}...")
            st.json(entry.payload)
            st.caption(f"Timestamp: {entry.timestamp}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    if col1.button("Verify Chain Integrity"):
        verified = trail.verify()
        if verified:
            st.success("Chain VERIFIED — all entries intact. Legally defensible.")
        else:
            st.error("Chain FAILED — tampering detected. Evidence compromised.")

    if col2.button("Simulate Tamper Attack"):
        if trail.entry_count > 0:
            trail._log[0].payload["tampered"] = "INJECTED BY ATTACKER"
            st.warning("Entry 1 payload modified. Run Verify to detect it.")
            st.rerun()
