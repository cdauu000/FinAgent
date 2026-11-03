import argparse
import json
from pathlib import Path

from eval.contracts import EvalReport
from finagent.observability.metric_contract import require_same_cohort


def compare(baseline: EvalReport, candidate: EvalReport) -> dict[str, object]:
    require_same_cohort(baseline.cohort_sha256, candidate.cohort_sha256)
    if baseline.suite != candidate.suite:
        raise ValueError("INCOMPARABLE_EVAL_COHORT")
    measured = {m.metric_id: m for m in baseline.metrics if m.value is not None}
    after = {m.metric_id: m for m in candidate.metrics if m.value is not None}
    higher = {"K01", "K02", "K03", "K05", "K06", "K09", "K10", "K11", "K13"}
    lower = {"K04", "K07", "K08", "K12", "K14", "K15", "K17"}
    changes: list[dict[str, str]] = []
    regression = False
    for key, before in measured.items():
        if key not in after:
            regression = True
            changes.append({"metric_id": key, "status": "MISSING_CANDIDATE_OBSERVATION"})
            continue
        left, right = before.value, after[key].value
        assert left is not None and right is not None
        if key not in higher | lower:
            changes.append({"metric_id": key, "status": "DIRECTION_POLICY_REQUIRED"})
            continue
        worse = right < left if key in higher else right > left
        regression |= worse
        changes.append(
            {
                "metric_id": key,
                "before": str(left),
                "after": str(right),
                "status": "REGRESSION" if worse else "NO_REGRESSION",
            }
        )
    return {
        "status": "NOT_EVALUATED"
        if not measured
        else "REGRESSION"
        if regression
        else "OBSERVED_COMPARISON",
        "reason": "No change in unmeasured metrics can demonstrate improvement or KPI compliance",
        "baseline_gate": baseline.phase_gate,
        "candidate_gate": candidate.phase_gate,
        "measured_metric_ids": sorted(measured),
        "changes": changes,
        "acceptance": "No statistical or full KPI acceptance implied by a point comparison",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    before = EvalReport.model_validate_json(args.baseline.read_text(encoding="utf-8"))
    after = EvalReport.model_validate_json(args.candidate.read_text(encoding="utf-8"))
    result = compare(before, after)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
