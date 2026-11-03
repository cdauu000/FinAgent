from typing import BinaryIO, Protocol

from finagent.contracts.base import ExecutionContext, Identifier, Selection
from finagent.store.models import (
    AvailablePeriod,
    BlobMetadata,
    BoundingBox,
    CanonicalSnapshot,
    CropRef,
    NoteTableView,
    PurgeReport,
    SnapshotRef,
    StatementRevisionRef,
    ValidatedBundle,
    ValidationReport,
)


class CanonicalRepository(Protocol):
    def read_snapshot(self, selection: Selection, ctx: ExecutionContext) -> CanonicalSnapshot: ...

    def publish(
        self, validated_bundle: ValidatedBundle, expected_revision: int, ctx: ExecutionContext
    ) -> SnapshotRef: ...

    def revisions(
        self, statement_id: Identifier, ctx: ExecutionContext
    ) -> tuple[StatementRevisionRef, ...]: ...

    def list_periods(
        self, entity_id: Identifier, ctx: ExecutionContext
    ) -> tuple[AvailablePeriod, ...]: ...

    def get_note_table(self, ref: Identifier, ctx: ExecutionContext) -> NoteTableView: ...

    def get_validation_report(self, ref: Identifier, ctx: ExecutionContext) -> ValidationReport: ...


class BlobStore(Protocol):
    def put(
        self, content: BinaryIO, metadata: BlobMetadata, ctx: ExecutionContext
    ) -> Identifier: ...

    def open(self, ref: Identifier, ctx: ExecutionContext) -> BinaryIO: ...

    def crop(
        self,
        ref: Identifier,
        bbox: BoundingBox,
        transform_ref: Identifier | None,
        ctx: ExecutionContext,
    ) -> CropRef: ...

    def purge(self, ref: Identifier, ctx: ExecutionContext) -> PurgeReport: ...


class ImageOperations(Protocol):
    def crop_bytes(self, content: bytes, bbox: BoundingBox) -> bytes: ...
