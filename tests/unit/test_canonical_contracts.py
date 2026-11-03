import json
from datetime import date
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from finagent.contracts.base import FlowPeriod, PeriodKey, StockPeriod
from finagent.store.models import DecimalValue, LineItem, MonetaryValue, Statement


@pytest.mark.parametrize("amount", [0, -1, 33067716327546, 9007199254740993, 10**37])
def test_money_json_roundtrip_is_exact_string(amount: int) -> None:
    original = MonetaryValue.model_validate(
        {"value": str(amount) if abs(amount) > 2**53 - 1 else amount}
    )
    wire = original.model_dump_json()
    assert json.loads(wire)["value"] == str(amount)
    assert MonetaryValue.model_validate_json(wire) == original


@pytest.mark.parametrize("amount", [True, 1.0, 1.2, "1,234", "01", "1e3", 10**38])
def test_finance_never_coerces_float_bool_or_ambiguous_text(amount: object) -> None:
    with pytest.raises(ValidationError):
        MonetaryValue.model_validate({"value": amount})


def test_decimal_preserves_exact_fraction_and_negative_sign() -> None:
    value = DecimalValue(kind="ratio", value=Decimal("-0.01215546438742628"))
    assert DecimalValue.model_validate_json(value.model_dump_json()) == value
    with pytest.raises(ValidationError):
        DecimalValue.model_validate({"kind": "ratio", "value": 0.1})


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "1e100", "0." + "1" * 39])
def test_nonfinite_or_unbounded_decimal_rejected(bad: str) -> None:
    with pytest.raises(ValidationError):
        DecimalValue.model_validate({"kind": "ratio", "value": bad})


def test_stock_and_flow_cannot_be_interchanged() -> None:
    stock = StockPeriod(as_of=date(2026, 3, 31), fiscal_year=2026)
    assert TypeAdapter(PeriodKey).validate_json(stock.model_dump_json()) == stock
    with pytest.raises(ValidationError):
        StockPeriod.model_validate({**stock.model_dump(), "start": date(2026, 1, 1)})
    with pytest.raises(ValidationError):
        FlowPeriod(
            start=date(2026, 4, 1),
            end=date(2026, 3, 31),
            period_type="quarter",
            fiscal_year=2026,
            fiscal_quarter=1,
        )


def line_data() -> dict[str, object]:
    return {
        "id": "line-a",
        "tenant_id": "tenant-a",
        "created_at": "2026-11-02T00:00:00Z",
        "pipeline_version": "draft",
        "statement_id": "statement-a",
        "statement_revision": 1,
        "source_column_id": "q1-current",
        "code": "420b",
        "canonical_id": "retained-profit",
        "label_vi": "Lợi nhuận kỳ này",
        "presence": "explicit_zero",
        "financial_value": {"kind": "money", "value": "0"},
        "trust_grade": "A",
        "provenance_refs": ["prov-a"],
    }


def test_missing_explicit_zero_and_derived_zero_are_distinct() -> None:
    data = line_data()
    assert LineItem.model_validate(data).code == "420b"
    with pytest.raises(ValidationError):
        LineItem.model_validate({**data, "presence": "missing"})
    with pytest.raises(ValidationError):
        LineItem.model_validate({**data, "presence": "derived_zero"})
    missing = LineItem.model_validate({**data, "presence": "missing", "financial_value": None})
    assert missing.financial_value is None
    derived = LineItem.model_validate(
        {**data, "presence": "derived_zero", "derivation_ref": "eq-a"}
    )
    assert derived.derivation_ref == "eq-a"
    with pytest.raises(ValidationError):
        LineItem.model_validate({**data, "financial_value": {"kind": "money", "value": "1"}})


def test_balance_sheet_rejects_flow_period() -> None:
    with pytest.raises(ValidationError, match="BALANCE_SHEET_REQUIRES_STOCK"):
        Statement.model_validate(
            {
                "id": "statement-a",
                "tenant_id": "tenant-a",
                "created_at": "2026-11-02T00:00:00Z",
                "pipeline_version": "draft",
                "revision": 1,
                "document_id": "doc-a",
                "entity_id": "entity-a",
                "template_ref": {"id": "fpt", "version": "1"},
                "statement_type": "B01",
                "scope": "separate",
                "unit_scale": 1,
                "verification_status": "VERIFIED",
                "line_refs": [],
                "complete": True,
                "period": {
                    "kind": "flow",
                    "start": "2026-01-01",
                    "end": "2026-03-31",
                    "period_type": "quarter",
                    "fiscal_year": 2026,
                    "fiscal_quarter": 1,
                },
            }
        )


def test_domain_objects_are_frozen_and_extra_fields_forbidden() -> None:
    value = MonetaryValue(value=1)
    with pytest.raises(ValidationError):
        value.value = 2
    with pytest.raises(ValidationError):
        MonetaryValue.model_validate({"value": 1, "raw_table": "CANARY"})
