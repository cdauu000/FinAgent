from decimal import Decimal, localcontext
from typing import Literal

from eval.contracts import MetricObservation
from finagent.observability.metric_contract import validate_metric_counts, validate_metric_direction


def fraction_metric(
    metric_id: str,
    numerator: int,
    denominator: int,
    *,
    threshold: Decimal,
    direction: Literal["at_least", "at_most"],
) -> MetricObservation:
    validate_metric_counts(numerator, denominator)
    validate_metric_direction(direction)
    if denominator == 0:
        return MetricObservation(
            metric_id=metric_id,
            status="NOT_EVALUATED",
            reason="EMPTY_DENOMINATOR",
            numerator=0,
            denominator=0,
        )
    with localcontext() as context:
        context.prec = 38
        value = Decimal(numerator) / Decimal(denominator)
    passed = value >= threshold if direction == "at_least" else value <= threshold
    return MetricObservation(
        metric_id=metric_id,
        status="PASS" if passed else "FAIL",
        reason="OBSERVED_COUNTS",
        numerator=numerator,
        denominator=denominator,
        value=value,
        threshold=threshold,
    )
