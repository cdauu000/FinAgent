# Ghi chú đọc đặc tả FinAgent — Bước 0

Lập01/11/2026, cập nhật02/11/2026 (Asia/Bangkok). **Bước0 đã duyệt;14 nhóm schema đã frozen. Trạng thái Phase0 hiện hành xem PROGRESS; các ghi chú dưới đây giữ bối cảnh đọc ban đầu**. Kết quả chạy thật ở PROGRESS; đính chính nguồn FPT ở§4.2.

## 1. Nguồn đã đọc và giới hạn xác minh

Bước0 ban đầu đã đọc toàn bộ `CLAUDE.md`, 1.438 dòng Báo cáo chính v2.0 (24 mục và hai phụ lục), 497 dòng Báo cáo 2 (kể cả phụ lục), 355 dòng định nghĩa chỉ số. Đã render cục bộ và xem cả28 trang PDF được chủ dự án bổ sung ở Bước0 ban đầu, rồi tính lại các ca dưới đây bằng Python `decimal`, không cài thư viện hay gọi dịch vụ ngoài. Lượt cập nhật02/11/2026 đã đọc **toàn bộ482 dòng LLM_GATEWAY_DESIGN.md, gồm mục20**; không chạy probes/đọc console tài khoản hoặc xác minh điều khoản nhà cung cấp trong lượt tài liệu này.

| Tên trong yêu cầu | Tệp thực tế được đọc |
| --- | --- |
| `CLAUDE.md` | [CLAUDE.md](../CLAUDE.md) |
| `docs/bao-cao-chinh.md` | [Báo cáo chính v2.0](<Báo cáo tiền dự án FinAgent – Hệ thống Agent phân tích báo cáo tài chính.md>) |
| `docs/bao-cao-2-huong-phat-trien.md` | [Báo cáo 2](<Báo cáo 2 Hướng phát triển FinAgent sau khi hoàn thành core.md>) |
| `docs/LLM_GATEWAY_DESIGN.md` | [Thiết kế Gateway, gồm §20](LLM_GATEWAY_DESIGN.md) |
| `docs/15_financial_ratios.md` | [Định nghĩa 15 chỉ số](15_financial_ratios.md) |
| `samples/FPT_BCTC_rieng_Q1_2026.pdf` | [PDF FPT](../data/public_reports/20260424_-_FPT_-_BCTC_rieng_Quy_1_nam_2026_1777344035.pdf) |

Không đổi tên hoặc sao chép các nguồn để tránh tạo hai nguồn sự thật. Trong bộ tài liệu này, “§” chỉ mục của Báo cáo chính, “PDF p.” là trang vật lý tính từ 1; số trang in được ghi riêng. Workspace `C:\FinAgent` chưa có Git, mã nguồn, manifest, CI hoặc bộ kiểm thử. Không có `AGENTS.md` trên các đường dẫn cha và thư mục liên quan đã kiểm tra; áp dụng hướng dẫn AGENTS do người dùng cung cấp trong chat.

SHA-256 của nguồn lúc đọc:

```text
CLAUDE.md: 81705c15fb3a086b1fd360785773d2fd6068eaf5592cf087d53a61c37b12dab2
Báo cáo chính: 02951ad91d78bf7098e43b8493a71ef523f6f96c28b548f5c2a04cae2d691a1e
Báo cáo 2: b5b50ebe7f5a4994266f197ba74d157948adb815b625d4fbcb29b4b89498ac26
15_financial_ratios.md: 14c3942526334d05207468865909c1effaf7b87bcec57fc53a08a1b70e24d121
PDF FPT: 11c9709914cdc5f1561f47045283598c359f7466f94e5ffbc21893e28b0315fa
LLM_GATEWAY_DESIGN.md: e0ffbca7a92323cc519b9c2e6a0d47edd7482b502e25a3c6934f19e084cc6df3
```

**VERIFIED**: nội dung các tệp trên, cấu trúc PDF, các ô được dẫn cụ thể và phép tính thủ công bên dưới. **PARTIALLY VERIFIED**: ánh xạ quan sát được trên một mẫu FPT, chưa phải kho mẫu biểu pháp quy đầy đủ hay nhãn vàng đã được chủ dự án duyệt. **UNVERIFIED**: KPI OCR/RAG/Agent, hiệu năng, nguồn và quyền sử dụng kho lớn, hạn mức/model/điều khoản nhà cung cấp, khả năng triển khai thực tế. **CONFLICTING**: các điểm xung đột được ghi trong [ASSUMPTIONS.md](ASSUMPTIONS.md). Không có kết quả kiểm thử sản phẩm ở Bước 0.

## 2. Hiểu từng mục của Báo cáo chính

### §1. Tóm tắt điều hành

Backend đọc nhiều định dạng, chuẩn hóa dữ liệu, tính bằng công cụ tất định và trả lời có nguồn. Ba trụ cột là OCR được kiểm bằng kế toán, LLM không làm nguồn số, và ba trạng thái trả lời. Groq/Gemini chỉ xử lý ngôn ngữ tại hai vị trí; OpenAI/DeepSeek là dự phòng trả phí tắt. Báo cáo 2 chỉ định hình hợp đồng mở rộng, không mở phạm vi triển khai.

### §2. Mục tiêu, phạm vi, KPI

Mỗi module phải có interface/test hợp đồng, mọi tool có schema, không vòng phụ thuộc. Đích OCR: native ≥99,5%, scan ≥98,5%; mọi mã tổng được kiểm hoặc gắn cờ. Đích hỏi đáp: không có số không truy vết, recall ABSTAIN ≥95%, citation precision ≥95%. Hỗ trợ corporate VAS, riêng/hợp nhất, quý/bán niên/năm, Việt/Anh; chặn bộ chỉ số doanh nghiệp cho ngân hàng/chứng khoán/bảo hiểm. SME chỉ nhận khi có mẫu được xác minh, không suy ánh xạ từ TT200. Xem A03–A05, A40–A42.

### §3. Tài liệu mẫu và rủi ro OCR

FPT là công ty mẹ, kỳ 01/01–31/03/2026, VND; thư công bố nhắc hợp nhất nhưng bảng trong file là riêng. Cần phân vai cột, nối bảng, chuẩn hướng, giữ memo, phân biệt 0/missing và đơn vị VND/triệu đồng. Các đẳng thức và bất nhất cổ phiếu là ca vàng. Số dư so sánh B01 là 31/12/2025; dòng chảy so sánh là Q1/2025. Holding làm nhiều chỉ số tính được nhưng kém ý nghĩa. Các phát hiện trực tiếp từ PDF ở mục 4 dưới đây.

### §4. Kiến trúc

Luồng ingestion → router → extraction → statement understanding → validation/review → canonical; từ canonical tách analytics và retrieval, hội tụ tại Agent/Gate/Verifier/export. Security, policy, privacy, jobs và trace xuyên suốt. “Composer sau Verifier” trong sơ đồ §4.2 không được hiểu là cho phép bỏ hậu kiểm văn bản sau sinh; luồng mới theo D-GW-1/2 là composer mù giá trị →OutputValidator →renderer/khôi phục tên cục bộ →Verifier trước mọi answer/export. SSE chỉ tiến độ/result_ref theo A60, không answer streaming (A32).

### §5. OCR, S0–S10

Native-first theo từng trang; OCR cục bộ nhiều engine; lưu ảnh gốc và phép biến đổi. S0 triage, S1 xử lý ảnh, S2 layout, S3 cấu trúc bảng, S4 OCR ô, S5 chuẩn hóa, S6 ghép/dựng cây, S7 mapping, S8 kiểm kế toán, S9 sửa ứng viên có ràng buộc, S10 duyệt tay. Chỉ sửa khi một ứng viên quan sát được là nghiệm duy nhất, không tính ngược ô thiếu. A sạch/đẳng thức, B đồng thuận, C đơn nguồn, D nghi ngờ; kết quả lấy độ tin cậy thấp nhất. OCR phải benchmark trước chọn engine; nhãn bạc không thay vàng. A06–A10, A40–A42.

### §6. Canonical

Document/Page/Table/Statement/LineItem/Provenance/Issue/ReviewAction/Entity; bổ sung định danh tenant, phiên bản, nguồn gốc và quyền riêng tư xuyên mọi thực thể. Số dư dùng `as_of`, dòng chảy dùng khoảng ngày, không ghép nhầm cột so sánh. Lưu VND nguyên; số cổ phiếu, mệnh giá, tỷ lệ sở hữu cần kiểu đại lượng riêng. Báo cáo riêng/hợp nhất, gốc/điều chỉnh và mọi sửa tay tồn tại đồng thời, không ghi đè. A11–A14.

### §7. Validation

Sáu nhóm A–F: định dạng, nội bảng, liên báo cáo, liên kỳ, hợp lý, scope/đơn vị. Rule phải thuộc template/version cụ thể; memo không cộng lần hai. Dung sai VND đầy đủ bằng 0; số làm tròn ±1 đơn vị hiển thị. VERIFIED là đạt mọi BLOCK khả áp dụng với độ đầy đủ được ghi; PARTIAL cho phép phần độc lập; REJECTED không vào canonical phục vụ phân tích. Rule thiếu đầu vào là NOT_EVALUATED, không PASS. Phân biệt sai OCR, sai nguồn và khác định nghĩa; không sửa nguồn để khớp đẳng thức. A15–A18, A49–A51.

### §8. Evidence Gate

Gate xét coverage, period, scope, trust, consistency, recency và applicability trước sinh. Thiếu thiết yếu/sai kỳ-scope/REJECTED thì ABSTAIN; phần cốt lõi có bằng chứng thì có thể CAVEATS. Kết quả có verdict, evidence, calculations, assumptions, warnings, missing, next_actions. Các mã lý do §8.3 là enum chung. Nội dung tài liệu không có quyền đổi policy hoặc chọn tool. Hậu kiểm cần kiểm liên kết số–đại lượng–kỳ–scope–nguồn, không chỉ xem cùng một chuỗi số có xuất hiện đâu đó (A31–A33).

### §9. Analytics

15 chỉ số là các định nghĩa versioned, tách giá trị khỏi applicability và điểm. Current/Quick/Cash/đòn bẩy/margin/ROA/ROE/OCF dùng đúng chính sách; số quý mặc định không quy năm. Vòng quay dùng bình quân hai thời điểm đúng khoảng. Piotroski là lớp riêng, mỗi F là 0/1/UNAVAILABLE, khoảng điểm minh bạch; strict cần 9 thành phần mới gán nhãn, useful cần ≥7. Trend cần ≥3 điểm mới kết luận xu hướng, hai điểm chỉ báo biến động. Industry chỉ thêm nguồn/cờ, không đổi giá trị hoặc điểm cơ bản. Assessment cần ≥ceil(2n/3) chỉ số/trụ cột và ≥3/5 trụ cột; điểm/độ tin cậy tách riêng. Trọng số, bảng chuyển điểm, nhãn và trần rủi ro chưa được đặc tả đầy đủ (A19–A30).

### §10. Agent

Một Orchestrator: intake → ý định → kế hoạch → tool → Gate → bổ sung có giới hạn → soạn → Verifier → trả. Chốt entity/scope/period trước, hỏi rõ tối đa một câu; không dùng trí nhớ hội thoại làm nguồn số. 16 tool trong §10.2, kể cả hai tên chung một dòng, có schema vào/ra, quyền, timeout và hạn mức. `request_review` cần quyền riêng. Trace lưu hành động và kết quả, không lưu/phơi suy luận thô. A34–A35.

### §11. Chức năng bổ sung

Bắt buộc: completeness, Review API/CLI, template registry, compare_periods. Các mục “Nên có/Có thể” không mặc nhiên thành backlog core: chỉ lấy phần đã được các mục khác yêu cầu (ví dụ cờ phụ thuộc cổ tức, nguồn bối cảnh, export Excel ở §23). Chưa triển khai DuPont/CCC, Altman/Beneish, đồ thị đầu tư, cảnh báo tự động hay benchmark ngành. A36.

### §12. Công nghệ, API, bảo mật, Gateway

Python ≥3.11, FastAPI/Pydantic v2, PostgreSQL, file local hoặc S3 adapter, truy xuất lai cục bộ, job memory/Redis, trace có cấu trúc. API key/admin key, rate limit, MIME thực, giới hạn tài nguyên, SSRF, XML/zip/macro, tenant isolation, retention/xóa/audit. Mục tiêu native25p <30s, scan25p <180s, QA p95 <15s; idempotency và cache versioned. Gateway chỉ nhà cung cấp ngoài, có schema/capability registry/routing/quota/retry/circuit/cache/budget/mock; local inference qua LocalModelPort. Quota account_scope/model và công bằng tenant, tách runtime/dev keys, structured ladder và training_use/retention theo D-GW. OCR/embedding/rerank tuyệt đối local. CPU mặc định; GPU chỉ sau số đo, không provision ở Bước 0. A37–A39, A43–A48.

### §13. Kiểm thử

Unit/property → contract/integration → OCR golden → retrieval/Agent → security/load/expert. Đo các mẫu số rõ ràng, không đánh đồng test tổng hợp với dữ liệu thực. Corpus tách theo doanh nghiệp, test đóng băng, calibration chỉ dev. Mỗi metric có artifact và lệnh tái lập; hiện chưa có harness hoặc số đo KPI. [TEST_PLAN.md](TEST_PLAN.md) quy định cách đo và cổng CI.

### §14. Kho mã

Giữ các ranh giới module đã đề xuất. `analytics` đọc snapshot từ store, không đọc OCR hay gọi mạng; `agent` dùng tool registry; extraction không phụ thuộc analytics. Điểm ghép adapter nằm tại composition root. `tests/`, `eval/`, `docs/` ở gốc repo; package `finagent/` giữ các module nghiệp vụ, không tạo tài liệu chuẩn trùng lặp. Bước 0 chỉ tạo tài liệu.

### §15. Phase và cổng

Phase 0 nền tảng/dữ liệu; 1 S0–S5/OCR/huấn luyện; 2 S6–S10/store/review; 3 analytics; 4 retrieval/Gate/modes; 5 Gateway/Agent/API; 6 đánh giá/củng cố. Phase 1 đích ≥98% ô trước kế toán; Phase 2 ≥90% báo cáo VERIFIED và ô sai không cờ ≤0,1%; Phase 3 100% ca tính tay; Phase 6 đạt toàn bộ KPI. Dừng bắt buộc go/no-go sau Phase 1 và 2. 30 tuần là ước tính nhóm 3–4 người, không phải cam kết thời gian cho một phiên. Chưa đủ corpus không được tuyên bố đạt phase (A40–A42).

### §16. Rủi ro

Ưu tiên sai số âm thầm, sai template, sai nguồn, holding/tổ chức tài chính, model vượt quyền và privacy. Khắc phục bằng fail-closed, provenance, test đối kháng và review; không dùng hạ ngưỡng để vượt cổng. Giới hạn dữ liệu/hardware/API là phụ thuộc thật, phải báo rõ thay vì gắn PASS giả.

### §17. Quyết định đã chốt

Giữ nguyên 18 quyết định: đối tượng, privacy, ba chính sách chỉ số, hai mode, hai vị trí model, extractive QA, ẩn danh định danh, CPU trước, public-only training, industry sources-only, generic pack, single Agent, backend trước, chủ dự án duyệt. Câu “không còn vấn đề mở ở mức quyết định” không cung cấp các hằng số triển khai còn thiếu; các hằng số đó là đề xuất có nhãn ở ASSUMPTIONS, không thay quyết định nghiệp vụ đã chốt.

### §18. Tầng dữ liệu

Public/private/strict_private; không chắc public thì private. Nâng độ riêng tư được phép, hạ chỉ admin và audit. Mọi derivative kế thừa tầng nghiêm nhất. Strict_private không outbound API. Theo D-GW, private opt-in chỉ được gửi intent đã mask và descriptors mù giá trị khi training_use/retention đạt bound tenant; không gửi đáp số. Tài liệu không outbound kể cả public. Không đưa private vào corpus training; cache/log/trace chịu isolation. Artifacts private30ngày đã duyệt, khác bound lưu của provider. A43–A46.

### §19. Hai mode

Lớp N: không số sai không cờ, không số mất provenance. Useful chỉ cho hiện C kèm “chưa xác minh”, không dùng C để chấm điểm; D luôn chặn. Lớp Q: strict yêu cầu trực tiếp từng mệnh đề; useful trả phần đủ với caveats. KPI strict ≥99% support, false ABSTAIN ≤15%; useful ≥95%, ≤5%, coverage ≥90%. Assessment và export chính thức bắt buộc strict; precedence system → tenant → key → request trong giới hạn cha. Các mức KPI Q là đề xuất trong báo cáo nhưng dùng làm đích nghiệm thu cho tới khi chủ dự án duyệt thay đổi, không tự giảm. A29–A33, A41.

### §20. Registry và chính sách chỉ số

Cash mặc định 110, mở rộng 110+120 có cờ. Receivables mặc định 131, thiếu 131 mới fallback130 có cờ đúng nguyên văn; 131=0 không fallback. Debt/D/E chính dùng300, đồng thời xuất tham chiếu nợ vay có lãi; không đếm trùng trái phiếu đã nằm trong khoản vay. Registry là DSL khai báo an toàn, cấm Python/eval/import tùy ý; 15 core khóa theo version. Extended chỉ chấm khi được duyệt và có trọng số, experimental không chấm. A19–A24, A52.

### §21. Corpus

Sáu công dụng: đánh giá, chọn/huấn luyện OCR nhỏ, mapping, calibration confidence, benchmark tương lai, câu hỏi mẫu. Chia train/dev/test theo entity/group công ty để tránh leakage, không chia trang. Vàng cần chuyên gia duyệt ô; bạc từ VERIFIED/teacher chỉ phụ trợ. Đợt đầu ≥30 và cuối ≥100 báo cáo đa dạng; FPT hiện là một ca phát triển đã được mô tả công khai, không thể coi là test mù. A40–A42.

### §22. EP1–EP12

Core phải thực sự chạy qua registry/pack/template/rule/applicability/classifier/role/tool/Gateway/connector/flags/API-event. Chỉ ship `generic@1`, interface `spack/1`, chiến lược `single`. Pack versioned, kiểm schema/ref/min_core/test khi nạp; pack không sửa giá trị công thức. Có `statement_family`, `template_id`, `source_tier`, policy/definition/pack/mode version trong kết quả. Không chỉ tạo interface rỗng rồi bypass nó. Test chứng minh adapter thử nghiệm mới đi qua hợp đồng mà không sửa core; không ship tính năng mở rộng. A47–A48.

### §23. Backend hoàn chỉnh

Vận hành đủ qua API/CLI: ingestion/review/analysis/Agent/jobs/admin/privacy/export/eval/runbook. `/v1`, phân trang, idempotency, SSE, cell crop+bbox, public explanation, i18n và webhook job hoàn tất. D-GW-6 cấm streaming/hedging; A60 đề xuất SSE chỉ tiến độ/result_ref, lấy full answer sau Verifier qua GET. Webhook là tích hợp backend opt-in, không phải Codex lifecycle hook; mặc định tắt và chỉ payload tối thiểu. A37–A39, A46.

### §24. Ranh giới model

Outbound runtime chỉ `intent_parse` và `answer_compose`. Không raw tables, snippets, page images/PDF, embedding API, OCR API hoặc model verifier ngoài. Intent payload không được mang tài liệu người dùng dán vào câu hỏi, giá trị số user gõ hoặc assistant answers/tool results trong lịch sử; composer chỉ nhận claim descriptors mù giá trị, không nhận đáp số (D-GW-1). Anonymizer giữ mapping/value placeholders local, tokens random từng run (tenant-stable chỉ admin-approved). Quá hạn mức/lỗi/schema/verifier/budget/private policy thì local intent + template; vẫn Gate/Verifier. Public VLM labeling là công cụ phát triển riêng, không chung đường runtime; core không hiện thực hai cờ tóm tắt tài liệu/ngành dù dành sẵn EP11. A31–A35, A43–A48.

### Phụ lục A

15 ca theo quý, chưa annualize, cộng Piotroski/scope/source conflict là bắt buộc. Dùng số VND đầy đủ trong PDF để tạo oracle; số tỷ đồng làm tròn trong phụ lục chỉ kiểm cách hiển thị. Không đảo công thức từ con số mong muốn. Kết quả kiểm tra thủ công ở mục 4 và catalog tại TEST_PLAN.

### Phụ lục B

Là mapping quan sát một mẫu, không phải danh mục mọi thông tư. PDF xác nhận mã321 là vay ngắn hạn, 322 là dự phòng, B02 mã22 là doanh thu tài chính và24 là memo chi phí đi vay. Không áp mapping mẫu cũ từ trí nhớ. Căn cứ văn bản/mốc hiệu lực mẫu chưa được cung cấp đủ; template FPT ban đầu gắn hash mẫu đã quan sát, chỉ phát hành mapping tổng quát sau bước xác minh Phase 0 (A03–A05).

## 3. Ghi chú hai tài liệu còn lại

**Báo cáo 2:** đã đọc D1–D14, giả định ngân hàng A1–A7 và checklist A–E. Core chỉ chuẩn bị EP. D1/D2/D4 cần pack/classifier; D3/D7/D8/D14 cần template/rules/canonical concepts; D5 cần role/schema messages/budget/trace tree; D6 cần DSL/registry; D9/D10/D12 cần flags/adapters; D11 dùng `/v1`/events/crops; D13 thêm tool. Không hứa mọi mở rộng đều chỉ đổi cấu hình: báo cáo 2 §2/§11 thừa nhận cần đổi core nếu thiếu kiểu dữ liệu, phép toán hoặc giao thức. Đặc biệt P/E/P/B cần thực thể giá thị trường, ngoài core. D9 gửi snippet công khai xung đột bất biến runtime hiện hành: chỉ giữ cờ và policy capability bị chặn, cần quyết định chính sách sau này.

**15_financial_ratios.md:** đủ 15 công thức và diễn giải, nhưng chưa có hàm chấm điểm hoàn chỉnh. Debt “>0,5 rủi ro” giao với dải “0,4–0,6 lý tưởng”; D/E “<1 an toàn” giao với “1–2,5 lý tưởng”; OCF/assets cuối tài liệu “10–20% tối ưu” giao với đoạn trước “>20% mạnh”. Biên gộp, receivable turnover và asset turnover có dải chồng/gap. Không tự biến ví dụ theo ngành thành Sector Pack. §20 báo cáo chính giải quyết nghĩa “nợ”, “tiền”, “phải thu”; không hỏi lại các quyết định đó. Catalog ngưỡng và phần cần duyệt nằm trong ARCHITECTURE/A25–A28.

## 4. Đối chiếu PDF FPT

### 4.1 Bản đồ trang và quan sát

| Trang PDF | Trang in / nội dung | Điều đã đối chiếu |
| --- | --- | --- |
| 1–3 | Thư công bố, bìa, mục lục | Thư nhắc cả hai scope; bìa/bảng xác định riêng; 28 trang vật lý |
| 4–5 | 3–4, B01 | Số hiện tại/31-12-2025, đơn vị, tổng, dòng321/322, memo411a/420a/420b |
| 6 | 5, B02 ngang | Bốn cột Q1/YTD, mã22/24, VND, khoản giảm trừ và thuế hiện hành gạch ngang |
| 7 | 6, giải trình ngang | Triệu đồng, phí quản lý nội bộ và tăng thu nhập cổ tức; chỉ là đối chiếu phụ |
| 8–9 | 7–8, B03 | OCF âm, đầu tư/tài chính, tỷ giá61, tiền cuối70 |
| 10–14 | 9–13, chính sách | VND, niên độ01/01–31/12, đầu tư, FIFO, khấu hao, doanh thu, thuế |
| 15–16 | 14–15, TM1–4 | Tiền tương đương≤3 tháng;120 có cả tiền gửi, cho vay, lãi; đầu tư nhiều cột gross/net |
| 17–18 | 16–17, TM5–6 | Hai thành phần khấu hao khớp CF02 |
| 19–21 | 18–20, TM7–12 | Công ty con/liên kết, phải trả, thuế, chi phí; số dư khác dòng chảy |
| 22 | 21, TM13 ngang | Vay6.327.887.440.200; vay nội bộ4.664.000.000.000; roll-forward |
| 23–24 | 22–23, TM14–17 | Vốn góp không đổi trong quý, LNST, sai số cổ phiếu cột31/12, doanh thu/giá vốn/cổ tức |
| 25 | 24, TM18–20 | Chi phí tài chính có khoản tỷ giá âm; thuế; danh sách bên liên quan |
| 26–28 | 25–27, TM20–21 | Số dư/giao dịch liên quan; xác nhận cơ sở kỳ so sánh |

### 4.2 Đẳng thức và bất nhất

- `10.626.141.721.085 + 22.441.574.606.461 = 33.067.716.327.546` (PDF4).
- `7.757.537.821.182 + 25.310.178.506.364 = 33.067.716.327.546` (PDF5).
- B01-110 và B03-70 bằng `2.231.448.721.940` (PDF4/9).
- `−401.953.448.193 + 2.381.155.178.054 − 1.653.002.529.850 = 326.199.200.011` (PDF8/9).
- `326.199.200.011 + 1.905.249.672.046 − 150.117 = 2.231.448.721.940`. Nhãn in PDF9 ghi `70=50+60`, thiếu61; lưu nhãn gốc, kiểm số theo rule đầy đủ §7.
- LNST `1.828.028.020.122` khớp B02-60/B01-420b/TM14 (PDF6/5/23).
- `29.035.596.118 + 6.561.356.227 = 35.596.952.345` (PDF17/18/8).
- Vốn góp `17.035.071.210.000 / 10.000 = 1.703.507.121` cổ phiếu; cột31/12/2025 TM14 ghi `1.471.069.183`, lệch `232.437.938` (PDF5/23/24). Giữ nguyên và gắn `SOURCE_INCONSISTENCY`.
- **Đính chính nguồn trước khi dùng oracle:** ảnh cắt trực tiếp PDF vật lý6 xác nhận B02-23 **97.623.991.644**, từng nhóm chữ số `97 / 623 / 991 / 644`; xem [cận số](evidence/fpt_q1_2026/b02-code23-digits.png) và [bảng/nhãn cột](evidence/fpt_q1_2026/b02-rows20-30.png). Số97.623.971.644 trước đây là lỗi đọc của hồ sơ, không phải bất nhất PDF. Đẳng thức độc lập: `134.766.471.688 + 1.947.580.037.222 − 5.768.333 − 147.247.456.935 − 97.623.991.644 = 1.837.469.291.998` (mã30).
- [Ảnh TM18, PDF25](evidence/fpt_q1_2026/note18-finance-costs.png) xác nhận `(1.685.413.336)`, từng nhóm `1 / 685 / 413 / 336`, và tổng97.623.991.644. `99.309.404.980 − 1.685.413.336 = 97.623.991.644`; B02-24 vẫn lớn hơn23 nên rule hợp lý E phát WARN, không BLOCK/sửa số đúng.
- [CF04, PDF8](evidence/fpt_q1_2026/cf04-current-prior.png) âm1.685.263.219; TM18 âm1.685.413.336: chênh150.117 bằng trị tuyệt đối CF61 kỳ này ([PDF9](evidence/fpt_q1_2026/cf61-current-prior.png)). **Chưa chứng minh bridge:** kỳ trước `1.533.326.629 − 1.498.048.003 = 35.278.626`, khác trị tuyệt đối CF61 `35.278.716` đúng90 đồng. Giữ CLASSIFICATION_DIFFERENCE_UNRESOLVED/WARN, tolerance exact0; không suy nguyên nhân, không tự sửa nguồn. Metadata render/crop và SHA256 ở [hồ sơ bằng chứng](evidence/fpt_q1_2026/README.md).

### 4.3 Tính lại chỉ số bằng Decimal

Số dưới đây là phép tính kiểm tra độc lập của Bước 0, **không phải kết quả kernel, OCR hoặc KPI**. TEST_PLAN ghi đầy đủ đầu vào, precision và test oracle dự kiến.

| Chỉ số | Kết quả chưa làm tròn (rút ngắn để đọc) | Kỳ vọng hiển thị |
| --- | --- | --- |
| Current | 1,408433294867 | 1,41 |
| Quick | 1,408326864702 | 1,41 |
| Cash110 / mở rộng110+120 | 0,295765552377 / 1,138648674961 | 0,30 / 1,14 |
| Debt / D/E | 0,234595511354 / 0,306498739992 | 0,235 / 0,306 |
| ICR | 19,502784983074 | 19,5; phụ thuộc cổ tức |
| Tồn kho | Phép chia thô49,154788429360 | N/A do applicability, không trình bày vòng quay thô như có ý nghĩa |
| Phải thu131 | 1,010381449078 | ≈1,01/quý, NOT_MEANINGFUL |
| Vòng quay tài sản | 0,005066306984 | ≈0,005/quý, NOT_MEANINGFUL |
| Biên gộp / ròng | 80,254839771001% / 1.088,609755929774% | 80,3% / ≈1.089%; ròng NOT_MEANINGFUL |
| ROA / ROE cuối kỳ | 5,528135060839% / 7,222501491494% | 5,53% / 7,22%; theo quý, cờ holding/cổ tức |
| OCF/nợ ngắn hạn | −0,053276592227 | −0,053 |
| OCF/tài sản | −1,215546438743% | −1,22% |
| Nợ vay/tài sản / vốn chủ | 0,191361489179 / 0,250013544496 | ≈0,191 /0,250; tham chiếu, không chấm điểm |

Không phát hiện lệch ca vàng do số học. ROA bình quân5,515231209183% và ROE bình quân7,493095975800% là biến thể khác, không thay5,53%/7,22%. Piotroski theo căn cứ Phụ lục A: F1=1, F2=0, F4=0, F7=1, F8=0; F3/F5/F6/F9 UNAVAILABLE →2 điểm, khoảng[2,6], không nhãn. F7 dựa roll-forward vốn quý PDF23; vẫn đính bất nhất bảng cổ phiếu PDF24, không xóa mâu thuẫn (A30).

## 5. Các điểm phải xử lý trước triển khai và nghiệm thu

Các khoảng trống A01–A61 tại [ASSUMPTIONS.md](ASSUMPTIONS.md). Bước0 đã duyệt; Assessment generic v0 là cơ sở đã duyệt nhưng kết quả trên kho chưa duyệt nên giữ POLICY_UNAPPROVED. Corpus Phase0 đổi rõ thành≥30 manifest+≥10 gold approved do chủ dự án cung cấp, gold còn lại Phase1–2; không tự thu thập. A53–A60 được duyệt theo mức ghi ở ASSUMPTIONS; K19/K20 chưa ngưỡng. A61 là chi tiết draft cần review cùng schema P0.05, không thay ngưỡng KPI.

Bước0 ban đầu chỉ docs; sau phê duyệt mới tạo Git/venv/scaffold/CI và draft contracts ở Phase0. Không tạo API keys, cài global tool/plugin/MCP hoặc hooks; không gọi provider. Snapshot tests không tự đóng băng schema. Dừng P0.05 trước P0.06–P0.11; kiểm tra tài liệu không thay KPI sản phẩm.

## 7. Đối chiếu toàn bộ thiết kế Gateway và phê duyệt mới

**Đã đọc:** §§1–4 nêu G1–G14, giới hạn hai task ngoài và các DTO; §§5–8 quy định call flow, mask user values, enum intent/clarification, value-blind compose/typed segments và adapters/structured ladder; §§9–13 về route/quota/budget/circuit/privacy/keys/cache; §§14–19 về trace/metrics, version freeze, phase/test/triển khai và các điểm chốt; **§20 đã đọc toàn bộ nhưng chỉ là tham khảo thứ cấp ngày01/11/2026**. Không ghi lại quota/điều khoản hay đánh giá eligibility của vendor từ phần này.

**Ưu tiên quyết định:** D-GW-1–8 do chủ dự án nêu ngày02/11/2026 thay thế các đoạn cũ về composer values, token tenant-stable, data_use hoặc streaming. Không chấp nhận ngoại lệ with_values; không cố định provider order theo bảng trong tài liệu. Bậc structured output và model/account eligibility phải được P0.10 xác minh riêng bằng official docs + actual account limits + terms, checked_at và quota source manual_console/probe/header_hint; thiếu quyền/keys ghi NOT_RUN. Khác khóa không tự chứng minh khác quota scope.

**Chỗ thiếu của nguồn và quyết định sau đó:** GatewayOutcome ở§4 bị cắt, phương án A59 đã được duyệt cơ sở. Chủ dự án đã chốt A54 không history và A60 SSE chỉ progress/result_ref. Tham số fairness/terms review còn chờ đo theo A55/A56; model-quality thresholds A57 chưa duyệt. Không dùng hằng số timeout/circuit hay terms tham khảo để lấp chỗ trống.

Audit G1–G14 trước/sau nằm trong [PROGRESS.md](PROGRESS.md); hợp đồng ở ARCHITECTURE§§2/5/10/13, tasks ở PLAN và GW01–GW14/T05/T14/T26–T29/K19–K20 ở TEST_PLAN. “Đã đáp ứng” trong audit nghĩa là **hồ sơ đã mô tả hợp đồng và kiểm thử cần có**, không phải sản phẩm đã triển khai hoặc các KPI đã đo.
