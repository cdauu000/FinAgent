"""Canonical/1 drafts: source observations remain distinct from admitted facts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from finagent.contracts.base import (
    ChunkText,
    CitationText,
    Contract,
    ExactDecimal,
    FlowPeriod,
    Identifier,
    Money,
    NonEmpty,
    PageText,
    PeriodKey,
    RegistryRef,
    SafeInt,
    Scope,
    Selection,
    Sha256,
    StockPeriod,
    Tier,
    TrustGrade,
    Verdict,
    VerificationStatus,
)


class TenantRecord(Contract):
    id: Identifier
    tenant_id: Identifier
    source_tier: Tier = Tier.PRIVATE
    created_at: datetime
    pipeline_version: NonEmpty


class Entity(TenantRecord):
    legal_name: NonEmpty
    aliases: tuple[NonEmpty, ...] = ()
    ticker: NonEmpty | None = None
    industry_label: Identifier | None = None
    industry_evidence_refs: tuple[Identifier, ...] = ()


class Document(TenantRecord):
    entity_id: Identifier | None = None
    filename: NonEmpty
    source_kind: Literal["upload", "official_url", "text"]
    source_url: str | None = None
    sha256: Sha256
    mime_type: NonEmpty
    blob_ref: Identifier
    language: Literal["vi", "en", "bilingual", "unknown"] = "unknown"
    page_count: SafeInt = Field(ge=0)
    public_evidence_refs: tuple[Identifier, ...] = ()
    job_ref: Identifier

    @model_validator(mode="after")
    def public_requires_evidence(self) -> Self:
        if self.source_tier == Tier.PUBLIC and not self.public_evidence_refs:
            raise ValueError("PUBLIC_EVIDENCE_REQUIRED")
        return self


class BoundingBox(Contract):
    x1: float = Field(ge=0, allow_inf_nan=False)
    y1: float = Field(ge=0, allow_inf_nan=False)
    x2: float = Field(gt=0, allow_inf_nan=False)
    y2: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("INVALID_BOUNDING_BOX")
        return self


class Page(TenantRecord):
    document_id: Identifier
    physical_index: SafeInt = Field(ge=0)
    printed_label: str | None = None
    width: float = Field(gt=0, allow_inf_nan=False)
    height: float = Field(gt=0, allow_inf_nan=False)
    rotation: Literal[0, 90, 180, 270] = 0
    page_kind: Literal["native", "scan", "hybrid", "unknown"]
    raster_ref: Identifier | None = None
    transform_ref: Identifier | None = None
    native_text: PageText | None = None


class TableColumn(Contract):
    id: Identifier
    role: Literal["code", "note", "label", "value"]
    period: PeriodKey | None = None


class Table(TenantRecord):
    document_id: Identifier
    page_refs: tuple[Identifier, ...] = Field(min_length=1)
    columns: tuple[TableColumn, ...] = Field(min_length=1)
    statement_type: Literal["B01", "B02", "B03", "B09", "unknown"]
    note_number: str | None = None
    unit_scale: Literal[1, 1000, 1000000, 1000000000] | None = None
    unit_evidence_refs: tuple[Identifier, ...] = ()
    complete: bool = False


class SourceCell(TenantRecord):
    table_id: Identifier
    page_id: Identifier
    row_index: SafeInt = Field(ge=0)
    column_id: Identifier
    role: Literal["code", "note", "label", "value"]
    raw_text: PageText
    bbox: BoundingBox
    candidate_refs: tuple[Identifier, ...] = ()


class Reading(Contract):
    engine: Identifier
    version: NonEmpty
    raw_text: PageText
    kind: Literal["native", "ocr", "human"]
    confidence: float | None = Field(default=None, ge=0, le=1)


class Provenance(TenantRecord):
    document_id: Identifier
    document_sha256: Sha256
    page_id: Identifier
    physical_index: SafeInt = Field(ge=0)
    printed_page: str | None = None
    bbox: BoundingBox
    source_cell_ids: tuple[Identifier, ...] = Field(min_length=1)
    readings: tuple[Reading, ...] = Field(min_length=1)
    chosen_reading: SafeInt = Field(ge=0)
    trust_grade: TrustGrade
    validation_run_refs: tuple[Identifier, ...] = ()
    review_action_refs: tuple[Identifier, ...] = ()
    transform_ref: Identifier | None = None

    @model_validator(mode="after")
    def chosen_exists(self) -> Self:
        if self.chosen_reading >= len(self.readings):
            raise ValueError("UNKNOWN_READING")
        return self


class MonetaryValue(Contract):
    kind: Literal["money"] = "money"
    currency: Literal["VND"] = "VND"
    value: Money


class CountValue(Contract):
    kind: Literal["count"] = "count"
    value: Money
    unit: Identifier


class DecimalValue(Contract):
    kind: Literal["ratio"] = "ratio"
    value: ExactDecimal
    representation: Literal["fraction"] = "fraction"
    scale: SafeInt = Field(default=0, ge=0, le=38)
    rounding_mode: Literal["ROUND_HALF_UP"] = "ROUND_HALF_UP"
    display_kind: Literal["decimal", "percent"] = "decimal"

    @model_validator(mode="before")
    @classmethod
    def infer_scale(cls, data: object) -> object:
        from finagent.contracts.base import exact_decimal

        if isinstance(data, dict) and "value" in data and "scale" not in data:
            value = exact_decimal(data["value"])
            exponent = value.as_tuple().exponent
            if isinstance(exponent, int):
                return {**data, "scale": max(0, -exponent)}
        return data

    @model_validator(mode="after")
    def scale_matches_fraction(self) -> Self:
        exponent = self.value.as_tuple().exponent
        if not isinstance(exponent, int) or self.scale != max(0, -exponent):
            raise ValueError("DECIMAL_SCALE_MISMATCH")
        return self


FinancialValue = Annotated[MonetaryValue | CountValue | DecimalValue, Field(discriminator="kind")]


class Dimensions(Contract):
    counterparty_id: Identifier | None = None
    relationship: Literal["related", "unrelated", "unknown"] | None = None
    debt_type: Literal["loan", "bond", "lease", "other"] | None = None
    maturity: Literal["current", "noncurrent"] | None = None
    measurement_basis: Literal["gross", "net"] | None = None
    subcategory: Identifier | None = None


class LineItem(TenantRecord):
    statement_id: Identifier
    statement_revision: SafeInt = Field(ge=1)
    source_column_id: Identifier
    code: Annotated[str, Field(pattern=r"^[0-9]+[a-z]?$", min_length=1)]
    canonical_id: Identifier
    label_vi: NonEmpty
    label_en: str | None = None
    presence: Literal["value", "explicit_zero", "derived_zero", "missing"]
    financial_value: FinancialValue | None = None
    original_display: str | None = None
    original_unit_scale: Literal[1, 1000, 1000000, 1000000000] | None = None
    is_total: bool = False
    is_memo: bool = False
    parent_id: Identifier | None = None
    dimensions: Dimensions = Dimensions()
    trust_grade: TrustGrade
    provenance_refs: tuple[Identifier, ...] = Field(min_length=1)
    derivation_ref: Identifier | None = None

    @model_validator(mode="after")
    def presence_matches_value(self) -> Self:
        if (self.presence == "missing") != (self.financial_value is None):
            raise ValueError("PRESENCE_VALUE_MISMATCH")
        if self.presence in {"explicit_zero", "derived_zero"} and (
            self.financial_value is None or self.financial_value.value != 0
        ):
            raise ValueError("ZERO_VALUE_REQUIRED")
        if self.presence == "derived_zero" and self.derivation_ref is None:
            raise ValueError("DERIVED_ZERO_LINEAGE_REQUIRED")
        return self


class Statement(TenantRecord):
    schema_version: Literal["canonical/1"] = "canonical/1"
    revision: SafeInt = Field(ge=1)
    document_id: Identifier
    entity_id: Identifier
    statement_family: Identifier = "corporate"
    template_ref: RegistryRef
    statement_type: Literal["B01", "B02", "B03", "B09"]
    scope: Scope
    period: PeriodKey
    audit_status: Literal["audited", "reviewed", "unaudited", "unknown"] = "unknown"
    audit_evidence_refs: tuple[Identifier, ...] = ()
    currency: Literal["VND"] = "VND"
    unit_scale: Literal[1, 1000, 1000000, 1000000000]
    verification_status: VerificationStatus
    line_refs: tuple[Identifier, ...]
    complete: bool
    supersedes_ref: Identifier | None = None

    @model_validator(mode="after")
    def correct_period_kind(self) -> Self:
        if self.statement_type == "B01" and not isinstance(self.period, StockPeriod):
            raise ValueError("BALANCE_SHEET_REQUIRES_STOCK")
        if self.statement_type in {"B02", "B03"} and not isinstance(self.period, FlowPeriod):
            raise ValueError("FLOW_STATEMENT_REQUIRES_FLOW")
        if self.audit_status in {"audited", "reviewed"} and not self.audit_evidence_refs:
            raise ValueError("AUDIT_EVIDENCE_REQUIRED")
        return self


class ValidationIssue(TenantRecord):
    statement_id: Identifier
    rule_ref: RegistryRef
    outcome: Literal["PASS", "FAIL", "NOT_EVALUATED", "NOT_APPLICABLE"]
    severity: Literal["BLOCK", "WARN", "INFO"]
    origin: Literal["READING", "SOURCE", "CLASSIFICATION", "UNKNOWN"]
    affected_refs: tuple[Identifier, ...]
    discrepancy: ExactDecimal | None = None
    tolerance: ExactDecimal
    reason_code: Identifier
    explanation_evidence_refs: tuple[Identifier, ...] = ()


class DerivedFact(TenantRecord):
    definition_ref: RegistryRef
    input_fact_refs: tuple[Identifier, ...] = Field(min_length=1)
    financial_value: FinancialValue
    period: PeriodKey
    warning_codes: tuple[Identifier, ...] = ()


class StatementRevisionRef(Contract):
    statement_id: Identifier
    revision: SafeInt = Field(ge=1)


class CanonicalSnapshot(TenantRecord):
    schema_version: Literal["canonical/1"] = "canonical/1"
    selection: Selection
    statement_refs: tuple[StatementRevisionRef, ...] = Field(min_length=1)
    admitted_fact_refs: tuple[Identifier, ...]
    ruleset_ref: RegistryRef
    policy_ref: RegistryRef
    pack_ref: RegistryRef
    content_hash: Sha256
    unavailable_refs: tuple[Identifier, ...] = ()
    conflict_refs: tuple[Identifier, ...] = ()


class ReviewAction(TenantRecord):
    case_id: Identifier
    expected_revision: SafeInt = Field(ge=1)
    reviewer_id: Identifier
    action: Literal["confirm_reading", "correct_reading", "acknowledge_source_conflict"]
    before_value: FinancialValue | None = None
    after_value: FinancialValue | None = None
    reason: NonEmpty
    idempotency_key: Identifier
    resulting_revision: SafeInt = Field(ge=1)


class ReviewCase(TenantRecord):
    statement_ref: StatementRevisionRef
    crop_refs: tuple[Identifier, ...]
    candidate_refs: tuple[Identifier, ...]
    issue_refs: tuple[Identifier, ...]
    status: Literal["open", "resolved", "source_conflict_acknowledged"]
    action_refs: tuple[Identifier, ...] = ()


class EvidenceChunk(TenantRecord):
    document_id: Identifier
    document_revision: SafeInt = Field(ge=1)
    text: ChunkText
    heading_ref: Identifier | None = None
    note_ref: Identifier | None = None
    provenance_refs: tuple[Identifier, ...]
    entity_id: Identifier
    scope: Scope
    period: PeriodKey
    trust_grade: TrustGrade
    numeric_fact_refs: tuple[Identifier, ...]
    embedding_model_ref: Identifier | None = None
    index_version: str


class SourceQuote(Contract):
    evidence_ref: Identifier
    text: CitationText
    provenance_refs: tuple[Identifier, ...] = Field(min_length=1)


class NumericClaim(Contract):
    claim_id: Identifier
    financial_value: FinancialValue
    entity_id: Identifier
    scope: Scope
    period: PeriodKey
    variant_id: Identifier
    definition_ref: RegistryRef | None = None
    evidence_refs: tuple[Identifier, ...] = Field(min_length=1)
    calculation_ref: Identifier | None = None
    allowed_display_strings: tuple[NonEmpty, ...] = Field(min_length=1)
    warning_codes: tuple[Identifier, ...] = ()


class AnalysisRecord(TenantRecord):
    snapshot_ref: Identifier
    policy_ref: RegistryRef
    claims: tuple[NumericClaim, ...]
    verdict: Verdict
    warning_codes: tuple[Identifier, ...]
    assumption_ids: tuple[Identifier, ...]
    missing_refs: tuple[Identifier, ...]
    verifier_receipt_ref: Identifier | None = None
    trace_ref: Identifier


class CanonicalCatalog(Contract):
    """Schema root for review; no in-memory database or persistence implementation."""

    entities: tuple[Entity, ...] = ()
    documents: tuple[Document, ...] = ()
    pages: tuple[Page, ...] = ()
    tables: tuple[Table, ...] = ()
    cells: tuple[SourceCell, ...] = ()
    provenance: tuple[Provenance, ...] = ()
    statements: tuple[Statement, ...] = ()
    lines: tuple[LineItem, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()
    derived: tuple[DerivedFact, ...] = ()
    snapshots: tuple[CanonicalSnapshot, ...] = ()
    review_cases: tuple[ReviewCase, ...] = ()
    review_actions: tuple[ReviewAction, ...] = ()
    evidence_chunks: tuple[EvidenceChunk, ...] = ()
    source_quotes: tuple[SourceQuote, ...] = ()
    analysis_records: tuple[AnalysisRecord, ...] = ()
    validated_bundle: ValidatedBundle | None = None
    snapshot_ref: SnapshotRef | None = None
    available_periods: tuple[AvailablePeriod, ...] = ()
    note_table_view: NoteTableView | None = None
    validation_report: ValidationReport | None = None
    blob_metadata: BlobMetadata | None = None
    crop_ref: CropRef | None = None
    purge_report: PurgeReport | None = None


class ValidatedBundle(Contract):
    tenant_id: Identifier
    source_tier: Tier
    statements: tuple[Statement, ...]
    lines: tuple[LineItem, ...]
    issues: tuple[ValidationIssue, ...]
    validation_run_refs: tuple[Identifier, ...]


class SnapshotRef(Contract):
    tenant_id: Identifier
    snapshot_id: Identifier
    content_hash: Sha256


class AvailablePeriod(Contract):
    period: PeriodKey
    scope: Scope
    statement_type: Literal["B01", "B02", "B03", "B09"]
    statement_ref: StatementRevisionRef


class NoteTableView(Contract):
    table: Table
    facts: tuple[LineItem, ...]


class ValidationReport(Contract):
    statement_ref: StatementRevisionRef
    issues: tuple[ValidationIssue, ...]
    ruleset_ref: RegistryRef


class BlobMetadata(Contract):
    tenant_id: Identifier
    source_tier: Tier
    sha256: Sha256
    mime_type: NonEmpty


class CropRef(Contract):
    blob_ref: Identifier
    original_bbox: BoundingBox
    transform_ref: Identifier | None = None


class PurgeReport(Contract):
    resource_ref: Identifier
    deleted_refs: tuple[Identifier, ...]
    pending_backup_expiry_refs: tuple[Identifier, ...]
    blocked_refs: tuple[Identifier, ...]


CanonicalCatalog.model_rebuild()
