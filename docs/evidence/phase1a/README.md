# Bằng chứng phạm vi Phase1a ngày03/11/2026

Phase0 vẫn INCOMPLETE/NO_GO; Phase1 chưa mở. Không đo OCR/KPI, không chọn engine hoặc gọi provider.

- [check-results.json](check-results.json): commands/stdout/exit code/time thực; [JUnit](pytest.xml)300 tests, gồm2 Windows integration thật.
- [summary.json](summary.json): corpus counts, source/snapshot SHA256, current88 review cases, official P0.10 evidence và các operation traces thực. Thời gian/RAM chỉ cho inspect một PDF28 trang, prepare một trang, hai crop; không phải benchmark/pipeline peak/KPI.
- [Manifest mới](../../../data/runtime/phase1a/20261103/verified/inventory/manifest.json), [inspection](../../../data/runtime/phase1a/20261103/verified/inventory/inspection.json), [trace](../../../data/runtime/phase1a/20261103/verified/inventory/trace.jsonl).
- [Gói ứng viên](../../../data/runtime/phase1a/20261103/verified/review/review.json), [trace crop](../../../data/runtime/phase1a/20261103/verified/review/trace.jsonl), hai ảnh [hiện tại](../../../data/runtime/phase1a/20261103/verified/review/B02-23-current-candidate.png)/[so sánh](../../../data/runtime/phase1a/20261103/verified/review/B02-23-comparative-candidate.png). Runtime local bị ignore, không được đếm lại vào corpus.

Lệnh đã chạy exit0, chạy tái lập phải đổi output sang thư mục mới:

```powershell
.\.venv\Scripts\python.exe -m eval.phase1a manifest --previous eval/datasets/manifest.json --output data/runtime/phase1a/20261103/verified/inventory
.\.venv\Scripts\python.exe -m eval.phase1a review --report data/public_reports/20260424_-_FPT_-_BCTC_rieng_Quy_1_nam_2026_1777344035.pdf --candidates eval/datasets/fpt-q1-2026-draft.json --frames docs/evidence/fpt_q1_2026/evidence.json --output data/runtime/phase1a/20261103/verified/review
```

Nguồn PDF và nhãn cũ không đổi. Gói80 candidates chỉ có2 bbox sẵn, nên xuất2 crop;78 ô còn NEEDS_BBOX, không tự tạo geometry hoặc approval. Ref raster metadata lấy kích thước thật từ evidence đã có, không dùng nominal DPI cũ để suy pixel. Chỉ đọc originals dưới data/public_reports; candidates/frames là metadata review.

Các thư mục review/review-fixed/review-dpi trước verified thuộc các lần thử lỗi giao thức/DPI, không phải output hoàn chỉnh. Regression đã giữ trong tests/fixtures/schema_review_cases.json. PROGRESS mô tả giới hạn native extraction, scanner, memory durability và NOT_RUN.
