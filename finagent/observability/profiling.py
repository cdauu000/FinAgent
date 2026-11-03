"""Local operation measurements, not OCR quality, benchmark selection or KPI evaluation."""

import ctypes
import json
import os
import time
import tracemalloc
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from finagent.ingestion.errors import ProcessingError


def working_set_bytes() -> int | None:
    if os.name != "nt":
        return None
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(Counters),
        wintypes.DWORD,
    ]
    if not psapi.GetProcessMemoryInfo(
        kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        return None
    return int(counters.WorkingSetSize)


@dataclass
class OperationMeasurement:
    span_id: str
    stage: str
    started_at: str
    elapsed_ns: int = 0
    cpu_ns: int = 0
    python_traced_peak_bytes: int = 0
    rss_before_bytes: int | None = None
    rss_after_bytes: int | None = None
    child_peak_working_set_bytes: int | None = None
    status: str = "RUNNING"
    error_code: str | None = None


class OperationProfiler:
    def __init__(self, trace: Path) -> None:
        self.trace = trace
        self.records: list[OperationMeasurement] = []
        trace.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def measure(self, stage: str) -> Iterator[OperationMeasurement]:
        if stage not in {
            "inventory",
            "pdf_inspect",
            "render_prepare",
            "crop_export",
            "ingestion",
            "number_normalize",
            "skew_estimate",
        }:
            raise ProcessingError("UNKNOWN_PROFILE_STAGE")
        record = OperationMeasurement(
            "span-" + uuid4().hex,
            stage,
            datetime.now(UTC).isoformat(),
            rss_before_bytes=working_set_bytes(),
        )
        tracing = tracemalloc.is_tracing()
        if tracing:
            raise ProcessingError("PROFILE_NESTING_NOT_SUPPORTED")
        tracemalloc.start()
        started, cpu = time.perf_counter_ns(), time.process_time_ns()
        try:
            yield record
            record.status = "COMPLETED"
        except BaseException as exc:
            record.status = "FAILED"
            record.error_code = exc.code if isinstance(exc, ProcessingError) else "UNEXPECTED_ERROR"
            raise
        finally:
            record.elapsed_ns = time.perf_counter_ns() - started
            record.cpu_ns = time.process_time_ns() - cpu
            record.python_traced_peak_bytes = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            record.rss_after_bytes = working_set_bytes()
            self.records.append(record)
            with self.trace.open("a", encoding="utf-8") as output:
                output.write(json.dumps(asdict(record), sort_keys=True) + "\n")
