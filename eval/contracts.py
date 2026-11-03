from typing import Literal

from finagent.contracts.base import Contract, ExactDecimal, Identifier, SafeInt, Sha256


class CountDetail(Contract):
    name: Identifier
    count: SafeInt


class MetricObservation(Contract):
    metric_id: Identifier
    status: Literal[
        "PASS",
        "FAIL",
        "PARTIAL",
        "NOT_RUN",
        "NOT_EVALUATED",
        "INSUFFICIENT_DATA",
        "PENDING_APPROVAL",
    ]
    reason: str
    numerator: SafeInt | None = None
    denominator: SafeInt | None = None
    value: ExactDecimal | None = None
    threshold: ExactDecimal | None = None
    details: tuple[CountDetail, ...] = ()


class EvalReport(Contract):
    schema_version: Literal["eval/1"] = "eval/1"
    suite: str
    cohort_sha256: Sha256
    scope: str
    metrics: tuple[MetricObservation, ...]
    phase_gate: Literal["GO", "NO_GO"]
    reason: str
