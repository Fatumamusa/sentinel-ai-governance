import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sentinel.model_card import (
    ModelCard, ModelCardGenerator, BiasEvaluation, ApprovalRecord
)


def make_card(dir_value=0.782, gender_dir=0.934):
    return ModelCard(
        model_id    = "test-model",
        model_name  = "Test Model",
        version     = "1.0",
        model_type  = "classifier",
        authors     = ["tester@sentinel.ai"],
        created_at  = "2024-01-01",
        intended_uses         = ["Screening applications"],
        out_of_scope_uses     = ["Final decisions without human review"],
        requires_human_review = ["All denials above $300k"],
        training_data_source  = "test-data",
        training_data_size    = 100000,
        training_cutoff_date  = "2023-12-31",
        known_data_gaps       = ["Limited data for group X"],
        overall_accuracy      = 0.884,
        explainability_method = "SHAP",
        bias_evaluations = [
            BiasEvaluation("race",   {"a": 0.78, "b": 0.61},
                           dir_value, 0.058),
            BiasEvaluation("gender", {"m": 0.76, "f": 0.71},
                           gender_dir, 0.018),
        ],
        potential_harms = ["Discriminatory outcomes"],
        approval = ApprovalRecord(
            approver_name = "Jane Smith",
            approver_role = "Chief Risk Officer",
            approved_at   = "2024-10-01",
            review_type   = "INITIAL",
            next_review   = "2025-04-01",
            conditions    = ["Monthly bias review"],
        ),
    )


def test_markdown_contains_model_name():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card())
    assert "Test Model" in md


def test_markdown_contains_approval_chain():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card())
    assert "Jane Smith" in md
    assert "Chief Risk Officer" in md


def test_markdown_contains_bias_section():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card())
    assert "Disaggregated Metrics" in md
    assert "DIR=" in md


def test_bias_flag_detected():
    gen = ModelCardGenerator()
    flags = gen.bias_flags(make_card(dir_value=0.782))
    assert "race" in flags


def test_bias_flag_not_raised_when_compliant():
    gen = ModelCardGenerator()
    flags = gen.bias_flags(make_card(dir_value=0.85, gender_dir=0.92))
    assert len(flags) == 0


def test_violation_label_in_markdown():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card(dir_value=0.74))
    assert "VIOLATION" in md


def test_ok_label_in_markdown():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card(gender_dir=0.95))
    assert "OK" in md


def test_out_of_scope_in_markdown():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card())
    assert "Out of Scope" in md
    assert "NOT:" in md


def test_training_data_size_formatted():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card())
    assert "100,000" in md


def test_approval_conditions_in_markdown():
    gen = ModelCardGenerator()
    md = gen.to_markdown(make_card())
    assert "Monthly bias review" in md
