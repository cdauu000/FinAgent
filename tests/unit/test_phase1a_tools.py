import json
from pathlib import Path

import pytest

from finagent.contracts.errors import ProcessingError
from finagent.corpus.review_tools import runtime_output, supplied_report, write_new
from finagent.extraction.media import parse_media_result
from finagent.observability.profiling import OperationProfiler


def test_source_output_isolation_and_no_overwrite(tmp_path) -> None:
    (tmp_path / "data/public_reports").mkdir(parents=True)
    report = tmp_path / "data/public_reports/r.pdf"
    report.write_bytes(b"unit pdf")
    assert supplied_report(tmp_path, "data/public_reports/r.pdf") == report
    with pytest.raises(ProcessingError, match="SOURCE_OUTSIDE_SUPPLIED_REPORTS"):
        supplied_report(tmp_path, "data/public_reports/../../../secret.pdf")
    with pytest.raises(ProcessingError, match="REVIEW_OUTPUT_OUTSIDE_RUNTIME"):
        runtime_output(tmp_path, tmp_path / "data/public_reports/output")
    with pytest.raises(FileExistsError):
        write_new(report, "overwritten")
    assert report.read_bytes() == b"unit pdf"


def test_media_protocol_contamination_rejected() -> None:
    with pytest.raises(ProcessingError, match="WINDOWS_MEDIA_PROTOCOL_ERROR"):
        parse_media_result(b'System.VoidValueTypeParameter\n{"ok":true,"peak_working_set_bytes":1}')


def test_measurements_are_actual_safe_operation_records(tmp_path) -> None:
    profiler = OperationProfiler(tmp_path / "trace.jsonl")
    with profiler.measure("number_normalize"):
        allocated = bytearray(10000)
        assert len(allocated) == 10000
    with pytest.raises(ProcessingError, match="TEST_FAILURE"), profiler.measure("crop_export"):
        raise ProcessingError("TEST_FAILURE")
    rows = [json.loads(line) for line in profiler.trace.read_text().splitlines()]
    assert rows[0]["elapsed_ns"] > 0 and rows[0]["python_traced_peak_bytes"] >= 10000
    assert rows[0]["started_at"] and rows[1]["error_code"] == "TEST_FAILURE"
    assert not any("raw" in key or "value" in key for row in rows for key in row)


def test_corpus_checks_resolved_path_before_reading_bytes(tmp_path, monkeypatch) -> None:
    from finagent.corpus.inventory import inventory

    supplied = tmp_path / "data/public_reports"
    supplied.mkdir(parents=True)
    path = supplied / "escaped.pdf"
    path.write_bytes(b"do not read")
    original_resolve = Path.resolve
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self, *args, **kwargs: (
            tmp_path / "outside.pdf" if self == path else original_resolve(self, *args, **kwargs)
        ),
    )

    def must_not_read(source):
        raise AssertionError("source hash read before path confinement")

    monkeypatch.setattr("finagent.corpus.inventory.source_hash", must_not_read)
    with pytest.raises(ValueError, match="CORPUS_PATH_OUTSIDE_SUPPLIED_REPORTS"):
        inventory(tmp_path)


def test_media_helper_uses_fixed_code_and_does_not_inherit_provider_keys(
    tmp_path, monkeypatch
) -> None:
    import os
    from types import SimpleNamespace

    from finagent.extraction.media import WindowsMedia

    if os.name != "nt":
        pytest.skip("NOT_RUN: Windows subprocess adapter platform")
    monkeypatch.setenv("GROQ_API_KEY", "synthetic-secret-canary")
    monkeypatch.setenv("GOOGLE_API_KEY", "synthetic-secret-canary")
    monkeypatch.setattr("finagent.extraction.media.shutil.which", lambda name: "powershell.exe")

    def run(command, **kwargs):
        environment = kwargs["env"]
        assert "GROQ_API_KEY" not in environment and "GOOGLE_API_KEY" not in environment
        assert "-EncodedCommand" in command and "-ExecutionPolicy" not in command
        assert "user-input" not in command[-1]
        request = Path(environment["FINAGENT_MEDIA_REQUEST"])
        assert json.loads(request.read_text())["input_path"] == "user-input"
        return SimpleNamespace(returncode=0, stdout=b'{"ok":true,"peak_working_set_bytes":1}')

    monkeypatch.setattr("finagent.extraction.media.subprocess.run", run)
    assert WindowsMedia(tmp_path).call({"action": "inspect_pdf", "input_path": "user-input"}).ok
