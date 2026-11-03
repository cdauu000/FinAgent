# Tiến độ và bằng chứng FinAgent

## 03/11/2026 — Bàn giao phạm vi Phase1a, dừng chờ corpus

**SCHEMAS_FROZEN / PHASE0_INCOMPLETE / NO_GO. Ngoại lệ Phase1a đã thực hiện phần được phép; Phase1 đầy đủ CHƯA MỞ. DỪNG chờ corpus và xác nhận của chủ dự án.** Không tự nghiệm thu Phase0, không chạy cổng GO/NO-GO1.

### Xác nhận P0.10 trước khi bắt đầu

Đã có bằng chứng đọc tài liệu chính thức Groq và Google AI Studio/Gemini, **checked_at=2026-11-02T10:53:39Z**,9 nguồn với URL/trạng thái tại [official review JSON](../eval/providers/official-review-2026-11-02.json) và [bản đọc](PROVIDER_REVIEW.md). Đây là phần public docs không cần khóa; không bị chặn bởi mạng trong lần đọc đã lưu. Lượt Phase1a đối chiếu lại hồ sơ đó, không ghi thành một lần kiểm tra terms/account mới. Không lấy quota/terms từ thiết kế§20, không thêm model/route/quota/terms chưa xác minh vào registry. Provider calls=0; account console/live/token-copy vẫn NOT_RUN vì chưa có quyền/khóa.

### Phần đã triển khai và giới hạn

| Phần | Bằng chứng thực tế | Trạng thái trong ngoại lệ |
| --- | --- | --- |
| P1.01 | [Ingestion](../finagent/ingestion/service.py) và FileInput/Receipt/PdfInspector/FileScanner; actual MIME/hash/page/office archive/XML/macro guards, scanner-required fail-closed; URL check public DNS/pinned IP/TLS hostname/redirect/deadline/body; local blob hash/tenant/tier/crop/purge; job memory lease/checkpoint/retry/cancel/idempotency | Đã triển khai phần service local, tests offline và ingestion FPT thật. Scanner hiện UNAVAILABLE có warning; PDF lexical active-content check chỉ heuristic. API/business worker/DB/Redis/purge toàn derivatives và production encryption chưa triển khai, không báo production-ready |
| P1.02 phần được phép | [Router](../finagent/router/pages.py) từng trang từ PageFeatures, không dùng signature-only text làm native body; [WindowsMedia](../finagent/extraction/media.py)/[preprocessor](../finagent/extraction/preprocess.py) inspect/render300–400 DPI, original/processed, xoay và deskew explicit, affine thuận/nghịch; crop/bounds/source hash/tier | Render/geometry đã chạy thật. **PARTIAL đối với P1.02 toàn bộ:** native text extraction NOT_RUN vì không có library; router tín hiệu giả không chứng minh đã phân loại FPT native/scan. Thiếu orientation180° phải review, projection score chưa calibration. Không chọn OCR engine |
| P1.05 S5 | [Normalizer](../finagent/extraction/numbers.py) vi-VN groups3/dấu phẩy/ngoặc/minus/scale/zero/missing/role/unit, integer/Decimal không float, output financial_eligible=false | S5 độc lập engine đã kiểm. Chưa S4 OCR candidates/disagreement, S8/repair/canonical admission; candidate đọc sai nhưng format hợp lệ vẫn giữ để validation sau, không sửa theo oracle |
| Harness thao tác | [OperationProfiler](../finagent/observability/profiling.py) có wall/process CPU/Python allocation peak/RSS trước-sau/helper peak/timestamp/span/safe error; local traces từ inspect/render/crop thực | Chỉ đo thao tác đã chạy, không benchmark/chọn engine, không peak RSS toàn pipeline hoặc KPI. Chạy tuần tự, không nesting |
| Corpus/review tools | [CLI](../eval/phase1a.py), [implementation](../finagent/corpus/review_tools.py), hướng dẫn README; chỉ đọc originals resolve trong data/public_reports và ghi output mới dưới data/runtime, không overwrite source/gold | Manifest mới cho1 báo cáo/28 trang. Review giữ80 candidates, xuất2 crop có bbox,78 NEEDS_BBOX,0 gold approval; không bịa bbox/nguồn/date/terms |

Các interfaces/call paths/DTO bổ sung được ghi ở ARCHITECTURE§14, phạm vi PLAN§3.1, ca kiểm TEST_PLAN§9. Không sửa14 nhóm/28 snapshots frozen hoặc canonical lifecycle; chưa có canonical publish/first real write. **A64 mới: PROPOSED** cho triage/resource/geometry/job/DNS bounds và giới hạn adapter; không tự coi là approved financial thresholds hoặc kết quả calibration.

### Kết quả kiểm tra thật

[Commands/stdout/exit status](evidence/phase1a/check-results.json), [JUnit](evidence/phase1a/pytest.xml), [tổng hợp hash/corpus/trace/counts](evidence/phase1a/summary.json), [hướng dẫn bằng chứng](evidence/phase1a/README.md).

| Check | Kết quả thật cuối lượt |
| --- | --- |
| python -m ruff check . | PASS, exit0 |
| python -m ruff format --check . | PASS,105 files |
| python -m mypy finagent eval | PASS,62 source files |
| python -m pytest --junitxml=docs/evidence/phase1a/pytest.xml | **300 passed**,0 failed/errors/skips;8,49s trong lượt lưu JUnit, gồm2 integration Windows chạy thật |
| python -m finagent.schema_catalog --check | PASS,14 versions/frozen=true;28 snapshot hashes giữ nguyên |
| Nguồn và review archive | Sáu nguồn gốc gồm PDF/CLAUDE/đặc tả/ratios/Gateway design khớp hash READING_NOTES; archive59 ca lúc freeze giữ nguyên. Current88 ca (29 đúng/59 sai),10 ca sai mới sau freeze |

Các ca mới kiểm tenant/idempotency/concurrency, ZIP/XML/SSRF/DNS/pinning, checkpoint stale/invalid, số38 chữ số và giữ nguồn sai định dạng hợp lệ, affine/rotation/bbox, renderer/helper không kế thừa keys. Integration dùng báo cáo thật và hình đường kẻ tổng hợp riêng để kiểm góc, không đăng ký hình tổng hợp vào corpus hoặc tính OCR accuracy. Toàn bộ golden FPT source-correction tests vẫn đạt; không sửa oracle hoặc bridge CF04/TM18.

Hai lỗi khi chạy crop đầu đã được sửa và giữ regression: WinRT await-action ghi VoidValueTypeParameter trước JSON; host LogicalDpi120 làm raster lệch kích thước nominal. Adapter nay suppress void output, bù DIP theo DPI và dùng PNG IHDR thực cho geometry; lệch ngoài lượng tử cho phép vẫn chặn. Đã xem crop mã23 hiện tại **97.623.991.644** và so sánh **73.476.847.438**, khớp bằng chứng đã có; không dùng các số này để chỉnh normalizer. Lỗi mypy annotations và Ruff import/format ban đầu đã sửa, chạy lại đạt. Emitter bằng chứng tạm từng lỗi cp1252 khi in tên Việt và chép nhầm một ký tự hash ratios; đã đối chiếu READING_NOTES/sửa emitter, không sửa nguồn hoặc expected financial value. Kết quả test đã lưu giữ nguyên.

### Artifacts công cụ và trạng thái corpus

Hai lệnh CLI đã chạy exit0 bằng phiên bản cuối, outputs tại [inventory](../data/runtime/phase1a/20261103/verified/inventory/manifest.json) và [review.json](../data/runtime/phase1a/20261103/verified/review/review.json). [Crop mã23 kỳ này](../data/runtime/phase1a/20261103/verified/review/B02-23-current-candidate.png), [kỳ so sánh](../data/runtime/phase1a/20261103/verified/review/B02-23-comparative-candidate.png); trace.jsonl nằm cạnh mỗi output và được tổng hợp trong summary. Thư mục runtime bị Git ignore, không phải corpus mới; artifacts cũ và bản nhãn gốc không bị ghi đè. Các lần xuất lỗi trước giữ riêng, không tính là gói hoàn chỉnh.

**Hiện1 báo cáo thật;0 manifest đủ nguồn/ngày/điều khoản;0 gold approved. CHƯA đạt≥30 complete manifests và≥10 gold.**80 ô ứng viên,2 crop hay các bản render không được đếm thành báo cáo/nhãn vàng. Không tải thêm hoặc nhân dữ liệu. Công cụ chỉ tạo bản nháp để người duyệt bổ sung metadata/bbox và quyết định approval.

### NOT_RUN và việc còn chờ

Giữ **NOT_RUN:** provider live, account limits/terms account-specific, token-copy; Docker/build/compose, Postgres, Redis, hosted CI và Linux/Python3.11 chưa có môi trường. Native text parser chưa có library, không cài package mới. OCR/layout tuning/engine benchmark/selection/training/teacher/P1.08/KPI/GO1 không chạy theo phạm vi ngoại lệ; không báo số đo OCR hoặc KPI. Không bật hook/plugin/MCP, không đổi Git global config/ACL/.git; repo vẫn chưa có commit, nên không có Git diff tracked để so mọi tệp. Kiểm nguyên vẹn nguồn/frozen dựa hash và schema checker đã chạy.

**DỪNG chờ chủ dự án cung cấp đủ corpus theo hạn ngạch và≥10 full-gold approvals, rồi xác nhận chạy phần còn lại Phase1.** Không cần hỏi lại freeze hoặc các quyết định đã duyệt. A64 giữ PROPOSED; thông số chỉ được calibration khi có phạm vi/dữ liệu phù hợp. Phase0 vẫn INCOMPLETE/NO_GO.

## 02/11/2026 — Freeze đã thực hiện; kết thúc lượt Phase0 ở NO_GO

**Trạng thái hiện tại: SCHEMAS_FROZEN / PHASE0_INCOMPLETE / NO_GO. DỪNG trước Phase1, chờ xác nhận của chủ dự án.** Các việc làm được trong P0.06–P0.11 đã có artifact và kiểm thử; không tuyên bố Phase0 hoàn thành khi thiếu corpus/nhãn vàng/môi trường.

### Freeze và sáu điều kiện

Đã nhận chữ `freeze`, tạo [manifest frozen](../schemas/frozen/manifest.json) cho đúng14 nhóm/28 snapshots. `frozen_at=2026-11-02T10:36:55.888100+00:00`, frozen=true, owner approval; `git_commit=null`, lý do NO_HEAD_COMMIT vì repo chưa có commit. Không tạo commit, không đổi Git global config hoặc quyền.git. [Diff lúc freeze](evidence/phase0/freeze/freeze-diff.json) chứng minh nội dung28 schema chỉ đổi metadata x-finagent-status draft→frozen, giữ hash draft đã duyệt và hash frozen.

Điều kiện ghi ở ASSUMPTIONS D-SCH-1–6/A61–A63, ARCHITECTURE§13 và manifest: cùng major chỉ thêm DTO/optional field; finite enum closed, **extensible=[]**, thêm giá trị xử lý đủ nhánh là breaking/version mới. Canonical/1 có cửa sổ ADR/hash/diff tới first real persistence P2.01; [lifecycle](../schemas/lifecycle/canonical-1.json) vẫn chưa có first-write. Các nhóm khác strict frozen ngay. P2.01 phải đóng cửa sổ ở đường ghi thật đầu tiên; chưa có canonical DB write trong Phase0.

Mọi đường nạp registry đĩa/DB phải qua registry.bundle và có tests không bypass. Mỗi lỗi sau freeze thêm ca sai vào current fixture; archive tại freeze bất biến. A61 đã duyệt là biên kỹ thuật, không phải threshold tài chính; chạm dữ liệu thật báo/xin duyệt, không cắt/bỏ. Live token-copy giữ NOT_RUN, không đặt ngưỡng.

### P0.06–P0.11: đạt và chưa đạt

| Task | Kết quả thực tế | Trạng thái / phần còn thiếu |
| --- | --- | --- |
| P0.06 | [Config/source catalog](PHASE0_CONFIG.md):15 core,40 variants,2 references; mẫu FPT chỉ hash quan sát;43 bands draft; generic profile POLICY_UNAPPROVED. Business/prompt/model loaders đĩa và DB-source port qua gate, spy/AST tests | ĐẠT phần khai báo/offline. Không phải Ratio Kernel/Validator engine; DB-source fake không thay PostgreSQL integration |
| P0.07 | [Corpus card](../eval/datasets/DATASET_CARD.md), typed manifest/split/gold DTOs; đúng hash FPT,28 trang,80 draft cells; hai bbox B02-23 trên raster thật; giữ ba source-conflict flags | PARTIAL: chưa full bbox/per-page route labels hoặc full-document gold approval; không tự gọi gold đã duyệt |
| P0.08 | Chỉ xử lý1 báo cáo thật trong data/public_reports; entry nguồn owner_supplied và missing metadata rõ. Không tải thêm/copy/synthetic | **CHƯA ĐẠT:**0 manifest đủ nguồn/ngày/điều khoản,0 gold approved; cần≥30 complete manifests và≥10 gold. Ngày tên file chỉ hint, không đoán source_date/URL/license |
| P0.09 | Guard local allowlist che số/tên user, random8 tokens/run, value map local, typed period/scope/clarification, no history; private training/retention cross-product và strict-private/default-local tests | ĐẠT phần guard/contracts offline có giới hạn A63; chưa đo coverage hoặc lắp thành Agent/HTTP/provider transport. Full OutputValidator/renderer/Verifier ở Phase4–5 chưa làm |
| P0.10 | [Official review](PROVIDER_REVIEW.md):9 nguồn chính thức, checked_at/URL/quan sát, không lấy§20. Prompt/model registry empty draft, không route/model/quota/terms account nào được xác minh | Official-doc READ; account/limits/Data Controls/terms account-specific/live/structured/token-copy/latency/usage/cost **NOT_RUN**. Không khóa, không provider call, chưa chốt provider order |
| P0.11 | [Baseline report](../eval/runs/phase0-baseline/summary.json), [run metadata](../eval/runs/phase0-baseline/run.json), typed metrics/report, fraction scorer/comparator, inventory port/cohort hash/annotation binding | ĐẠT harness baseline. K01 PARTIAL với7 declared ports, không bịa tỉ lệ conformance; K16 INSUFFICIENT_DATA; K02–K15/K17–K18 NOT_EVALUATED; K19/K20 PENDING_APPROVAL không giá trị/ngưỡng. Baseline exit2/**NO_GO** là kết quả đúng |

Registry loader tests phủ các đường hiện hữu bằng sentinel tại gate và AST cấm direct construction/deserialization ngoài module; đây là bằng chứng của inventory code hiện có, không phải chứng minh tuyệt đối cho mọi Python code tương lai. Mỗi task thêm loader phải giữ tiêu chí này. Artifact/source catalog không thực thi mã; approved definition khác approved rating/model route.

### Kiểm tra đã chạy thật

[Freeze checks](evidence/phase0/freeze/check-results.json): Ruff/mypy/pytest/schema checker đạt ngay sau chuyển trạng thái, **162 tests**. Kết quả đó không thay kiểm lại sau P0.06–P0.11.

[Kết quả cuối](evidence/phase0/completion/check-results.json), [JUnit](evidence/phase0/completion/pytest.xml), [current review counts](evidence/phase0/completion/current-review-counts.json), [baseline command và exit2](evidence/phase0/completion/baseline-command.json).

| Check | Kết quả thật |
| --- | --- |
| Ruff check | PASS, exit0 |
| Ruff format --check | PASS,76 files |
| mypy finagent eval | PASS,40 source files |
| pytest full offline | **219 passed**,0 failed/errors/skips;3,14s ở lượt lưu artifact |
| schema_catalog --check | PASS,14 groups/28 frozen snapshots; archive59 cases + current78 cases (29 đúng/49 sai) |
| eval baseline | **exit2/NO_GO**, có report; không chuyển thành PASS để qua Phase0 |

Current fixtures có19 ca sai bổ sung sau freeze; các lỗi/lỗ hổng được giữ bằng regression cho gate source/base refs, manifest duplicate/type/count tampering, corpus path/annotation path, query document/token/number/scope, metric impossible counts và cohort binding. Có unit test bind bytes nhãn để đổi annotations không giữ cohort. Đính chính mô tả FLAG_ONLY ở review cũ; enum thật vẫn APPLICABLE/N_A/NOT_MEANINGFUL, thêm ca sai từ chối FLAG_ONLY, không sửa frozen enum.

Lịch sử kiểm đầu vẫn lưu: [freeze initial](evidence/phase0/freeze/check-initial.json) có expected readiness SCHEMA_DRAFT cũ sau chuyển frozen và UTC lint; đã đồng bộ test với trạng thái owner duyệt, vẫn readiness503 vì persistence thiếu. [Completion initial](evidence/phase0/completion/check-initial.json) có lỗi dòng mô tả dài; đã ngắt literal, chạy lại Ruff/format. Mypy từng báo Mapping variance, đã sửa kiểu đọc-only. Không nới validator, sửa số FPT/oracle hoặc hạ KPI để qua check.

### NOT_RUN và điều kiện chưa thể xác nhận

[Môi trường](evidence/phase0/completion/environment.json): không có docker/make/psql/redis-server trong PATH. Docker Compose/build, Postgres/Redis integration, hosted CI/Python3.11/Linux **NOT_RUN**, không tự cài hoặc provision. Các helper shell chạy qua escalation do lỗi sandbox setup trước process; không sửa sandbox/Git settings/ACL.

Chưa có corpus đủ strata/approved gold nên chưa đo OCR/ratio engine/retrieval/Agent/performance/KPI quality. Các số215 tests,74 schema review cases,80 draft cells không phải số báo cáo corpus hay accuracy mẫu lớn. Bản thân nguồn FPT và sáu nguồn đặc tả gốc giữ nguyên; source WARN TM18/CF04 và shares không bị sửa để làm đẹp kết quả.

Không gọi provider hoặc đọc secret values; tên runtime/dev env tách sẵn. Account/live/token-copy NOT_RUN theo yêu cầu chủ dự án; official docs không tự cấp training_use=none_verified, retention bound, quota hay capability. Không có model entries thực hoặc quota numbers trong registry. Tham số/ngưỡng K19/K20 vẫn chờ số đo và duyệt, không lấy A61 làm quality target.

### A-ID, khác biệt và điểm cần chủ dự án

A61 đã được duyệt. **A62 mới:** không có enum extensible vì chưa có fallback đã khai báo/kiểm. **A63 mới:** guard allowlist bảo thủ Phase0, chưa chứng minh coverage/semantics đầy đủ; các DTO corpus/gold/eval mới là additive, chưa nằm trong14 nhóm frozen. Không có breaking schema change trong lượt này, không cần ADR/migration cho baseline đã duyệt.

Thiếu cần cung cấp/xác minh: thêm báo cáo thật theo hạn ngạch để đủ30 complete manifests, nguồn/ngày/quyền sử dụng có chứng cứ và≥10 full-gold approvals; quyền/môi trường cho các kiểm chứng đang NOT_RUN. Không hỏi lại các phê duyệt thiết kế/freeze. Assessment corpus approval và quality thresholds chỉ xin duyệt sau khi có kết quả thật.

**DỪNG ở đây, chưa bắt đầu Phase1. Phase0 vẫn INCOMPLETE/NO_GO; chỉ tiếp tục theo xác nhận tiếp theo của chủ dự án, giữ nguyên các điều kiện chưa đạt.**

## 02/11/2026 — Trình lại P0.05 sau R1–R7, chờ chữ freeze

**Trạng thái hiện tại: INCOMPLETE / DRAFT_READY_FOR_REVIEW / WAITING_EXPLICIT_FREEZE. Schema vẫn draft, frozen=false.** Chủ dự án đã duyệt hướng chung §13.1/A61, yêu cầu sửa và trình lại; chưa có xác nhận `freeze`. Không tiếp tục P0.06–P0.11 hoặc Phase1.

[Bản tóm tắt14 nhóm](SCHEMA_REVIEW_SUMMARY.md) là hồ sơ xem lần này; [manifest](../schemas/draft/manifest.json), [validator/OpenAPI](OPENAPI.md), [OpenAPI JSON thực tế](openapi.json). Bản cũ29 tệp được lưu nguyên kèm hash tại [baseline](evidence/phase0/schema-review-r1-r7/before/baseline-hashes.json); [diff JSON Pointer](evidence/phase0/schema-review-r1-r7/snapshot-diff.json) có hash trước/sau từng tệp.

### Đã sửa trong phạm vi review

- R1: ent_/num_ +8 ký tự theo run thay32 hex; allocator dùng randomness hệ thống, giữ UUID128 local, bỏ candidate trùng câu hỏi gốc đã NFKC/casefold hoặc suffix đã cấp. Hết retry budget thì local-only. Đã test va chạm/đổi run/token cũ. P0.10 thêm đo chép token bằng prompt tổng hợp; chưa đo model.
- R2: safe JSON integer±(2^53−1); số lớn dùng canonical string cho money/count; strict/safe metadata integers. Xuất minimum/maximum đúng và giữ bound field riêng; nullable ge/gt được chuyển thành từ khóa JSON Schema chuẩn.
- R3: text trang/chunk/quote/export có alias/trần riêng, test4097 và đúng trần/trần+1; không dùng NonEmpty4096 cho các nội dung này, không truncate.
- R4: ratio fraction string, scale, rounding_mode, display_kind; bỏ percentage kind/measure_kind để tránh hiểu nhầm; test roundtrip không nhân100/quy năm.
- R5: iterative AST preflight với depth32, tổng1024 occurrences,100 inputs/node; rule chia tổng node cho hai vế; chặn cycle. Giá trị giới hạn còn **PROPOSED A61**.
- R6:14 nhóm/28 snapshots có SHA256; manifest thêm compat_policy và bộ59 ca dedicated (29 đúng,30 sai), mỗi nhóm có ca âm; số đếm lấy từ chạy JSON validation và được checker tái kiểm.
- R7:36 custom validators có symbol/scope/điều kiện, công bố trong OpenAPI và snapshot extension liên quan; test inventory/decorators và OpenAPI persisted/runtime đồng nhất.

Tệp thay đổi theo chức năng: common/canonical/API contracts, Gateway token/probe schemas và allocator, AST guard/policy contracts, catalog/exporter schema, tooling review/probe, tests/fixture và28 snapshots/manifest; docs ASSUMPTIONS A61, ARCHITECTURE, PLAN P0.05/P0.10, TEST_PLAN, README/AGENTS, SCHEMA_REVIEW_SUMMARY, OPENAPI và PROGRESS. Giữ nguyên nguồn đặc tả/PDF/FPT oracle. Không thêm dependency, provider route/quota/terms, hooks hoặc global config.

### Kết quả kiểm tra thật của lượt review

[Commands/stdout/exit status](evidence/phase0/schema-review-r1-r7/check-results.json), [JUnit](evidence/phase0/schema-review-r1-r7/pytest.xml), [lượt check có lỗi Ruff trước sửa](evidence/phase0/schema-review-r1-r7/check-initial.json).

| Check | Kết quả quan sát |
| --- | --- |
| Ruff check | PASS, exit0 |
| Ruff format --check | PASS,58 files |
| mypy finagent eval | PASS,30 source files |
| pytest full offline | **160 passed**,0 failed/errors/skips;2,09s ở lượt lưu JUnit |
| schema_catalog --check | PASS,14 versions/28 snapshots;59 dedicated cases đúng outcome; frozen=false |

Các lỗi phát hiện đã sửa: annotation SafeInt ban đầu che ge=0; bản export nullable giữ từ khóa ge/gt thay minimum/exclusiveMinimum dù validator server vẫn đúng; OpenAPI invalidation làm mất extension và tuple/list JSON khác nhau. Thêm regression/giữ ngày âm bị chặn, không thay oracle để hợp thức hóa lỗi. Ruff còn một dòng dài ở lượt lưu log đầu, đã ngắt literal giữ nguyên nội dung và chạy lại Ruff đạt; các checks khác không đổi kết quả.

### NOT_RUN, giả định và cổng tiếp theo

**Token-copy model NOT_RUN:** đã chuẩn bị4 prompt synthetic với30 vị trí alias và scorer không kết nối mạng. Unit tests với responses giả chỉ kiểm phép đếm, không phải chất lượng model. Chưa có keys/quyền, không gọi provider, không tự đặt ngưỡng. P0.10 official docs/account limits/terms vẫn chưa tới vì cổng; sau cổng đọc nguồn chính thức/checked_at, phần account/live vẫn cần quyền tương ứng, không lấy số/điều khoản từ thiết kế§20.

Docker/DB/Redis/hosted CI, OCR/Agent/corpus KPI, full OutputValidator/renderer/Verifier/provider runtime vẫn **NOT_RUN hoặc NOT_IMPLEMENTED** theo phạm vi của từng phase; không suy từ160 tests thành KPI đạt. Retention/provider privacy không được chứng minh bằng fixtures. Giữ số đo/giới hạn môi trường ở lượt trước bên dưới.

**A-ID mới: không có. A61 đã sửa:** R1–R7 là yêu cầu trực tiếp; alphabet/retry32, trần text riêng, depth32/node1024 và lexical details vẫn **PROPOSED** để xem cùng snapshots. Không đổi ngưỡng tài chính/KPI, không tự coi profile Assessment đã được corpus approval. Sai lệch lớn so đặc tả: không thêm; đây là làm rõ wire/schema trong draft, chưa frozen.

**Cần chủ dự án quyết:** xem bản trình lại và chi tiết A61 còn PROPOSED; khi đồng ý, xác nhận bằng chữ **`freeze`**. Sau đó mới frozen theo chính sách cùng major chỉ thêm optional fields; breaking nâng major kèm ADR, migration và full snapshots, rồi tiếp tục P0.06–P0.11 theo PLAN. Chưa tạo frozen artifacts hay tự triển khai phase sau.

## 02/11/2026 — Lượt trước: sửa nguồn và trình schema P0.05 lần đầu

**Trạng thái hiện tại: INCOMPLETE / DRAFT_READY_FOR_REVIEW. Bước0 đã duyệt; Phase0 đã bắt đầu, chưa hoàn thành; schema CHƯA frozen.** Dừng đúng cổng P0.05 do chủ dự án yêu cầu trước P0.06–P0.11. Chưa chuyển Phase1.

### Đính chính chặn trước khi dùng oracle

Đã render lại PDF cục bộ, cắt/xem trực tiếp trang vật lý6/25 độ phân giải cao; thêm crop8/9 để đối chiếu CF04/CF61. [Bằng chứng, tọa độ và hashes](evidence/fpt_q1_2026/README.md), [metadata JSON](evidence/fpt_q1_2026/evidence.json). Nguồn PDF giữ SHA25611c9709914cdc5f1561f47045283598c359f7466f94e5ffbc21893e28b0315fa.

| Ô/chênh lệch | Hồ sơ cũ đọc sai | Số xác nhận từ ảnh gốc |
| --- | --- | --- |
| B02-23 |97.623.971.644|**97.623.991.644** |
| TM18 tỷ giá |(1.685.433.336)|**(1.685.413.336)** |
| TM18/CF04 chênh trị tuyệt đối |170.117|**150.117** |

Đã sửa READING_NOTES§4.2, TEST_PLAN§3.1/FPT-E08/E10 và ASSUMPTIONS A50/A51, giữ cảnh báo heuristic interest>finance cost. Đẳng thức30=20+22−25−26−23 khớp độc lập với số đọc. Ca mới FPT-E13/regression nguồn cố ý thay một chữ số23→97.623.971.644 làm residual+20.000, phải phát hiện; không lấy kernel output để chỉnh oracle.

**Bridge vẫn UNVERIFIED/WARN:**150.117 trùng trị tuyệt đối CF61 kỳ này, nhưng kỳ trước delta35.278.626 khác CF61=35.278.716 đúng90đ. Không sửa nguồn/tăng tolerance0/đóng CLASSIFICATION_DIFFERENCE_UNRESOLVED. Tests hiện là oracle/source regression, không phải chứng minh S8/OCR đã hiện thực.

### Tiến độ task theo thứ tự/cổng

| Task | Trạng thái thực tế |
| --- | --- |
| P0.01 | Đã kiểm workspace, Python3.12.10, Git2.56.0.windows.3; tạo repo main local, không commit/publish. Không tìm docker/make/psql/redis-server trong PATH; chưa xác nhận service DB/Redis. Git owner constraint trên host còn lưu ý bên dưới |
| P0.02 | Đã tạo .venv, pyproject và scaffold;11 direct/build/dev package versions đối chiếu PyPI metadata chính thức, installed resolution43 constraints trong requirements-lock.txt. Không cài global |
| P0.03 | Đã dựng Ruff/mypy strict/pytest/pre-commit manual, Makefile, env example, Dockerfile/Compose/API-worker profiles, CI. Các checks Python/manual đã chạy đạt; Docker config/build/services và hosted CI NOT_RUN |
| P0.04 | Đã dựng canonical/common drafts: tagged periods, exact financial types, tenant/tier/provenance, revisions/zero states, review/evidence/results và storage ports. Có tests; không có PostgreSQL persistence hoặc pipeline admission thật |
| P0.05 | **WAITING_OWNER_SCHEMA_REVIEW:**14 version groups, 28 validation/serialization snapshots + manifest draft, registry validators/import graph/contract tests. Không auto-freeze. [Bảng review](ARCHITECTURE.md#131-bộ-schema-dự-thảo-trình-review-p005) |
| P0.06–P0.11 | **NOT_STARTED:** bị chặn theo thứ tự bởi cổng P0.05; không đánh dấu các task sau hoàn thành chỉ vì đã có DTO dự thảo |

AGENTS.md được tạo từ nguyên văn CLAUDE.md rồi thêm các điều chỉnh đã duyệt; CLAUDE gốc không sửa. Các module hiện thực trong phase sau vẫn chưa làm: OCR/S8/store adapters/Ratio Kernel/Assessment execution/retrieval/Agent/OutputValidator đầy đủ/renderer/Verifier/provider adapters/Redis quota. Worker skeleton báo unavailable; health readiness503. Interface/schema không được tính là implementation hoàn chỉnh.

### Kiểm tra đã chạy thật

[Commands/stdout/exit status](evidence/phase0/check-results.json), [JUnit](evidence/phase0/pytest.xml), [lịch sử lỗi ban đầu](evidence/phase0/check-history.json).

| ruff | PASS | 0 |
| format | PASS | 0 |
| mypy | PASS | 0 |
| pytest | PASS | 0 |
| schema_snapshots | PASS | 0 |
| dependency_consistency | PASS | 0 |
| precommit_config | PASS | 0 |
| precommit_manual | PASS | 0 |
| docker_compose_config | NOT_RUN | — |
| postgres_redis_integration | NOT_RUN | — |
| hosted_ci | NOT_RUN | — |
| provider_live | NOT_RUN | — |
| provider_official_review | NOT_RUN | — |

Kết quả cuối: **pytest 67 passed,0failed/0errors/0skips**; mypy strict25 source files; Ruff check và format48 files đạt; schema snapshots14 nhóm/28 bản khớp; pip check và pre-commit validate/manual đạt. Manual pre-commit chạy cùng4 checks, không install hooks; kiểm kê active Git hooks=0.

[Kiểm hồ sơ](evidence/phase0/document-checks.json) xác nhận hash6 nguồn gốc giữ nguyên, AGENTS giữ nguyên văn CLAUDE, Markdown/UTF-8/code fences và liên kết cục bộ hợp lệ; frozen=false. Parser link lần đầu nhận nhầm cú pháp `[string](...)` trong code block PowerShell, đã sửa parser bỏ qua code blocks; không sửa tài liệu hoặc oracle để né lỗi.

Các lần đầu không đạt được giữ trong history: Ruff21 issues trước format; pytest60pass/1fail do guard socket chặn loopback IPC mà Windows event loop cần. Đã tạo riêng IPC event loop trước guard và dùng ASGITransport trong-process, **không mở ngoại lệ kết nối cho tests**; có test xác nhận outbound vẫn bị chặn. Render WinRT lần đầu lỗi binding AsTask, đã chạy lại thành công rồi mới xem/hash/crop; không dùng PNG lỗi.

### Môi trường và các phần NOT_RUN

Sandbox exec bị lỗi setup refresh trước khi khởi động tiến trình; các lệnh cần thiết chạy qua escalation được cho phép, không sửa sandbox/settings. .git do CodexSandboxOffline khởi tạo khác ADMIN nên Git báo dubious ownership. Windows từ chối yêu cầu sửa owner riêng thư mục.git; không có owner/ACL/global Git config nào được đổi. Pre-commit đã chạy thành công với **safe.directory chỉ theo tiến trình cho đúng C:/FinAgent**, giữ cấu hình scope có trước; cách tái lập ở README. Ownership trong IDE vẫn cần quyền quản trị phù hợp, không coi đã sửa xong.

Docker/Compose build/config và integration Postgres/Redis **NOT_RUN**: CLI không có trong PATH, services/chức năng persistence chưa được kiểm tra/triển khai trong phạm vi hiện tại. Hosted CI/ma trận Python3.11/Linux **NOT_RUN**; chỉ có số đo test trên Windows/Python3.12.10. Không tự cài Docker/Make hoặc service toàn cục.

**Không gọi provider, không tạo keys, không có registry entries thực cho model/quota/terms.** P0.10 official-doc review chưa tới vì cổng P0.05, không phải vì thiếu keys; sau cổng vẫn đọc được nguồn chính thức và phải ghi checked_at. Live/account console/terms account-specific giữ NOT_RUN tới khi có keys/quyền. Không lấy bất kỳ quota number hay điều khoản nào từ thiết kế§20.

Các nguồn kỹ thuật đã đọc để dựng P0.02–P0.03 (checked_at02/11/2026): [Pydantic serialization](https://docs.pydantic.dev/latest/concepts/serialization/), [Ruff](https://docs.astral.sh/ruff/configuration/), [mypy](https://mypy.readthedocs.io/en/stable/config_file.html), [FastAPI Docker](https://fastapi.tiangolo.com/deployment/docker/), [pgvector](https://github.com/pgvector/pgvector#docker), [Python images](https://hub.docker.com/_/python), [Redis images](https://hub.docker.com/_/redis), [checkout v4](https://github.com/actions/checkout/tree/v4), [setup-python v5](https://github.com/actions/setup-python/tree/v5). Package metadata/source URLs và thời điểm UTC ở [inventory](evidence/phase0/environment-and-dependencies.json). Đây không phải bằng chứng vendor LLM terms/quota.

### Quyết định, khác biệt đặc tả và KPI

Đã đồng bộ các phê duyệt A20/A21/A25–A28/A37/A38/A46/A53–A60. Assessment generic v0 chỉ là cơ sở; giữ POLICY_UNAPPROVED đến khi kết quả corpus run được duyệt, OCF14 chỉ score ở cashflow; không đưa config/ranking execution vào trước P0.06. Các cap/disclaimer/weights đã phản ánh trong hồ sơ/draft DTO.

**Thay đổi tiêu chí có chủ dự án duyệt:** K16/PLAN P0.08/Phase0 exit đổi từ≥30 gold thành≥30 manifest nguồn/ngày/điều khoản/hash +≥10 gold approved; gold còn lại bổ sung Phase1–2, Phase6≥100 gold giữ nguyên. Hiện chỉ1 PDF,0 full-gold approvals/manifest corpus đủ trường; metadata crop không thay manifest corpus hoặc gold approval. Không thu thập thêm hoặc nhân mẫu bằng copy/synthetic.

A-ID mới: **A61 PROPOSED** — lexical formats/lengths/token spelling/AST width và wire numeric representation trong drafts, cần xem cùng schema. Có TODO(verify):A61 trong code. Không tự chốt tuning/quality thresholds; K19/K20 vẫn PENDING_APPROVAL sau baseline.

Không đo OCR accuracy, report VERIFIED rate, QA coverage/ABSTAIN/faithfulness/citation, runtime latency/cost hoặc chất lượng provider. Không suy67 unit/contract/source tests thành K01=100% mọi module hoặc KPI runtime đạt; các phép đo này NOT_EVALUATED/NOT_RUN theo phase tương ứng. Các ngưỡng K01–K15/K17–K18 giữ nguyên; K16 đổi bằng quyết định tường minh nêu trên, không tự hạ để pass.

**Cần chủ dự án xem:** bộ14 nhóm schema tại ARCHITECTURE§13.1 và A61 trước frozen. Không cần hỏi lại Assessment cơ sở, corpus plan, keys, A54/A60 hoặc dependencies đã duyệt. Chỉ tiếp P0.06 sau cổng này; cuối Phase0 còn phải dừng riêng trước Phase1.

---

Lịch sử bên dưới là hồ sơ **trước** lần phê duyệt bắt đầu Phase0; các điểm chờ duyệt cũ được quyết định mới ở trên thay thế.

## 02/11/2026 — Bước0: cập nhật thiết kế Gateway theo D-GW-1–8

**Trạng thái:** cập nhật hồ sơ, chờ xác nhận bản sửa đổi; **Phase0 CHƯA BẮT ĐẦU**. Chưa có product code, manifest/CI/tests hoặc registry sản phẩm; workspace chưa là Git repo. Không có schema code đã đóng băng để migrate. D-GW-1–8 đã duyệt; điều này không đồng nghĩa mọi proposal A-ID hoặc toàn bộ hồ sơ Bước0 đã được duyệt.

**Phạm vi đã đọc:** toàn bộ docs/LLM_GATEWAY_DESIGN.md,482 dòng gồm§20; đối chiếu toàn bộ ARCHITECTURE/PLAN/TEST_PLAN/ASSUMPTIONS/READING_NOTES hiện có, CLAUDE và hướng dẫn AGENTS trong chat. Báo cáo chính/Báo cáo2/file chỉ số/PDF28 trang đã được đọc đầy đủ ở Bước0 ban đầu; lượt này không tính lại hoặc thay các ca vàng. Source thiết kế SHA256 `e0ffbca7a92323cc519b9c2e6a0d47edd7482b502e25a3c6934f19e084cc6df3`.

### Audit G1–G14

“Trước” là hồ sơ Bước0 trước lượt cập nhật này; “Sau” chỉ đánh giá độ đầy đủ **của hồ sơ**, không phải implementation/tests đã đạt. G13 đáp ứng yêu cầu đề xuất cách đo và để ngưỡng chờ duyệt; không ghi quality gate đã đạt. Các tham số còn proposal được nêu A53–A60.

| Gap | Trước | Bằng chứng trước / thiếu gì | Sau | Hợp đồng, task và test sau |
| --- | --- | --- | --- | --- |
| G1 | Thiếu | FinalAnswerPayload trước có FinalNumericClaim/value | Đã đáp ứng ở hồ sơ | ARCH§10.1 value-blind descriptors; P4.04/P4.05/P5.02; GW01 canary giá trị |
| G2 | Một phần | Có AnswerSet/Verifier nhưng draft/renderer chưa tách | Đã đáp ứng ở hồ sơ | ARCH§§5/9/10.1 typed segments/OutputValidator/renderer; P4.04/P4.06; T26/T27/GW02 và T29 renderer fault |
| G3 | Một phần | Một câu làm rõ nhưng clarification_request còn tự do | Đã đáp ứng ở hồ sơ | ARCH§10.1 enum và §10.2 local templates; P5.03; T14/GW03 |
| G4 | Một phần | Guard chặn pasted report, chưa che số user | Đã đáp ứng ở hồ sơ | ARCH§10.2 masking + verify_user_claim placeholder; P0.09/P4.05; T05/GW04 |
| G5 | Một phần | Session selection có, outbound history chưa giới hạn | Đã đáp ứng ở hồ sơ | ARCH§10.2 user-only masked history; P5.03; T14/T28/GW05; N đề xuất A54 |
| G6 | Một phần | Token ghi stable theo run/tenant, chưa random per-run | Đã đáp ứng ở hồ sơ | ARCH§10.2 run-random và admin opt-in tenant-stable; P0.09/P4.05; GW06 cross-run |
| G7 | Một phần | Có bucket provider/model, thiếu account_scope/Redis atomic/fairness tenant | Đã đáp ứng ở hồ sơ | ARCH§10.4 QuotaStore account/model + tenant allocation; P5.01/P6.04; GW07 multiworker/fairness |
| G8 | Một phần | Dev/public riêng về ý định, chưa chặn runtime import/tách khóa | Đã đáp ứng ở hồ sơ | ARCH§§2/10.4/10.6 factories/imports/keys; P1.07/P0.10; GW08 |
| G9 | Một phần | Có schema/capability chung, chưa có structured ladder | Đã đáp ứng ở hồ sơ | ARCH§10.3 native/tool/JSON→ineligible; P0.10 structured_strategy/P5.01; GW09 |
| G10 | Một phần | Chặn raw token trước Verifier, chưa cố định no-stream/no-hedge | Đã đáp ứng ở hồ sơ | ARCH§§10.3/11.2 không streaming/hedging; P5.02/P5.05; GW10; A60 phạm vi SSE |
| G11 | Thiếu | Terms chỉ refs chung, chưa có training_use/retention eligibility | Đã đáp ứng ở hồ sơ | ARCH§10.5 tagged terms/tenant bound; P0.10; GW11 unknown fail-closed |
| G12 | Một phần | Freeze schemas chung, thiếu ba version Gateway rõ ràng | Đã đáp ứng ở hồ sơ | ARCH§13/P0.05 thêm gateway/1,prompt/1,model-registry/1; GW12 |
| G13 | Một phần | Có usage/latency và KPI chung, chưa quality theo model | Đã đáp ứng ở hồ sơ | P5.08/P6.05 và K19/K20/GW13; A57 ngưỡng PENDING_APPROVAL |
| G14 | Một phần | Local OCR đã có nhưng Gateway còn image/local embedding/dev capabilities | Đã đáp ứng ở hồ sơ | ARCH§§2/5/10 external-only + LocalModelPort; P5.01; GW14 |

### Tệp thay đổi và tác động

| Tệp | Cập nhật có giới hạn |
| --- | --- |
| ARCHITECTURE.md | Value-blind payload, typed draft/validator/local renderer; enum/masking/history/run tokens; account quota atomic/fairness; structured ladder và training/retention; external-only Gateway/LocalModelPort; teacher/key boundary, no streaming/hedging, versions |
| PLAN.md | P0.05/09/10, P1.07, P4.04–06, P5.01–03/05/08, P6.04–05 và tiêu chí Phase0/4/5; P0.10 evidence thật, quota sources, measured routes, NOT_RUN; điểm dừng trước Phase0 |
| TEST_PLAN.md | Viết lại T05/T14/T26–28, thêm T29 lỗi renderer, GW01–GW14; private terms matrix, multiworker/fairness/import/key/streaming tests; K19/K20 đề xuất, ngưỡng chờ duyệt |
| ASSUMPTIONS.md | Ghi riêng D-GW-1–8 đã duyệt; sửa A31/32/35/43/44/47 đã lỗi thời; thêm A53–A60 PROPOSED |
| READING_NOTES.md | Ghi đọc đủ thiết kế, source/hash và ưu tiên quyết định; sửa các mô tả composer/SSE/token/Gateway cũ; không chép quota/terms§20 |
| PROGRESS.md | Entry Bước0 theo yêu cầu trực tiếp; audit trước/sau, checks và điểm dừng này |

Không sửa CLAUDE, ba đặc tả, PDF hoặc LLM_GATEWAY_DESIGN.md. Không tạo schema/registry/mã sản phẩm, không cài dependency/plugin/hook và không gọi provider.

### A-ID mới và phần còn cần quyết định

A53 manifest/render slots/prose guard; A54 N=0 user history đề xuất; A55 fair queue/tham số tenant chưa chốt; A56 missing/stale private terms/bound→local đề xuất; A57 K19/K20 và ngưỡng chờ baseline; A58 cache run-bound/idempotency uncertain; A59 hoàn chỉnh GatewayOutcome nguồn bị cắt; A60 SSE chỉ progress/result_ref để cùng thỏa đặc tả chính và D-GW-6. Chi tiết/trạng thái ở ASSUMPTIONS§7.

Chỉ cần xác nhận bản sửa đổi trước khi cho phép Phase0; lưu ý A54/A60. Ngưỡng K19/K20 chỉ trình duyệt sau baseline, không tự gán ngay. Assessment A25–A28 và corpus A40 còn mở từ Bước0 trước, không thay quyết định Gateway và không được gọi đã giải quyết.

### Xác minh và giới hạn

- **PASS — kiểm hồ sơ bằng Python standard library:** đã chạy `python -X utf8 -` với script qua PowerShell stdin, exit0. Kiểm tập tệp sửa đúng5 hồ sơ cũ +1 PROGRESS mới, không xóa tệp; SHA256 của6 nguồn giữ nguyên (CLAUDE, Báo cáo chính, Báo cáo2, chỉ số, PDF, thiết kế Gateway).
- **PASS — cấu trúc:**14 hàng G1–G14,14 test specifications GW01–GW14,8 quyết định D-GW-1–8,8 proposal A53–A60; đủ gateway/1,prompt/1,model-registry/1 ở hợp đồng/P0.05; bảng Markdown, code fences và UTF-8 hợp lệ;22 liên kết cục bộ tồn tại.
- **PASS — so sánh nội dung với baseline trong phiên:** đọc lại6 tệp sau ghi; toàn bộ TEST_PLAN§3 (ca vàng FPT) và từng dòng K01–K18 giữ nguyên. IntentPlan.clarification là enum nullable; không có ngoại lệ with_values. Rà diff theo baseline nội dung vì workspace không có Git; rà mô tả cũ bằng rg, các nhắc FinalNumericClaim/clarification_request/data_use còn lại chỉ nói lịch sử hoặc yêu cầu thay thế.
- Các PASS trên chỉ là **kiểm tài liệu**, không phải kết quả test sản phẩm/Gateway hay số đo KPI.

**NOT_RUN:** ruff/mypy/pytest/CI/integration Redis/Postgres, toàn bộ GW/trap/product tests và mọi KPI runtime — chưa có mã/manifest trong phạm vi Bước0. Live provider probes, account console limits và terms review **NOT_RUN**: đây là P0.10 chưa được phép bắt đầu và chưa xác nhận availability/quyền sử dụng keys/account. Không coi việc đọc§20 là kiểm tra chính thức; không ghi bất kỳ quota number/terms nào từ đó. K19/K20 chưa có tử/mẫu/đo baseline và chưa có threshold đã duyệt.

**Điểm dừng:** cập nhật chạm **hợp đồng schema dự kiến và tiêu chí hoàn thành/bàn giao Phase0/4/5**, nên dừng chờ xác nhận theo yêu cầu chủ dự án trước mọi việc Phase0, đặc biệt schema/Gateway. Không có thay đổi KPI K01–K18 hoặc số/điều kiện ca vàng FPT; không hạ ngưỡng để qua cổng. D-GW-1–8 không cần hỏi duyệt lại.
