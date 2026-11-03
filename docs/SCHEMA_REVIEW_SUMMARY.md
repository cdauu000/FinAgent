# Bản trình lại schema P0.05 sau R1–R7

**Hồ sơ lịch sử lúc trình review.** Chủ dự án đã xác nhận `freeze` sau bản này; A61 đã duyệt, [manifest frozen](../schemas/frozen/manifest.json) và [PROGRESS](PROGRESS.md) là trạng thái hiện hành. Các kết quả160 tests/59 cases và diff bên dưới giữ nguyên bằng chứng của lần trình, không đại diện lần kiểm cuối Phase0.

Ngày02/11/2026. **DRAFT_READY_FOR_REVIEW — CHƯA frozen.** Chủ dự án đã duyệt hướng chung, chưa duyệt đóng băng. Dừng chờ xác nhận bằng chữ **`freeze`**; chưa thực hiện P0.06–P0.11.

[Manifest hiện hành](../schemas/draft/manifest.json) có14 nhóm,28 snapshot validation/serialization, SHA256 từng tệp, compat_policy và kết quả ca đúng/sai. [Baseline trước sửa](evidence/phase0/schema-review-r1-r7/before/baseline-hashes.json) lưu nguyên29 tệp cũ gồm manifest; [diff đầy đủ theo JSON Pointer](evidence/phase0/schema-review-r1-r7/snapshot-diff.json) kèm hash trước/sau. Chênh lệch dưới đây so với baseline đó, không so với oracle/kernel output. Chưa có frozen baseline nào để phải nâng version trong lần sửa draft này.

## Thay đổi cần xem

| Yêu cầu | Kết quả trong draft |
| --- | --- |
| R1 | ent_/num_ +8 ký tự ngẫu nhiên theo run thay32 hex; allocator cục bộ loại va chạm query gốc/suffix sau NFKC/casefold và alias đã cấp. UUID128 giữ local. Alphabet Crockford32, budget32 lần còn PROPOSED A61. Hết budget local-only; không dùng candidate va chạm. Thêm probe chép token vào P0.10 |
| R2 | Bare JSON integer chỉ trong±(2^53−1); ngoài khoảng tiền/count dùng canonical string, output luôn string; metadata integer strict/safe và giữ bound riêng. Chuẩn hóa ge/le/gt/lt ở nullable integers thành từ khóa JSON Schema minimum/maximum/exclusiveMinimum/exclusiveMaximum |
| R3 | NonEmpty4096 không áp page/chunk/export/quote. Trần riêng PROPOSED:1.000.000/64.000/10.000.000/64.000 ký tự. DTO thật nhận4097; test các trần và trần+1 |
| R4 | Ratio wire value là Decimal string phân số, representation=fraction, scale và ROUND_HALF_UP; percent chỉ display_kind. Bỏ kind/measure_kind percentage để tránh hai nghĩa; không tự đổi value/làm tròn/quy năm |
| R5 | Thêm iterative preflight: **PROPOSED** depth32 (root1), tổng1024 occurrences, fanout100/node. Rule dùng chung tổng1024 cho hai vế; chặn cycle; chưa có số đo corpus để khẳng định đủ |
| R6 | Giữ/tái kiểm SHA256 từng snapshot; thêm compat_policy, hash fixture,29 ca đúng/30 ca sai và số đạt theo14 nhóm. Checker chạy lại các ca, không chỉ chép số đếm |
| R7 | [Catalog36 validator](OPENAPI.md) công bố symbol/scope/điều kiện và phần chưa triển khai; có trong OpenAPI thật, OpenAPI JSON và extension từng snapshot liên quan |

Không thêm A-ID mới: cập nhật **A61**, tách yêu cầu trực tiếp R1–R7 khỏi các trị số/alphabet/budget **PROPOSED**. Không đặt hoặc hạ ngưỡng KPI. Token ngắn là alias, không phải secret/ACL. Allocator chưa thay query guard đầy đủ.

## Trường, ràng buộc và khác biệt của từng nhóm

Tất cả DTO domain dùng extra-forbid/frozen output. Identifier≤160, NonEmpty≤4096 là biên ngắn của A61; các lớp text riêng ghi ở trên. JSON Schema có regex/enum/bound/discriminator nhưng không thay Pydantic/preflight/loader. IDs validator chính xác và số ca theo nhóm ở bảng kế tiếp; [OpenAPI](OPENAPI.md) giải thích từng ID và symbol. Loader `registry.bundle` phải gọi riêng, không tự chạy khi chỉ parse DTO.

| Nhóm | Trường chính | Ràng buộc chính | Khác biệt so với snapshot trước |
| --- | --- | --- | --- |
| canonical/1 | entities, documents, pages, tables, cells, provenance, statements, lines, issues, derived, snapshots, review_cases/actions, evidence_chunks, source_quotes, analysis_records và views/refs | Tenant/tier/version/provenance; stock/flow; financial values typed; missing/explicit/derived zero khác nhau; chosen reading và audit/public evidence | Safe integers; fraction/scale/rounding/display; Page.native_text, SourceQuote/source_quotes mới; raw_text1M, chunk64K, quote64K. Bỏ percentage union member |
| api/1 | error, health, readiness, ResultEnvelope[AnalysisRecord], text_export | Kết quả typed có mode/tier/versions; TextExportContent có artifact_id/format/content/verifier_receipt_ref; đây là DTO, chưa có export endpoint | TextExportContent/content≤10M và text_export mới; kế thừa safe integer/ratio fraction. Không thêm route nghiệp vụ |
| event/1 | event_id, seq, time_utc, tenant/resource/run/trace IDs, mode, source_tier, policy_version, payload | Payload union progress/result_ref/failure; extra answer text bị chặn; seq dương | Seq có safe upper bound; thêm catalog validator chung, không đổi loại event |
| spack/1 | id/version/status/source/tests, min_core_version, template_refs, ratio_memberships, thresholds, assessment_policy, applicability_refs, piotroski_policy | Ngưỡng ordered; một scoring membership; OCF14 chỉ cashflow; năm trụ20%; POLICY_UNAPPROVED tới corpus approval | Decimal threshold/weight/cap integer input có safe bounds; serialization vẫn string; thêm catalog, không thay profile/ngưỡng tài chính |
| role/1 | definition (strategy, allowed_tool_refs, schema refs, budgets), message (run/parent/from/to/payload/evidence refs, trace/context) | Strategy single ở loader mặc định; message typed refs, không số tài chính tự do; budgets dương | Budget integers có safe bounds và strict input; catalog loader/period tương ứng. Không thêm multi-agent |
| tool/1 | id/version/status/source/tests, input/output_schema_ref, permissions, side_effect, budget_class | Finite declarative contracts; required permissions; không code/handler tự do từ tài liệu | Chỉ thêm metadata catalog; không đổi trường nghiệp vụ; ca sai thiếu permission/code extra |
| template/1 | id/version/status/source/tests, statement_family, observed_source_hashes, mappings, required_total_codes | Code string giữ leading zero; statement_type/code duy nhất; mapping declarative, không eval | Chỉ thêm catalog unique-code/loader; không đổi mapping hay số nguồn |
| ratio-def/1 | id/version/source/tests, formula, input_concepts, dependencies, measure_kind, period_basis, display_kind, definition_role, base_definition_ref, rounding, decimal_precision | AST whitelist + preflight; Decimal38/ROUND_HALF_UP; dependency DAG ở loader; percent chỉ hiển thị | Bỏ measure_kind percentage; safe integer constant input; depth/node guards là custom validators không hiện thành maxDepth JSON Schema |
| rule/1 | id/version/source/tests, template_ref, group, severity, left/right, comparison, tolerance | Group A–F; tolerance≥0; hai AST theo whitelist, depth/tổng budget; template ref ở loader | Safe integer Decimal input; budget chung hai vế, depth/cycle custom; không đổi đẳng thức hay oracle |
| policy/1 | policy_ref, mode, source_tier, paid_fallback, private, limits, registry_refs, content_hash, resolved_at | Private opt-in/retention; giới hạn không âm/dương theo field; registry refs typed | Safe/strict integer bounds cho mọi limit/retention; giữ nguyên ge/le cũ; chưa triển khai resolver/egress runtime |
| applicability/1 | id/version/status/source/tests, condition_refs, required_evidence_concepts, effect, warning_codes | Effect APPLICABLE/N_A/NOT_MEANINGFUL; refs declarative; không executable code | Đính chính mô tả FLAG_ONLY nhầm trước đây, không đổi enum snapshot; có ca sai từ chối FLAG_ONLY |
| gateway/1 | request, provider_request/result, outcome, error, draft, manifest, permit, quota reservation/denied, synthetic_probe/probe_result | Hai external task; value-blind; typed draft/refs; clarification enum; task/schema khớp; stream=false, không history; private opt-in/strict-private deny ở DTO | Token8 thay32 hex ở mọi vị trí; probe case token_copy; token collision preflight; safe usage/budget/quota integers và cost Decimal; không provider runtime |
| prompt/1 | schema_version, status, entries (id/version/task/language/status/template/hash/input/output refs/tests) | Task/schema đúng cặp; hash UTF-8 template; id/version/language duy nhất; template là trường ngắn | Chỉ thêm catalog; không ship/kích hoạt prompt provider |
| model-registry/1 | schema_version, status, entries(provider/model/account_scope/checked_at/training_use/retention/structured/quota/evidence), evidence | Unknown terms mặc định; verified có evidence; refs tồn tại; quota có source/account_scope; synthetic fixture không chứng minh vendor thật | Safe/strict context_tokens/retention/quota limits; thêm catalog; không thêm record quota/terms/provider thật |

## Ca đúng/sai và validator theo nhóm

Đơn vị đếm là **một row dedicated trong [fixture](../tests/fixtures/schema_review_cases.json), validate một lần bằng JSON**. Không nhân đôi theo hai snapshot, không cộng test boundary/loader khác vào bảng.59/59 ca đạt nghĩa là29 đầu vào đúng được nhận và30 đầu vào sai bị từ chối; không phải59 báo cáo tài chính hay đo độ chính xác model.

| Nhóm | Ca đúng đạt/tổng | Ca sai chặn/tổng | Thất bại | Validator tùy biến liên quan | Số JSON Pointer thay đổi validation/serialization |
| --- | --- | --- | --- | --- | --- |
| canonical/1 | 3/3 | 2/2 | 0 | `integer.wire`, `decimal.exact`, `integer.metadata`, `integer.schema_bounds`, `period.interval`, `document.public_evidence`, `bbox.ordered`, `provenance.chosen`, `ratio.infer_scale`, `ratio.scale`, `line.presence`, `statement.period_audit` | 42/37 |
| api/1 | 2/2 | 2/2 | 0 | `integer.wire`, `decimal.exact`, `integer.metadata`, `integer.schema_bounds`, `period.interval`, `ratio.infer_scale`, `ratio.scale` | 15/12 |
| event/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds` | 2/2 |
| spack/1 | 2/2 | 2/2 | 0 | `decimal.exact`, `integer.metadata`, `integer.schema_bounds`, `threshold.bounds`, `membership.scoring`, `assessment.owner_policy`, `pack.memberships`, `registry.bundle` | 18/15 |
| role/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds`, `registry.bundle` | 7/7 |
| tool/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds`, `registry.bundle` | 1/1 |
| template/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds`, `template.codes`, `registry.bundle` | 1/1 |
| ratio-def/1 | 2/2 | 2/2 | 0 | `decimal.exact`, `integer.metadata`, `integer.schema_bounds`, `ast.budget`, `registry.bundle` | 5/4 |
| rule/1 | 2/2 | 2/2 | 0 | `decimal.exact`, `integer.metadata`, `integer.schema_bounds`, `ast.budget`, `rule.combined_budget`, `rule.tolerance`, `registry.bundle` | 3/1 |
| policy/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds` | 18/18 |
| applicability/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds`, `registry.bundle` | 1/1 |
| gateway/1 | 2/2 | 4/4 | 0 | `decimal.exact`, `integer.metadata`, `integer.schema_bounds`, `intent.rewrite`, `intent.selection`, `intent.clarification`, `compose.claim_refs`, `draft.numeric_prose`, `draft.manifest_refs`, `gateway.manifest`, `provider.task`, `provider.result`, `permit.tier`, `model.evidence`, `token.collision` | 22/21 |
| prompt/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds`, `prompt.binding_hash`, `prompt.unique` | 1/1 |
| model-registry/1 | 2/2 | 2/2 | 0 | `integer.metadata`, `integer.schema_bounds`, `model.evidence`, `model.registry_refs` | 5/5 |

Số pointer gồm cả metadata catalog và các bound; đây chỉ là kích thước diff, không phải chất lượng. Manifest trước đã có SHA256; R6 bổ sung compat_policy/case_catalog và tái kiểm hash, không tuyên bố hash là mới. Các ca sai cụ thể bao gồm: unsafe integer/derived-zero thiếu lineage; export thiếu receipt/bool money; event extra answer/seq unsafe; duplicate pack/OCF score sai trụ; role budget0/financial field; tool thiếu permission/code; template duplicate/eval; ratio eval/exponent; rule tolerance âm/depth33; policy retention âm/unknown limit; applicability unknown effect/code; gateway token cũ/stream/unknown required ref/value leak; prompt hash/task sai; registry ref lạ/data_use cũ.

## Kiểm chứng và giới hạn

Kết quả chạy thật trên Windows/Python3.12.10, offline: [command/stdout/exit status](evidence/phase0/schema-review-r1-r7/check-results.json), [JUnit](evidence/phase0/schema-review-r1-r7/pytest.xml). Log lần kiểm tra có lỗi dòng dài trước sửa được giữ tại [check-initial](evidence/phase0/schema-review-r1-r7/check-initial.json).

| Lệnh | Kết quả |
| --- | --- |
| `python -m ruff check .` | PASS, exit0 |
| `python -m ruff format --check .` | PASS,58 files |
| `python -m mypy finagent eval` | PASS,30 source files |
| `python -m pytest -q` (kèm JUnit) | **160 passed**,0 failed/errors/skips;2,09s lần có artifact |
| `python -m finagent.schema_catalog --check` | PASS,14 versions,28 snapshots, frozen=false;59 ca dedicated chạy lại |

Kiểm tra đã phát hiện và sửa: bound SafeInt từng che ge=0 ở một lần ghép annotation ban đầu; sau đó nullable integer còn xuất từ khóa ge/gt không chuẩn dù server đã chặn đúng. Giữ test ngày âm và thêm kiểm mọi integer schema/bound. OpenAPI cần giữ extension sau cơ chế invalidation cache của FastAPI, đồng thời dùng list JSON cho catalog; các lỗi này đã được sửa trước kết quả trên. Không làm yếu negative cases để cho qua.

Phép đo **model chép token: NOT_RUN** — đã có [bốn prompt tổng hợp,30 vị trí token](evidence/phase0/schema-review-r1-r7/token-copy-probe.json) và prepare/scorer không kết nối mạng. Unit tests kiểm scorer với response giả không được tính là số đo model. P0.10 phải chạy khi có keys/quyền và báo theo model/task/version, không tự đặt ngưỡng. Official/account review P0.10 vẫn chưa tới do cổng P0.05; không copy thiết kế§20, không gọi provider.

Đây là kiểm chứng DTO/snapshot/loader/preflight/health OpenAPI. Chưa chứng minh query guard, OutputValidator đầy đủ, renderer/Verifier, OCR/admission/store/Ratio Kernel/Assessment execution hoặc Redis/provider runtime. Docker/DB/Redis/hosted CI/corpus KPI vẫn chưa được xác nhận theo PROGRESS. Không sửa số FPT/oracle/threshold để qua test.

**Điểm duy nhất chờ chủ dự án:** xem các chi tiết A61 còn PROPOSED cùng bản trình lại này. Khi đồng ý, xác nhận bằng chữ **`freeze`**; lúc đó mới đóng băng. Chính sách đã nêu: cùng bản chính chỉ thêm trường tùy chọn; mọi breaking change nâng bản chính kèm ADR, migration và chạy lại toàn bộ snapshot. Chưa tạo frozen manifest, chưa đi tiếp P0.06.
