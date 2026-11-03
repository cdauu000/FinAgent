"""Local review-case harness. Test fixtures are data, never runtime business inputs."""

from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, JsonValue, ValidationError

CASE_PATH = Path(__file__).resolve().parents[1] / "tests/fixtures/schema_review_cases.json"


class ReviewCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    group: str
    expect: Literal["valid", "invalid"]
    payload: dict[str, JsonValue]
    expected_error: str | None = None
    validator: Literal[
        "schema",
        "registry.bundle",
        "corpus.manifest",
        "query_guard",
        "metric_counts",
        "frozen.manifest",
        "review.counts",
        "cohort.binding",
        "p1a.safety",
    ] = "schema"


class ReviewCases(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cases: tuple[ReviewCase, ...]


def load_review_cases(path: Path = CASE_PATH) -> tuple[ReviewCase, ...]:
    cases = ReviewCases.model_validate_json(path.read_text(encoding="utf-8")).cases
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("DUPLICATE_REVIEW_CASE_ID")
    return cases


def check_review_case(case: ReviewCase, model: type[BaseModel]) -> tuple[bool, str]:
    import json

    try:
        content = json.dumps(case.payload, ensure_ascii=False)
        if case.validator == "registry.bundle":
            from finagent.policy.registry import registry_bundle

            if case.group == "model-registry/1":
                registry_bundle(content, kind="model")
            elif case.group == "prompt/1":
                registry_bundle(content, kind="prompt")
            else:
                registry_bundle(content)
        elif case.validator == "corpus.manifest":
            from finagent.corpus.contracts import CorpusManifest
            from finagent.corpus.inventory import validate_manifest

            validate_manifest(CorpusManifest.model_validate_json(content), CASE_PATH.parents[2])
        elif case.validator == "query_guard":
            from uuid import UUID

            from finagent.contracts.base import Scope, Tier
            from finagent.llm_gateway.query_guard import KnownEntity, guard_query

            question = case.payload.get("question")
            if not isinstance(question, str):
                raise ValueError("GUARD_QUESTION_REQUIRED")
            guard_query(
                question,
                (KnownEntity(UUID(int=1), ("FPT",)),),
                selected_entity=UUID(int=1),
                period_code="q1_2026",
                scope=Scope.SEPARATE,
                tier=Tier.PUBLIC,
            )
        elif case.validator == "metric_counts":
            from finagent.observability.metric_contract import (
                validate_metric_counts,
                validate_metric_direction,
            )

            validate_metric_counts(case.payload.get("numerator"), case.payload.get("denominator"))
            if "direction" in case.payload:
                direction = case.payload["direction"]
                if not isinstance(direction, str):
                    raise ValueError("UNKNOWN_METRIC_DIRECTION")
                validate_metric_direction(direction)
        elif case.validator == "frozen.manifest":
            from finagent.contracts.compatibility import validate_frozen_index

            validate_frozen_index(case.payload)
        elif case.validator == "review.counts":
            validate_review_counts(case.payload.get("observed"), case.payload.get("expected"))
        elif case.validator == "cohort.binding":
            from finagent.observability.metric_contract import require_same_cohort

            require_same_cohort(case.payload.get("expected"), case.payload.get("actual"))
        elif case.validator == "p1a.safety":
            check_phase1a_safety(case.payload)
        else:
            model.model_validate_json(content)
    except (ValidationError, ValueError) as exc:
        messages = (
            " ".join(str(error["msg"]) for error in exc.errors(include_input=False))
            if isinstance(exc, ValidationError)
            else str(exc)
        )
        matched = case.expected_error is None or case.expected_error in messages
        return case.expect == "invalid" and matched, "rejected"
    return case.expect == "valid", "accepted"


def check_phase1a_safety(payload: dict[str, JsonValue]) -> None:
    from finagent.corpus.review_tools import require_page_annotations, supplied_report
    from finagent.extraction.media import MediaResult, bind_raster_dimensions, parse_media_result
    from finagent.extraction.numbers import RawNumericCell, normalize
    from finagent.ingestion.file_safety import safe_filename
    from finagent.ingestion.service import require_same_request
    from finagent.ingestion.url_fetch import check_url, resolve_before_deadline
    from finagent.jobs.memory import JobRecord

    target = payload.get("target")
    value = payload.get("value")
    if target == "checkpoint":
        JobRecord.model_validate(
            {
                "job_id": "job-a",
                "document_id": "doc-a",
                "tenant_id": "tenant-a",
                "source_tier": "private",
                "checkpoint_ref": value,
            }
        )
    elif target == "number":
        normalize(
            RawNumericCell.model_validate(
                {
                    "cell_id": "cell-a",
                    "raw_text": value,
                    "role": "value",
                    "measure": "money",
                    "currency": "VND",
                    "unit_scale": 1,
                }
            )
        )
    elif isinstance(value, str):
        if target == "media_protocol":
            parse_media_result(value.encode())
        elif target == "filename":
            safe_filename(value)
        elif target == "url":
            check_url(value, lambda host, port: ("127.0.0.1",))
        elif target == "idempotency":
            require_same_request("original-url-fingerprint", value)
        else:
            raise ValueError("UNKNOWN_P1A_SAFETY_CASE")
    elif target == "render_dimensions":
        bind_raster_dimensions(
            MediaResult(
                ok=True, width=3509, height=2482, logical_dpi=120, peak_working_set_bytes=0
            ),
            4386,
            3102,
        )
    elif target == "dns_deadline":
        resolve_before_deadline(lambda h, p: ("93.184.216.34",), "example.com", 443, 0)
    elif target == "page_annotation_duplicates":
        require_page_annotations((0, 0), 28)
    elif target == "report_path":
        supplied_report(CASE_PATH.parents[2], "samples/FPT_BCTC_rieng_Q1_2026.pdf")
    else:
        raise ValueError("UNKNOWN_P1A_SAFETY_CASE")


def validate_review_counts(observed: object, expected: object) -> None:
    if observed != expected:
        raise ValueError("REVIEW_CASE_COUNTS_MISMATCH")


def review_case_counts(
    models: dict[str, type[BaseModel]], *, case_path: Path = CASE_PATH
) -> dict[str, dict[str, int]]:
    counts = {
        group: Counter(
            {
                "positive_cases": 0,
                "negative_cases": 0,
                "positive_passed": 0,
                "negative_passed": 0,
                "failed": 0,
            }
        )
        for group in models
    }
    for case in load_review_cases(case_path):
        if case.group not in models:
            raise ValueError("UNKNOWN_REVIEW_CASE_GROUP")
        passed, _ = check_review_case(case, models[case.group])
        kind = "positive" if case.expect == "valid" else "negative"
        counts[case.group][kind + "_cases"] += 1
        counts[case.group][kind + "_passed"] += int(passed)
        counts[case.group]["failed"] += int(not passed)
        if not passed:
            raise ValueError(f"REVIEW_CASE_FAILED: {case.id}")
    for group, values in counts.items():
        if not values["positive_cases"] or not values["negative_cases"]:
            raise ValueError(f"REVIEW_CASE_POLARITY_MISSING: {group}")
    return {group: dict(values) for group, values in counts.items()}
