import hashlib
import re
import threading
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from finagent.contracts.base import ExecutionContext, Identifier
from finagent.contracts.errors import ProcessingError
from finagent.contracts.geometry import Affine
from finagent.policy.contracts import Limits
from finagent.security.permissions import TIER_ORDER, authorize, require_tier
from finagent.store.models import BlobMetadata, BoundingBox, CropRef, PurgeReport
from finagent.store.ports import ImageOperations

MAX_FILE_BYTES = Limits().file_bytes


class LocalBlobStore:
    def __init__(
        self,
        root: Path,
        images: ImageOperations | None = None,
        transforms: dict[str, Affine] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.images = images
        self.transforms = transforms or {}
        self._lock = threading.RLock()

    def _directory(self, tenant_id: str) -> Path:
        path = self.root / hashlib.sha256(tenant_id.encode()).hexdigest()
        if not path.resolve().is_relative_to(self.root):
            raise ProcessingError("UNSAFE_BLOB_PATH")
        path.mkdir(exist_ok=True)
        return path

    def _paths(self, ref: str, ctx: ExecutionContext) -> tuple[Path, Path]:
        if not re.fullmatch(r"blob-[0-9a-f]{32}", ref):
            raise ProcessingError("RESOURCE_NOT_FOUND")
        directory = self._directory(ctx.tenant_id)
        body, meta = directory / (ref + ".bin"), directory / (ref + ".json")
        if not body.resolve().is_relative_to(self.root) or not meta.resolve().is_relative_to(
            self.root
        ):
            raise ProcessingError("UNSAFE_BLOB_PATH")
        return body, meta

    def metadata(self, ref: str, ctx: ExecutionContext) -> BlobMetadata:
        authorize(ctx, "document:read")
        body, meta = self._paths(ref, ctx)
        if not body.is_file() or not meta.is_file():
            raise ProcessingError("RESOURCE_NOT_FOUND")
        try:
            metadata = BlobMetadata.model_validate_json(meta.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ProcessingError("BLOB_METADATA_CORRUPT") from exc
        authorize(ctx, "document:read", metadata.tenant_id)
        return metadata

    def put(self, content: BinaryIO, metadata: BlobMetadata, ctx: ExecutionContext) -> Identifier:
        authorize(ctx, "document:write", metadata.tenant_id)
        require_tier(ctx, metadata.source_tier)
        chunks = []
        total = 0
        while chunk := content.read(64 * 1024):
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                raise ProcessingError("FILE_SIZE_LIMIT")
            chunks.append(chunk)
        data = b"".join(chunks)
        if hashlib.sha256(data).hexdigest() != metadata.sha256:
            raise ProcessingError("BLOB_HASH_MISMATCH")
        with self._lock:
            ref = "blob-" + uuid4().hex
            body, meta = self._paths(ref, ctx)
            with body.open("xb") as target:
                target.write(data)
            try:
                with meta.open("x", encoding="utf-8") as target_meta:
                    target_meta.write(metadata.model_dump_json())
            except OSError:
                body.unlink()
                raise
            return ref

    def open(self, ref: str, ctx: ExecutionContext) -> BinaryIO:
        metadata = self.metadata(ref, ctx)
        body, _ = self._paths(ref, ctx)
        stream = body.open("rb")
        if body.stat().st_size > MAX_FILE_BYTES:
            stream.close()
            raise ProcessingError("BLOB_SIZE_CORRUPT")
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != metadata.sha256:
            stream.close()
            raise ProcessingError("BLOB_HASH_MISMATCH")
        stream.seek(0)
        return stream

    def crop(
        self, ref: str, bbox: BoundingBox, transform_ref: str | None, ctx: ExecutionContext
    ) -> CropRef:
        authorize(ctx, "review:read")
        metadata = self.metadata(ref, ctx)
        if metadata.mime_type != "image/png" or self.images is None:
            raise ProcessingError("IMAGE_CROP_UNAVAILABLE")
        transformed = bbox
        if transform_ref is not None:
            if transform_ref not in self.transforms:
                raise ProcessingError("TRANSFORM_UNAVAILABLE")
            transformed = self.transforms[transform_ref].bounds(bbox)
        with self.open(ref, ctx) as stream:
            result = self.images.crop_bytes(stream.read(), transformed)
        tier = max((metadata.source_tier, ctx.source_tier), key=TIER_ORDER.__getitem__)
        crop_meta = BlobMetadata(
            tenant_id=ctx.tenant_id,
            source_tier=tier,
            sha256=hashlib.sha256(result).hexdigest(),
            mime_type="image/png",
        )
        import io

        new_ref = self.put(io.BytesIO(result), crop_meta, ctx)
        return CropRef(blob_ref=new_ref, original_bbox=bbox, transform_ref=transform_ref)

    def purge(self, ref: str, ctx: ExecutionContext) -> PurgeReport:
        authorize(ctx, "document:delete")
        self.metadata(ref, ctx)
        with self._lock:
            body, meta = self._paths(ref, ctx)
            body.unlink()
            meta.unlink()
        # Only this adapter's blob files; canonical/index/backup purge is a separate service.
        return PurgeReport(
            resource_ref=ref, deleted_refs=(ref,), pending_backup_expiry_refs=(), blocked_refs=()
        )
