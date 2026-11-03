import io
import stat
import zipfile
from pathlib import PurePosixPath
from typing import Literal
from xml.etree import ElementTree

from finagent.ingestion.contracts import FileInput, FileInspection, FileScanner, PdfInspector
from finagent.ingestion.errors import ProcessingError

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_PAGES = 300
MAX_EXPANDED_BYTES = 200 * 1024 * 1024
MAX_ARCHIVE_RATIO = 100
# TODO(verify): A64 technical entry bound, not a corpus or quality threshold.
MAX_ARCHIVE_ENTRIES = 10_000


class UnavailableScanner:
    def scan(self, content: bytes) -> Literal["UNAVAILABLE"]:
        return "UNAVAILABLE"


def safe_filename(filename: str) -> None:
    if (
        not filename
        or len(filename) > 255
        or filename.strip() != filename
        or filename in {".", ".."}
        or any(ch in filename for ch in "/\\:\x00")
        or any(ord(ch) < 32 for ch in filename)
    ):
        raise ProcessingError("UNSAFE_FILENAME")


def inspect_office(content: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise ProcessingError("ARCHIVE_ENTRY_LIMIT")
            names: set[str] = set()
            expanded = 0
            for info in infos:
                normalized = info.filename.replace("\\", "/")
                path = PurePosixPath(normalized)
                if path.is_absolute() or ".." in path.parts or ":" in normalized:
                    raise ProcessingError("UNSAFE_ARCHIVE_PATH")
                folded = normalized.casefold()
                if folded in names or info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                    raise ProcessingError("UNSAFE_ARCHIVE_ENTRY")
                names.add(folded)
                expanded += info.file_size
                if expanded > MAX_EXPANDED_BYTES or info.file_size > MAX_ARCHIVE_RATIO * max(
                    1, info.compress_size
                ):
                    raise ProcessingError("ARCHIVE_EXPANSION_LIMIT")
                if any(
                    word in folded
                    for word in ("vbaproject", "activex", "embeddings/", "externallinks/")
                ):
                    raise ProcessingError("OFFICE_ACTIVE_CONTENT")
                if not info.is_dir():
                    body = archive.read(info)  # bounded above; CRC checked; never executed
                    if folded.endswith((".xml", ".rels")):
                        try:
                            text = body.decode(
                                "utf-16"
                                if body.startswith((b"\xff\xfe", b"\xfe\xff"))
                                else "utf-8-sig"
                            )
                            if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
                                raise ProcessingError("XML_ENTITIES_FORBIDDEN")
                            xml = ElementTree.fromstring(text)
                        except (UnicodeError, ElementTree.ParseError) as exc:
                            raise ProcessingError("OFFICE_XML_INVALID") from exc
                        for node in xml.iter():
                            if node.attrib.get("TargetMode", "").casefold() == "external":
                                raise ProcessingError("OFFICE_EXTERNAL_LINK")
                            if any(
                                term in (node.text or "").upper() for term in ("DDEAUTO", "DDE ")
                            ):
                                raise ProcessingError("OFFICE_ACTIVE_CONTENT")
            if "[content_types].xml" not in names:
                raise ProcessingError("UNSUPPORTED_ARCHIVE")
            if "word/document.xml" in names and "xl/workbook.xml" not in names:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if "xl/workbook.xml" in names and "word/document.xml" not in names:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            raise ProcessingError("UNSUPPORTED_ARCHIVE")
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ProcessingError("INVALID_OFFICE_ARCHIVE") from exc


def inspect_file(
    content: bytes,
    request: FileInput,
    inspector: PdfInspector,
    scanner: FileScanner | None = None,
    *,
    scanner_required: bool = False,
) -> FileInspection:
    safe_filename(request.filename)
    if not content or len(content) > MAX_FILE_BYTES:
        raise ProcessingError("FILE_SIZE_LIMIT")
    pages = None
    if content.startswith(b"%PDF-"):
        if any(
            token in content for token in (b"/JavaScript", b"/JS ", b"/Launch", b"/EmbeddedFile")
        ):
            raise ProcessingError("PDF_ACTIVE_CONTENT")
        pdf = inspector.inspect_pdf(content)
        if pdf.password_protected:
            raise ProcessingError("PDF_ENCRYPTED")
        if pdf.page_count > MAX_PAGES:
            raise ProcessingError("PAGE_LIMIT")
        pages = pdf.page_count
        mime = "application/pdf"
    elif content.startswith(b"PK\x03\x04"):
        mime = inspect_office(content)
    else:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeError as exc:
            raise ProcessingError("UNSUPPORTED_MIME") from exc
        if "\x00" in text or any(ord(ch) < 32 and ch not in "\r\n\t" for ch in text):
            raise ProcessingError("UNSUPPORTED_MIME")
        if "<" in text or ">" in text:
            raise ProcessingError("HTML_UPLOAD_REQUIRES_TEXT_ROUTE")
        mime = "text/plain"
    extensions = {
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }
    if request.declared_mime != mime or not request.filename.casefold().endswith(extensions[mime]):
        raise ProcessingError("MIME_MISMATCH")
    status = scanner.scan(content) if scanner is not None else "UNAVAILABLE"
    if status == "REJECTED":
        raise ProcessingError("FILE_SCANNER_REJECTED")
    if status not in {"CLEAN", "UNAVAILABLE"} or scanner_required and status != "CLEAN":
        raise ProcessingError("SCANNER_REQUIRED_UNAVAILABLE")
    return FileInspection(
        mime_type=mime,
        size=len(content),
        page_count=pages,
        scanner_status=status,
        warnings=("SCANNER_UNAVAILABLE",) if status != "CLEAN" else (),
    )
