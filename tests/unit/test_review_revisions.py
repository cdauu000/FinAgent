import json
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import TypeAdapter, ValidationError

from finagent.api.contracts import TextExportContent
from finagent.contracts.base import (
    CHUNK_TEXT_LIMIT,
    CITATION_TEXT_LIMIT,
    EXPORT_TEXT_LIMIT,
    JSON_SAFE_INTEGER,
    PAGE_TEXT_LIMIT,
    ChunkText,
    CitationText,
    ExportText,
    NonEmpty,
    PageText,
    SafeInt,
)
from finagent.llm_gateway.contracts import EntityToken, NumberPlaceholder
from finagent.llm_gateway.tokens import RunTokenAllocator, TokenAllocationError
from finagent.policy.contracts import Expression, RuleDefinition
from finagent.store.models import DecimalValue, EvidenceChunk, MonetaryValue, Page, SourceQuote


def record() -> dict[str, object]:
    return {
        "id": "synthetic-a",
        "tenant_id": "tenant-a",
        "source_tier": "private",
        "created_at": "2026-11-02T00:00:00Z",
        "pipeline_version": "draft",
    }


def test_short_aliases_retry_query_and_local_collisions_without_using_rejected_tokens() -> None:
    draws = iter(["abcdefgh", "23456789", "23456789", "98765432"])
    allocator = RunTokenAllocator("User typed ENT_ABCDEFGH", draw=lambda: next(draws))
    entity_id, number_id = UUID(int=1), UUID(int=2)
    entity = allocator.allocate("ent", entity_id)
    assert entity == "ent_23456789"
    assert allocator.allocate("ent", entity_id) == entity
    number = allocator.allocate("num", number_id)
    assert number == "num_98765432"
    assert TypeAdapter(EntityToken).validate_python(entity) == entity
    assert TypeAdapter(NumberPlaceholder).validate_python(number) == number
    assert isinstance(allocator.run_id, UUID)
    assert allocator.run_id.hex not in entity + number


def test_collision_exhaustion_is_local_failure_not_a_reused_token() -> None:
    allocator = RunTokenAllocator("abcdefgh", draw=lambda: "abcdefgh", max_attempts=2)
    with pytest.raises(TokenAllocationError, match="TOKEN_COLLISION_BUDGET_EXHAUSTED"):
        allocator.allocate("ent", UUID(int=1))


def test_original_question_collision_is_checked_after_unicode_normalization() -> None:
    draws = iter(["abcdefgh", "23456789"])
    allocator = RunTokenAllocator("ＥＮＴ＿ＡＢＣＤＥＦＧＨ", draw=lambda: next(draws))
    assert allocator.allocate("ent", UUID(int=1)) == "ent_23456789"


def test_same_entity_is_retokenized_for_each_run_and_old_128_bit_aliases_rejected() -> None:
    entity_id = UUID(int=1)
    first = RunTokenAllocator("query", draw=lambda: "abcdefgh")
    second = RunTokenAllocator("query", draw=lambda: "23456789")
    assert first.run_id != second.run_id
    assert first.allocate("ent", entity_id) != second.allocate("ent", entity_id)
    with pytest.raises(ValidationError):
        TypeAdapter(EntityToken).validate_python("ent_" + "a" * 32)


@pytest.mark.parametrize("value", [-JSON_SAFE_INTEGER, JSON_SAFE_INTEGER])
def test_safe_json_integer_boundaries(value: int) -> None:
    assert MonetaryValue.model_validate_json(json.dumps({"value": value})).value == value


@pytest.mark.parametrize("value", [JSON_SAFE_INTEGER + 1, -JSON_SAFE_INTEGER - 1, True, 1.0])
def test_metadata_integers_are_strict_and_safe(value: object) -> None:
    with pytest.raises(ValidationError):
        TypeAdapter(SafeInt).validate_json(json.dumps(value))


@pytest.mark.parametrize("value", [-JSON_SAFE_INTEGER - 1, JSON_SAFE_INTEGER + 1, 10**37])
def test_unsafe_integer_requires_canonical_string_in_both_input_paths(value: int) -> None:
    with pytest.raises(ValidationError, match="UNSAFE_JSON_INTEGER"):
        MonetaryValue.model_validate_json(json.dumps({"value": value}))
    with pytest.raises(ValidationError, match="UNSAFE_JSON_INTEGER"):
        MonetaryValue(value=value)
    parsed = MonetaryValue.model_validate_json(json.dumps({"value": str(value)}))
    assert parsed.value == value
    assert json.loads(parsed.model_dump_json())["value"] == str(value)


@pytest.mark.parametrize("value", [True, 1.0, "01", "+1", "1e3", "9,007,199,254,740,992"])
def test_alternate_numeric_spellings_do_not_bypass_canonical_wire_contract(value: object) -> None:
    with pytest.raises(ValidationError):
        MonetaryValue.model_validate({"value": value})


def test_nonempty_budget_is_not_a_page_chunk_export_or_citation_budget() -> None:
    text = "x" * 4097
    with pytest.raises(ValidationError):
        TypeAdapter(NonEmpty).validate_python(text)
    page = Page.model_validate(
        {
            **record(),
            "document_id": "doc-a",
            "physical_index": 0,
            "width": 1,
            "height": 1,
            "page_kind": "native",
            "native_text": text,
        }
    )
    chunk = EvidenceChunk.model_validate(
        {
            **record(),
            "document_id": "doc-a",
            "document_revision": 1,
            "text": text,
            "provenance_refs": ["prov-a"],
            "entity_id": "entity-a",
            "scope": "separate",
            "period": {"kind": "stock", "as_of": "2026-03-31", "fiscal_year": 2026},
            "trust_grade": "A",
            "numeric_fact_refs": [],
            "index_version": "draft",
        }
    )
    quote = SourceQuote(evidence_ref="evidence-a", text=text, provenance_refs=("prov-a",))
    export = TextExportContent(
        artifact_id="export-a", format="md", content=text, verifier_receipt_ref="receipt-a"
    )
    assert page.native_text == chunk.text == quote.text == export.content == text


@pytest.mark.parametrize(
    ("kind", "limit"),
    [
        (PageText, PAGE_TEXT_LIMIT),
        (ChunkText, CHUNK_TEXT_LIMIT),
        (CitationText, CITATION_TEXT_LIMIT),
        (ExportText, EXPORT_TEXT_LIMIT),
    ],
)
def test_long_text_types_have_explicit_distinct_boundaries(kind: object, limit: int) -> None:
    adapter = TypeAdapter(kind)
    assert len(adapter.validate_python("x" * limit)) == limit
    with pytest.raises(ValidationError):
        adapter.validate_python("x" * (limit + 1))


def test_ratio_wire_preserves_fraction_scale_and_rounding_without_percent_scaling() -> None:
    ratio = DecimalValue.model_validate({"value": "0.1250", "display_kind": "percent"})
    wire = json.loads(ratio.model_dump_json())
    assert ratio.value == Decimal("0.1250")
    assert wire == {
        "kind": "ratio",
        "value": "0.1250",
        "representation": "fraction",
        "scale": 4,
        "rounding_mode": "ROUND_HALF_UP",
        "display_kind": "percent",
    }
    assert DecimalValue.model_validate_json(ratio.model_dump_json()) == ratio
    with pytest.raises(ValidationError, match="DECIMAL_SCALE_MISMATCH"):
        DecimalValue.model_validate({"value": "0.1250", "scale": 2})
    with pytest.raises(ValidationError):
        DecimalValue.model_validate({"kind": "percentage", "value": "12.50"})


def constant() -> dict[str, object]:
    return {"kind": "constant", "value": "1"}


def chain(depth: int) -> dict[str, object]:
    node = constant()
    for _ in range(depth - 1):
        node = {"kind": "aggregate", "op": "sum", "inputs": [node]}
    return node


def wide_tree(leaves: int) -> dict[str, object]:
    # 1 root + 10 intermediate nodes + 1000 leaves + extra root leaves.
    groups = [
        {"kind": "aggregate", "op": "sum", "inputs": [constant() for _ in range(100)]}
        for _ in range(10)
    ]
    return {
        "kind": "aggregate",
        "op": "sum",
        "inputs": groups + [constant() for _ in range(leaves)],
    }


def test_ast_depth_and_total_node_boundaries_and_repeated_occurrences() -> None:
    adapter = TypeAdapter(Expression)
    assert adapter.validate_python(chain(32))
    with pytest.raises(ValidationError, match="AST_MAX_DEPTH_EXCEEDED"):
        adapter.validate_python(chain(33))
    assert adapter.validate_python(wide_tree(13))  # 1024 nodes, count occurrences.
    with pytest.raises(ValidationError, match="AST_MAX_NODES_EXCEEDED"):
        adapter.validate_python(wide_tree(14))
    shared = constant()
    with pytest.raises(ValidationError, match="AST_MAX_INPUTS_EXCEEDED"):
        adapter.validate_python({"kind": "aggregate", "op": "sum", "inputs": [shared] * 101})
    cycle = {"kind": "aggregate", "op": "sum", "inputs": []}
    cycle["inputs"].append(cycle)
    with pytest.raises(ValidationError, match="AST_CYCLE_FORBIDDEN"):
        adapter.validate_python(cycle)


def test_rule_budget_counts_both_sides_together() -> None:
    rule = {
        "id": "rule-a",
        "version": "1",
        "source_refs": ["source-a"],
        "mandatory_test_refs": ["test-a"],
        "template_ref": {"id": "template-a", "version": "1"},
        "group": "B",
        "severity": "BLOCK",
        "comparison": "equal",
        "tolerance": "0",
        "left": wide_tree(13),
        "right": constant(),
    }
    with pytest.raises(ValidationError, match="AST_MAX_NODES_EXCEEDED"):
        RuleDefinition.model_validate(rule)
