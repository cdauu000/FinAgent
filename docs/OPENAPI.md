# OpenAPI và validator tùy biến — schema dự thảo P0.05

Cập nhật02/11/2026 sau lệnh **freeze**. [Baseline14 nhóm](../schemas/frozen/manifest.json) đã frozen; [OpenAPI JSON](openapi.json) xuất từ `create_app().openapi()`, vẫn chỉ có hai endpoint health. Extension `x-finagent-custom-validators` công bố catalog bên dưới; `x-finagent-schema-review` ghi frozen và controls chưa làm. Không coi tên validator là implementation đầy đủ của các đường nghiệp vụ tương lai.

Mỗi snapshot JSON Schema có extension validator liên quan tới các model trong nhóm. Catalog có `id`, `symbol`, `models`, `rule`, `scope`; `scope=pydantic` chạy khi validate DTO, `common` là quy ước chung, `preflight` chạy trước parse hoặc tại allocator, `loader` phải gọi riêng sau validate bundle. Nguồn thực thi và catalog nằm tại [base](../finagent/contracts/base.py), [canonical](../finagent/store/models.py), [policy](../finagent/policy/contracts.py), [loader](../finagent/policy/registry.py), [Gateway](../finagent/llm_gateway/contracts.py), [registry](../finagent/llm_gateway/model_registry.py), [prompts](../finagent/llm_gateway/prompts.py), [inventory](../finagent/contracts/validator_catalog.py). Catalog machine ghi symbol đầy đủ; bảng dưới dùng tên ngắn.

| ID | Symbol / phạm vi | Điều kiện tùy biến ngoài JSON Schema thuần |
| --- | --- | --- |
| integer.wire | exact_integer | Không bool/float; integer JSON vượt±(2^53−1) cần canonical string; tối đa38 chữ số |
| decimal.exact | exact_decimal | Không bool/float/nonfinite/exponent text; kiểm precision/scale38 và unsafe integer; Decimal nội bộ được phép |
| integer.metadata | safe_metadata_integer | Metadata integer strict trong safe range; ge/le riêng vẫn giữ |
| integer.schema_bounds | Contract.__get_pydantic_json_schema__ | Xuất safe bound giao với bound sẵn có, không ghi đè thành giới hạn rộng hơn |
| period.interval | FlowPeriod.valid_interval | start≤end; quarter cần fiscal_quarter |
| document.public_evidence | Document.public_requires_evidence | Public cần evidence refs; chưa xác thực nguồn/ACL của refs |
| bbox.ordered | BoundingBox.ordered | x2>x1, y2>y1 |
| provenance.chosen | Provenance.chosen_exists | chosen_reading phải trỏ vào reading tồn tại |
| ratio.infer_scale | DecimalValue.infer_scale | Thiếu scale thì suy từ Decimal, không làm tròn/nhân100 |
| ratio.scale | DecimalValue.scale_matches_fraction | Scale khớp số chữ số thập phân của value fraction |
| line.presence | LineItem.presence_matches_value | Missing tương ứng null; explicit/derived zero phải có0; derived zero có lineage |
| statement.period_audit | Statement.correct_period_kind | B01 stock, B02/B03 flow; audited/reviewed có evidence |
| intent.rewrite | ReadAction.rewrite_has_no_numbers | Rewrite chỉ chữ/khoảng trắng; kiểm tên thật đầy đủ còn ở Phase4 |
| intent.selection | ReadAction.explicit_selectors_for_financial_actions | Tác vụ tài chính có entity/scope/period; statement type và hai kỳ so sánh khi cần |
| intent.clarification | IntentPlan.unresolved_does_not_dispatch | Không dispatch cùng clarification; cần action hoặc clarification |
| compose.claim_refs | FinalAnswerPayload.unique_claims_and_known_relations | Claim IDs duy nhất; quan hệ chỉ tới claim đã có |
| draft.numeric_prose | ProseSegment.no_numeric_characters | Chặn ký tự số Unicode; chưa thay guard tên/số viết bằng chữ/ngữ nghĩa |
| draft.manifest_refs | ReferenceManifest.required_refs_are_allowed | Required claim/warning/slot thuộc allowed refs; chưa kiểm toàn bộ draft binding |
| gateway.manifest | GatewayRequest.composition_requires_manifest | Compose bắt buộc có manifest mù giá trị |
| provider.task | ProviderRequest.task_matches_payload_and_schema | Task, typed user payload và output schema ref phải khớp |
| provider.result | ProviderResult.result_matches_task | Intent trả IntentPlan; compose trả AnswerDraft |
| permit.tier | EgressPermit.tier_allows_external | Strict-private chặn; private cần opt-in; chưa thay terms/deadline/one-use runtime |
| model.evidence | ModelCapability.verified_requires_evidence | Verified cần ngày/evidence/probe; training/retention xác minh cần terms refs |
| model.registry_refs | ModelRegistry.references_exist | Evidence/model-account keys duy nhất; quota/probe/terms refs tồn tại |
| prompt.binding_hash | PromptDefinition.task_contract_matches | Task/schema đúng cặp; SHA256 khớp template UTF-8 chính xác |
| prompt.unique | PromptRegistry.unique_versions | Khóa id/version/language duy nhất |
| ast.budget | guard_expression / preflight | **A61 đã duyệt:** depth32, tổng1024 occurrences, fanout100; chặn cycle trước Pydantic |
| rule.combined_budget | RuleDefinition.combined_expression_budget | Hai vế rule cùng budget1024 node, không hai budget riêng |
| rule.tolerance | RuleDefinition.nonnegative_tolerance | Tolerance không âm |
| template.codes | TemplateDefinition.unique_codes | statement_type/code không trùng, giữ mã dạng string |
| threshold.bounds | ThresholdBand.ordered_bounds | Cận có thứ tự; cận bằng nhau cần hai đầu inclusive; xử lý overlap/gap liên band ở Phase3 |
| membership.scoring | RatioMembership.scoring_is_displayed | Trụ chấm điểm thuộc trụ hiển thị; role và scoring_pillar nhất quán |
| assessment.owner_policy | AssessmentPolicy.profile_matches_owner_decision | Năm trụ riêng đều20%, ICR cap1,5; APPROVED cần corpus-run approval ref |
| pack.memberships | SectorPack.single_scoring_membership | Không lặp ratio membership; OCF14 chỉ score ở cashflow |
| registry.bundle | validate_bundle / loader | Entries/version/refs/source/tests/status hợp lệ; strategy/core tương thích; ratio dependency DAG; generic pack khi runtime |
| token.collision | RunTokenAllocator.allocate / preflight | Alias8 ký tự theo run; loại va chạm query đã chuẩn hóa hoặc suffix trong run; hết budget thì local-only; UUID128 chỉ nội bộ |

JSON Schema biểu diễn được kiểu, enum, regex, extra-forbid, phần lớn bound độ dài/số và discriminated union. Nó **không diễn tả đầy đủ** quan hệ trường/refs, hash nội dung, precision Decimal và kiểu Python, DAG/cycle/depth/tổng AST, NFKC/collision với câu hỏi gốc hoặc checks của loader. Một số ràng buộc có thể diễn tả một phần bằng schema phức tạp; client vẫn phải dùng validator server. Test inventory kiểm mọi decorated model/field validator trong project có mục trong catalog; các helper Annotated/preflight/loader được liệt kê tường minh.

Quy ước số và văn bản của dự thảo:

| Loại | Ràng buộc wire / trần |
| --- | --- |
| Money/Count | Bare integer JSON trong±9.007.199.254.740.991; ngoài khoảng dùng canonical string tối đa38 chữ số; JSON output luôn string |
| Metadata integer | Safe range và bound riêng, strict integer; không nhận bool/float hoặc chuỗi thay số metadata |
| Ratio | `kind=ratio`, value chuỗi Decimal fixed-point **phân số**, `representation=fraction`, scale0..38, `rounding_mode=ROUND_HALF_UP`, display_kind decimal/percent |
| NonEmpty |1..4096 ký tự, chỉ trường ngắn |
| PageText |≤1.000.000 ký tự; Page.native_text, SourceCell/Reading.raw_text |
| ChunkText |≤64.000 ký tự; EvidenceChunk.text |
| CitationText |≤64.000 ký tự; SourceQuote.text |
| ExportText |≤10.000.000 ký tự; TextExportContent.content (md/json), không áp cho blob/XLSX |

Các trần văn bản và chi tiết alphabet/retry/AST vẫn **APPROVED A61**. Đếm ký tự Unicode, không byte/token. Nhận4097 ký tự được chứng minh trên bốn DTO thật; test đúng trần/trần+1 ở từng alias. Không truncate khi lỗi. Ratio `0.1250` scale4 giữ nguyên phân số; formatter tương lai mới hiển thị12,50%, DTO không tính/làm tròn/quy năm. Precision/rounding metadata chưa thay kiểm thử Ratio Kernel.

Các controls **chưa triển khai** và không được suy từ schema: query guard/anonymizer đầy đủ, tên thật/số viết bằng chữ, OutputValidator binding đầy đủ, renderer/Verifier, admission/ACL/persistence, engine AST tài chính, Redis quota/fairness, provider adapters và terms eligibility runtime. Model registry trong ca thử chỉ fixture synthetic; không có vendor/account nào được xác minh từ các ca này. Phép đo token-copy model đang NOT_RUN, không có ngưỡng tự đặt.

Tái lập: `python -m finagent.schema_catalog --check`, `pytest tests/contract/test_schema_review_catalog.py`. [Manifest](../schemas/frozen/manifest.json) frozen=true, giữ hash và archive ca đúng/sai khi duyệt; current regressions được chạy lại độc lập. Cùng major chỉ thêm DTO/optional fields; finite enum closed, extensible=[]; breaking cần major/ADR/migration/full snapshots. Ngoại lệ canonical/1 trước first real write qua ADR/hash/diff theo ARCHITECTURE§13; chưa có sửa breaking trong lượt này.
