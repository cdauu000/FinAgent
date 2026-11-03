import hashlib
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pytest

from finagent.ingestion.contracts import FileInput, PdfInspection
from finagent.ingestion.errors import ProcessingError
from finagent.ingestion.file_safety import inspect_file, inspect_office
from finagent.ingestion.service import IngestionJournal, LocalIngestionGateway
from finagent.jobs.memory import MemoryJobStore
from finagent.store.local_blob import LocalBlobStore
from finagent.store.models import BlobMetadata


class Inspector:
    def inspect_pdf(self, content: bytes) -> PdfInspection:
        return PdfInspection(page_count=2)


def request(key="key-a", name="report.txt", mime="text/plain") -> FileInput:
    return FileInput(filename=name, declared_mime=mime, idempotency_key=key)


def test_ingestion_idempotency_concurrent_dedup_tenant_and_restart_blob(
    tmp_path, processing_ctx
) -> None:
    blobs = LocalBlobStore(tmp_path / "blobs")
    jobs = MemoryJobStore()
    journal = IngestionJournal()
    service = LocalIngestionGateway(blobs, jobs, Inspector(), journal=journal)
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(
            pool.map(lambda _: service.submit(b"unit text", request(), processing_ctx), range(8))
        )
    assert len({r.document_id for r in receipts}) == 1 and len({r.job_id for r in receipts}) == 1
    with pytest.raises(ProcessingError, match="IDEMPOTENCY_BODY_CONFLICT"):
        service.submit(b"changed", request(), processing_ctx)
    duplicate = service.submit(b"unit text", request("key-b"), processing_ctx)
    assert duplicate.dedup_hit and duplicate.blob_ref == receipts[0].blob_ref
    other = processing_ctx.model_copy(update={"tenant_id": "tenant-b"})
    assert service.submit(b"unit text", request(), other).document_id != receipts[0].document_id
    with pytest.raises(ProcessingError, match="RESOURCE_NOT_FOUND"):
        blobs.open(receipts[0].blob_ref, other)
    restarted = LocalBlobStore(tmp_path / "blobs")
    with restarted.open(receipts[0].blob_ref, processing_ctx) as stream:
        assert stream.read() == b"unit text"
    body = next((tmp_path / "blobs").rglob(receipts[0].blob_ref + ".bin"))
    body.write_bytes(b"tampered")
    with pytest.raises(ProcessingError, match="BLOB_HASH_MISMATCH"):
        restarted.open(receipts[0].blob_ref, processing_ctx)


def test_blob_permission_hash_tier_and_purge_are_scoped_to_own_resource(
    tmp_path, processing_ctx
) -> None:
    store = LocalBlobStore(tmp_path)
    meta = BlobMetadata(
        tenant_id="tenant-a",
        source_tier="private",
        mime_type="text/plain",
        sha256=hashlib.sha256(b"a").hexdigest(),
    )
    with pytest.raises(ProcessingError, match="BLOB_HASH_MISMATCH"):
        store.put(io.BytesIO(b"b"), meta, processing_ctx)
    with pytest.raises(ProcessingError, match="TIER_DOWNGRADE"):
        store.put(
            io.BytesIO(b"a"), meta.model_copy(update={"source_tier": "public"}), processing_ctx
        )
    ref = store.put(io.BytesIO(b"a"), meta, processing_ctx)
    assert store.purge(ref, processing_ctx).deleted_refs == (ref,)
    with pytest.raises(ProcessingError, match="RESOURCE_NOT_FOUND"):
        store.open(ref, processing_ctx)


def test_file_mime_page_limit_scanner_and_name_are_checked() -> None:
    with pytest.raises(ProcessingError, match="MIME_MISMATCH"):
        inspect_file(b"text", request(name="evil.pdf", mime="application/pdf"), Inspector())
    with pytest.raises(ProcessingError, match="UNSAFE_FILENAME"):
        inspect_file(b"text", request(name="../evil.txt"), Inspector())
    with pytest.raises(ProcessingError, match="SCANNER_REQUIRED_UNAVAILABLE"):
        inspect_file(b"text", request(), Inspector(), scanner_required=True)

    class ManyPages:
        def inspect_pdf(self, content: bytes) -> PdfInspection:
            return PdfInspection(page_count=301)

    with pytest.raises(ProcessingError, match="PAGE_LIMIT"):
        inspect_file(b"%PDF-unit", request(name="x.pdf", mime="application/pdf"), ManyPages())


def archive(extra: dict[str, bytes]) -> bytes:
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as data:
        data.writestr("[Content_Types].xml", b"<Types/>")
        data.writestr("word/document.xml", b"<document/>")
        for name, value in extra.items():
            data.writestr(name, value)
    return target.getvalue()


@pytest.mark.parametrize(
    "extra",
    [
        {"../outside": b"bad"},
        {"word/vbaProject.bin": b"bad"},
        {
            "word/_rels/document.xml.rels": b'<Relationships><Relationship TargetMode="External" Target="https://x"/></Relationships>'
        },
        {"word/bad.xml": b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///x">]><x>&e;</x>'},
        {"word/bomb": b"0" * 100000},
    ],
)
def test_office_paths_macro_external_entity_and_zip_bomb_blocked(extra) -> None:
    with pytest.raises(ProcessingError):
        inspect_office(archive(extra))


def test_safe_office_is_inspected_without_evaluating_workbook_or_word() -> None:
    assert inspect_office(archive({})).endswith("wordprocessingml.document")
