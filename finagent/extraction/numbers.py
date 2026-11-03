"""S5: locale-aware parsing independent of OCR, equations or expected answers."""

import re
from decimal import Decimal, localcontext
from typing import Literal

from pydantic import Field

from finagent.contracts.base import Contract, ExactDecimal, Identifier, SafeInt, exact_integer
from finagent.ingestion.errors import ProcessingError


class RawNumericCell(Contract):
    cell_id: Identifier
    raw_text: str = Field(max_length=1_000_000)
    role: Literal["code", "note", "label", "value"]
    currency: Literal["VND"] | None = None
    unit_scale: Literal[1, 1000, 1000000, 1000000000] | None = None
    measure: Literal["money", "count", "ratio"] = "money"
    empty: bool = False


class NormalizationResult(Contract):
    cell_id: Identifier
    presence: Literal["value", "explicit_zero", "missing", "not_numeric"]
    value: ExactDecimal | None = None
    original_display: str
    applied_scale: SafeInt | None = Field(default=None, gt=0)
    financial_eligible: Literal[False] = False


def normalize(cell: RawNumericCell) -> NormalizationResult:
    raw = cell.raw_text
    if cell.role != "value":
        return NormalizationResult(
            cell_id=cell.cell_id, presence="not_numeric", original_display=raw
        )
    text = raw.strip().replace("\u00a0", " ").replace("\u202f", " ")
    if cell.empty or not text:
        if cell.empty and text:
            raise ProcessingError("EMPTY_CELL_HAS_TEXT")
        return NormalizationResult(cell_id=cell.cell_id, presence="missing", original_display=raw)
    if cell.measure == "money" and (cell.currency != "VND" or cell.unit_scale is None):
        raise ProcessingError("UNIT_AMBIGUOUS")
    if text in {"-", "–", "—", "−"}:
        number = Decimal(0)
    else:
        negative = False
        if text.startswith("(") and text.endswith(")"):
            negative, text = True, text[1:-1].strip()
        elif text.startswith(("-", "−")):
            negative, text = True, text[1:].strip()
        if not text or any(ch in text for ch in "()+−-"):
            raise ProcessingError("INVALID_NUMBER_SIGN")
        parts = text.split(",")
        if len(parts) > 2 or len(parts) == 2 and not re.fullmatch(r"[0-9]+", parts[1]):
            raise ProcessingError("INVALID_VI_NUMBER")
        integral = parts[0]
        if "." in integral and " " in integral:
            raise ProcessingError("MIXED_THOUSANDS_SEPARATORS")
        separator = "." if "." in integral else " " if " " in integral else None
        if separator:
            if not re.fullmatch(r"[0-9]{1,3}(?:" + re.escape(separator) + r"[0-9]{3})+", integral):
                raise ProcessingError("INVALID_THOUSANDS_GROUPING")
            integral = integral.replace(separator, "")
        elif not re.fullmatch(r"[0-9]+", integral):
            raise ProcessingError("INVALID_VI_NUMBER")
        if len(integral) > 1 and integral.startswith("0"):
            raise ProcessingError("NONCANONICAL_NUMBER")
        canonical = integral + ("." + parts[1] if len(parts) == 2 else "")
        if len(integral) > 38 or len(parts) == 2 and len(parts[1]) > 38:
            raise ProcessingError("NUMBER_PRECISION_EXCEEDED")
        number = Decimal(("-" if negative else "") + canonical)
    scale = cell.unit_scale if cell.measure == "money" else 1
    with localcontext() as context:
        context.prec = max(80, len(number.as_tuple().digits) + 12)
        value = number * (scale or 1)
    if cell.measure in {"money", "count"}:
        if value != value.to_integral_value():
            raise ProcessingError("FRACTIONAL_INTEGER_MEASURE")
        try:
            exact_integer(str(int(value)))
        except ValueError as exc:
            raise ProcessingError("NUMBER_PRECISION_EXCEEDED") from exc
        value = value.to_integral_value()
    elif len(value.as_tuple().digits) > 38:
        raise ProcessingError("NUMBER_PRECISION_EXCEEDED")
    return NormalizationResult(
        cell_id=cell.cell_id,
        presence="explicit_zero" if value == 0 else "value",
        value=value,
        original_display=raw,
        applied_scale=scale,
    )
