"""Draft common contracts; monetary values never pass through float."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Generic, Literal, Self, TypeVar

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    GetJsonSchemaHandler,
    PlainSerializer,
    StringConstraints,
    WithJsonSchema,
    model_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema

# A61 approved technical bounds. Real-data violations require owner review, never truncation.
Identifier = Annotated[
    str, StringConstraints(pattern=r"^[a-zA-Z][a-zA-Z0-9_.:-]*$", max_length=160)
]
NonEmpty = Annotated[str, StringConstraints(min_length=1, max_length=4096)]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Version = Annotated[str, StringConstraints(pattern=r"^[0-9]+(?:\.[0-9]+){0,2}$")]
JSON_SAFE_INTEGER = 2**53 - 1


def safe_metadata_integer(value: int) -> int:
    if abs(value) > JSON_SAFE_INTEGER:
        raise ValueError("UNSAFE_METADATA_INTEGER")
    return value


SafeInt = Annotated[int, Field(strict=True), AfterValidator(safe_metadata_integer)]


def bound_schema_integers(value: object) -> None:
    if isinstance(value, dict):
        if value.get("type") == "integer":
            # Nullable constrained Annotated integers can retain Pydantic keywords
            # around function validators. Publish standard JSON Schema bounds.
            for source, target in (
                ("ge", "minimum"),
                ("le", "maximum"),
                ("gt", "exclusiveMinimum"),
                ("lt", "exclusiveMaximum"),
            ):
                if source in value:
                    constraint = value.pop(source)
                    if target in value:
                        combine = max if source in {"ge", "gt"} else min
                        constraint = combine(value[target], constraint)
                    value[target] = constraint
            value["minimum"] = max(value.get("minimum", -JSON_SAFE_INTEGER), -JSON_SAFE_INTEGER)
            value["maximum"] = min(value.get("maximum", JSON_SAFE_INTEGER), JSON_SAFE_INTEGER)
        for child in value.values():
            bound_schema_integers(child)
    elif isinstance(value, list):
        for child in value:
            bound_schema_integers(child)


# A61 approved Unicode-character budgets, distinct from financial thresholds.
PAGE_TEXT_LIMIT = 1_000_000
CHUNK_TEXT_LIMIT = 64_000
CITATION_TEXT_LIMIT = 64_000
EXPORT_TEXT_LIMIT = 10_000_000
PageText = Annotated[str, StringConstraints(max_length=PAGE_TEXT_LIMIT)]
ChunkText = Annotated[str, StringConstraints(max_length=CHUNK_TEXT_LIMIT)]
CitationText = Annotated[str, StringConstraints(max_length=CITATION_TEXT_LIMIT)]
ExportText = Annotated[str, StringConstraints(max_length=EXPORT_TEXT_LIMIT)]


def exact_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("INTEGER_REQUIRED")
    if isinstance(value, str) and not re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        raise ValueError("CANONICAL_INTEGER_REQUIRED")
    if isinstance(value, int) and abs(value) > JSON_SAFE_INTEGER:
        raise ValueError("UNSAFE_JSON_INTEGER_USE_CANONICAL_STRING")
    number = int(value)
    if len(str(abs(number))) > 38:
        raise ValueError("PRECISION_EXCEEDED")
    return number


def exact_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, str, Decimal)):
        raise ValueError("EXACT_DECIMAL_REQUIRED")
    if isinstance(value, int) and abs(value) > JSON_SAFE_INTEGER:
        raise ValueError("UNSAFE_JSON_INTEGER_USE_CANONICAL_STRING")
    if isinstance(value, str) and not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value):
        raise ValueError("CANONICAL_DECIMAL_REQUIRED")
    number = Decimal(value)
    if not number.is_finite() or len(number.as_tuple().digits) > 38:
        raise ValueError("FINITE_DECIMAL_PRECISION_REQUIRED")
    exponent = number.as_tuple().exponent
    if not isinstance(exponent, int) or abs(exponent) > 38:
        raise ValueError("DECIMAL_SCALE_EXCEEDED")
    if len(number.as_tuple().digits) + max(0, exponent) > 38:
        raise ValueError("FINITE_DECIMAL_PRECISION_REQUIRED")
    return number


Money = Annotated[
    int,
    BeforeValidator(exact_integer),
    PlainSerializer(str, return_type=str, when_used="json"),
    WithJsonSchema(
        {
            "anyOf": [
                {"type": "integer", "minimum": -JSON_SAFE_INTEGER, "maximum": JSON_SAFE_INTEGER},
                {"type": "string", "pattern": r"^-?(0|[1-9][0-9]{0,37})$"},
            ]
        },
        mode="validation",
    ),
    WithJsonSchema(
        {"type": "string", "pattern": r"^-?(0|[1-9][0-9]{0,37})$"}, mode="serialization"
    ),
]
ExactDecimal = Annotated[
    Decimal,
    BeforeValidator(exact_decimal),
    PlainSerializer(lambda value: format(value, "f"), return_type=str, when_used="json"),
    WithJsonSchema(
        {
            "anyOf": [
                {"type": "integer", "minimum": -JSON_SAFE_INTEGER, "maximum": JSON_SAFE_INTEGER},
                {"type": "string", "pattern": r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$"},
            ]
        },
        mode="validation",
    ),
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema = handler(core_schema)
        bound_schema_integers(schema)
        return schema


class Mode(StrEnum):
    STRICT = "strict"
    USEFUL = "useful"


class Tier(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    STRICT_PRIVATE = "strict_private"


class Scope(StrEnum):
    SEPARATE = "separate"
    CONSOLIDATED = "consolidated"


class TrustGrade(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class VerificationStatus(StrEnum):
    VERIFIED = "VERIFIED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"


class Verdict(StrEnum):
    ANSWER = "ANSWER"
    CAVEATS = "ANSWER_WITH_CAVEATS"
    ABSTAIN = "ABSTAIN"


class StockPeriod(Contract):
    kind: Literal["stock"] = "stock"
    as_of: date
    fiscal_year: SafeInt = Field(ge=1900, le=9999)


class FlowPeriod(Contract):
    kind: Literal["flow"] = "flow"
    start: date
    end: date
    period_type: Literal["quarter", "ytd", "annual", "ttm", "custom"]
    fiscal_year: SafeInt = Field(ge=1900, le=9999)
    fiscal_quarter: SafeInt | None = Field(default=None, ge=1, le=4)
    months: SafeInt | None = Field(default=None, ge=1, le=12)
    derivation_refs: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def valid_interval(self) -> Self:
        if self.start > self.end:
            raise ValueError("INVALID_PERIOD_INTERVAL")
        if self.period_type == "quarter" and self.fiscal_quarter is None:
            raise ValueError("FISCAL_QUARTER_REQUIRED")
        return self


PeriodKey = Annotated[StockPeriod | FlowPeriod, Field(discriminator="kind")]


class Selection(Contract):
    entity_id: Identifier
    statement_family: Identifier = "corporate"
    scope: Scope
    period: PeriodKey
    revision_policy: Literal["pinned", "latest_approved"] = "pinned"
    snapshot_refs: tuple[Identifier, ...] = ()


class RegistryRef(Contract):
    id: Identifier
    version: Version


class ExecutionContext(Contract):
    tenant_id: Identifier
    principal_id: Identifier
    permissions: tuple[Identifier, ...]
    request_id: Identifier
    trace_id: Identifier
    policy_ref: RegistryRef
    mode: Mode
    source_tier: Tier = Tier.PRIVATE
    deadline: datetime


class DomainError(Contract):
    code: Identifier
    message_key: Identifier
    retryable: bool = False
    correlation_id: Identifier
    missing_requirements: tuple[Identifier, ...] = ()


class Warning(Contract):
    code: Identifier
    severity: Literal["BLOCK", "WARN", "INFO"]
    message_key: Identifier
    evidence_ids: tuple[Identifier, ...]
    affected_ids: tuple[Identifier, ...] = ()
    assumption_ids: tuple[Identifier, ...] = ()
    blocking: bool = False


T = TypeVar("T")


class PageResult(Contract, Generic[T]):
    """Pagination with an endpoint-specific item type."""

    items: tuple[T, ...]
    next_cursor: str | None = None
    limit: SafeInt = Field(ge=1)
