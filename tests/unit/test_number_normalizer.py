from decimal import Decimal

import pytest

from finagent.extraction.numbers import RawNumericCell, normalize
from finagent.ingestion.errors import ProcessingError


def test_well_formed_wrong_reading_is_preserved_for_later_equation_validation() -> None:
    candidate = normalize(
        RawNumericCell(
            cell_id="cell-a", raw_text="97.623.971.644", role="value", currency="VND", unit_scale=1
        )
    )
    assert candidate.value == 97623971644 and candidate.financial_eligible is False


@pytest.mark.parametrize(
    ("raw", "scale", "value"),
    [
        ("97.623.991.644", 1, "97623991644"),
        ("(1.685.413.336)", 1, "-1685413336"),
        ("−150.117", 1, "-150117"),
        ("1 234 567", 1, "1234567"),
        ("1\u00a0234", 1000, "1234000"),
        ("1,25", 1000, "1250"),
        ("-", 1, "0"),
        ("—", 1000000, "0"),
        ("0", 1, "0"),
        ("99999999999999999999999999999999999999", 1, "99999999999999999999999999999999999999"),
    ],
)
def test_vi_numbers_exact_sign_scale_and_original_preserved(raw, scale, value) -> None:
    result = normalize(
        RawNumericCell(
            cell_id="cell-a", raw_text=raw, role="value", currency="VND", unit_scale=scale
        )
    )
    assert result.value == Decimal(value) and result.original_display == raw
    assert result.presence == ("explicit_zero" if value == "0" else "value")
    assert result.financial_eligible is False


@pytest.mark.parametrize(
    "raw", ["97.623.971.64", "1.23", "1,2,3", "1.234 567", "1e5", "(+12)", "--12", "01", "(−12)"]
)
def test_malformed_format_is_error_never_repaired_to_an_expected_answer(raw: str) -> None:
    with pytest.raises(ProcessingError):
        normalize(
            RawNumericCell(
                cell_id="cell-a", raw_text=raw, role="value", currency="VND", unit_scale=1
            )
        )


def test_zero_missing_units_and_note_code_roles_are_distinct() -> None:
    assert normalize(RawNumericCell(cell_id="c-a", raw_text="", role="value")).presence == "missing"
    for role in ("code", "note", "label"):
        result = normalize(RawNumericCell(cell_id="c-a", raw_text="4/7", role=role))
        assert result.presence == "not_numeric" and result.value is None
    with pytest.raises(ProcessingError, match="UNIT_AMBIGUOUS"):
        normalize(RawNumericCell(cell_id="c-a", raw_text="100", role="value"))
    with pytest.raises(ProcessingError, match="FRACTIONAL_INTEGER_MEASURE"):
        normalize(
            RawNumericCell(
                cell_id="c-a", raw_text="1,25", role="value", currency="VND", unit_scale=1
            )
        )
    with pytest.raises(ProcessingError, match="NUMBER_PRECISION_EXCEEDED"):
        normalize(
            RawNumericCell(
                cell_id="c-a", raw_text="9" * 38, role="value", currency="VND", unit_scale=1000
            )
        )
