# Thiết kế chi tiết LLM Gateway cho FinAgent

*Bổ sung cho ARCHITECTURE.md mục 10 và 12, đối chiếu với Báo cáo chính v2.0 mục 12.5 và 24 · 01/11/2026 · Chỉ thiết kế, chưa viết mã*

## 0. Cách dùng tài liệu này

Tài liệu này đã đọc toàn bộ ARCHITECTURE.md (13 mục) và đối chiếu mục 10 với các mục liên quan: module (mục 2, 5), công cụ Agent (mục 8), Gate và Verifier (mục 9), API và sự kiện (mục 11), điểm mở rộng (mục 12). Mọi nội dung ở đây là **đề xuất chờ chủ dự án duyệt**, không tự thay đổi bất biến nào của đặc tả. Những chỗ khác với ARCHITECTURE hoặc đặc tả được gắn nhãn **\[ĐỀ XUẤT THAY ĐỔI\]** và tổng hợp ở mục 17.

## 1. Kết quả đọc: mục 10 đã đúng ở đâu, còn thiếu gì

### 1.1 Giữ nguyên (đã đúng và nhất quán toàn kiến trúc)

- Chỉ hai tác vụ ra ngoài (`intent_parse`, `answer_compose`); mọi thứ khác cục bộ.
- Chuỗi bước Gateway: phân loại tác vụ → tầng dữ liệu và cờ → ẩn danh/query guard → payload whitelist có kiểu → chọn năng lực → giữ chỗ hạn mức và ngân sách → EgressGuard cấp permit → gọi adapter → kiểm schema → đối soát usage → trace và cache an toàn.
- `EgressPermit` dùng một lần, gắn hash payload, tác vụ, provider/model, hạn dùng.
- `paid_fallback=false` mặc định; ngân sách cứng theo tháng, job, người dùng; giá chưa biết thì không coi là miễn phí.
- Không retry lỗi xác thực hay chính sách; lỗi tạm thời dùng backoff có jitter trong deadline; circuit breaker theo provider/model.
- Tắt hết provider vẫn chạy được lõi số và đường khuôn mẫu (T24–T27, K15).

### 1.2 Khoảng trống tìm thấy

| # | Khoảng trống | Hệ quả nếu không xử lý | Mục xử lý |
| --- | --- | --- | --- |
| G1 | `FinalAnswerPayload` gửi **giá trị cuối** của số liệu. Ẩn danh tên doanh nghiệp không đủ vì số liệu đặc trưng vẫn tái nhận diện được (Báo cáo chính 24.6) | Rò rỉ gián tiếp, đặc biệt ở tầng riêng tư | 7.1 |
| G2 | `AnswerDraft` là văn bản tự do, nên Verifier phải bắt số sai bằng đối chiếu chuỗi (khó, dễ sót như ROE gán thành ROA, Q1 thành Q2) | Số sai lọt hoặc chặn nhầm | 7.2 |
| G3 | `IntentPlan.clarification_request?` là văn bản do model viết | Văn bản không kiểm soát được đi thẳng tới người dùng | 6.3 |
| G4 | Số do người dùng gõ trong câu hỏi (ví dụ T05 “doanh thu là 1.680 tỷ”) vẫn đi trong `IntentPayload` | Số của người dùng có thể là số thật của doanh nghiệp | 6.2 |
| G5 | Lịch sử hội thoại: mục 10 chỉ nói “pseudonymous context selectors” | Chưa rõ lượt trước nào được gửi, có chứa đáp số cũ không | 6.4 |
| G6 | Token ẩn danh “ổn định theo run/tenant” mơ hồ | Nếu ổn định theo tenant, nhà cung cấp có thể liên kết cùng một doanh nghiệp qua nhiều lời gọi | 12.2 |
| G7 | Chưa nói trạng thái hạn mức dùng chung khi có nhiều worker; chưa có công bằng giữa các tenant | Một tenant ăn hết hạn mức miễn phí, hoặc đếm sai khi chạy nhiều tiến trình | 10 |
| G8 | Chưa phân tách khóa và hạn mức giữa runtime và gắn nhãn phát triển (`dev_public_labeling`) | Việc gắn nhãn hàng loạt làm cạn hạn mức của runtime | 9.4 |
| G9 | Chưa có thang năng lực cho đầu ra có cấu trúc khi provider không hỗ trợ schema gốc | Adapter xử lý mỗi nơi một kiểu | 8.2 |
| G10 | Chưa nói gì về streaming và gọi song song (hedging) | Streaming trái “chỉ phát output đã verified”; hedging nhân đôi hạn mức và lượng dữ liệu ra ngoài | 5.3 |
| G11 | Dữ liệu cảnh báo phân biệt “điều khoản gói miễn phí chưa xác minh” chưa gắn vào định tuyến | Tầng riêng tư có thể rơi vào gói không rõ điều khoản | 12.3 |
| G12 | Lược đồ của Gateway (`IntentPayload`, `FinalAnswerPayload`, `AnswerDraft`) không nằm trong danh sách phiên bản đóng băng ở Phase 0 (mục 13) | Đổi schema giữa chừng làm vỡ cache, test và prompt | 15 |
| G13 | Chưa có đo chất lượng theo model cho composer (tỉ lệ bị Verifier từ chối) | Không biết model nào đáng giữ trong chuỗi | 14 |
| G14 | Gateway vừa là cổng ngoài vừa nói “local intent/template”: ranh giới với suy luận cục bộ (embedding, rerank, phân loại) chưa rõ | Dễ nhét suy luận cục bộ vào Gateway hoặc ngược lại | 2 |

## 2. Phạm vi và ranh giới

- **Gateway chỉ phục vụ nhà cung cấp bên ngoài** cho đúng hai tác vụ. Suy luận cục bộ (embedding, rerank, phân loại trang, nhận diện ý định dự phòng) đi qua cổng riêng `LocalModelPort`, **không** đi qua Gateway.
- Gateway điều phối thứ tự thử: nhà cung cấp ngoài → bộ nhận diện ý định cục bộ hoặc template cục bộ. Kết quả luôn mang `source=provider|local` và danh sách lý do chuyển bước.
- Gateway **không** biết Evidence Gate, Verifier, tool, snapshot hay kho chuẩn. Nó chỉ nhận payload đã dựng từ module gọi và trả kết quả có kiểu.
- **Không import chéo:** chỉ `llm_gateway/adapters/*` được import HTTP client của provider; không module nào khác được import adapters. Kiểm tra bằng AST có cạnh bắc cầu (mục 16).

## 3. Thành phần

| Thành phần | Trách nhiệm | Phụ thuộc |
| --- | --- | --- |
| `GatewayFacade` | Hai phương thức `parse_intent`, `compose_answer`; điều phối toàn bộ chuỗi bước | Tất cả bên dưới |
| `TaskPolicy` | Phân loại tác vụ, quyết định chuỗi thử theo tầng, chế độ, cờ | `policy.PolicyResolver`, `FeaturePolicy` |
| `PayloadBuilder` | Dựng payload có kiểu từ whitelist; từ chối trường ngoài whitelist | Schemas `gateway/1` |
| `AnonymizerPort`, `QueryGuardPort` | Ẩn danh, che số, phát hiện văn bản dán vào câu hỏi (cục bộ) | Chạy trước Gateway; không import adapters |
| `PromptRegistry` | Lưu prompt có phiên bản theo tác vụ và ngôn ngữ | Tệp khai báo có hash |
| `ModelRegistry` | Danh sách model và năng lực đã xác minh (`ModelCapability`) | Kết quả P0.10, tệp có `checked_at` |
| `Router` | Lọc rồi xếp hạng ứng viên (mục 9) | Registry, Quota, Breaker, Budget |
| `QuotaStore` | Token bucket theo (provider, model, khóa): RPM, TPM, RPD; giữ chỗ và đối soát | Bộ nhớ hoặc Redis |
| `BudgetLedger` | Ngân sách tháng, job, người dùng, tenant; bảng giá có nguồn và ngày | Postgres hoặc bộ nhớ |
| `CircuitBreaker` | Trạng thái đóng, mở, nửa mở theo provider/model | Bộ nhớ hoặc Redis |
| `EgressGuardPort` | Cấp `EgressPermit` một lần | `security` |
| `ProviderAdapter` (×4 + mock) | Chuyển yêu cầu chuẩn sang định dạng provider và ngược lại | HTTP client |
| `OutputValidator` | Kiểm schema, trường lạ, quy tắc đầu ra (mục 6, 7) | Schemas |
| `GatewayCache` | Cache theo khóa an toàn (mục 13) | Bộ nhớ hoặc Redis |
| `LocalIntentParserPort`, `TemplateComposerPort` | Đường dự phòng cục bộ | Module agent |
| `GatewayTrace` | Metadata an toàn cho trace và metric | `observability` |

## 4. Hợp đồng dữ liệu (`gateway/1`)

### 4.1 Lời gọi chuẩn và kết quả

| Schema | Trường chính |
| --- | --- |
| `GatewayRequest[T]` | task, payload kiểu `T`, `ExecutionContext` tham chiếu (tenant, tier, mode, deadline, priority), `PolicySnapshot` đã resolve, prompt/schema version cần dùng |
| `ProviderRequest` | provider, model, task, messages có vai trò, schema đầu ra, tham số sinh (nhiệt độ thấp, giới hạn token ra, không streaming), timeout, permit ID |
| `ProviderResult` | kết quả đã parse, provider/model, phiên bản schema/prompt/model-registry, usage (token vào/ra), độ trễ, chi phí ước tính + nguồn và ngày bảng giá, số lần thử, lỗi đã chuẩn hóa |
| `GatewayOutcome[T]` | \`source=provider |
| `GatewayError` | mã chuẩn hóa (mục 5.2), `retryable`, lý do an toàn; không chứa payload hay thông điệp thô của provider |

### 4.2 Quy ước

- Pydantic v2, `extra='forbid'`, bất biến; đầu ra provider có trường lạ thì bị loại, không dùng.
- Không số tài chính dạng float; usage và độ trễ được phép là float/int.
- Mọi payload, kết quả và lỗi có `schema_version`; `gateway/1` được đóng băng ở Phase 0 cùng các phiên bản khác (mục 15).

## 5. Quy trình gọi

### 5.1 Trình tự

1. **Phân loại tác vụ và dữ liệu:** lấy tier hiệu lực (nghiêm nhất trong các nguồn), chế độ, cờ.
2. **Quyết định đường:** nếu tier là strict\_private, tenant chưa opt-in, query guard báo có dữ liệu dán vào, hoặc không còn provider đủ điều kiện, đi thẳng đường cục bộ (bước 12).
3. **Ẩn danh và che số** (mục 6.2, 7.1) cục bộ; lưu bảng ánh xạ cục bộ theo run.
4. **Dựng payload whitelist**; schema từ chối mọi trường ngoài danh sách.
5. **Tra cache** (mục 13); trúng thì đi tiếp đến bước 11.
6. **Chọn ứng viên** theo Router (mục 9); nếu không có thì bước 12.
7. **Giữ chỗ hạn mức và ngân sách** (mục 10).
8. **Xin `EgressPermit`**; bị từ chối thì chuyển bước 12, không thử provider khác.
9. **Gọi adapter** với timeout lấy từ deadline còn lại của yêu cầu.
10. **Kiểm đầu ra:** schema, trường lạ, quy tắc đặc thù tác vụ (mục 6, 7). Sai thì áp dụng ma trận lỗi (mục 5.2).
11. **Đối soát usage, ghi trace và cache**, trả kết quả cho nơi gọi (rồi nơi gọi tự khôi phục định danh cục bộ và chạy Verifier).
12. **Đường cục bộ:** `LocalIntentParserPort` hoặc `TemplateComposerPort`; đánh dấu `source=local`, `degraded=true`.

### 5.2 Ma trận lỗi và hành vi

| Loại lỗi (đã chuẩn hóa) | Hành vi |
| --- | --- |
| `TIMEOUT`, `UPSTREAM_5XX`, lỗi mạng | Thử lại cùng provider tối đa 2 lần với backoff mũ cộng jitter, trong deadline; hết thì ứng viên kế tiếp (xin permit mới) |
| `RATE_LIMITED` (429) | Không dồn dập thử lại; đánh dấu bucket cạn đến thời điểm reset (dùng thông tin provider trả về làm gợi ý, không tin tuyệt đối); ứng viên kế tiếp |
| `AUTH_FAILED` (401/403) | Không thử lại; mở circuit cho khóa đó; cảnh báo quản trị; ứng viên kế tiếp |
| `POLICY_DENIED` (permit, ngân sách, cờ) | Không thử lại; không đi đường trả phí; chuyển đường cục bộ |
| `SCHEMA_INVALID`, đầu ra không parse được | Thử lại một lần cùng model chỉ với mã lỗi schema (không chứa nội dung); sau đó ứng viên kế tiếp |
| `CONTENT_BLOCKED` hoặc model từ chối | Ứng viên kế tiếp; hết thì cục bộ |
| `MODEL_UNAVAILABLE` (bị gỡ, không tồn tại) | Đánh dấu `deprecated` trong registry (cục bộ), cảnh báo; ứng viên kế tiếp |
| `CONTEXT_TOO_LARGE` | Coi là lỗi lập trình (payload nhỏ theo thiết kế); cảnh báo và đường cục bộ |
| `BUDGET_EXCEEDED` | Không gọi; đường cục bộ |
| Verifier từ chối bản soạn | Một lần soạn lại với mã lỗi (mục 7.4); sau đó template cục bộ |

### 5.3 Điều không làm

- **Không streaming từ provider.** Mọi lời gọi là không streaming; kết quả chỉ được phát ra sau Verifier (đúng ARCHITECTURE mục 11.2).
- **Không gọi song song để giảm độ trễ (hedging):** nhân đôi hạn mức và lượng dữ liệu ra ngoài.
- **Không để model gọi công cụ trên kết quả tài liệu.** Mục 10 đã quy định đúng; Gateway chỉ nhận giản đồ hành động, không nhận kết quả công cụ.

## 6. Tác vụ `intent_parse`

### 6.1 Danh mục hành động model được chọn

Model không nhận 16 công cụ đầy đủ. Nó nhận **danh mục hành động chỉ đọc** (kiểu `IntentAction`), vì công cụ có tác dụng phụ (`request_review`, `export_result`) không do model kích hoạt.

| Hành động | Tham số (kiểu chặt, không văn bản tự do) |
| --- | --- |
| `get_statement` | `entity_token`, `statement_type`, `scope`, `period` |
| `list_periods`, `list_documents`, `get_document_status` | `entity_token?`, `document_ref?` |
| `compute_ratios` | `entity_token`, `ratio_ids` (liệt kê trước), `scope`, `period`, `cash_basis?`, `receivables_basis?` |
| `compute_trend`, `compare_periods` | `entity_token`, `ratio_ids?`, hai `period` hoặc dãy kỳ |
| `compute_piotroski`, `assess_health` | `entity_token`, `scope`, `period`, `comparison_mode?` |
| `explain_ratio` | `ratio_id`, `variant?` |
| `search_evidence` | `entity_token?`, `scope?`, `period?`, `query_rewrite` (chuỗi ngắn, chỉ ký tự chữ, không chữ số) |
| `get_note_table`, `get_validation_report`, `get_industry_context` | tham chiếu có kiểu |
| `verify_user_claim` | `claim_kind`, `placeholder_ref` (xem 6.2); giá trị do cục bộ đọc |
| `request_export` | `format`, `purpose`; chỉ ghi nhận ý định, việc xuất phải qua API có quyền `export:create` |
| `decline` | `reason` thuộc enum: `OUT_OF_DOMAIN_ADVICE`, `FORECAST`, `MARKET_PRICE`, `UNSUPPORTED` |

Không có tham số kỳ ngầm định như “mới nhất”: kỳ không rõ thì `period=UNSPECIFIED` và đi vào làm rõ (T14).

### 6.2 Che số trong câu hỏi **\[ĐỀ XUẤT THAY ĐỔI\]**

Bộ ẩn danh thay mọi **số do người dùng gõ** (ví dụ “1.680 tỷ”, “49”) bằng ký hiệu `⟦N1⟧`, giữ giá trị cục bộ. Model chỉ thấy ký hiệu; hành động `verify_user_claim` tham chiếu `⟦N1⟧`, và cục bộ đọc giá trị để đối chiếu với kho (T05, T06). Lý do: số người dùng nêu có thể là số thật của doanh nghiệp. Năm và quý được giữ vì cần cho tham số kỳ; giá trị tiền, tỉ lệ và đếm bị che.

### 6.3 Làm rõ bằng mã, không bằng văn bản

`IntentPlan` có trường `clarification` kiểu enum: `ENTITY`, `PERIOD`, `SCOPE`, `RATIO`, `AMBIGUOUS_REQUEST`. **Câu hỏi làm rõ do mẫu cục bộ sinh ra** (một câu gộp, đúng yêu cầu T14). Cách này thay `clarification_request` văn bản tự do. **\[ĐỀ XUẤT THAY ĐỔI\]**

### 6.4 Ngữ cảnh hội thoại

Payload chứa tối đa N lượt người dùng gần nhất đã được ẩn danh và che số, cùng `SessionSelection` giả danh (entity token, scope, kỳ đang xét). **Không** chứa câu trả lời của hệ thống, đáp số, hay kết quả công cụ. Đổi entity, scope, kỳ phải có lựa chọn mới và xác nhận (T28).

### 6.5 Chống chỉ thị trong câu hỏi

Câu hỏi người dùng là **dữ liệu không tin cậy**. Prompt đặt câu hỏi trong khung dữ liệu; đầu ra chỉ được là JSON theo schema; mọi hành động nằm ngoài danh mục bị loại. Quyền, tenant, chế độ, tier không bao giờ là tham số model đưa ra.

### 6.6 Đường cục bộ khi không có provider

`LocalIntentParserPort` trả đúng schema `IntentPlan`, gồm luật theo từ khóa và khe (tên chỉ số, năm, quý, riêng/hợp nhất) cộng bộ phân loại nhỏ huấn luyện từ báo cáo công khai (EP6). Không chắc thì trả `clarification` hoặc `decline`, không đoán. Chấp nhận khả năng hiểu câu hỏi tự do thấp hơn.

## 7. Tác vụ `answer_compose`

### 7.1 Payload không chứa giá trị **\[ĐỀ XUẤT THAY ĐỔI\]**

Đặc tả hiện cho phép gửi giá trị cuối. Đề xuất mặc định **“mù giá trị” (value-blind)**: model nhận cho mỗi `claim` chỉ `claim_id`, `kind`, nhãn khái niệm (khóa i18n của tên chỉ số), `status` (bình thường, N/A, NOT\_MEANINGFUL, UNAVAILABLE), `band` đã tính cục bộ từ ngưỡng đã duyệt (`weak|medium|good|unscored`), `direction`, quan hệ định tính đã tính cục bộ (ví dụ “C1 cao hơn C2”), mã cảnh báo, mã kỳ và scope. **Giá trị số không rời hạ tầng.** Lợi ích: giải quyết G1 (không còn số đặc trưng nào ra ngoài), và model không thể sinh số vì không có số.

Tùy chọn `payload_detail=with_values` chỉ cho tầng công khai, bật bằng cờ và chỉ khi bộ đo ở mục 14 cho thấy chất lượng văn bản cần giá trị. Mặc định `value_blind` cho mọi tầng.

### 7.2 Soạn bằng chỗ giữ chỗ (placeholder-first) **\[ĐỀ XUẤT THAY ĐỔI\]**

`AnswerDraft` không phải chuỗi tự do mà là danh sách đoạn có kiểu:

- `prose(text)`: văn bản diễn giải do model viết. **Cấm chữ số, cấm tên doanh nghiệp, cấm ký hiệu không thuộc danh sách cho phép.**
- `claim_ref(claim_id, render)`: vị trí chèn giá trị; `render` thuộc `value|label|period|scope|status`.
- `warning_ref(code)`: vị trí chèn cảnh báo đã duyệt.
- `entity_ref(token)`: vị trí chèn tên doanh nghiệp (cục bộ khôi phục).

Bộ hiển thị cục bộ ghép các đoạn thành văn bản cuối: số luôn do bộ định dạng cục bộ sinh từ `AnswerSet`, **cảnh báo luôn được chèn nguyên văn từ kho cảnh báo đã duyệt** (đặc biệt cờ mã 130 nguyên văn), không do model viết lại. Verifier vẫn chạy trên văn bản cuối (mục 9 của ARCHITECTURE) nên đây là lớp phòng thủ thêm, không thay thế. Lợi ích: T26 (nhãn ROA/kỳ Q2 đổi chỗ) trở thành lỗi cấu trúc dễ bắt; T27 (bỏ NOT\_MEANINGFUL) bị chặn vì cảnh báo và trạng thái là đoạn bắt buộc.

### 7.3 Ràng buộc nội dung

- Chỉ mô tả và giải thích. Không khuyến nghị mua bán, không dự báo, không đánh giá “định giá hấp dẫn” (Báo cáo chính 24.3); prompt nêu rõ và có danh sách cụm bị cấm từ gói chung.
- Mọi `claim` bắt buộc phải xuất hiện ít nhất một lần dưới dạng `claim_ref`; `claim_ref` lạ bị loại. Trạng thái N/A hoặc NOT\_MEANINGFUL bắt buộc có cảnh báo tương ứng.
- Ngôn ngữ do `LanguagePolicy` quyết định; nhiệt độ thấp, một ứng viên (n=1).

### 7.4 Soạn lại sau khi Verifier từ chối

Gateway chỉ nhận **mã lỗi** từ nơi gọi (ví dụ `MISSING_CLAIM`, `UNKNOWN_PLACEHOLDER`, `FORBIDDEN_TEXT`), không nhận nội dung lỗi. Tối đa một lần soạn lại; sau đó dùng `TemplateComposerPort` trên cùng `AnswerSet`, rồi Verifier lần nữa (đúng ARCHITECTURE mục 9).

### 7.5 Đường template

Template cục bộ dùng cùng cấu trúc đoạn có kiểu, nên Verifier và bộ hiển thị không phân biệt nguồn. Đây cũng là đường chạy khi tầng riêng tư tuyệt đối hoặc khi không có provider.

## 8. Adapter nhà cung cấp

### 8.1 Giao diện chuẩn

`ProviderAdapter` (Protocol) gồm: `capabilities()` trả `ModelCapability[]` đã xác minh; `call(ProviderRequest) -> ProviderResult`; `normalize_error(raw) -> GatewayError`; `probe(SyntheticPrompt) -> ProbeResult`. Adapter **không** biết tier, tenant, ngân sách hay chính sách; những việc đó đã xong trước khi tới adapter. Adapter không ghi log nội dung, không tự thử lại, không tự chọn model.

### 8.2 Thang đầu ra có cấu trúc (xử lý G9)

Registry ghi `structured_strategy` đã thăm dò cho từng model, theo thứ tự ưu tiên:

1. **Schema gốc của provider** (ràng buộc đầu ra theo JSON schema).
2. **Gọi hàm/công cụ làm khung schema** (khi chỉ hỗ trợ tool-call có schema).
3. **Chế độ JSON + kiểm schema cục bộ** (OutputValidator là chốt cuối).
4. Không đạt bậc nào: model **không được chọn** cho tác vụ.

Ý nghĩa prompt không đổi giữa các bậc; chỉ cách ràng buộc đầu ra đổi. Kiểm schema cục bộ luôn chạy, kể cả bậc 1.

### 8.3 Bốn adapter và điều cần xác minh ở P0.10

Tôi không ghi giả định về API cụ thể của nhà cung cấp nào. Với mỗi adapter, P0.10 phải ghi kết quả thăm dò thật vào `ModelRegistry` rồi mới được dùng trong tuyến chạy thật.

| Adapter | Vai trò theo cấu hình | Cần xác minh và ghi `checked_at` |
| --- | --- | --- |
| Groq | `intent_parse` chính; `answer_compose` dự phòng miễn phí | Danh sách model hiện hành; bậc đầu ra có cấu trúc; gọi công cụ; hạn mức RPM/TPM/RPD; độ trễ thực; điều khoản dữ liệu gói miễn phí |
| Google AI Studio (Gemini) | `answer_compose` chính; `intent_parse` dự phòng miễn phí | Như trên |
| OpenAI | Trả phí, **tắt**; có contract test | Như trên, cộng bảng giá có nguồn |
| DeepSeek | Trả phí, **tắt**; có contract test | Như trên, cộng nơi xử lý dữ liệu |
| Mock | Mọi bài test offline | Mô phỏng đầy đủ ma trận lỗi mục 5.2 |

Một số nhà cung cấp có endpoint tương thích định dạng của nhà khác; vẫn viết adapter và chạy bộ contract riêng cho từng cái, không dùng chung bằng giả định.

### 8.4 Khóa

- Khóa chỉ từ biến môi trường hoặc secret provider; có `.env.example` với giá trị giả; không ghi log; che trong mọi lỗi.
- Hỗ trợ nhiều khóa mỗi provider để xoay vòng hoặc thu hồi. **Hạn mức không tính theo khóa:** theo tài liệu công khai hiện hành (mục 20), Groq áp dụng hạn mức theo tổ chức và Google AI Studio theo dự án, nên thêm khóa trong cùng tổ chức hoặc dự án không thêm hạn mức. Hạn mức tính theo `account_scope` (tổ chức hoặc dự án); circuit breaker tính theo khóa để phát hiện khóa hỏng.
- Khóa runtime và khóa phát triển tách riêng. Vì hạn mức theo tổ chức hoặc dự án, **tách khóa chưa đủ để tách hạn mức**: công cụ phát triển cần tổ chức hoặc dự án riêng, hoặc trần mềm nội bộ để không làm cạn hạn mức của runtime (xử lý G8).
- Core không hỗ trợ khóa riêng theo tenant; nếu sau này cần, đó là mở rộng qua EP9.

## 9. Định tuyến

### 9.1 Chuỗi mặc định

| Tác vụ | Chuỗi | Đường cục bộ |
| --- | --- | --- |
| `intent_parse` | Groq → Gemini → (trả phí nếu `paid_fallback` bật) | `LocalIntentParserPort` |
| `answer_compose` | Gemini → Groq → (trả phí nếu bật) | `TemplateComposerPort` |
| `dev_public_labeling` | Chỉ trong công cụ phát triển riêng | Không có đường chạy thật |

Chuỗi nằm trong tệp cấu hình có phiên bản, đổi bằng cấu hình, **không tự học**.

Thứ tự trong chuỗi là **cấu hình quyết định ở P0.10 theo dư hạn mức đo được**, không cố định như mặc định của ARCHITECTURE. Nếu hạn mức hằng ngày của một provider quá nhỏ cho một tác vụ (mục 20), đổi thứ tự thay vì giữ nguyên rồi để tác vụ rơi vào đường cục bộ gần như mọi lúc.

### 9.2 Thuật toán chọn ứng viên

1. **Lọc cứng:** tier và permit cho phép; cờ bật; `ModelCapability.status=verified`; `structured_strategy` đạt; model chưa `deprecated`; circuit không mở; ngân sách đủ; hạn mức còn (dự kiến); với tầng riêng tư: `data_use=verified_no_retention` và tenant đã opt-in.
2. **Giữ thứ tự chuỗi.** Trong cùng một mức, ưu tiên khóa có hạn mức còn nhiều hơn rồi độ trễ p50 thấp hơn.
3. Trả phí chỉ được xét khi `paid_fallback=true` **và** nguyên nhân chuyển là hết hạn mức, lỗi liên tục, model bị gỡ, hoặc schema liên tục sai (đúng bảng ở Báo cáo chính 12.5).
4. Không có ứng viên: đi thẳng đường cục bộ, ghi lý do.

### 9.3 Công bằng và hàng đợi

- **Ba mức ưu tiên:** P0 tương tác (hỏi đáp), P1 tác vụ nền, P2 công cụ phát triển (không dùng chung khóa với runtime).
- **Hạn mức theo tenant:** mỗi tenant có phần tối đa của RPM/TPM của provider (có burst), để một tenant không làm cạn hạn mức miễn phí của tất cả. Tenant hết phần của mình thì đi đường cục bộ, **không bị chặn**.
- **Chờ tối đa** trong hàng đợi bị giới hạn bởi deadline; quá thời gian thì đường cục bộ. Không để người dùng chờ vô hạn.

### 9.4 Tách runtime và gắn nhãn phát triển

`dev_public_labeling` nằm ở `corpus/teacher` với adapter factory riêng, `FINAGENT_ENV=dev`, mục kho phải có `public_classification` và `rights_review=approved`. Gói runtime không import gói này (kiểm bằng AST). Kết quả là nhãn bạc, không vào KPI chính thức.

## 10. Hạn mức, ngân sách và chi phí

### 10.1 `QuotaStore`

- Port có hai triển khai: **bộ nhớ** (một tiến trình, dev và test) và **Redis** (nhiều worker, bắt buộc khi chạy nhiều tiến trình; xử lý G7). Giữ chỗ phải **nguyên tử**.
- Chiều đo: RPM, TPM, RPD (và TPD, số lời gọi đồng thời) theo (provider, `account_scope`, model). Một số tổ chức còn bị giới hạn riêng token vào và token ra theo phút; registry phải mô tả được các chiều này.
- Mỗi giới hạn lưu **nguồn** và `observed_at`: `manual_console` (quản trị nhập từ trang giới hạn của dự án, cần với Google AI Studio vì tài liệu không công bố số theo model), `probe` (đo bằng prompt tổng hợp) hoặc `header_hint` (gợi ý từ phản hồi). Adapter chuẩn hóa header của từng provider thành `QuotaHint`; **ý nghĩa header khác nhau giữa provider** (ví dụ ở Groq, header giới hạn yêu cầu là theo ngày còn header giới hạn token là theo phút), nên không dùng chung một bộ phân tích.
- **Giữ chỗ trước, đối soát sau** theo usage thực tế. Không dựa vào việc token đã cache có thể không bị tính để giữ chỗ ít hơn.
- Đồng hồ giả (mock clock) cho mọi test.

### 10.2 `BudgetLedger`

- Phạm vi: tháng, job, người dùng, tenant; trần cứng. Cảnh báo ở 80%.
- **Bảng giá** `PriceEntry`: provider, model, đơn giá theo đơn vị, `source`, `effective_date`, `free_tier_verified`. Chỉ coi chi phí bằng 0 khi `free_tier_verified=true` kèm ngày; **giá không biết thì coi là trả phí và phải qua cổng ngân sách**, không bao giờ coi là miễn phí.
- Giữ ngân sách trước lời gọi, đối soát sau; vượt trần thì `BUDGET_EXCEEDED` và đường cục bộ.
- Mọi lời gọi trả phí ghi trace (provider, model, token, chi phí, lý do chuyển).

### 10.3 Ước lượng token

Dùng bộ đếm xấp xỉ cục bộ. Payload nhỏ theo thiết kế nên sai số ít quan trọng; mỗi tác vụ có trần token ra riêng. Đối soát theo usage thực tế là nguồn sự thật cho ngân sách.

## 11. Chịu lỗi và suy giảm

### 11.1 Circuit breaker

Trạng thái đóng, mở, nửa mở, theo (provider, model, khóa). Đề xuất khởi điểm (chỉnh ở P6.05): mở khi 5 lỗi liên tiếp hoặc quá 50% lỗi trong 60 giây; giữ mở 30 giây; nửa mở chỉ cho **một** lời gọi thăm dò **tổng hợp, không chứa dữ liệu tài chính** hay dữ liệu người dùng. Lỗi xác thực mở circuit đến khi quản trị xử lý.

### 11.2 Thang suy giảm

| Mức | Trạng thái | Biểu hiện |
| --- | --- | --- |
| L0 | Chuỗi chính miễn phí hoạt động | Bình thường |
| L1 | Dùng ứng viên miễn phí kế tiếp | `degraded=false`, ghi vào trace |
| L2 | Dùng trả phí (nếu bật và trong ngân sách) | Ghi chi phí; cảnh báo quản trị |
| L3 | Cục bộ: nhận diện ý định cục bộ và template | `degraded=true`; kết quả vẫn qua Gate và Verifier |
| L4 | Chỉ có khuôn mẫu có cấu trúc tối thiểu (khi template cũng thất bại) | ABSTAIN có cấu trúc, không số sai |

Người dùng thấy `degraded` trong `ResultEnvelope`. Hết mọi provider không làm dừng lõi số, chỉ giảm khả năng hiểu câu hỏi tự do và độ trôi chảy.

### 11.3 Phân bổ thời gian (đề xuất, hiệu chỉnh ở P6.04)

Mục tiêu hỏi đáp p95 dưới 15 giây. Đề xuất: `intent_parse` tối đa 5 giây, `answer_compose` tối đa 8 giây; timeout từng lời gọi là phần còn lại của deadline, không lớn hơn mức trần của tác vụ. Phần còn lại dành cho công cụ cục bộ và Verifier. Đây là con số khởi điểm chưa đo.

## 12. Riêng tư và egress

### 12.1 Ma trận tầng

| Tầng | `intent_parse` | `answer_compose` | Điều kiện kèm theo |
| --- | --- | --- | --- |
| Công khai | Được, gói miễn phí được phép | Được, `value_blind` mặc định | Theo chính sách hệ thống, tenant, khóa |
| Riêng tư | Chỉ khi tenant opt-in | Chỉ khi tenant opt-in | Ẩn danh, che số, `data_use=verified_no_retention`; mặc định đường cục bộ |
| Riêng tư tuyệt đối | Cấm | Cấm | Không có permit kể cả khi yêu cầu bật cờ |
| Nhiều tài liệu khác tầng | Mức nghiêm nhất | Mức nghiêm nhất |  |

### 12.2 Token ẩn danh **\[ĐỀ XUẤT THAY ĐỔI\]** (xử lý G6)

Mặc định **token ngẫu nhiên theo từng run** để nhà cung cấp không liên kết cùng một doanh nghiệp qua nhiều lời gọi. Đánh đổi: cache giữa các run kém hiệu quả hơn (chấp nhận được vì payload nhỏ). Token ổn định theo tenant chỉ bật khi admin chấp nhận rõ đánh đổi. Bảng ánh xạ chỉ lưu cục bộ, không vào log, cache chung, trace hay bất cứ thứ gì gửi ra ngoài.

### 12.3 Điều khoản dữ liệu của gói (xử lý G11)

`ModelCapability` ghi **hai trường tách biệt** thay cho một trường `data_use` (điều chỉnh sau kiểm chứng, mục 20): `training_use` thuộc `none_verified`, `may_use`, `unknown`; và `retention` thuộc `none_verified`, `limited(days)`, `indefinite`, `unknown`; kèm `plan` (miễn phí hay trả phí), `region`, `terms_checked_at`. **`unknown` được coi như `may_use` và lưu giữ không giới hạn.** Tầng riêng tư yêu cầu `training_use=none_verified` và thời hạn lưu không vượt mức tenant chấp nhận (`private.max_retention_days`; 0 nghĩa là phải không lưu); tầng công khai dùng được mọi model. Tôi không khẳng định điều khoản của nhà nào ngoài những gì đã đọc và ghi nguồn ở mục 20; mọi giá trị phải được xác minh lại ở P0.10.

### 12.4 Vòng đời `EgressPermit`

Một permit cho **một lần gửi** (mỗi lần thử lại là một permit mới), gắn hash payload, tác vụ, provider, model, tenant, tier, hạn ngắn, ngân sách token. Không dùng lại cho payload khác; không hạ tầng; bị từ chối thì không thử provider khác. EgressGuard chặn mọi truyền dữ liệu ra ngoài không có permit, kể cả của connector, webhook và telemetry (kiểm tra bằng bắt gói và canary).

## 13. Cache và idempotency

- **Khóa cache:** tenant, tier, tác vụ, hash payload đã ẩn danh, phiên bản chính sách, prompt, model, schema, chế độ; với compose thêm hash `AnswerSet` và hash snapshot.
- Nội dung cache là JSON đã ẩn danh (kế hoạch ý định, các đoạn bản nháp); **khôi phục tên cục bộ sau khi lấy từ cache**. Không chia sẻ cache giữa tenant ở tầng riêng tư.
- Vô hiệu hóa theo phiên bản bất biến (snapshot, chính sách, prompt, model); xóa dữ liệu (purge) làm mất hiệu lực cache liên quan.
- Mỗi `request_id` gọi Gateway là idempotent: gọi lại không phát sinh lời gọi và chi phí thứ hai nếu đã có kết quả.

## 14. Quan sát và đo chất lượng

**Metric:** số lời gọi, token, độ trễ p50/p95 theo (provider, model, tác vụ); tỉ lệ cache; mức dùng hạn mức theo khóa; tỉ lệ chuyển ứng viên và chuyển đường cục bộ theo lý do; trạng thái circuit; chi phí theo ngày/tháng/tenant; tỉ lệ vi phạm schema.

**Chất lượng theo model (xử lý G13):**

- `intent_parse`: khớp với bộ câu hỏi có nhãn (gồm các ca bẫy T05, T14, T15, T16, T19, T24, T25, T28), theo từng model.
- `answer_compose`: **tỉ lệ bản nháp bị Verifier từ chối theo từng model** và nguyên nhân; tỉ lệ phải dùng template.
- Dùng hai số này để quyết định model nào ở lại trong chuỗi (P6.05).

**Trace:** provider, model, tác vụ, hash payload, usage, độ trễ, chi phí, lý do chuyển, trạng thái permit, `source`, `degraded`. Nội dung yêu cầu và phản hồi chỉ ở kho kiểm toán cục bộ khi cần, có thời hạn lưu; không vào log hay hệ thống ngoài hạ tầng.

**Quản trị thay đổi model:** ghim phiên bản model; model mới phải qua bộ parity (bốn adapter dùng chung) và bộ ca có nhãn trước khi vào chuỗi; có thể quay lại cấu hình trước.

## 15. Cấu hình và phiên bản

Phase 0 đóng băng thêm `gateway/1`, `prompt/1`, `model-registry/1` bên cạnh các phiên bản ở ARCHITECTURE mục 13 (xử lý G12).

| Khóa cấu hình | Mặc định đề xuất |
| --- | --- |
| `gateway.enabled` | true (tắt thì toàn bộ đường cục bộ) |
| `gateway.paid_fallback` | **false** |
| `gateway.payload_detail` | `value_blind` |
| `gateway.anon_token_scope` | `run` |
| `gateway.stream` | false (không đổi được) |
| `gateway.hedging` | false (không đổi được) |
| `timeouts.intent_ms`, `timeouts.compose_ms` | 5000, 8000 (chưa đo) |
| `retry.transient_max` | 2 |
| `retry.schema_max` | 1 |
| `compose.retry_after_verifier` | 1 |
| `breaker.failures` / `window_s` / `open_s` | 5 / 60 / 30 (chưa đo) |
| `budget.month_cap`, `job_cap`, `user_cap` | Bắt buộc đặt khi bật trả phí; không có mặc định ngầm |
| `tenant.max_share_rpm` | Đặt ở P0.10 theo hạn mức đo được |
| `cache.ttl` | Theo tác vụ; ngắn với riêng tư |

Mọi giá trị chỉ là đề xuất khởi điểm, cần hiệu chỉnh ở P6.04 và P6.05. Cấu hình không hợp lệ làm hệ thống không khởi động (`policy` fail startup).

## 16. Kiểm thử

| Tầng | Nội dung | Tiêu chí |
| --- | --- | --- |
| Contract | Bộ chung cho cả bốn adapter và mock: schema vào/ra, chuẩn hóa lỗi, timeout, thang đầu ra có cấu trúc, usage | 100% adapter qua bộ chung (K01) |
| Tiêm lỗi | Timeout, 429, 5xx, lỗi xác thực, JSON hỏng, tool-args sai, model bị gỡ, năng lực không hỗ trợ, circuit mở, hết hạn mức, hết ngân sách, claim sai, mất cảnh báo | Hành vi đúng ma trận 5.2; trả phí tắt thì 0 lời gọi |
| Riêng tư | Canary trong tệp, văn bản, ảnh cắt, ghi chú, metadata, câu hỏi dán; bắt mọi byte ra ngoài; tầng strict\_private có 0 lời gọi ngoài | K15 = 0 |
| Ràng buộc kiến trúc | AST có cạnh bắc cầu: không module ngoài `adapters/` import HTTP provider; runtime không import `corpus/teacher` | Không vi phạm |
| Renderer và placeholder | Thuộc tính: prose không chứa chữ số; placeholder lạ bị loại; claim bắt buộc phải xuất hiện; cảnh báo chèn nguyên văn (cờ mã 130) | 100% |
| Hồi quy prompt | Bộ ca có nhãn cho intent (gồm T05, T14, T15, T16, T19, T25, T28) và compose (T26, T27) theo từng model | Theo báo cáo, không hạ ngưỡng để đạt |
| Đồng thời | Nhiều worker cùng giữ chỗ hạn mức trên Redis; không vượt giới hạn | Không vượt |
| Ngân sách | Giữ chỗ và đối soát; giá không biết; âm; trả phí tắt | Fail-closed |
| Parity trực tiếp | Khóa thật, prompt tổng hợp không tài chính, đo hạn mức và độ trễ; tách khỏi CI offline | NOT\_RUN nếu thiếu khóa, không lấy mock thay |

## 17. Quyết định cần chủ dự án duyệt

| # | Nội dung | Khuyến nghị |
| --- | --- | --- |
| D-GW-1 | Soạn câu trả lời **mù giá trị** (model không thấy số) | Duyệt, mặc định cho mọi tầng; `with_values` chỉ cho tầng công khai nếu đo cho thấy cần |
| D-GW-2 | Bản nháp **placeholder-first**: model không viết chữ số, tên, cảnh báo | Duyệt |
| D-GW-3 | Che **số do người dùng gõ** trong câu hỏi trước khi gửi | Duyệt |
| D-GW-4 | Làm rõ bằng enum, câu hỏi do mẫu cục bộ sinh | Duyệt |
| D-GW-5 | Token ẩn danh **ngẫu nhiên theo run** | Duyệt; tenant có thể xin ổn định |
| D-GW-6 | Không streaming, không hedging | Duyệt, cố định |
| D-GW-7 | `data_use=unknown` coi như có thể giữ; tầng riêng tư chỉ dùng model `verified_no_retention` | Duyệt |
| D-GW-8 | Hạn mức theo tenant (công bằng) và tách khóa runtime với khóa dev | Duyệt |

D-GW-1 và D-GW-2 thay đổi nội dung của `FinalAnswerPayload` và `AnswerDraft` trong ARCHITECTURE mục 10.1; nên chốt trước khi Phase 0 đóng băng schema.

**Điều chỉnh D-GW-7 sau kiểm chứng:** thay `data_use` bằng hai trường `training_use` và `retention` (mục 12.3). Tầng riêng tư chỉ dùng model có `training_use=none_verified` và thời hạn lưu trong mức tenant chấp nhận. Theo kết quả đọc tài liệu (mục 20), điều này loại gói miễn phí của Google AI Studio khỏi tầng riêng tư, và chỉ cho phép OpenAI khi tenant chấp nhận thời hạn lưu mặc định hoặc đã có phê duyệt không lưu.

## 18. Kế hoạch triển khai theo phase

| Phase và việc | Nội dung Gateway |
| --- | --- |
| P0.05 | Đóng băng `gateway/1`, `prompt/1`, `model-registry/1` và các Protocol; PLAN.md P0.05 hiện chỉ liệt kê spack, template, rule, ratio, role, tool, model, event, api nên cần thêm gateway và prompt |
| P0.09 | Hợp đồng egress, anonymizer, query guard, cờ tính năng |
| P0.10 | Thăm dò Groq và Gemini bằng prompt tổng hợp: model, đầu ra có cấu trúc, gọi công cụ, hạn mức, độ trễ, điều khoản; điền `ModelRegistry`, `PriceEntry` |
| P4.05 | Anonymizer, che số, query guard, whitelist payload cuối (P4.05); renderer placeholder và danh sách cảnh báo đã duyệt (P4.04 và P4.06) |
| P5.01 | Thứ tự: hợp đồng, mock adapter, registry, quota, ngân sách, circuit, router, bốn adapter, cache, trace |
| P5.02 | Permit, hai vị trí model, đường cục bộ, template dùng chung cấu trúc đoạn |
| P5.08 | Parity trực tiếp (khi có khóa), đo chất lượng theo model |
| P6.05 | Chốt tuyến, ngưỡng breaker, thời gian, theo dữ liệu đo |

## 19. Phụ lục

### A. Bốn kịch bản mẫu

1. **“Tính ROE của công ty X quý 1/2026”:** ẩn danh X thành token; không có số cần che; `intent_parse` trả `compute_ratios` với `ratio_ids=[roe]`; cục bộ khôi phục tên, chạy công cụ, tạo `AnswerSet`; `answer_compose` nhận claim mù giá trị; trả đoạn có `claim_ref`; renderer chèn số và cảnh báo; Verifier kiểm.
2. **Người dùng dán bảng vào câu hỏi (T25):** query guard phát hiện; không gửi gì ra ngoài; nhận diện ý định cục bộ, trả lời bằng khuôn mẫu.
3. **Composer đổi nhãn ROA/kỳ Q2 (T26):** với placeholder, nhãn và kỳ do renderer lấy từ `AnswerSet` nên lỗi này không xảy ra ở dạng văn bản; nếu model chèn `claim_ref` sai, Verifier từ chối, soạn lại một lần rồi template.
4. **Hết hạn mức miễn phí, trả phí tắt:** chuyển ứng viên miễn phí kế tiếp; hết thì đường cục bộ, `degraded=true`; không phát sinh chi phí; trace ghi lý do.

### B. Kiểm tra khi thêm provider hoặc model

1. Viết adapter đúng Protocol; chuẩn hóa lỗi. 2. Thăm dò bằng prompt tổng hợp; ghi năng lực, hạn mức, độ trễ, bậc đầu ra có cấu trúc, `data_use` và `terms_checked_at`. 3. Thêm `PriceEntry` có nguồn và ngày. 4. Thêm vào chuỗi, mặc định tắt. 5. Chạy bộ contract, tiêm lỗi, parity, hồi quy prompt. 6. Đặt ngân sách và cờ. 7. Cập nhật tài liệu và bảng quyết định.

### C. Mã lỗi chuẩn hóa

`TIMEOUT`, `UPSTREAM_5XX`, `NETWORK_ERROR`, `RATE_LIMITED`, `AUTH_FAILED`, `POLICY_DENIED`, `BUDGET_EXCEEDED`, `SCHEMA_INVALID`, `CONTENT_BLOCKED`, `MODEL_UNAVAILABLE`, `CONTEXT_TOO_LARGE`, `NO_ELIGIBLE_PROVIDER`.

## 20. Kết quả kiểm chứng ngày 01/11/2026

Ba việc chưa kiểm chứng ở bản trước đã được xử lý như sau. Nguồn là trang tài liệu công khai và tổng hợp của bên thứ ba đọc trong ngày; **chưa phải xác minh chính thức**. P0.10 phải đọc lại trang chính thức, trang giới hạn trong tài khoản thật và điều khoản, rồi ghi `checked_at` vào registry.

### 20.1 Việc 1: hạn mức và điều khoản của bốn nhà cung cấp

| Điều kiểm tra | Kết quả đọc được | Độ tin cậy | Hệ quả thiết kế |
| --- | --- | --- | --- |
| Groq: phạm vi hạn mức | Hạn mức tính **theo tổ chức**, thêm khóa hay thành viên không thêm dung lượng; tài liệu Groq nói bảng công khai chỉ là mẫu, trang giới hạn trong tài khoản là chính xác | Tài liệu Groq và tổng hợp bên thứ ba | `account_scope` thay cho khóa (8.4, 10.1) |
| Groq: header phản hồi | Có `retry-after` và các header `x-ratelimit-*`; header giới hạn yêu cầu theo **ngày**, header giới hạn token theo **phút**; một số tổ chức có giới hạn riêng token vào và ra theo phút | Tài liệu Groq | Bộ phân tích header riêng cho từng adapter (10.1) |
| Groq: số giới hạn gói miễn phí | Một nguồn thứ ba ghi mẫu cho vài model: 30 yêu cầu mỗi phút, 1.000 yêu cầu mỗi ngày, 8.000 token mỗi phút, 200.000 token mỗi ngày | **Thấp** (bên thứ ba, trang đọc tháng 9/2026); không dùng cho cấu hình | Phải đo thật ở P0.10 |
| Gemini: phạm vi hạn mức | Hạn mức tính **theo dự án**, không theo khóa; yêu cầu mỗi ngày reset nửa đêm giờ Thái Bình Dương | Nhiều nguồn nhất quán | Như trên |
| Gemini: số giới hạn gói miễn phí | Tài liệu **không còn công bố** số theo model; chỉ xem được trong trang giới hạn của AI Studio theo dự án. Một nguồn thứ ba ghi số yêu cầu mỗi ngày rất nhỏ (cỡ vài chục) cho một model Flash | **Thấp**; chưa xác minh | Nếu đúng, Gemini không thể là provider chính cho `answer_compose` ở gói miễn phí; thứ tự chuỗi do đo quyết định (9.1) |
| Gemini: dữ liệu gói miễn phí | Nội dung gửi qua phần miễn phí **được dùng để cải thiện sản phẩm Google và người duyệt có thể đọc**, ngoại trừ người dùng ở EEA, Thụy Sĩ, Anh; gói trả phí không dùng | Trang tài liệu Google, bản trích điều khoản | Gói miễn phí **không đủ** cho tầng riêng tư (12.3) |
| OpenAI | API mặc định không dùng dữ liệu để huấn luyện; log chống lạm dụng lưu đến khoảng 30 ngày; không lưu hoặc giảm giám sát cần được OpenAI phê duyệt | Tổng hợp bên thứ ba | `retention=limited(30)` mặc định; ZDR là tùy chọn có phê duyệt |
| DeepSeek | Chính sách ghi dữ liệu được thu thập, xử lý và lưu **tại Trung Quốc**, không nêu thời hạn lưu cho API; việc dùng đầu vào API để huấn luyện **không rõ ràng** (chính sách liệt kê huấn luyện là mục đích và có quyền từ chối, điều khoản API không nói) | Tổng hợp bên thứ ba, mâu thuẫn nhau | Coi là `unknown`; chỉ cho tầng công khai; hỏi nhà cung cấp bằng văn bản trước khi dùng bất cứ gì khác |

### 20.2 Việc 2: các con số ở mục 15

Không thể kiểm chứng bằng đọc tài liệu: timeout 5 và 8 giây, ngưỡng circuit breaker 5 lỗi trong 60 giây, số lần thử lại, TTL cache đều là đề xuất khởi điểm. Cách xác nhận: đo độ trễ và tỉ lệ lỗi thật trong P0.10 (prompt tổng hợp) và P6.04 (tải, hồi phục, hạn mức), rồi chỉnh. Có một ước tính định hướng, **dựa trên giả định của tôi**: mỗi câu hỏi hai lời gọi, khoảng 1.500 đến 2.000 token tổng. Nếu số mẫu của Groq ở trên đúng (8.000 token mỗi phút, 200.000 token mỗi ngày), gói miễn phí chỉ đủ cỡ 4 đến 5 câu hỏi mỗi phút và 100 đến 130 câu hỏi mỗi ngày cho cả tổ chức. Đủ cho phát triển và pilot nhỏ; **không đủ cho nhiều người dùng đồng thời**. Khi đó hệ thống tự rơi về đường cục bộ (vẫn an toàn nhưng kém trôi chảy), hoặc cần bật gói trả phí theo ngân sách đã duyệt. Quyết định này nên được đưa ra có số đo ở P0.10 và P6.04.

### 20.3 Việc 3: đối chiếu `PLAN.md` và `TEST_PLAN.md`

| Hạng mục | Kết quả |
| --- | --- |
| ID tác vụ P0.05, P0.09, P0.10, P4.04, P4.05, P4.06, P5.01, P5.02, P5.03, P5.08, P6.04, P6.05 | Tất cả tồn tại; nội dung khớp, trừ hai chỗ sửa dưới đây |
| P0.05 | Danh sách đóng băng **không có** `gateway` và `prompt` (G12 xác nhận) |
| P4.05 so với renderer và danh sách cảnh báo | PLAN đặt formatter ở P4.04 và template composer ở P4.06; bảng ở mục 18 đã sửa |
| P6.04, P6.05 | Có hạn mức, công bằng, circuit, ngân sách, model bị gỡ; khớp mục 11 và 14 |
| TEST\_PLAN T05, T14, T15, T16, T19, T24, T25, T28 | Có đủ, đúng ý các ca được nhắc |
| TEST\_PLAN T26, T27 | Hiện kỳ vọng “Verifier chặn, template fallback”. Với soạn placeholder-first nên **viết lại**: dùng composer giả sinh bản nháp có chữ số, `claim_ref` lạ, thiếu claim bắt buộc; kỳ vọng OutputValidator chặn trước khi hiển thị; giữ thêm một ca thử Verifier với lỗi của bộ hiển thị |
| TEST\_PLAN K01, K15 | Có và khớp (100% adapter có test; 0 payload bị cấm) |
| Đã có sẵn trong TEST\_PLAN | Bộ mock lỗi (timeout, 429, 5xx, xác thực, JSON và tool-args sai, model bị gỡ, capability không hỗ trợ, circuit mở, hết hạn mức và ngân sách, claim sai, mất cảnh báo); parity bốn adapter; paid-disabled có 0 lời gọi; canary egress và network-deny |
| Còn thiếu trong TEST\_PLAN | Che số người dùng gõ (canary số); payload composer không chứa giá trị; token ẩn danh khác nhau giữa các run; hạn mức nguyên tử nhiều worker; công bằng giữa tenant; lọc tầng riêng tư theo `training_use` và `retention`; công cụ phát triển không được import vào runtime; không streaming và không gọi song song |

### 20.4 Điều chỉnh thiết kế rút ra

1. Hạn mức theo `account_scope`, không theo khóa.
2. Nguồn hạn mức có `manual_console` vì Google AI Studio không công bố số theo model.
3. Tách `data_use` thành `training_use` và `retention`; `unknown` coi như xấu nhất.
4. Thứ tự chuỗi do đo ở P0.10 quyết định; Gemini có thể không làm được vai trò chính ở gói miễn phí.
5. Phải nêu rõ cho chủ dự án: gói miễn phí chỉ phù hợp phát triển và pilot nhỏ.
6. Mọi giá trị ở mục này phải được đọc lại từ nguồn chính thức ở P0.10 trước khi vào registry.

*Kết thúc thiết kế LLM Gateway.*
