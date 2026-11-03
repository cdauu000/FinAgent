import re

from finagent.contracts.base import JSON_SAFE_INTEGER


def validate_metric_counts(numerator: object, denominator: object) -> None:
    if (
        not isinstance(numerator, int)
        or isinstance(numerator, bool)
        or not isinstance(denominator, int)
        or isinstance(denominator, bool)
        or numerator < 0
        or denominator < 0
        or numerator > denominator
        or denominator > JSON_SAFE_INTEGER
    ):
        raise ValueError("INVALID_METRIC_COUNTS")


def require_same_cohort(expected: object, actual: object) -> None:
    if (
        not isinstance(expected, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected)
        or expected != actual
    ):
        raise ValueError("INCOMPARABLE_EVAL_COHORT")


def validate_metric_direction(direction: str) -> None:
    if direction not in {"at_least", "at_most"}:
        raise ValueError("UNKNOWN_METRIC_DIRECTION")
