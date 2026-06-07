"""
Sentinel — Module M5: Bias Auditor
Legal basis: ECOA, Fair Housing Act, Title VII, EU AI Act Art.10
Answers: Is the AI biased against certain groups?
         Is there disparate impact on protected classes?
"""

from typing import List, Dict


class GroupStats:
    """Prediction outcomes for one demographic group."""

    def __init__(self, group_name, total, positive_pred,
                 true_positive, false_positive, actual_positive):
        self.group_name      = group_name
        self.total           = total
        self.positive_pred   = positive_pred
        self.true_positive   = true_positive
        self.false_positive  = false_positive
        self.actual_positive = actual_positive

    @property
    def positive_rate(self):
        """Fraction of group receiving positive outcome."""
        return self.positive_pred / self.total if self.total > 0 else 0.0

    @property
    def tpr(self):
        """True Positive Rate — of those who deserved positive, how many got it."""
        return (self.true_positive / self.actual_positive
                if self.actual_positive > 0 else 0.0)

    @property
    def fpr(self):
        """False Positive Rate — of those who did not deserve positive, how many got it."""
        actual_neg = self.total - self.actual_positive
        return (self.false_positive / actual_neg
                if actual_neg > 0 else 0.0)


class BiasAuditor:
    # EEOC 4/5ths rule — primary litigation threshold
    DIR_THRESHOLD = 0.80
    # Equalized odds — max acceptable FPR gap
    EOG_THRESHOLD = 0.05
    # Demographic parity — max acceptable outcome rate gap
    DPG_THRESHOLD = 0.05

    def audit(self, groups: List[GroupStats]) -> Dict:
        """
        Compute three fairness metrics across all groups.
        Returns structured audit result for model card and policy engine.
        """
        rates = {g.group_name: g.positive_rate for g in groups}
        fprs  = {g.group_name: g.fpr           for g in groups}
        tprs  = {g.group_name: g.tpr           for g in groups}

        max_rate = max(rates.values())
        min_rate = min(rates.values())

        # Metric 1 — Disparate Impact Ratio (primary litigation metric)
        dir_val  = min_rate / max_rate if max_rate > 0 else 1.0
        dir_flag = dir_val < self.DIR_THRESHOLD

        # Metric 2 — Equalized Odds Gap (FPR disparity)
        eog      = max(fprs.values()) - min(fprs.values())
        eog_flag = eog > self.EOG_THRESHOLD

        # Metric 3 — Demographic Parity Gap
        dpg      = max_rate - min_rate
        dpg_flag = dpg > self.DPG_THRESHOLD

        flags: List[str] = []
        if dir_flag:
            flags.append(
                f"DIR={dir_val:.3f} < {self.DIR_THRESHOLD} "
                f"— 4/5ths rule violated (ECOA / Fair Housing Act)"
            )
        if eog_flag:
            flags.append(
                f"EOG={eog:.3f} > {self.EOG_THRESHOLD} "
                f"— equalized odds violated"
            )
        if dpg_flag:
            flags.append(
                f"DPG={dpg:.3f} > {self.DPG_THRESHOLD} "
                f"— demographic parity violated"
            )

        legal_risk = (
            "HIGH"   if dir_flag else
            "MEDIUM" if (eog_flag or dpg_flag) else
            "LOW"
        )

        return {
            "positive_rates": {k: round(v, 3) for k, v in rates.items()},
            "false_pos_rates": {k: round(v, 3) for k, v in fprs.items()},
            "true_pos_rates":  {k: round(v, 3) for k, v in tprs.items()},
            "dir":       round(dir_val, 3),
            "dir_flag":  dir_flag,
            "eog":       round(eog, 3),
            "eog_flag":  eog_flag,
            "dpg":       round(dpg, 3),
            "dpg_flag":  dpg_flag,
            "flags":     flags,
            "compliant": len(flags) == 0,
            "legal_risk": legal_risk,
        }


if __name__ == "__main__":
    auditor = BiasAuditor()

    groups = [
        GroupStats(
            group_name="group_a_majority",
            total=5000, positive_pred=3900,
            true_positive=3700, false_positive=200,
            actual_positive=4100,
        ),
        GroupStats(
            group_name="group_b_minority",
            total=2800, positive_pred=1708,
            true_positive=1560, false_positive=148,
            actual_positive=1900,
        ),
    ]

    result = auditor.audit(groups)

    print("\nSentinel Bias Audit — Loan AI v3")
    print("=" * 45)
    print(f"Positive rates: {result['positive_rates']}")
    print(f"FPR rates:      {result['false_pos_rates']}")
    print()
    print(f"DIR:  {result['dir']} {'VIOLATION' if result['dir_flag'] else 'OK'} (threshold >= {BiasAuditor.DIR_THRESHOLD})")
    print(f"EOG:  {result['eog']} {'VIOLATION' if result['eog_flag'] else 'OK'} (threshold <= {BiasAuditor.EOG_THRESHOLD})")
    print(f"DPG:  {result['dpg']} {'VIOLATION' if result['dpg_flag'] else 'OK'} (threshold <= {BiasAuditor.DPG_THRESHOLD})")
    print()
    print(f"Legal risk: {result['legal_risk']}")
    print(f"Compliant:  {result['compliant']}")
    if result["flags"]:
        print("\nFlags:")
        for f in result["flags"]:
            print(f"  - {f}")
    print("=" * 45)
