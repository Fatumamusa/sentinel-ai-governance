"""
Sentinel — Module M6: Model Card Generator
Legal basis: EU AI Act Art.13 (transparency documentation)
             GDPR Art.22 (automated decision explainability)
Answers: Can we explain AI decisions?
         Who approved this AI system?
         Where did training data come from?
"""

from typing import List, Dict, Optional


class ApprovalRecord:
    """Formal human oversight record. EU AI Act Art.14."""
    def __init__(self, approver_name, approver_role,
                 approved_at, review_type, next_review, conditions=None):
        self.approver_name = approver_name
        self.approver_role = approver_role
        self.approved_at   = approved_at
        self.review_type   = review_type
        self.next_review   = next_review
        self.conditions    = conditions or []


class BiasEvaluation:
    """Disaggregated performance metrics across one protected attribute."""
    def __init__(self, protected_attribute, group_metrics,
                 disparate_impact_ratio, equalized_odds_gap):
        self.protected_attribute    = protected_attribute
        self.group_metrics          = group_metrics
        self.disparate_impact_ratio = disparate_impact_ratio
        self.equalized_odds_gap     = equalized_odds_gap

    @property
    def flagged(self):
        return self.disparate_impact_ratio < 0.80


class ModelCard:
    """Complete model documentation artifact."""

    def __init__(
        self,
        model_id,
        model_name,
        version,
        model_type,
        authors,
        created_at,
        intended_uses,
        out_of_scope_uses,
        requires_human_review,
        training_data_source,
        training_data_size,
        training_cutoff_date,
        known_data_gaps,
        overall_accuracy,
        bias_evaluations,
        explainability_method,
        potential_harms,
        approval,
    ):
        self.model_id              = model_id
        self.model_name            = model_name
        self.version               = version
        self.model_type            = model_type
        self.authors               = authors
        self.created_at            = created_at
        self.intended_uses         = intended_uses
        self.out_of_scope_uses     = out_of_scope_uses
        self.requires_human_review = requires_human_review
        self.training_data_source  = training_data_source
        self.training_data_size    = training_data_size
        self.training_cutoff_date  = training_cutoff_date
        self.known_data_gaps       = known_data_gaps
        self.overall_accuracy      = overall_accuracy
        self.bias_evaluations      = bias_evaluations
        self.explainability_method = explainability_method
        self.potential_harms       = potential_harms
        self.approval              = approval


class ModelCardGenerator:

    def bias_flags(self, card: ModelCard) -> List[str]:
        """Return attributes where DIR < 0.80."""
        return [b.protected_attribute for b in card.bias_evaluations
                if b.flagged]

    def to_markdown(self, card: ModelCard) -> str:
        """Render model card as Markdown for regulators."""
        flags = self.bias_flags(card)
        flag_str = ", ".join(flags) if flags else "None"

        bias_lines = "\n".join(
            f"- **{b.protected_attribute}**: "
            f"DIR={b.disparate_impact_ratio:.3f} "
            f"({'VIOLATION' if b.flagged else 'OK'} — threshold >= 0.80) | "
            f"EOG={b.equalized_odds_gap:.3f}"
            for b in card.bias_evaluations
        )

        intended = "\n".join(f"- {u}" for u in card.intended_uses)
        oos = "\n".join(f"- NOT: {u}" for u in card.out_of_scope_uses)
        human = "\n".join(f"- {r}" for r in card.requires_human_review)
        gaps = ", ".join(card.known_data_gaps) or "None identified"
        harms = "\n".join(f"- {h}" for h in card.potential_harms)
        conds = "; ".join(card.approval.conditions) or "None"

        return f"""# Model Card: {card.model_name} v{card.version}

**ID**: {card.model_id}
**Type**: {card.model_type}
**Created**: {card.created_at}
**Authors**: {", ".join(card.authors)}

---

## Intended Use
{intended}

### Out of Scope — Do NOT use for
{oos}

### Requires Human Review
{human}

---

## Training Data
- **Source**: {card.training_data_source}
- **Size**: {card.training_data_size:,} records
- **Cutoff**: {card.training_cutoff_date}
- **Known gaps**: {gaps}

---

## Performance and Bias Evaluation
- **Overall accuracy**: {card.overall_accuracy:.1%}
- **Explainability**: {card.explainability_method}

### Disaggregated Metrics
{bias_lines}

**Bias flags (DIR < 0.80)**: {flag_str}

---

## Potential Harms
{harms}

---

## Approval Chain
- **Approver**: {card.approval.approver_name} ({card.approval.approver_role})
- **Approved**: {card.approval.approved_at}
- **Review type**: {card.approval.review_type}
- **Next review**: {card.approval.next_review}
- **Conditions**: {conds}
"""


if __name__ == "__main__":
    card = ModelCard(
        model_id    = "loan-ai-v3",
        model_name  = "LoanApproval-AI",
        version     = "3.0.1",
        model_type  = "binary_classifier",
        authors     = ["sentinel-team@bank.com"],
        created_at  = "2024-09-15",
        intended_uses = [
            "Automate initial mortgage application screening",
            "Flag applications for human underwriter review",
        ],
        out_of_scope_uses = [
            "Final loan approval without human review",
            "Applications outside the United States",
            "Commercial real estate loans",
        ],
        requires_human_review = [
            "All applications within 10% of decision boundary",
            "All denials above $300,000 loan value",
        ],
        training_data_source = "FDIC loan history 2005-2023",
        training_data_size   = 847234,
        training_cutoff_date = "2023-12-31",
        known_data_gaps = [
            "Under-representation of non-binary applicants",
        ],
        overall_accuracy      = 0.884,
        explainability_method = "SHAP TreeExplainer",
        bias_evaluations = [
            BiasEvaluation("race",   {"group_a": 0.78, "group_b": 0.61},
                           disparate_impact_ratio=0.782,
                           equalized_odds_gap=0.058),
            BiasEvaluation("gender", {"male": 0.76, "female": 0.71},
                           disparate_impact_ratio=0.934,
                           equalized_odds_gap=0.018),
        ],
        potential_harms = [
            "Discriminatory denial of credit to protected classes",
            "Reinforcement of historical lending disparities",
        ],
        approval = ApprovalRecord(
            approver_name = "Dr. James Wilson",
            approver_role = "Chief Risk Officer",
            approved_at   = "2024-10-01",
            review_type   = "INITIAL",
            next_review   = "2025-04-01",
            conditions    = [
                "Monthly bias metric review required",
                "Auto-retrain if DIR drops below 0.75",
            ],
        ),
    )

    gen = ModelCardGenerator()
    md = gen.to_markdown(card)
    print(md)

    flags = gen.bias_flags(card)
    print(f"Bias flags: {flags}")
    print(f"Card generated successfully for {card.model_name}")
