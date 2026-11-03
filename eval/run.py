"""Offline Phase0 harness. Unimplemented suites produce NOT_RUN, never fabricated scores."""

import argparse
import ast
import hashlib
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

from eval.contracts import CountDetail, EvalReport, MetricObservation
from finagent.corpus.contracts import CorpusManifest
from finagent.corpus.inventory import cohort_hash, corpus_counts, validate_manifest
from finagent.policy.registry import load_bundle
from finagent.schema_catalog import check_frozen
from finagent.schema_review import review_case_counts


def declared_ports(root: Path) -> tuple[str, ...]:
    ports: list[str] = []
    for path in (root / "finagent").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(base, ast.Name) and base.id == "Protocol" for base in node.bases
            ):
                ports.append(path.relative_to(root).as_posix() + ":" + node.name)
    return tuple(sorted(ports))


def baseline(root: Path, dataset: Path) -> EvalReport:
    check_frozen(root)
    load_bundle(root / "config/registries/core.json")
    manifest = CorpusManifest.model_validate_json(dataset.read_text(encoding="utf-8"))
    validate_manifest(manifest, root)
    counts = corpus_counts(manifest)
    metrics = [
        MetricObservation(
            metric_id="K01",
            status="PARTIAL",
            reason="DECLARED_PORTS_NOT_FULL_BACKEND_IMPLEMENTATIONS",
            details=(CountDetail(name="declared_ports", count=len(declared_ports(root))),),
        )
    ]
    for number in range(2, 21):
        if number == 16:
            metrics.append(
                MetricObservation(
                    metric_id="K16",
                    status="PASS" if counts["status"] == "PASS" else "INSUFFICIENT_DATA",
                    reason="UNIQUE_SUPPLIED_REPORTS_WITH_SOURCE_DATE_TERMS_AND_APPROVED_GOLD",
                    details=tuple(
                        CountDetail(name=name, count=count_integer(counts[name]))
                        for name in (
                            "unique_real_reports",
                            "complete_manifests",
                            "gold_approved",
                            "required_manifests",
                            "required_gold",
                        )
                    ),
                )
            )
        else:
            metrics.append(
                MetricObservation(
                    metric_id=f"K{number:02}",
                    status="PENDING_APPROVAL" if number in {19, 20} else "NOT_EVALUATED",
                    reason="QUALITY_THRESHOLD_PENDING_BASELINE_NO_MODEL_RESPONSES"
                    if number in {19, 20}
                    else "REQUIRED_PIPELINE_OR_APPROVED_COHORT_NOT_AVAILABLE_PHASE0",
                )
            )
    return EvalReport(
        suite="baseline",
        cohort_sha256=cohort_hash(root, manifest),
        scope="P0.11 inventory only; no OCR/analytics/Agent/model quality measurements",
        metrics=tuple(metrics),
        phase_gate="NO_GO",
        reason="PHASE0_INCOMPLETE_CORPUS_AND_UNVERIFIED_ENVIRONMENT; owner confirmation required",
    )


def count_integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("INVALID_INVENTORY_COUNT")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline evaluation with explicit missing-data status"
    )
    parser.add_argument(
        "--suite",
        choices=[
            "baseline",
            "ocr",
            "validation",
            "analytics",
            "retrieval",
            "agent",
            "privacy",
            "performance",
        ],
        required=True,
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", default="visible_regression")
    args = parser.parse_args()
    root = Path.cwd()
    if args.suite == "baseline":
        report = baseline(root, args.dataset)
    else:
        manifest = CorpusManifest.model_validate_json(args.dataset.read_text(encoding="utf-8"))
        validate_manifest(manifest, root)
        report = EvalReport(
            suite=args.suite,
            cohort_sha256=cohort_hash(root, manifest),
            scope=f"Requested suite {args.suite}, split {args.split}",
            metrics=(),
            phase_gate="NO_GO",
            reason="NOT_RUN: suite implementation or approved gold unavailable in Phase0",
        )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    from finagent.schema_catalog import SCHEMAS

    metadata = {
        "recorded_at": datetime.now(UTC).isoformat(),
        "command": sys.argv,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "schema_manifest_sha256": hashlib.sha256(
            (root / "schemas/frozen/manifest.json").read_bytes()
        ).hexdigest(),
        "dataset_sha256": report.cohort_sha256,
        "configuration_hashes": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (root / "config/registries").glob("*.json")
        },
        "split": args.split,
        "declared_ports": declared_ports(root),
        "current_schema_review_cases": review_case_counts(SCHEMAS),
        "frozen": True,
        "provider_calls": 0,
    }
    (args.output / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    raise SystemExit(0 if report.phase_gate == "GO" else 2)


if __name__ == "__main__":
    main()
