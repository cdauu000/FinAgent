from datetime import date
from typing import Literal

from pydantic import Field

from finagent.contracts.base import (
    Contract,
    Identifier,
    Money,
    PeriodKey,
    SafeInt,
    Scope,
    Sha256,
    Tier,
)


class PageAnnotation(Contract):
    physical_index: SafeInt = Field(ge=0)
    printed_label: str | None = None
    content_label: str
    route_label: Literal["native", "scan", "hybrid", "unknown"] = "unknown"
    difficulty: Literal["normal", "hard", "unknown"] = "unknown"


class DatasetEntry(Contract):
    id: Identifier
    local_path: str
    sha256: Sha256
    source_origin: Literal["owner_supplied"] = "owner_supplied"
    source_url: str | None = None
    source_date: date | None = None
    filename_date_hint: date | None = None
    source_evidence_ref: str | None = None
    terms_status: Literal["unknown", "permitted_verified", "denied"] = "unknown"
    terms_evidence_ref: str | None = None
    effective_tier: Tier = Tier.PRIVATE
    entity_id: Identifier | None = None
    group_id: Identifier | None = None
    scope: Scope | None = None
    period: PeriodKey | None = None
    industry: str | None = None
    audit_status: Literal["unknown", "unaudited", "reviewed", "audited"] = "unknown"
    pages: tuple[PageAnnotation, ...] = ()
    split: Literal["unassigned", "visible_regression", "train", "dev", "test"] = "unassigned"
    gold_path: str | None = None
    gold_approval_ref: Identifier | None = None
    missing: tuple[str, ...] = ()


class CorpusManifest(Contract):
    schema_version: Literal["corpus/1"] = "corpus/1"
    entries: tuple[DatasetEntry, ...]
    supplied_only: Literal[True] = True
    split_path: str | None = None


class GroupSplit(Contract):
    group_id: Identifier
    split: Literal["train", "dev", "test", "visible_regression", "unassigned"]


class SplitManifest(Contract):
    schema_version: Literal["split/1"] = "split/1"
    status: Literal["draft", "frozen"] = "draft"
    groups: tuple[GroupSplit, ...]
    holdout_entities: tuple[Identifier, ...] = ()
    seed: SafeInt | None = None
    reason: str


class RasterBox(Contract):
    x1: SafeInt = Field(ge=0)
    y1: SafeInt = Field(ge=0)
    x2: SafeInt = Field(gt=0)
    y2: SafeInt = Field(gt=0)
    dpi: SafeInt = Field(gt=0)
    raster_ref: str


class GoldCell(Contract):
    id: Identifier
    code: str
    concept_id: Identifier
    statement_type: Literal["B01", "B02", "B03", "B09"]
    period: PeriodKey
    scope: Scope
    physical_index: SafeInt = Field(ge=0)
    raw_text: str
    value: Money
    unit: Literal["VND", "count"] = "VND"
    bbox: RasterBox | None = None
    evidence_refs: tuple[str, ...]
    flags: tuple[Identifier, ...] = ()


class GoldDocument(Contract):
    schema_version: Literal["gold/1"] = "gold/1"
    document_sha256: Sha256
    status: Literal["draft", "approved"] = "draft"
    approver_ref: Identifier | None = None
    cells: tuple[GoldCell, ...]
    source_conflicts: tuple[Identifier, ...] = ()
