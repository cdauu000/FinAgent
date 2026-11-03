from decimal import Decimal
from pathlib import Path

import pytest

from eval.compare import compare
from eval.contracts import EvalReport
from eval.measure import fraction_metric
from eval.run import baseline

ROOT = Path(__file__).resolve().parents[2]


def test_measured_counts_and_empty_denominator_never_become_fake_perfect_scores() -> None:
    observed = fraction_metric("K02", 985, 1000, threshold=Decimal("0.985"), direction="at_least")
    assert observed.status == "PASS" and observed.value == Decimal("0.985")
    empty = fraction_metric("K02", 0, 0, threshold=Decimal("0.985"), direction="at_least")
    assert empty.status == "NOT_EVALUATED" and empty.value is None
    with pytest.raises(ValueError, match="INVALID_METRIC_COUNTS"):
        fraction_metric("K02", 2, 1, threshold=Decimal("1"), direction="at_least")


def test_real_phase0_baseline_is_no_go_and_quality_has_no_invented_values() -> None:
    result = baseline(ROOT, ROOT / "eval/datasets/manifest.json")
    assert result.phase_gate == "NO_GO" and len(result.metrics) == 20
    assert all(metric.value is None for metric in result.metrics)
    k16 = next(metric for metric in result.metrics if metric.metric_id == "K16")
    assert k16.status == "INSUFFICIENT_DATA"
    assert {d.name: d.count for d in k16.details}["unique_real_reports"] == 1
    for metric in result.metrics:
        if metric.metric_id in {"K19", "K20"}:
            assert metric.status == "PENDING_APPROVAL" and metric.threshold is None


def test_comparison_rejects_cohort_mismatch_and_detects_observed_loss() -> None:
    def report(numerator: int, cohort: str = "a" * 64) -> EvalReport:
        return EvalReport(
            suite="ocr",
            cohort_sha256=cohort,
            scope="unit-only",
            metrics=(
                fraction_metric(
                    "K02", numerator, 1000, threshold=Decimal("0.985"), direction="at_least"
                ),
            ),
            phase_gate="NO_GO",
            reason="unit count fixture",
        )

    assert compare(report(990), report(980))["status"] == "REGRESSION"
    with pytest.raises(ValueError, match="INCOMPARABLE_EVAL_COHORT"):
        compare(report(990), report(990, "b" * 64))
