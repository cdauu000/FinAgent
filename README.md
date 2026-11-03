# FinAgent backend

**14 nhóm schema frozen; Phase0 INCOMPLETE/NO_GO. Ngoại lệ Phase1a đã được cho phép và bàn giao; dừng chờ corpus, chưa mở Phase1 đầy đủ.** Đây là nền tảng cùng ingestion/render/normalizer/công cụ local, chưa phải backend hoàn chỉnh. [PLAN](docs/PLAN.md), [kiến trúc và baseline](docs/ARCHITECTURE.md), [kết quả thật](docs/PROGRESS.md) là hồ sơ chính.

Python≥3.11; môi trường đã kiểm tra tại máy là Python3.12.10. Cài dependencies trong virtualenv của workspace, không cài global hoặc hooks:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-lock.txt -e ".[dev]"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy finagent eval
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m finagent.schema_catalog --check
```

Linux/macOS dùng `.venv/bin/python` hoặc kích hoạt virtualenv rồi `make check`. Makefile là tùy chọn; các lệnh Python trên tương đương. `requirements-lock.txt` ghi các version dependency đã resolve trên Windows/Python3.12; kết quả nền tảng khác chỉ được xác nhận sau CI chạy thật.

Pre-commit chỉ chạy thủ công; không `pre-commit install`:

```powershell
$env:PATH = (Join-Path (Get-Location) '.venv\Scripts') + [IO.Path]::PathSeparator + $env:PATH
$env:PRE_COMMIT_HOME = (Join-Path (Get-Location) '.cache\pre-commit')
.\.venv\Scripts\python.exe -m pre_commit run --all-files --hook-stage manual --verbose
```

Máy này hiện có `.git` do CodexSandboxOffline tạo, khác chủ sở hữu ADMIN; Windows không cho đổi owner bằng quyền hiện có. Lần kiểm tra manual dùng `safe.directory=C:/FinAgent` **chỉ trong tiến trình kiểm tra**, không sửa Git config toàn cục hay ACL. Khi gặp `dubious ownership`, có thể dùng scope tạm trong terminal của chính dự án (đóng terminal sẽ mất):

```powershell
$finagentGitEntries = 0
if ($env:GIT_CONFIG_COUNT) { $finagentGitEntries = [int]$env:GIT_CONFIG_COUNT }
[Environment]::SetEnvironmentVariable("GIT_CONFIG_KEY_$finagentGitEntries", 'safe.directory', 'Process')
[Environment]::SetEnvironmentVariable("GIT_CONFIG_VALUE_$finagentGitEntries", (Get-Location).Path.Replace('\', '/'), 'Process')
$env:GIT_CONFIG_COUNT = [string]($finagentGitEntries + 1)
```

Scope này chỉ tin cậy repository của dự án, không dùng wildcard; vấn đề ownership ở IDE vẫn cần xử lý bằng quyền quản trị phù hợp. Không tự đổi cấu hình toàn cục.

Baseline hiện hành ở [schemas/frozen](schemas/frozen/manifest.json), có SHA256/thời điểm/approval/Git commit nếu có. `--check` kiểm frozen và current regressions; writer draft bị khóa. [Draft cũ](schemas/draft/manifest.json) giữ lịch sử duyệt. Không cập nhật baseline/oracle để giấu lỗi.

Review R1–R7 giữ tại [tóm tắt14 nhóm](docs/SCHEMA_REVIEW_SUMMARY.md); [validator/OpenAPI](docs/OPENAPI.md), [OpenAPI JSON](docs/openapi.json). Cùng major chỉ thêm DTO/optional fields; finite enum đều closed, extensible rỗng; breaking cần major/ADR/migration/full snapshots. Canonical/1 có cửa sổ ADR/hash/diff trước first real persistence P2.01; [lifecycle](schemas/lifecycle/canonical-1.json) hiện chưa ghi thật. A61 đã duyệt, không truncate dữ liệu để vừa trần.

```powershell
.\.venv\Scripts\python.exe -m uvicorn finagent.api.app:create_app --factory
```

API hiện chỉ có `/health` và `/health/ready`: liveness trả200 nhưng readiness503 vì persistence chưa triển khai. Không có giao diện hoặc business endpoints. Worker vẫn skeleton, chưa tiêu thụ jobs. Guard module có tests cục bộ, chưa được ghép thành Agent/renderer/Verifier.

Compose có PostgreSQL/pgvector, Redis và profiles api/worker. Chưa được kiểm tra build/run trên máy hiện tại vì không có Docker; CI có bước `docker compose ... config`. Không coi YAML parse là kiểm tra Compose hoặc integration thật. Không tự cài Docker/Make/Postgres/Redis.

Không có provider adapter hoạt động, không gọi provider hay đọc dev key cho runtime. `.env.example` chỉ placeholders. [P0.10 official review](docs/PROVIDER_REVIEW.md) có checked_at/URL; account/live/token-copy NOT_RUN. Không dùng mục20 để điền quota/terms. Model/prompts registry empty draft, chỉ đọc qua gate tập trung.

[Config P0.06](docs/PHASE0_CONFIG.md), [corpus card](eval/datasets/DATASET_CARD.md): hiện1 real report,0 complete manifests,0 approved gold; thiếu≥30/≥10. Không thu thập thêm hoặc nhân mẫu.

```powershell
.\.venv\Scripts\python.exe -m eval.run --suite baseline --dataset eval/datasets/manifest.json --output eval/runs/phase0-baseline
```

Baseline trả exit2/NO_GO khi chưa đủ nghiệm thu; không coi exit2 này là crash hoặc sửa ngưỡng để thành0. K01/K16 có inventory thật, các KPI chưa có pipeline/cohort không có giá trị giả. Suite OCR/analytics/Agent chưa triển khai sẽ ghi NOT_RUN. Fraction scorer và comparator có unit fixtures, không thay chất lượng backend.

Ca hồi quy đính chính nguồn FPT có [ảnh crop và metadata](docs/evidence/fpt_q1_2026/README.md); chúng không thay gold corpus approved hoặc chứng minh độ chính xác OCR/S8/analytics.

Phase1a: `LocalIngestionGateway`, `LocalBlobStore`, `MemoryJobStore`, router theo tín hiệu từng trang, Windows render/rotation/deskew/crop, S5 vi-VN và OperationProfiler có kiểm thử. Chưa có native text library hoặc OCR engine. Windows adapter chỉ dùng hệ điều hành sẵn có; nền tảng khác chưa xác nhận. API/worker pipeline vẫn chưa ghép ở phase này.

Công cụ chỉ đọc originals trong data/public_reports, ghi **output mới** dưới data/runtime, không tải thêm/copy corpus, không overwrite manifest/gold. Manifest giữ source/date/terms unknown; không tự lấy ngày từ filename. Với ảnh ứng viên, candidates và frames là metadata người duyệt cung cấp, không phải nguồn báo cáo mới. `bbox.raster_ref` phải khớp reference raster trong frames có kích thước thật; thiếu bbox thì giữ NEEDS_BBOX. Bổ sung bbox/metadata ở bản nhãn dự thảo mới rồi chạy lại; công cụ không tạo approval.

```powershell
.\.venv\Scripts\python.exe -m eval.phase1a manifest --previous eval/datasets/manifest.json --output data/runtime/my-new-inventory
.\.venv\Scripts\python.exe -m eval.phase1a review --report data/public_reports/20260424_-_FPT_-_BCTC_rieng_Quy_1_nam_2026_1777344035.pdf --candidates eval/datasets/fpt-q1-2026-draft.json --frames docs/evidence/fpt_q1_2026/evidence.json --dpi 300 --output data/runtime/my-new-review
```

Mỗi lần dùng thư mục output mới. `review.json` kèm crop PNG, ứng viên, source hash/tier và transform; trace.jsonl chỉ wall/process CPU/Python allocation peak/RSS trước-sau/helper working set, không phải OCR benchmark/KPI. Lượt bàn giao giữ80 candidates,2 crop thật,78 NEEDS_BBOX,0 gold approval; xem đường dẫn artifact trong PROGRESS. Bộ hình kẻ tổng hợp chỉ là unit/integration fixture hình học, không tăng số báo cáo corpus.
