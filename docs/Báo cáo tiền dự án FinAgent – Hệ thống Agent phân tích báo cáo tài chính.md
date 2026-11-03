# Báo cáo tiền dự án: FinAgent – Hệ thống Agent phân tích báo cáo tài chính

*Phiên bản 2.0 (bản hoàn chỉnh, đi kèm Báo cáo 2: Hướng phát triển) · 28/10/2026 · Giai đoạn: tiền dự án (chỉ ý tưởng và thiết kế, chưa viết code)*

## 1. Tóm tắt điều hành

FinAgent là hệ thống Agent đọc báo cáo tài chính (PDF, Word, Excel, text, URL), trích xuất thành dữ liệu chuẩn, trả lời hỏi đáp có trích dẫn, tính 15 chỉ số tài chính và Piotroski F-Score để đánh giá sức khỏe tài chính.

Ba quyết định thiết kế quan trọng nhất:

1. **OCR là xương sống, không phải bước phụ.** Pipeline theo nguyên tắc *native-first, vision-fallback, verify-by-accounting*: ưu tiên text layer gốc, dùng OCR cục bộ khi cần, và **mọi bảng số đều phải qua kiểm tra đẳng thức kế toán** trước khi được tin dùng.

2. **Agent không tự tính, không tự nhớ số.** Mọi con số đến từ công cụ tất định (kho dữ liệu chuẩn + Ratio Kernel). LLM chỉ lập kế hoạch, gọi công cụ và diễn giải.

3. **Chính sách ba trạng thái trả lời:** ANSWER  (đủ bằng chứng), ANSWER_WITH_CAVEATS (thiếu một phần, nêu rõ giả định), ABSTAIN  (không đủ bằng chứng, từ chối và chỉ ra cần bổ sung gì). Một Evidence Gate bắt buộc đứng giữa truy xuất và sinh câu trả lời.

Tài liệu mẫu (BCTC riêng quý 1/2026 của FPT) đã được phân tích để rút ra các thách thức OCR thực tế và để làm ca kiểm thử vàng đầu tiên (xem mục 3 và Phụ lục A).

Về mô hình ngôn ngữ: **Groq** và **Google AI Studio (Gemini)** gói miễn phí là nhà cung cấp chính qua một LLM Gateway; **OpenAI** và **DeepSeek** là phương án trả phí dự phòng, mặc định tắt (mục 12.5). Model API chỉ xuất hiện ở **hai vị trí**: nhận diện ý định và trích xuất tham số, và viết câu trả lời từ kết quả tính toán. **Tài liệu không bao giờ rời hạ tầng khi chạy thật** (mục 24).

**Cấu trúc bộ báo cáo.** Bộ báo cáo gồm hai tài liệu. **Báo cáo chính** (tài liệu này) mô tả đầy đủ dự án, core của hệ thống và các điểm mở rộng để phát triển sau mà không sửa core (mục 22). **Báo cáo 2: Hướng phát triển** (mở báo cáo 2) chi tiết từng hướng phát triển: cần gì, có đổi core không, thêm vào như thế nào và các phần liên quan.

<!-- Page 1 of 58 -->

## 2. Mục tiêu, phạm vi và tiêu chí thành công

### 2.1 Ba tiêu chí của dự án và cách đo

| # | Tiêu chí | Cách hiện thực hóa | Chỉ số đo (KPI mục tiêu) |
| --- | --- | --- | --- |
| 1 | Kiến trúc rõ ràng, khoa học, chi tiết | Kiến trúc phân lớp, module hợp đồng rõ ràng (input/output/schema), tool registry cho Agent | 100% module có interface và test hợp đồng; không phụ thuộc vòng; mọi tool có schema |
| 2 | OCR mạnh với bảng khó | Pipeline nhiều tầng, đa engine, bỏ phiếu, kiểm tra kế toán, hàng đợi duyệt tay | Độ chính xác cấp ô số ≥ 99,5% (PDF có text layer), ≥ 98,5% (PDF scan); 100% mã số cấp tổng hợp hoặc khớp đẳng thức hoặc bị gắn cờ |
| 3 | Tự nhận biết thiếu bằng chứng, không bịa | Evidence Gate, provenance từng con số, kiểm tra điều kiện áp dụng chỉ số, chính sách ABSTAIN | 0 con số không truy vết được trên bộ test vàng; recall ABSTAIN ≥ 95% trên bộ câu hỏi thiếu bằng chứng; độ chính xác trích dẫn ≥ 95%; số liệu và chỉ số luôn 100% ở cả hai chế độ vận hành, câu hỏi định tính ≥ 95% (mục 19) |

### 2.2 Phạm vi

- **Trong phạm vi:** doanh nghiệp niêm yết là đối tượng chính; doanh nghiệp chưa niêm yết và doanh nghiệp nhỏ và vừa được hỗ trợ khi khách hàng yêu cầu, với chế độ riêng tư (mục 18). Theo chế độ kế toán VAS: mẫu B01/B02/B03/B09-DN của Thông tư 200 và các mẫu biểu khác như mẫu cho doanh nghiệp nhỏ và vừa (cần xác minh khi dựng kho mẫu biểu); báo cáo riêng và hợp nhất; quý, bán niên, năm; song ngữ Việt–Anh.

- **Ngoài phạm vi (giai đoạn đầu):** IFRS đầy đủ, ngân hàng, chứng khoán và bảo hiểm (mẫu biểu khác; hiện chỉ nhận diện để cảnh báo không áp dụng, bộ chỉ số riêng làm ở giai đoạn mở rộng, xem Báo cáo 2), giao diện người dùng (làm sau khi backend hoàn chỉnh), dự báo giá cổ phiếu, khuyến nghị mua/bán.

- **Nguyên tắc pháp lý:** hệ thống hỗ trợ phân tích, không thay thế kiểm toán hay tư vấn đầu tư.

<!-- Page 2 of 58 -->

## 3. Phân tích tài liệu mẫu để định hướng OCR

### 3.1 Tổng quan tài liệu

File gồm thư công bố thông tin song ngữ, trang bìa, mục lục và 25 trang báo cáo. Điểm cần chú ý ngay: đây là **báo cáo tài chính RIÊNG (công ty mẹ)**, không phải hợp nhất, kỳ từ 01/01/2026 đến 31/03/2026, đơn vị VND. Thư công bố nhắc cả báo cáo riêng và hợp nhất, nên Agent phải luôn xác định *phạm vi báo cáo* (riêng/hợp nhất) trước khi tính chỉ số.

Cấu trúc: Bảng cân đối kế toán (B01-DN, trang 3–4), Kết quả kinh doanh (B02-DN, trang 5), trang giải trình biến động (trang 6, đơn vị *triệu đồng*), Lưu chuyển tiền tệ (B03-DN, trang 7–8), Thuyết minh (B09-DN, trang 9–27) gồm chính sách kế toán dạng văn bản và các bảng chi tiết.

### 3.2 Các đặc điểm khó của tài liệu và thiết kế ứng phó

| Đặc điểm quan sát được | Rủi ro nếu xử lý ngây thơ | Thiết kế ứng phó |
| --- | --- | --- |
| Số theo định dạng Việt Nam: dấu chấm phân cách hàng nghìn, số âm trong ngoặc, dấu gạch ngang nghĩa là 0 | Đọc 1.837.500.567.142 thành số thập phân; mất dấu âm; bỏ trống thay vì 0 | Bộ chuẩn hóa số riêng cho vi-VN, kiểm tra số chữ số theo nhóm 3, ngoặc = âm, gạch ngang = 0 có gắn cờ explicit_zero |
| Nhiều cột số cùng lúc: Mã số, Thuyết minh, kỳ này, kỳ trước | Nhầm cột Thuyết minh (ví dụ 4/7, 4/8) thành số liệu; lệch cột | Nhận diện tiêu đề cột, gán vai trò cột (code, note, current, prior); cột Thuyết minh chỉ nhận dạng ghi chú |
| Kết quả kinh doanh có 4 cột số: Quý 1 (2026, 2025) và Lũy kế (2026, 2025) với giá trị trùng nhau | Trùng lặp hoặc nhầm kỳ | Mô hình kỳ báo cáo: mỗi giá trị gắn period_type (quarter, ytd), period_end, và quy tắc khử trùng lặp khi quý 1 = lũy kế |
| Kỳ so sánh khác nhau giữa các báo cáo: bảng cân đối so với 31/12/2025, còn kết quả kinh doanh và lưu chuyển tiền so với quý 1/2025 (xác nhận ở Thuyết minh số 21) | Dùng sai số đầu kỳ khi tính chỉ số bình quân | Mỗi giá trị lưu as_of hoặc period chính xác; kho dữ liệu cấm hoán đổi hai loại này |

<!-- Page 3 of 58 -->

| Đặc điểm quan sát được | Rủi ro nếu xử lý ngây thơ | Thiết kế ứng phó |
| --- | --- | --- |
| Bảng trải qua nhiều trang, có dòng (Tiếp theo): cân đối trang 3–4, lưu chuyển tiền trang 7–8 | Mất dòng, gộp sai phần Tài sản và Nguồn vốn | Bộ nối bảng liên trang theo tiêu đề lặp, mã số liên tục và đẳng thức tổng |
| Một số trang xoay ngang (trang 5, 6, 15, 16, 21, 22) | Layout detection và bảng bị sai nếu không chỉnh hướng | Phát hiện và xoay chuẩn hướng ở bước tiền xử lý, chấm điểm hướng bằng nhận dạng chữ |
| Phân cấp qua thụt lề và đánh số (A, I, 1, 2…), dòng nghiêng (222, 223, 411a, 420a, 420b) | Mất quan hệ cha–con; nhầm dòng con là dòng tổng | Dựng cây từ Mã số (key chính), kiểm tra tổng con = cha |
| Dòng Trong đó (ví dụ mã 24 chi phí đi vay nằm trong mã 23 chi phí tài chính) | Cộng trùng lặp; tính sai EBIT | Schema đánh dấu is_memo_item = true; không đưa vào phép cộng tổng |
| Con dấu đỏ, chữ ký số và chữ ký tay đè lên chữ (khối ký ở trang 4, 6, 8, 27) | Nhiễu ký tự, sinh chữ rác trong ô số | Lọc kênh màu đỏ/xanh chữ ký, loại vùng chữ ký khỏi bảng, đánh dấu vùng không đáng tin |
| Dấu tiếng Việt dày (ơ, ư, ạ, ặ, ộ…) và tên riêng | Sai dấu làm hỏng ánh xạ tên chỉ tiêu | Ánh xạ chỉ tiêu theo mã số trước, tên chỉ tiêu chỉ để đối chiếu mờ (fuzzy) |
| Trang giải trình dùng đơn vị triệu đồng, báo cáo chính dùng đồng, kèm làm tròn (168 tỷ, 1.828 tỷ) | Trộn đơn vị, lệch 10^6 | Mỗi bảng có unit_scale suy ra từ tiêu đề; mọi giá trị lưu ở đơn vị VND gốc kèm đơn vị hiển thị |
| Trang bìa, mục lục, văn bản chính sách kế toán dài (trang 9–13) | Tạo chunk nhiễu cho RAG, kéo tụt chất lượng truy xuất | Phân loại trang (cover, toc, statement, note_table, note_text, signature) rồi định tuyến khác nhau |

### 3.3 Kiểm chứng đẳng thức kế toán trên chính tài liệu mẫu

Các đẳng thức sau đã được đối chiếu thủ công trên số liệu của file và đều khớp. Chúng chính là loại kiểm tra mà hệ thống phải tự chạy để biết OCR có đọc đúng hay không:

<!-- Page 4 of 58 -->

| Đẳng thức | Kết quả trên file |
| --- | --- |
| Tài sản ngắn hạn (100) + Tài sản dài hạn (200) = Tổng tài sản (280) | 10.626.141.721.085 + 22.441.574.606.461 = 33.067.716.327.546 (khớp) |
| Nợ phải trả (300) + Vốn chủ sở hữu (400) = Tổng nguồn vốn (440) | 7.757.537.821.182 + 25.310.178.506.364 = 33.067.716.327.546 (khớp) |
| Tổng tài sản (280) = Tổng nguồn vốn (440) | Khớp ở cả 31/03/2026 và 31/12/2025 |
| Tiền cuối kỳ trên lưu chuyển tiền (mã 70) = Tiền và tương đương tiền trên cân đối (mã 110) | 2.231.448.721.940 (khớp) |
| Lưu chuyển thuần kỳ (50) = HĐKD (20) + Đầu tư (30) + Tài chính (40) | −401.953.448.193 + 2.381.155.178.054 − 1.653.002.529.850 = 326.199.200.011 (khớp) |
| Lợi nhuận sau thuế (kết quả kinh doanh, mã 60) = Lợi nhuận kỳ này (420b) = dòng Lợi nhuận trong kỳ ở Thuyết minh 14 | 1.828.028.020.122 (khớp cả ba nơi) |
| Khấu hao ở Thuyết minh 5 + 6 = Khấu hao ở lưu chuyển tiền (mã 02) | 29.035.596.118 + 6.561.356.227 = 35.596.952.345 (khớp) |

### 3.4 Hai điểm bất thường cần hệ thống tự gắn cờ

1. **Số cổ phiếu ở Thuyết minh 14 không khớp vốn góp ở cột 31/12/2025.** Vốn góp 31/12/2025 là 17.035.071.210.000 đồng với mệnh giá 10.000 đồng, tương ứng khoảng 1.703.507.121 cổ phiếu, nhưng cột 31/12/2025 của bảng số cổ phiếu ghi 1.471.069.183 (con số này tương ứng vốn góp đầu năm 2025). Đây là **bất nhất ngay trong nguồn**, không phải lỗi OCR. Hệ thống cần phân biệt hai loại: *lỗi đọc* (sửa/duyệt tay) và *bất nhất của tài liệu gốc* (giữ nguyên số, gắn cờ cảnh báo cho người dùng). Quy tắc kiểm tra chéo: vốn góp ÷ mệnh giá phải bằng số cổ phiếu đã phát hành.

2. **Chênh lệch nhỏ giữa các bảng cho cùng một khái niệm.** Ví dụ lãi/lỗ chênh lệch tỷ giá ở lưu chuyển tiền (mã 04) khác Thuyết minh 18 một khoản nhỏ vì cách phân loại (có phần thực hiện/chưa thực hiện). Hệ thống cần ngưỡng dung sai và phân loại lý do, không coi mọi chênh lệch là lỗi OCR.

### 3.5 Hệ quả đặc thù: đây là báo cáo của công ty mẹ dạng holding

Doanh thu thuần của báo cáo riêng (≈ 168 tỷ đồng) chủ yếu là phí quản lý chi hộ, phân bổ cho các công ty thành viên (đúng như trang giải trình nêu), còn doanh thu tài chính ≈ 1.948 tỷ đồng chủ yếu là cổ tức từ công ty con (≈ 1.792 tỷ đồng). Hệ quả: nhiều chỉ số trong bộ 15

<!-- Page 5 of 58 -->

chỉ số (biên lợi nhuận ròng, vòng quay hàng tồn kho, vòng quay tài sản) cho **giá trị tính được nhưng không có ý nghĩa phân tích**. Đây là lý do hệ thống cần *lớp kiểm tra điều kiện áp dụng* (applicability gate) chứ không chỉ lớp tính toán. Chi tiết ở mục 9 và Phụ lục A.

## 4. Kiến trúc tổng thể

### 4.1 Nguyên tắc thiết kế

1. **Tách rời “đọc” và “hiểu”:** trích xuất (OCR/parser) → dữ liệu chuẩn (canonical) → phân tích. Mỗi lớp kiểm thử độc lập.

2. **Số liệu là công dân hạng nhất:** mỗi con số có *provenance* đầy đủ (file, trang, vùng chữ nhật, engine đọc, độ tin cậy, kết quả kiểm tra).

3. **Tất định trước, xác suất sau:** tính toán bằng module tất định; LLM không bao giờ là nguồn của con số.

4. **Fail-closed:** không đủ bằng chứng thì từ chối hoặc nêu rõ giới hạn; không đoán.

5. **Kiểm tra bằng nhiều nguồn độc lập:** đẳng thức kế toán, đồng thuận giữa các engine OCR, đối chiếu chéo giữa các báo cáo.

6. **Có người trong vòng lặp khi cần:** hàng đợi duyệt tay cho ô số nghi ngờ; sửa tay được ghi lại để học.

7. **Quan sát được:** trace toàn bộ từ file đầu vào đến câu trả lời cuối, tái lập được.

### 4.2 Sơ đồ phân lớp

```text
[Client / API]
      │
[L1 Ingestion Gateway] ── xác thực, kiểm tra file, antivirus, chống SSRF,
hàng đợi job
      │
[L2 Document Router] ── phân loại: PDF text / PDF scan / Excel / Word / Text
/ URL
      │
 ┌────┴───────────────────────────────────────────────┐
 │ L3 Extraction                                      │
 │  PDF text layer ─┐                                 │
 │  OCR + Layout  ──┤→ Page Classifier → Table Engine │
 │  Excel / Word  ──┤                                 │
 │  Text / URL    ──┘                                 │
 └────┬───────────────────────────────────────────────┘
      │
[L4 Financial Statement Understanding]
   Statement Detector → Mã-số Mapper → Period/Unit/Scope Resolver
      │
```

<!-- Page 6 of 58 -->

```text
[L5 Validation & Reconciliation] ── đẳng thức, liên báo cáo, dung sai, độ tin
cậy
      │            │
      │       [Review Queue (người duyệt)]
      ▼
[L6 Canonical Store] (SQL: báo cáo chuẩn + provenance)   [L6b Document Store
+ Vector/BM25 Index]
      │                                                          │
[L7 Analytics Kernel]                                      [L8 Retrieval +
Evidence Gate]
  Ratio(15) · Trend · Piotroski(9) · Industry · Assessment       │
      └──────────────────────┬───────────────────────────────────┘
                     [L9 Agent Orchestrator]
          Planner → Tool Router → Evidence Collector → Verifier → Composer
                             │
                [L10 Output] câu trả lời + trích dẫn + cảnh báo + export
JSON/Markdown
```

```text
Cắt ngang: Security · Observability/Trace · Evaluation · Job Store ·
Config/Policy · LLM Gateway (Groq, Gemini; OpenAI, DeepSeek trả phí)
```

### 4.3 Danh mục module và hợp đồng

| Module | Trách nhiệm | Đầu vào → Đầu ra | Cách Agent dùng |
| --- | --- | --- | --- |
| ingestion | Nhận file/URL/text, kiểm tra loại, kích thước, mã độc, an toàn URL | file → document_id + job_id | Không gọi trực tiếp |
| router | Quyết định đường xử lý theo từng trang, không chỉ theo file | document → page_plan | Nội bộ |
| ocr_layout | Tiền xử lý ảnh, layout, bảng, OCR đa engine | page → blocks, tables, độ tin cậy | Nội bộ |
| statement_extractor | Nhận diện B01/B02/B03, ánh xạ mã số, kỳ, đơn vị, phạm vi | tables → financial_statements (thô) | Nội bộ |
| validator | Chạy bộ quy tắc kế toán, tính điểm tin cậy | statements → validated_statements + issues | Tool: get_validation_report |
| canonical_store | Lưu dữ liệu chuẩn + provenance, phiên bản hóa | statements → bản ghi bất biến | Tool: get_statement, list_periods |
| indexer | Chunk, metadata, nhúng vector, BM25 | text/tables → index | Nội bộ |

<!-- Page 7 of 58 -->

| Module | Trách nhiệm | Đầu vào → Đầu ra | Cách Agent dùng |
| --- | --- | --- | --- |
| retriever | Truy xuất lai (hybrid) kèm tín hiệu tin cậy và độ mới | query → evidence set | Tool: search_evidence |
| evidence_gate | Chấm chất lượng bằng chứng, quyết định ANSWER/CAVEATS/ABSTAIN | evidence → verdict | Bắt buộc trước khi trả lời |
| ratio_kernel | 15 chỉ số, kiểm tra điều kiện áp dụng | statements → ratios + warnings | Tool: compute_ratios |
| trend_engine | Chuỗi nhiều kỳ, chất lượng dữ liệu, độ tin cậy xu hướng | ratios[] → trend | Tool: compute_trend |
| piotroski | 9 thành phần, trạng thái từng thành phần | statements (2 kỳ) → score + trạng thái | Tool: compute_piotroski |
| industry_context | Bối cảnh ngành từ nguồn có trích dẫn, không ghi đè nền tảng | news/docs → context | Tool: get_industry_context |
| assessment | Điểm tổng hợp minh bạch, tài chính là chính | ratios + piotroski + trend → rating | Tool: assess_health |
| agent | Lập kế hoạch, điều phối công cụ, trace, tổng hợp | câu hỏi → câu trả lời + trace | Điểm vào chính |
| exporter | Xuất JSON/Markdown | agent_result → file | Tool: export_result |
| security / jobs / observability | Xác thực API key, rate limit, job in-memory hoặc Redis, log/trace | — | Cắt ngang |

### 4.4 Các module chính sách, dữ liệu và mở rộng

- **Phân tầng dữ liệu và riêng tư (mục 18):** gắn tầng cho từng tài liệu và kế thừa xuống trang, chunk, ảnh cắt, embedding, cache, trace; điều khiển việc có được gọi API ngoài hay không.

- **Mode Policy (mục 19):** hai chế độ Nghiêm ngặt và Hữu ích, chuyển đổi theo hệ thống, tenant, khóa API, từng yêu cầu.

- **Ratio Registry (mục 20):** định nghĩa chỉ số dạng khai báo; 15 chỉ số lõi và phần mở rộng.

- **Corpus (mục 21):** kho báo cáo có nhãn, tập huấn luyện/đánh giá, vòng phản hồi từ duyệt tay.

- **Sector Pack và nhóm agent (mục 22):** gói cấu hình theo ngành và các agent chuyên biệt; làm sau khi lõi Agent hoàn thành.

- **Review API (mục 23):** duyệt tay không cần giao diện; hợp đồng API ổn định cho giao diện về sau.

<!-- Page 8 of 58 -->

## 5. Pipeline OCR và trích xuất bảng (trọng tâm)

### 5.1 Triết lý

Không tin một engine OCR duy nhất. Độ tin cậy của một con số đến từ **ba nguồn độc lập**: (a) nhiều engine đọc ra cùng giá trị, (b) giá trị đúng định dạng số Việt Nam, (c) giá trị làm các đẳng thức kế toán đồng thời đúng. Đây là lợi thế đặc thù của báo cáo tài chính: cấu trúc kế toán cho ta “đáp án kiểm tra” miễn phí mà văn bản thông thường không có.

Tài liệu mẫu có dấu hiệu là ảnh scan (nền nhiễu, chữ hơi nghiêng, chữ ký và con dấu đè lên chữ, nhiều trang xoay ngang). Vì vậy pipeline phải giả định cần OCR đầy đủ, còn bước phân loại trang sẽ tự quyết định trang nào dùng được text layer.

### 5.2 Các giai đoạn xử lý

| Giai đoạn | Mục đích | Kỹ thuật chính | Đầu ra |
| --- | --- | --- | --- |
| S0. Phân loại trang (triage) | Quyết định đường xử lý cho từng trang | Kiểm tra text layer: mật độ ký tự, tỉ lệ ký tự tiếng Việt hợp lệ, vị trí chữ so với ảnh; trang lai (một phần là ảnh) | page_plan: text / ocr / hybrid |
| S1. Tiền xử lý ảnh | Cho OCR đầu vào sạch nhất | Render 300–400 DPI; phát hiện và xoay hướng 0/90/180/270; chỉnh nghiêng (deskew); khử nhiễu; nhị phân thích ứng; tách kênh màu để loại con dấu đỏ và nét ký xanh; giữ cả bản gốc để đối chiếu | ảnh sạch + ảnh gốc |
| S2. Phân tích bố cục | Tách vùng chức năng | Phát hiện đầu trang/chân trang, tiêu đề, đoạn văn, bảng, khối ký tên và con dấu; loại vùng ký tên khỏi vùng số liệu | bản đồ vùng có nhãn |

<!-- Page 9 of 58 -->

| Giai đoạn | Mục đích | Kỹ thuật chính | Đầu ra |
| --- | --- | --- | --- |
| S3. Nhận diện bảng và cấu trúc | Dựng lưới hàng/cột | Bảng BCTC thường không kẻ ô, nên dựa vào căn cột theo trục x của các cụm số, tiêu đề cột và mã số; model nhận dạng cấu trúc bảng làm đề xuất, luật căn cột làm kiểm tra; xử lý ô nhiều dòng (nhãn dài xuống dòng) | bảng có lưới ô |
| S4. OCR cấp ô, đa engine | Đọc từng ô | Engine A chuyên bảng, engine B OCR tổng quát tiếng Việt, ô số bị ràng buộc bộ ký tự 0-9 . , ( ) - ; ô nghi ngờ được đọc lại bằng engine thứ ba hoặc ở độ phân giải cao hơn (khi chạy thật không dùng VLM bên ngoài); mỗi ô số được đọc ít nhất 2 lần độc lập | ứng viên giá trị + điểm từng engine |
| S5. Chuẩn hóa số vi-VN | Đưa chuỗi về số | Dấu chấm là phân cách nghìn, ngoặc là số âm, gạch ngang là 0 hiển thị, kiểm tra nhóm 3 chữ số, nhận diện đơn vị (đồng / nghìn đồng / triệu đồng) từ tiêu đề | giá trị VND + cờ định dạng |
| S6. Dựng báo cáo | Ghép trang, dựng cây | Nối bảng qua trang nhờ tiêu đề “(Tiếp theo)” và mã số liên tục; dựng quan hệ cha–con từ Mã số; gắn cờ dòng Trong đó | cây chỉ tiêu đầy đủ |
| S7. Ánh xạ ngữ nghĩa | Gắn mã chuẩn | Mã số → mã chuẩn (canonical); nhãn tiếng Việt chỉ dùng để đối chiếu mờ và phát hiện lệch | line_item chuẩn |
| S8. Kiểm tra kế toán | Xác minh | Chạy bộ quy tắc mục 7 | cờ tin cậy, danh sách vấn đề |

<!-- Page 10 of 58 -->

| Giai đoạn | Mục đích | Kỹ thuật chính | Đầu ra |
| --- | --- | --- | --- |
| S9. Sửa có ràng buộc | Cứu lỗi đọc | Nếu chỉ một ô sai làm lệch đẳng thức, thử các ứng viên khác của chính ô đó; chỉ chấp nhận khi duy nhất một phương án làm mọi đẳng thức đúng; ghi lại việc sửa | giá trị đã sửa + nhật ký |
| S10. Duyệt tay và học | Chốt các ô còn nghi | Review API trả ảnh cắt cạnh giá trị (giao diện làm sau); người duyệt xác nhận hoặc sửa qua API hoặc công cụ dòng lệnh; mọi sửa đổi được lưu để cải thiện luật và bộ test | giá trị đã duyệt |

### 5.3 Chiến lược engine (chọn sau khi benchmark ở Phase 1)

Kiến trúc dùng *adapter*, nên engine nào cũng thay được mà không động tới phần còn lại. Danh sách ứng viên để đo trên bộ vàng:

- **Text layer PDF:** PyMuPDF, pdfplumber (lấy tọa độ từng từ để dựng bảng khi PDF xuất từ phần mềm kế toán).

- **Layout và bảng:** Docling, PaddleOCR PP-Structure, Table Transformer, Surya.

- **OCR chữ:** PaddleOCR (có mô hình tiếng Việt), VietOCR, Tesseract vie  dùng làm engine đối chiếu giá rẻ.

- **VLM (mô hình thị giác):** chỉ dùng ở giai đoạn phát triển và huấn luyện, trên tài liệu công khai từ nguồn chính thống, để sinh nhãn bạc và đánh giá; không dùng làm nguồn số. Khi chạy thật không gửi tài liệu cho VLM bên ngoài (mục 24). Bộ đọc chính khi chạy thật là text layer và các engine OCR cục bộ.

- **Excel / Word:** openpyxl (xử lý ô gộp, công thức, nhiều sheet), python-docx (bảng lồng, ảnh nhúng chạy lại OCR).

Quy tắc ưu tiên: **text layer tốt > bất đồng thuận nhiều engine > một engine > VLM đơn lẻ**. Dù nguồn nào, mọi giá trị đều phải đi qua S5–S9.

<!-- Page 11 of 58 -->

### 5.4 Thang độ tin cậy cho từng ô

| Mức | Điều kiện | Cách dùng |
| --- | --- | --- |
| A – Đã xác minh | Nằm trong ít nhất một đẳng thức đúng, hoặc có text layer sạch | Dùng tự do |
| B – Đồng thuận | Hai engine trở lên cho cùng giá trị, định dạng hợp lệ, nhưng chưa thuộc đẳng thức nào | Dùng, ghi mức B |
| C – Đơn nguồn | Chỉ một engine, định dạng hợp lệ | Dùng có cảnh báo, ưu tiên đưa vào hàng đợi duyệt |
| D – Nghi ngờ | Engine bất đồng, định dạng sai, hoặc làm lệch đẳng thức | Chặn; không dùng để tính chỉ số cho đến khi duyệt |

Độ tin cậy của một chỉ số lấy theo mức thấp nhất của các đầu vào tạo ra nó, nên một ô mức D có thể làm chỉ số bị chặn đúng chỗ.

### 5.5 Các lỗi đọc số thường gặp và biện pháp

| Lỗi | Ví dụ | Phòng chống |
| --- | --- | --- |
| Nhầm ký tự gần giống | 0↔O, 1↔l↔7, 5↔S, 3↔8, 6↔b | Ràng buộc bộ ký tự cho ô số; đọc lại bằng engine khác |
| Nhầm dấu chấm và dấu phẩy | 2.101.700 thành 2,101,700 | Chuẩn hóa theo locale tài liệu; kiểm tra nhóm 3 chữ số |
| Mất dấu ngoặc (số âm) | (2.252.333.501) đọc thành dương | Nhận diện ngoặc ở cả hai phía; đối chiếu quy ước dấu từng mã số (ví dụ dòng dự phòng, hao mòn lũy kế luôn là âm) |
| Mất chữ số cuối hoặc đầu | Lề trang, con dấu che | So số chữ số với các ô cùng cột; đẳng thức sẽ lệch |
| Dính hai cột | “1.905.249.672.046 2.231…” | Cắt theo khoảng trống trục x; kiểm tra số lượng ô mỗi hàng |
| Gạch ngang bị đọc thành số hoặc bỏ trống | - nghĩa là 0 | Phân biệt explicit_zero với missing |
| Mã số và Thuyết minh bị lẫn với số liệu | “4/7”, “10” trong cột Thuyết minh | Gán vai trò cột bằng tiêu đề, không đoán theo giá trị |

<!-- Page 12 of 58 -->

### 5.6 Phần không phải bảng số

- **Thuyết minh dạng văn bản** (chính sách kế toán, cấu trúc doanh nghiệp): cắt theo mục (I, II, III…), giữ tiêu đề mục làm metadata, dùng cho RAG hỏi đáp định tính.

- **Bảng thuyết minh** (Thuyết minh 1–20): trích như bảng riêng có khóa là *số thuyết minh*; liên kết ngược với dòng ở báo cáo chính thông qua cột Thuyết minh (ví dụ mã 261 liên kết Thuyết minh 4/7). Các bảng này cung cấp chi tiết mà 15 chỉ số cần, như tiền gửi có kỳ hạn, vay theo từng bên, giao dịch với bên liên quan.

- **Trang giải trình** có đơn vị triệu đồng: trích như nguồn *đối chiếu phụ*, không dùng làm nguồn chính.

- **Trang hành chính** (bìa, mục lục, chữ ký): gắn nhãn và loại khỏi chỉ mục số liệu.

### 5.7 Các định dạng khác

| Định dạng | Cách xử lý | Lưu ý |
| --- | --- | --- |
| Excel | Đọc đủ các sheet, ô gộp, công thức (cả giá trị đã tính lẫn công thức), đơn vị trong tiêu đề; tự nhận diện sheet nào là B01/B02/B03 | Vẫn đi qua S5–S9: Excel cũng có thể sai |
| Word | Đọc bảng (kể cả bảng lồng), văn bản, ảnh nhúng chạy lại OCR | Văn bản Word được xem là tài liệu thuyết minh nếu không có bảng chuẩn |
| Text / Markdown | Chuẩn hóa, dò bảng dạng văn bản, hỏi lại nếu không rõ kỳ và đơn vị | Độ tin cậy mặc định thấp hơn |
| URL / tin tức | Làm sạch HTML, lấy ngày xuất bản, tên nguồn, chấm điểm nguồn | Không bao giờ coi là số liệu tài chính chính thức; chỉ phục vụ bối cảnh ngành |

### 5.8 Cách đo chất lượng OCR

- **Bộ vàng (golden set):** FPT là tài liệu số 1; mở rộng tối thiểu 30 tài liệu đa dạng: PDF scan nghiêng, PDF xuất từ Excel, báo cáo hợp nhất, báo cáo hai cột kỳ, bản kiểm toán, bản song ngữ, doanh nghiệp sản xuất và bán lẻ để kiểm thử cả 15 chỉ số.

- **Chỉ số:** độ chính xác cấp ô số (khớp tuyệt đối), độ chính xác theo hàng, **tỉ lệ báo cáo vượt toàn bộ đẳng thức**, tỉ lệ ô bị gắn cờ D, tỉ lệ ô sai nhưng *không* bị gắn cờ (chỉ số nguy hiểm nhất), thời gian mỗi trang, chi phí mỗi tài liệu.

- **Tiêu chí nghiệm thu OCR:** ô sai không bị gắn cờ ≤ 0,1% trên bộ vàng.

<!-- Page 13 of 58 -->

## 6. Mô hình dữ liệu chuẩn (canonical)

### 6.1 Các thực thể

| Thực thể | Trường chính |
| --- | --- |
| Document | document_id, nguồn, hash file, loại, ngôn ngữ, thời điểm nạp, trạng thái xử lý |
| Page | số trang, hướng, loại trang (cover, toc, statement, note_table, note_text, signature), đường xử lý |
| Table | table_id, page, bbox, loại, thuyết minh số, cấu trúc lưới |
| Statement | doc_id, statement_family (mặc định corporate), template_id, loại (B01/B02/B03), scope (riêng / hợp nhất), period_type (quarter / ytd / year / as_of), period_start, period_end, trạng thái kiểm toán (đã kiểm toán / soát xét / chưa), đơn vị, tiền tệ, phiên bản (điều chỉnh lại số liệu), trạng thái xác minh |
| LineItem | statement_id, vas_code (mã số), canonical_id, nhãn vi/en, giá trị VND, giá trị hiển thị, dấu, is_total, is_memo, parent, explicit_zero |
| Provenance | file, trang, bbox, engine, các ứng viên giá trị, điểm tin cậy, mức A–D, danh sách quy tắc đã chạy |
| ValidationIssue | rule_id, mức độ (BLOCK / WARN / INFO), mô tả, các ô liên quan |
| ReviewAction | người duyệt, giá trị trước/sau, lý do, thời điểm |
| Entity | doanh nghiệp, mã chứng khoán, ngành (phân loại), niên độ tài chính |

### 6.2 Quy tắc bất biến

1. Giá trị luôn lưu bằng **VND gốc**, kèm đơn vị hiển thị để truy vết.

2. Mỗi giá trị gắn *as_of* (số dư) hoặc *khoảng thời gian* (dòng chảy). **Cấm trộn hai loại** khi tính chỉ số.

3. Cùng một doanh nghiệp, hai bản báo cáo cho cùng kỳ (ví dụ riêng và hợp nhất) lưu thành hai Statement khác nhau, không ghi đè.

<!-- Page 14 of 58 -->

4. Số liệu so sánh trong báo cáo kỳ sau không ghi đè báo cáo gốc; nếu khác nhau thì lưu thành phiên bản điều chỉnh và gắn cờ *restated*.

5. Dữ liệu đã duyệt tay vẫn giữ giá trị OCR gốc để kiểm toán.

## 7. Hệ thống kiểm tra và đối chiếu

### 7.1 Danh mục quy tắc

| Nhóm | Quy tắc | Mức |
| --- | --- | --- |
| A. Định dạng | Nhóm 3 chữ số; ký tự hợp lệ; không có số thập phân bất thường; đơn vị suy ra được | BLOCK |
| B. Trong một báo cáo | Cha = tổng con (mọi mã tổng, ví dụ 100, 200, 220, 260, 300, 400); 280 = 100 + 200; 440 = 300 + 400; 280 = 440; KQKD: 10 = 01 − 02, 20 = 10 − 11, 30 = 20 + 22 − 23 − 25 − 26, 40 = 31 − 32, 50 = 30 + 40, 60 = 50 − 51 − 52 (nếu có các dòng khác như 21, 24 thì theo mẫu đầy đủ); LCTT: 20 + 30 + 40 = 50, 50 + 60 + 61 = 70 | BLOCK |
| C. Giữa các báo cáo | Tiền cuối kỳ LCTT (70) = mã 110 trên cân đối; lợi nhuận sau thuế KQKD (60) = 420b = dòng lợi nhuận trong kỳ ở Thuyết minh vốn chủ sở hữu; khấu hao ở Thuyết minh = mã 02 LCTT; LNTT KQKD (50) = mã 01 LCTT; số dư đầu kỳ thuyết minh = cuối kỳ trước | BLOCK với chênh lệch lớn, WARN với chênh lệch nhỏ có lý giải |
| D. Giữa các kỳ | Cột 31/12/2025 của cân đối kỳ này = cột cuối kỳ của báo cáo kiểm toán năm 2025 đã có trong hệ thống; số lũy kế cùng kỳ năm trước khớp báo cáo năm trước | WARN, hoặc restated |
| E. Hợp lý | Doanh thu ≥ 0; tài sản không âm (trừ khoản dự phòng/hao mòn mang dấu âm); vốn góp ÷ mệnh giá = số cổ phiếu; chi phí đi vay ≤ chi phí tài chính; tỉ lệ thuế hợp lệ | WARN |

<!-- Page 15 of 58 -->

| Nhóm | Quy tắc | Mức |
| --- | --- | --- |
| F. Phạm vi và đơn vị | Một bộ báo cáo cùng scope, cùng kỳ, cùng đơn vị; không trộn riêng và hợp nhất | BLOCK |

Dòng *Trong đó* (is_memo) bị loại khỏi mọi phép cộng. Dung sai: bằng 0 đối với số VND đầy đủ; ±1 đơn vị hiển thị khi báo cáo đã làm tròn (ví dụ triệu đồng).

### 7.2 Trạng thái báo cáo

- **VERIFIED:** mọi quy tắc BLOCK đạt; cho phép tính toán đầy đủ.

- **PARTIAL:** một số mục bị D hoặc thiếu; chỉ các chỉ số không phụ thuộc mục đó được tính, phần còn lại ghi “chưa đủ dữ liệu”.

- **REJECTED:** lệch đẳng thức lõi (ví dụ 280 ≠ 440) mà không có ứng viên sửa duy nhất; chuyển hàng đợi duyệt, **không** đưa vào kho chuẩn.

## 8. Cơ chế chống bịa thông tin và Evidence Gate

### 8.1 Năm lớp phòng thủ

| Lớp | Cơ chế | Ngăn chặn điều gì |
| --- | --- | --- |
| 1. Nguồn số duy nhất | Mọi con số định lượng lấy từ kho chuẩn hoặc kernel tính toán; LLM không được “nhớ” hay tự tính | Bịa số, sai số học |
| 2. Truy xuất có điều kiện | Lọc theo doanh nghiệp, scope, kỳ, độ tin cậy; xếp hạng kết hợp tương đồng, độ mới và độ tin cậy nguồn | Lấy nhầm kỳ hoặc nhầm công ty |
| 3. Evidence Gate | Chấm bằng chứng và ra quyết định ANSWER / CAVEATS / ABSTAIN trước khi sinh câu trả lời | Trả lời khi chưa đủ căn cứ |
| 4. Sinh có ràng buộc và hậu kiểm | Mỗi con số trong câu trả lời phải mang tham chiếu tới evidence_id; bộ hậu kiểm tách mọi số trong văn bản và đối chiếu với evidence, số không có nguồn thì chặn | Số “lọt” vào lời diễn giải |
| 5. Từ chối có hướng dẫn | Khi thiếu: nêu rõ thiếu gì, cần file nào, có thể trả lời một phần nào | Làm người dùng bế tắc |

<!-- Page 16 of 58 -->

### 8.2 Tiêu chí Evidence Gate

| Tiêu chí | Câu hỏi kiểm tra |
| --- | --- |
| Coverage | Mọi mục dữ liệu mà câu hỏi cần đều có mặt? |
| Period match | Kỳ và loại kỳ (quý, lũy kế, năm, số dư) khớp câu hỏi? |
| Scope match | Riêng hay hợp nhất khớp câu hỏi? |
| Trust | Báo cáo ở trạng thái VERIFIED? Các ô liên quan ở mức A/B? |
| Consistency | Các nguồn không mâu thuẫn nhau? |
| Recency | Với thông tin bối cảnh/tin tức, đủ mới? |
| Applicability | Chỉ số có ý nghĩa với loại doanh nghiệp và báo cáo này? |

Quyết định: tất cả đạt → **ANSWER**; thiếu hoặc yếu nhưng còn trả lời được phần cốt lõi, hoặc chỉ số tính được nhưng kém ý nghĩa → **ANSWER_WITH_CAVEATS** (nêu giả định, cảnh báo); thiếu mục thiết yếu, sai phạm vi/kỳ, hoặc báo cáo REJECTED → **ABSTAIN**.

### 8.3 Phân loại lý do “không đủ thông tin”

| Mã | Ý nghĩa | Hành vi |
| --- | --- | --- |
| MISSING_ITEM | Thiếu chỉ tiêu cần thiết | Nêu chỉ tiêu thiếu; trả lời phần còn lại |
| MISSING_PERIOD | Thiếu kỳ so sánh (ví dụ không có kỳ trước để tính bình quân hoặc ΔROA) | Tính biến thể có ghi rõ giả định hoặc từ chối |
| SCOPE_MISMATCH | Hỏi hợp nhất nhưng chỉ có báo cáo riêng | ABSTAIN, đề nghị tải báo cáo hợp nhất |
| UNIT_AMBIGUOUS | Không xác định được đơn vị | Hỏi lại hoặc ABSTAIN |
| LOW_OCR_CONFIDENCE | Đầu vào ở mức C/D | Chặn hoặc kèm cảnh báo, gợi ý duyệt tay |
| UNVERIFIED_STATEMENT | Báo cáo chưa VERIFIED | Cảnh báo rõ hoặc ABSTAIN tùy mức |
| CONFLICTING_SOURCES | Hai nguồn lệch nhau | Nêu cả hai, không chọn ngầm |

<!-- Page 17 of 58 -->

| Mã | Ý nghĩa | Hành vi |
| --- | --- | --- |
| NOT_APPLICABLE_RATIO | Chỉ số không có ý nghĩa với loại doanh nghiệp | Trả giá trị kèm giải thích hoặc N/A |
| STALE_SOURCE | Nguồn bối cảnh đã cũ | Cảnh báo hoặc bỏ qua |
| OUT_OF_DOMAIN | Ngoài phạm vi (dự báo giá, khuyến nghị mua/bán) | Từ chối lịch sự, giải thích giới hạn |

### 8.4 Cấu trúc câu trả lời chuẩn

Mọi câu trả lời của Agent là một đối tượng có cấu trúc, sau đó mới được diễn đạt thành văn bản: verdict , answer , evidence[]  (id, file, trang, giá trị, mức tin cậy), calculations[] (công thức, đầu vào, kết quả), assumptions[] , warnings[] , missing[] , next_actions[] .

Hai ví dụ minh họa với tài liệu mẫu:

- *“Doanh thu hợp nhất quý 1/2026 của FPT?”* → **ABSTAIN** (SCOPE_MISMATCH): file chỉ có báo cáo riêng của công ty mẹ; Agent đề nghị tải báo cáo hợp nhất.

- *“Biên lợi nhuận ròng quý 1/2026?”* → **ANSWER_WITH_CAVEATS**: tính được từ báo cáo riêng, nhưng lợi nhuận chủ yếu từ cổ tức công ty con nên tỉ số vượt 1.000% và **không phản ánh hiệu quả kinh doanh**; Agent giải thích và gợi ý dùng báo cáo hợp nhất.

### 8.5 Bảo vệ khỏi chỉ thị ẩn trong tài liệu

Tài liệu tải lên (đặc biệt Word, URL, tin tức) có thể chứa câu lệnh nhằm điều khiển Agent. Nguyên tắc: **nội dung tài liệu luôn là dữ liệu, không bao giờ là chỉ thị**. Nội dung được cách ly trong khung dữ liệu, công cụ không cho phép tài liệu thay đổi chính sách, bỏ qua Gate hoặc gọi công cụ ngoài danh sách.

### 8.6 Kiểm thử khả năng từ chối

Xây dựng bộ câu hỏi “bẫy”: hỏi kỳ không có trong file, hỏi hợp nhất khi chỉ có riêng, hỏi chỉ số khi thiếu đầu vào, hỏi số liệu cố tình sai để xem Agent có xác nhận bừa, hỏi ngoài phạm vi. Mục tiêu cụ thể theo từng chế độ vận hành (Nghiêm ngặt và Hữu ích) nằm ở mục 19.

<!-- Page 18 of 58 -->

## 9. Lớp phân tích: 15 chỉ số, Piotroski, xu hướng, ngành và đánh giá tổng hợp

### 9.1 Ratio Kernel: 15 chỉ số theo file định nghĩa

Mỗi chỉ số là một hàm thuần túy: đầu vào là các line item đã VERIFIED với kỳ và scope xác định, đầu ra gồm giá trị, công thức đã dùng, danh sách đầu vào kèm nguồn, mức tin cậy, cờ áp dụng và cảnh báo. Mã số bên dưới theo mẫu biểu của tài liệu mẫu (xem Phụ lục B).

| # | Nhóm | Chỉ số | Công thức (theo file) | Đầu vào (mã số) | Lưu ý áp dụng |
| --- | --- | --- | --- | --- | --- |
| 1 | Thanh khoản | Current Ratio | Tài sản ngắn hạn ÷ Nợ ngắn hạn | 100, 310 | Mẫu số ≤ 0 → N/A |
| 2 | Thanh khoản | Quick Ratio | (Tài sản ngắn hạn − Hàng tồn kho) ÷ Nợ ngắn hạn | 100, 140, 310 | Công thức phụ (tiền + phải thu + đầu tư ngắn hạn) lưu kèm để so sánh |
| 3 | Thanh khoản | Cash Ratio | (Tiền + tương đương tiền) ÷ Nợ ngắn hạn | 110, 310 | Mặc định không gồm tiền gửi có kỳ hạn trên 3 tháng (mã 120); cấu hình động: bật chế độ mở rộng thì cộng thêm mã 120 (mục 20) |
| 4 | Đòn bẩy | Debt Ratio | Tổng nợ ÷ Tổng tài sản | 300, 280 |  |
| 5 | Đòn bẩy | D/E | Tổng nợ ÷ Vốn chủ sở hữu | 300, 400 | VCSH ≤ 0 → N/A và cờ rủi ro |
| 6 | Đòn bẩy | Interest Coverage | EBIT ÷ Chi phí lãi vay | 50, 24 | EBIT = LNTT + chi phí lãi vay; lãi vay = 0 → “không có lãi vay”, không trả ∞ |
| 7 | Hiệu suất | Vòng quay hàng tồn kho | Giá vốn ÷ Tồn kho bình quân | 11, 140 (hai thời điểm) | Không có hàng tồn kho đáng kể → N/A; kỳ ngắn hơn năm → cần quy năm |
| 8 | Hiệu suất | Vòng quay khoản phải thu | Doanh thu thuần ÷ Phải thu bình quân | 10, 130 hoặc 131 | Mặc định cố định mã 131; dùng mã 130 thì tự phát cờ cảnh báo (mục 20) |
| 9 | Hiệu suất | Vòng quay tổng tài sản | Doanh thu thuần ÷ Tổng tài sản bình quân | 10, 280 (hai thời điểm) | Với công ty holding thường không có ý nghĩa |
| 10 | Sinh lời | Biên lợi nhuận gộp | Lợi nhuận gộp ÷ Doanh thu thuần | 20, 10 |  |
| 11 | Sinh lời | Biên lợi nhuận ròng | Lợi nhuận sau thuế ÷ Doanh thu thuần | 60, 10 | Cảnh báo khi lợi nhuận chủ yếu từ cổ tức/tài chính |
| 12 | Sinh lời | ROA | Lợi nhuận ròng ÷ Tổng tài sản | 60, 280 | Theo file dùng tổng tài sản; bản bình quân tính song song |

<!-- Page 19 of 58 -->

| # | Nhóm | Chỉ số | Công thức (theo file) | Đầu vào (mã số) | Lưu ý áp dụng |
| --- | --- | --- | --- | --- | --- |
| 13 | Sinh lời | ROE | Lợi nhuận ròng ÷ Vốn chủ sở hữu | 60, 400 | Báo cáo hợp nhất: tử số và mẫu số phải cùng phạm vi (cổ đông công ty mẹ) |
| 14 | Dòng tiền | OCF / Nợ ngắn hạn | Dòng tiền thuần từ HĐKD ÷ Nợ ngắn hạn | CF 20, 310 | Dòng tiền âm cho kết quả âm và có ý nghĩa cảnh báo |
| 15 | Dòng tiền | OCF / Tổng tài sản | Dòng tiền thuần từ HĐKD ÷ Tổng tài sản | CF 20, 280 |  |

Ba điểm từng còn tranh cãi (phạm vi “tiền” của Cash Ratio, khoản phải thu dùng cho vòng quay, và tổng nợ) đã được chốt thành chính sách ở mục 20. 15 chỉ số trong file là **bộ lõi**; Ratio Registry (mục 20) cho phép mở rộng thêm chỉ số mà không sửa kernel.

### 9.2 Cổng kiểm tra điều kiện áp dụng (Applicability Gate)

Tính được không đồng nghĩa với có ý nghĩa. Gate chạy sau khi tính, trước khi diễn giải:

<!-- Page 20 of 58 -->

| Điều kiện | Chỉ số bị ảnh hưởng | Kết quả |
| --- | --- | --- |
| Mẫu số ≤ 0 hoặc gần 0 | Mọi chỉ số chia | N/A kèm lý do |
| Báo cáo riêng của công ty mẹ dạng holding: doanh thu hoạt động nhỏ, lợi nhuận chủ yếu từ cổ tức công ty con | Biên lợi nhuận ròng, vòng quay tài sản, ROA, ROE | Giá trị + cờ NOT_MEANINGFUL, đề nghị dùng báo cáo hợp nhất |
| Hàng tồn kho gần như không có (doanh nghiệp dịch vụ/phần mềm) | Vòng quay hàng tồn kho | N/A |
| Kỳ báo cáo ngắn hơn năm | Mọi chỉ số dòng chảy so với số bình quân | Hiện giá trị theo kỳ và giá trị quy năm riêng; không so ngưỡng của file khi chưa quy năm; cảnh báo tính mùa vụ |
| Chỉ có số cuối kỳ, thiếu đầu kỳ | Các vòng quay dùng bình quân | Tính theo số cuối kỳ và nêu rõ cơ sở |
| Doanh nghiệp tài chính (ngân hàng, chứng khoán, bảo hiểm) | Nhiều chỉ số | Chặn bộ 15 chỉ số lõi; ngân hàng dùng bộ chỉ số riêng ở giai đoạn mở rộng (Báo cáo 2), chứng khoán và bảo hiểm làm sau |
| Chưa biết ngành | So sánh ngưỡng ngành | Dùng ngưỡng chung, nêu rõ |

Ngưỡng đánh giá lấy từ file (ví dụ Current Ratio tốt 1,5–2,5; D/E theo ngành; ICR > 3) được lưu thành **bảng ngưỡng cấu hình**, có phiên bản và nguồn, đóng gói theo ngành trong Sector Pack (mục 22) và được tính lại từ kho báo cáo (mục 21) khi đủ dữ liệu.

### 9.3 Piotroski F-Score (lớp riêng, 9 thành phần)

Mỗi thành phần có trạng thái ba giá trị: **1 (đạt)**, **0 (không đạt)**, **UNAVAILABLE (thiếu dữ liệu)**. Không gán 0 cho thành phần thiếu dữ liệu.

| # | Nhóm | Thành phần | Điều kiện đạt | Dữ liệu cần |
| --- | --- | --- | --- | --- |
| F1 | Sinh lời | ROA dương | Lợi nhuận ròng ÷ tổng tài sản (đầu kỳ hoặc bình quân, cấu hình) > 0 | LNST kỳ t, tổng tài sản |
| F2 | Sinh lời | Dòng tiền HĐKD dương | CFO > 0 | LCTT kỳ t |

<!-- Page 21 of 58 -->

| # | Nhóm | Thành phần | Điều kiện đạt | Dữ liệu cần |
| --- | --- | --- | --- | --- |
| F3 | Sinh lời | ROA tăng | ROA kỳ t > ROA kỳ t−1 | LNST và tổng tài sản của hai kỳ |
| F4 | Sinh lời | Chất lượng lợi nhuận (accrual) | CFO > Lợi nhuận ròng | LCTT và KQKD kỳ t |
| F5 | Đòn bẩy | Đòn bẩy giảm | Nợ dài hạn ÷ tài sản bình quân kỳ t < kỳ t−1 | Nợ dài hạn, tổng tài sản hai kỳ |
| F6 | Thanh khoản | Current Ratio tăng | CR kỳ t > CR kỳ t−1 | Cân đối hai thời điểm |
| F7 | Thanh khoản | Không phát hành thêm cổ phiếu | Không tăng vốn góp/ số cổ phiếu trong kỳ | Thuyết minh vốn chủ sở hữu |
| F8 | Hiệu quả | Biên gộp tăng | GM kỳ t > GM kỳ t−1 | KQKD hai kỳ cùng loại |
| F9 | Hiệu quả | Vòng quay tài sản tăng | ATO kỳ t > ATO kỳ t−1 | Doanh thu và tài sản hai kỳ |

Nguyên tắc báo cáo kết quả:

- Mặc định tính trên **dữ liệu năm** (năm t so với năm t−1) đúng thiết kế gốc. Với dữ liệu quý, dùng chế độ *cùng quý năm trước* hoặc *TTM*, đánh dấu rõ chế độ.

- Hiển thị: điểm hiện có, số thành phần UNAVAILABLE, và **khoảng điểm khả dĩ** (thấp nhất = điểm hiện có, cao nhất = điểm hiện có + số UNAVAILABLE).

- Chỉ gán nhãn (mạnh / trung bình / yếu) khi có ít nhất 7 trong 9 thành phần; dưới ngưỡng này nhãn là “chưa đủ dữ liệu”.

- F-Score là lớp **tách biệt**, không bị trộn vào 15 chỉ số; Assessment dùng nó như một tín hiệu bổ sung có trọng số thấp và có thể tắt.

### 9.4 Trend Engine

- Chuỗi chỉ số nhiều kỳ **cùng scope, cùng loại kỳ**; so sánh quý với cùng quý năm trước để tránh mùa vụ, thêm so sánh liền kề khi cần.

- Chất lượng dữ liệu theo từng điểm: mức tin cậy ô, báo cáo điều chỉnh (*restated*), khoảng trống kỳ.

- Quy tắc: dưới 3 điểm thì không kết luận xu hướng, chỉ báo thay đổi giữa hai kỳ; mỗi xu hướng có nhãn tin cậy (cao / vừa / thấp) dựa trên số điểm, chất lượng và độ biến động.

- Gắn nguyên nhân gợi ý bằng số liệu (ví dụ doanh thu tài chính tăng do cổ tức), không bằng suy đoán.

<!-- Page 22 of 58 -->

### 9.5 Industry Context

- Nguồn: tin tức, báo cáo ngành, thuyết minh doanh nghiệp, qua danh sách nguồn đáng tin có điểm tin cậy và ngày xuất bản.

- Mỗi mục bối cảnh có trích dẫn, ngày, điểm tin cậy; mục cũ hoặc nguồn yếu bị hạ trọng số hoặc loại.

- **Ràng buộc cứng:** bối cảnh ngành *không* làm đổi giá trị chỉ số và *không* nâng hay hạ điểm cơ bản. Nó chỉ được dùng để (a) chọn bộ ngưỡng ngành, (b) thêm cờ rủi ro hoặc cơ hội có nguồn, (c) giải thích ngữ cảnh.

### 9.6 Assessment: đánh giá tổng hợp “tài chính là chính”

| Thành phần | Nội dung | Vai trò |
| --- | --- | --- |
| 5 trụ cột | Thanh khoản (1–3, 14), Đòn bẩy (4–6), Hiệu suất (7–9), Sinh lời (10–13), Dòng tiền (14–15) | Cốt lõi, quyết định điểm |
| Piotroski | F-Score kèm khoảng điểm | Tín hiệu bổ sung, trọng số thấp, có thể tắt |
| Xu hướng | Hướng cải thiện hay suy giảm | Điều chỉnh nhỏ, có giới hạn |
| Bối cảnh ngành | Cờ và giải thích | Không đổi điểm |
| Cờ đỏ cứng | Vốn chủ âm; OCF âm kéo dài cùng ICR < 1,5; báo cáo chưa VERIFIED; dữ liệu không đủ | Giới hạn trần xếp hạng |

Cách chấm: mỗi chỉ số chuyển thành điểm theo dải ngưỡng của file (tốt / trung bình / yếu), chỉ số N/A bị loại. Trụ cột chỉ được chấm khi có ít nhất 2/3 số chỉ số của nó; xếp hạng tổng chỉ ra khi có ít nhất 3 trong 5 trụ cột, kèm **độ phủ dữ liệu (%)**. Điểm số và **độ tin cậy** là hai con số riêng: một xếp hạng cao nhưng dựa trên dữ liệu kém tin cậy vẫn hiển thị độ tin cậy thấp. Báo cáo đầu ra liệt kê đóng góp của từng chỉ số để người dùng kiểm chứng. Ở giai đoạn lõi, trọng số các trụ cột và ngưỡng dùng bộ chung theo file chỉ số; khi có Sector Pack (mục 22, làm sau) thì lấy theo ngành.

<!-- Page 23 of 58 -->

## 10. Thiết kế Agent

### 10.1 Vòng lặp điều khiển

INTAKE → PHÂN LOẠI Ý ĐỊNH → LẬP KẾ HOẠCH → THỰC THI (gọi công cụ) → EVIDENCE

GATE → (thiếu nhưng còn công cụ bù được: lặp lại, giới hạn số bước) → SOẠN CÂU TRẢ LỜI → HẬU KIỂM SỐ → TRẢ LỜI

Các ý định chính: tra cứu số, giải thích khái niệm, tính chỉ số, đánh giá sức khỏe tài chính, so sánh kỳ hoặc công ty, xu hướng, tóm tắt báo cáo, hỏi về chất lượng dữ liệu, ngoài phạm vi.

### 10.2 Tool registry

| Công cụ | Mục đích | Ghi chú |
| --- | --- | --- |
| list_documents / get_document_status | Xem tài liệu đã nạp và trạng thái xử lý OCR | Cho biết có thể hỏi chưa |
| list_periods | Các kỳ và scope có trong kho | Bước đầu của mọi phân tích |
| get_statement | Lấy B01/B02/B03 chuẩn cho một kỳ | Trả kèm trạng thái xác minh |
| get_note_table | Lấy bảng thuyết minh theo số | Chi tiết cho phải thu, vay, đầu tư |
| search_evidence | Truy xuất lai trong văn bản và bảng | Dùng cho câu hỏi định tính |
| get_validation_report | Kết quả quy tắc, danh sách ô nghi ngờ | Cho Gate và người dùng |
| compute_ratios | 15 chỉ số + Applicability Gate | Công cụ duy nhất tạo ra chỉ số |
| compute_trend | Xu hướng nhiều kỳ | Có nhãn tin cậy |
| compute_piotroski | F-Score + trạng thái từng thành phần | Lớp riêng |
| compare_periods | Biến động giữa hai kỳ, tự động “giải trình biến động” | Giống trang giải trình của báo cáo mẫu |
| get_industry_context | Bối cảnh ngành có trích dẫn | Không đổi điểm |
| assess_health | Đánh giá tổng hợp | Gọi các công cụ trên |

<!-- Page 24 of 58 -->

| Công cụ | Mục đích | Ghi chú |
| --- | --- | --- |
| request_review | Đưa ô nghi ngờ vào hàng đợi duyệt | Hành động có tác dụng phụ, cần quyền |
| explain_ratio | Giải thích công thức, ngưỡng, ý nghĩa | Dựa trên bảng định nghĩa |
| export_result | Xuất JSON và Markdown |  |

Công cụ có **schema đầu vào và đầu ra chặt**, thời gian chờ, giới hạn lần gọi mỗi lượt, và không có công cụ “tự do” để LLM tự tính số.

### 10.3 Quy tắc lập kế hoạch

1. Luôn xác định **doanh nghiệp, scope, kỳ** trước; nếu mơ hồ, hỏi lại tối đa một câu.

2. Số liệu lấy từ get_statement hoặc compute_*; RAG chỉ cho nội dung định tính và trích dẫn.

3. Không gọi compute_ratios khi báo cáo chưa có trạng thái VERIFIED hoặc PARTIAL phù hợp.

4. Nếu Gate báo thiếu và còn công cụ bù được (ví dụ chưa lấy bảng thuyết minh), Agent bổ sung; nếu không thì dừng ở ABSTAIN hoặc CAVEATS.

5. Giới hạn số bước và chi phí mỗi lượt, tránh vòng lặp vô hạn.

### 10.4 Trace và giải thích công khai

Mỗi lượt lưu **execution trace** có cấu trúc: công cụ đã gọi, tham số, tóm tắt kết quả, độ trễ, phán quyết Gate. Người dùng thấy bản *giải thích công khai* gồm “Dữ liệu tôi đã dùng”, “Cách tính”, “Giả định”, “Cảnh báo” và “Còn thiếu”. Trace nội bộ phục vụ gỡ lỗi và đánh giá; không phơi bày suy luận thô của mô hình.

### 10.5 Hội thoại

Phiên hội thoại nhớ doanh nghiệp, scope, kỳ đang xét và tài liệu đã chọn; khi người dùng đổi một trong các yếu tố, Agent phải xác nhận lại. Mặc định trả lời tiếng Việt, hỗ trợ tiếng Anh, giữ nguyên thuật ngữ gốc (Current Ratio, ROE…).

<!-- Page 25 of 58 -->

## 11. Các chức năng bổ sung đề xuất

| # | Chức năng | Giá trị | Ưu tiên |
| --- | --- | --- | --- |
| 1 | Kiểm tra độ đầy đủ tài liệu (đủ B01/B02/B03, đủ kỳ so sánh, có thuyết minh) trước khi cho hỏi | Ngăn hỏi trên dữ liệu thiếu | Phải có |
| 2 | Review API duyệt tay (giai đoạn backend: API và công cụ dòng lệnh; giao diện làm sau, mục 23) | Đóng vòng OCR | Phải có |
| 3 | Kho phiên bản mẫu biểu (mã số theo từng thông tư/phiên bản) | Mã số khác nhau giữa các mẫu và thông tư (kể cả mẫu cho doanh nghiệp nhỏ và vừa); không hard-code | Phải có |
| 4 | Giải trình biến động tự động giữa hai kỳ | Giống trang giải trình, tiết kiệm công sức | Phải có |
| 5 | Phát hiện cờ đỏ chất lượng lợi nhuận: CFO thấp hơn lợi nhuận kéo dài, phải thu tăng nhanh hơn doanh thu, phụ thuộc cổ tức, tập trung bên liên quan | Bổ sung góc nhìn cho 15 chỉ số | Nên có |
| 6 | Phân tích giao dịch và số dư bên liên quan | Báo cáo mẫu có rất nhiều số dư nội bộ tập đoàn | Nên có |
| 7 | DuPont (ROE phân rã) và chu kỳ chuyển đổi tiền (DSO, DIO, DPO) | Hiểu nguyên nhân của ROE và vốn lưu động | Nên có |
| 8 | Trích ý kiến kiểm toán và các vấn đề nhấn mạnh từ báo cáo kiểm toán | Thông tin sống còn, thường nằm ngoài bảng số | Nên có |
| 9 | So sánh với doanh nghiệp cùng ngành theo bộ ngưỡng ngành | Chuẩn so sánh có ý nghĩa | Nên có |
| 10 | Đồ thị cấu trúc đầu tư (công ty con, liên kết, tỉ lệ sở hữu) từ Thuyết minh | Hiểu cấu trúc tập đoàn | Có thể |
| 11 | Altman Z″ và Beneish M-score như lớp tham khảo tùy chọn, có nhãn giới hạn áp dụng | Bổ sung cảnh báo phá sản và thao túng | Có thể |
| 12 | Bảng điều khiển đánh giá (độ chính xác OCR, tỉ lệ ABSTAIN, lỗi theo loại) | Cải tiến liên tục | Nên có |

<!-- Page 26 of 58 -->

| # | Chức năng | Giá trị | Ưu tiên |
| --- | --- | --- | --- |
| 13 | Cảnh báo khi nạp báo cáo mới (tự so với kỳ trước) | Theo dõi định kỳ | Có thể |
| 14 | Xuất Excel có công thức cho người dùng tự kiểm | Minh bạch | Nên có |

## 12. Nền tảng kỹ thuật, API, bảo mật và vận hành

### 12.1 Ngăn xếp công nghệ đề xuất

| Thành phần | Đề xuất | Lý do |
| --- | --- | --- |
| Ngôn ngữ và API | Python 3.11+, FastAPI, Pydantic | Hợp hệ sinh thái OCR/ML; schema chặt cho công cụ Agent |
| CSDL chuẩn | PostgreSQL | Dữ liệu quan hệ, provenance, phiên bản hóa |
| Lưu file và ảnh trang | Object storage (S3 tương thích hoặc đĩa) | Giữ file gốc, ảnh cắt ô cho duyệt tay |
| Chỉ mục | pgvector hoặc Qdrant (vector) + BM25 (OpenSearch hoặc Postgres FTS) | Truy xuất lai |
| Hàng đợi job | In-memory (phát triển), Redis + worker (sản xuất) | Khớp yêu cầu job store hai chế độ |
| LLM / VLM | LLM Gateway: Groq và Google AI Studio (Gemini) làm chính; adapter OpenAI và DeepSeek dựng sẵn, mặc định tắt (mục 12.5) | Tránh khóa nhà cung cấp, thay engine dễ |
| Quan sát | OpenTelemetry, log có cấu trúc, trace theo job và theo lượt Agent | Truy vết đầu–cuối |
| Cấu hình chính sách | Tệp cấu hình có phiên bản (ngưỡng, chính sách chỉ số, gate) | Thay đổi không cần sửa code, có lịch sử |

<!-- Page 27 of 58 -->

### 12.2 Giao diện API (cấp ý tưởng)

| Nhóm | Endpoint (dự kiến) | Chức năng |
| --- | --- | --- |
| Tài liệu | POST /documents, POST /documents/url, POST /documents/text | Nạp file, URL, văn bản |
| Tiến trình | GET /jobs/{id} | Trạng thái theo từng giai đoạn S0–S10 |
| Dữ liệu chuẩn | GET /documents/{id}/statements, GET /statements/{id}/validation | Xem báo cáo đã trích xuất và kết quả kiểm tra |
| Duyệt tay | GET /reviews, POST /reviews/{id}/resolve | Hàng đợi ô nghi ngờ |
| Phân tích | GET /companies/{id}/ratios, /trend, /piotroski, /assessment | Truy cập trực tiếp kernel |
| Agent | POST /agent/run, GET /agent/runs/{id}, GET /agent/runs/{id}/export?format=json | md |
| Quản trị | /admin/keys, /admin/config, /health | Khóa, cấu hình, sức khỏe hệ thống |

### 12.3 Bảo mật

- **Xác thực và phân quyền:** API key cho người dùng, admin key riêng cho cấu hình và duyệt; giới hạn tốc độ theo khóa.

- **Nạp file an toàn:** kiểm tra MIME thật (không tin phần mở rộng), giới hạn dung lượng và số trang, chống zip-bomb, tắt macro trong Word/Excel, parse XML an toàn (chống XXE), quét mã độc nếu có.

- **Lấy URL an toàn (chống SSRF):** chỉ http/https, chặn dải IP nội bộ và loopback, kiểm tra lại IP sau khi phân giải DNS, giới hạn chuyển hướng, kích thước, thời gian và loại nội dung; không gửi thông tin xác thực.

- **Chống chỉ thị ẩn trong tài liệu:** xem mục 8.5.

- **Dữ liệu:** mã hóa khi lưu và khi truyền, chính sách lưu giữ và xóa, nhật ký kiểm toán cho truy cập và sửa dữ liệu, che dữ liệu nhạy cảm trong log.

- **Quyền riêng tư với LLM ngoài:** tài liệu không bao giờ rời hạ tầng khi chạy thật; chỉ câu hỏi đã ẩn danh và kết quả tính toán mới có thể tới API ngoài, theo tầng dữ liệu (mục 18, 24).

<!-- Page 28 of 58 -->

### 12.4 Hiệu năng và độ tin cậy (mục tiêu ban đầu)

- PDF có text layer 25 trang: dưới 30 giây. PDF scan 25 trang: dưới 3 phút. Hỏi đáp: p95 dưới 15 giây khi dữ liệu đã nạp.

- Job idempotent (nạp lại cùng file không nhân đôi dữ liệu nhờ hash), có thể thử lại theo từng giai đoạn.

- Cache kết quả theo (hash file, phiên bản pipeline), để khi đổi engine chỉ chạy lại phần cần thiết.

### 12.5 Chiến lược LLM/VLM: Groq và Google AI Studio là chính, OpenAI và DeepSeek là phương án trả phí

Mọi lời gọi mô hình đi qua **một LLM Gateway duy nhất**; không module nào gọi trực tiếp API nhà cung cấp. Groq và Google AI Studio (Gemini) là mặc định; adapter OpenAI và DeepSeek được dựng và kiểm thử sẵn nhưng **tắt theo mặc định**, chỉ bật bằng cấu hình khi cần chất lượng cao hơn hoặc khi hạn mức miễn phí không đủ. Tôi chưa kiểm tra hạn mức và danh sách model hiện hành của các nhà cung cấp, nên Phase 0 phải xác minh bằng thử nghiệm thực tế.

Quyết định: model API chỉ ở hai vị trí (mục 24) và tài liệu không bao giờ rời hạ tầng khi chạy thật, nên lượng dữ liệu qua API nhỏ và đã ẩn danh. LLM không phải nguồn của con số, vì vậy đổi nhà cung cấp chỉ ảnh hưởng chất lượng hiểu ý định và diễn đạt, không làm đổi số liệu.

**Phân vai theo tác vụ**

| Tác vụ | Chính | Dự phòng miễn phí | Trả phí (dựng sẵn, tắt) | Ghi chú |
| --- | --- | --- | --- | --- |
| Vị trí 1: nhận diện ý định, trích xuất tham số (function calling) | Groq | Gemini | OpenAI, DeepSeek | Đầu vào là câu hỏi đã ẩn danh; model phải hỗ trợ gọi công cụ và JSON theo schema |
| Vị trí 2: viết câu trả lời từ đáp số | Gemini | Groq | OpenAI, DeepSeek | Chỉ nhận kết quả đã tính (ẩn danh nếu tầng yêu cầu); hậu kiểm số cục bộ |
| Làm rõ câu hỏi, viết lại truy vấn khi cần | Groq | Gemini | OpenAI | Chỉ xử lý câu hỏi, không xử lý văn bản báo cáo |

<!-- Page 29 of 58 -->

| Tác vụ | Chính | Dự phòng miễn phí | Trả phí (dựng sẵn, tắt) | Ghi chú |
| --- | --- | --- | --- | --- |
| Giai đoạn phát triển: sinh nhãn bạc bằng VLM trên tài liệu công khai | Gemini | Groq nếu có model nhận ảnh | OpenAI | Chỉ khi phát triển và huấn luyện, không dùng khi chạy thật |
| Embedding và reranking | Model chạy cục bộ | — | — | Tài liệu không rời hạ tầng nên không dùng API embedding |

**Thiết kế LLM Gateway**

- **Giao diện thống nhất:** chat, đầu ra có cấu trúc (JSON schema), gọi công cụ, đầu vào ảnh hoặc PDF, embedding. Adapter của từng nhà cung cấp chuyển định dạng (đặc biệt là gọi công cụ và mã lỗi) về một định dạng nội bộ.

- **Registry năng lực theo model:** hỗ trợ ảnh, JSON schema, gọi công cụ, cửa sổ ngữ cảnh, giới hạn tốc độ. Router chỉ chọn model đáp ứng yêu cầu của tác vụ.

- **Chuỗi định tuyến theo tác vụ** (bảng trên) nằm trong tệp policy có phiên bản, không hard-code.

- **Quản lý hạn mức:** token bucket theo nhà cung cấp và model (yêu cầu/phút, token/phút, yêu cầu/ngày); hàng đợi có ưu tiên (hỏi đáp tương tác trước, kiểm tra OCR theo lô sau); theo dõi hạn mức còn lại.

- **Chịu lỗi:** thử lại có backoff cho lỗi tạm thời, circuit breaker khi nhà cung cấp lỗi liên tục, chuyển sang nhà cung cấp kế tiếp trong chuỗi.

- **Cache:** khóa theo (hash ảnh cắt hoặc prompt, phiên bản prompt, model) để không gọi lại.

- **Kiểm soát đầu ra:** mọi đầu ra có cấu trúc được kiểm schema; sai thì thử lại rồi chuyển nhà cung cấp; nhiệt độ thấp cho tác vụ trích xuất.

- **Prompt độc lập nhà cung cấp, có phiên bản;** bộ vàng chạy riêng cho từng nhà cung cấp để biết chất lượng chênh lệch bao nhiêu.

- **Quan sát:** trace ghi provider, model, phiên bản, số token, độ trễ, chi phí ước tính của từng lời gọi.

<!-- Page 30 of 58 -->

**Khi nào được chuyển sang trả phí**

| Điều kiện kích hoạt | Hành vi |
| --- | --- |
| Hết hạn mức miễn phí hoặc lỗi 429 kéo dài | Chuyển sang trả phí nếu cờ cho phép; nếu không, xếp hàng hoặc chuyển sang khuôn mẫu |
| Model bị gỡ hoặc nhà cung cấp ngừng hoạt động | Chuyển theo chuỗi |
| Đầu ra không qua schema sau N lần thử | Leo lên model mạnh hơn trong chuỗi |
| Hậu kiểm số của câu trả lời thất bại nhiều lần | Leo thang một lần; vẫn thất bại thì trả lời bằng khuôn mẫu |
| Tầng riêng tư tuyệt đối, hoặc tenant không cho gọi API | Không gọi API ngoài; ý định bằng bộ cục bộ, câu trả lời theo khuôn mẫu |

Ràng buộc chi phí: cờ *paid_fallback* mặc định tắt; ngân sách tối đa theo tháng, theo job và theo người dùng; vượt ngân sách thì dừng và báo; mỗi lời gọi trả phí được ghi vào trace.

**Quyền riêng tư và quản lý khóa**

- **Tài liệu không rời hạ tầng khi chạy thật;** chỉ câu hỏi đã ẩn danh và kết quả tính toán mới đến API.

- **Bộ ẩn danh cục bộ:** thay tên doanh nghiệp, mã chứng khoán, định danh bằng ký hiệu; bảng ánh xạ chỉ lưu cục bộ và dùng để khôi phục khi trả lời. Giới hạn: số liệu đặc trưng vẫn có thể giúp suy ra doanh nghiệp, nên tenant nhạy cảm dùng chế độ khuôn mẫu.

- Điều khoản dữ liệu của gói miễn phí có thể khác gói trả phí và thay đổi theo thời gian: đọc điều khoản hiện hành của từng nhà cung cấp và coi mọi thứ gửi lên gói miễn phí như có thể bị lưu giữ. Với DeepSeek cần xem thêm yêu cầu về nơi lưu trữ dữ liệu.

- API key lưu trong biến môi trường hoặc secret manager, không ghi log, không đưa vào kho mã; chỉ admin key mới đổi được cấu hình định tuyến.

**Chế độ suy giảm**

Khi không còn nhà cung cấp nào khả dụng, OCR cục bộ, validator, kho chuẩn, Ratio Kernel và Piotroski vẫn chạy. Agent chuyển sang **chế độ khuôn mẫu**: trả bảng số, chỉ số và cảnh báo theo mẫu, không diễn giải tự do, và báo rõ cho người dùng. Ô nghi ngờ vào hàng đợi duyệt tay như bình thường.

<!-- Page 31 of 58 -->

**Rủi ro riêng và tác động lên lộ trình**

- **Hạn mức và danh sách model thay đổi, gói miễn phí không có cam kết dịch vụ:** registry cấu hình, kiểm tra định kỳ, chuỗi dự phòng và chế độ suy giảm.

- **Chất lượng gọi công cụ khác nhau giữa nhà cung cấp:** bộ kiểm thử tương đương (parity) chạy cho từng nhà cung cấp trước khi đưa vào chuỗi.

- **Chi phí trả phí ngoài dự kiến:** ngân sách chặn cứng và cờ mặc định tắt.

- **Phase 0:** tạo khóa, đo hạn mức thực tế, xác nhận danh sách model và điều khoản dữ liệu. **Phase 1:** dùng VLM chỉ để sinh nhãn bạc trên tài liệu công khai. **Phase 4–5:** hoàn thiện LLM Gateway, Agent dùng Groq làm mặc định, adapter OpenAI và DeepSeek dựng sẵn và thử với ngân sách nhỏ. **Phase 6:** chạy đánh giá song song các nhà cung cấp rồi chốt chuỗi định tuyến.

### 12.6 Kế hoạch tài nguyên tính toán

Quyết định: chạy trên **CPU hoặc máy ảo trước; dùng GPU khi quá nặng.**

- **CPU là cấu hình mặc định:** engine adapter có chế độ CPU và GPU; khi benchmark ở Phase 1, mọi engine phải đo được thời gian mỗi trang trên CPU.

- Mọi xử lý tài liệu là job bất đồng bộ qua hàng đợi; tăng số worker theo chiều ngang trên máy ảo khi cần thông lượng.

- **Tiêu chí chuyển sang GPU:** (a) bản scan 25 trang vượt mục tiêu 3 phút trên CPU dù đã tối ưu; (b) mô hình layout hoặc bảng cần GPU để đạt độ chính xác mục tiêu ở Phase 1; (c) huấn luyện quá chậm trên CPU.

- **Cách dùng GPU:** máy ảo GPU theo giờ hoặc worker GPU bật theo nhu cầu, chỉ cho job nặng và huấn luyện; CPU luôn là đường lui.

- Huấn luyện có thể chạy trên máy ảo thuê ngắn hạn; dữ liệu huấn luyện chỉ là báo cáo công khai (mục 24.7).

- Trace ghi thời gian và tài nguyên của từng giai đoạn để quyết định nâng cấp dựa trên số đo.

## 13. Chiến lược kiểm thử và đánh giá

| Tầng | Nội dung | Ví dụ |
| --- | --- | --- |
| Đơn vị | Chuẩn hóa số vi-VN, luật ánh xạ mã số, từng quy tắc kiểm tra, từng chỉ số | Ratio kernel so với bảng tính tay của các ca vàng |

<!-- Page 32 of 58 -->

| Tầng | Nội dung | Ví dụ |
| --- | --- | --- |
| Dựa trên thuộc tính | Sinh báo cáo ngẫu nhiên thỏa mọi đẳng thức rồi làm hỏng đúng một ô, hệ thống phải phát hiện | Đo recall của bộ kiểm tra kế toán |
| Hồi quy OCR | Chạy lại bộ vàng mỗi lần đổi engine hoặc tham số | Cấm giảm tỉ lệ “ô sai không bị gắn cờ” |
| Truy xuất / RAG | Recall@k, độ chính xác trích dẫn, đúng kỳ và đúng scope | Bộ câu hỏi có đáp án gắn trang |
| Agent | Kiểm tra quỹ đạo gọi công cụ và phán quyết Gate | Câu hỏi bẫy: kỳ không có, thiếu scope, đơn vị mơ hồ |
| Bảo mật / red team | Tiêm chỉ thị trong Word và URL, SSRF, file độc hại | Agent phải bỏ qua chỉ thị, chặn URL nội bộ |
| Tải và độ bền | Nhiều job song song, file lớn, lỗi giữa chừng | Khôi phục và idempotent |
| Con người | Chuyên gia tài chính chấm mẫu câu trả lời | Chấm đúng, đủ, có cảnh báo hợp lý |

Chỉ số tổng hợp theo dõi liên tục: độ chính xác ô số, tỉ lệ báo cáo VERIFIED, ô sai không gắn cờ, hallucination rate (số không truy vết), citation precision, recall ABSTAIN, ABSTAIN thừa, độ trễ, chi phí mỗi tài liệu. Mỗi chỉ số có ngưỡng chặn trong CI.

## 14. Cấu trúc kho mã đề xuất

```text
finagent/
  api/                 # FastAPI routers, auth, rate limit, schemas
  ingestion/           # nhận file, kiểm tra an toàn, URL fetch, job
  router/              # phân loại tài liệu và trang
  extraction/
    pdf_text/          # text layer
    ocr_layout/        # tiền xử lý ảnh, layout, bảng, engine adapters
    office/            # excel, word
    text_url/          # text, HTML, tin tức
  statements/          # nhận diện báo cáo, ánh xạ mã số, kỳ, đơn vị, scope
  validation/          # bộ quy tắc, đối chiếu, sửa có ràng buộc
  review/              # hàng đợi duyệt, lịch sử sửa
  store/               # canonical model, provenance, repository
  retrieval/           # chunking, index, hybrid retriever, ranking
  evidence_gate/       # chấm bằng chứng, phán quyết, hậu kiểm số
  analytics/
```

<!-- Page 33 of 58 -->

```text
    ratios/            # kernel + Ratio Registry (15 lõi, mở rộng được),
applicability gate
    piotroski/         # 9 thành phần
    trend/
    industry/
    assessment/
  agent/               # orchestrator, tool registry, trace, composer;
agents/ (verifier, analyst, sector specialist...)
  export/              # JSON, Markdown, Excel
  policy/              # ngưỡng, chính sách chỉ số, phiên bản mẫu biểu, chế
độ vận hành, phân tầng riêng tư
  sector_packs/        # gói ngành: trọng số, ngưỡng, cờ đỏ, chỉ số bổ sung
  corpus/              # kho báo cáo, nhãn vàng/bạc, tập tách train/dev/test
  llm_gateway/         # adapter Groq, Gemini, OpenAI, DeepSeek; router;
quota; cache
  observability/
  tests/               # unit, property, golden, rag, agent, security
  docs/                # financial_index.md, kiến trúc, runbook
  eval/                # bộ vàng, câu hỏi bẫy, script đánh giá
```

Quy tắc phụ thuộc: analytics  chỉ đọc từ store ; agent  chỉ gọi analytics , retrieval , evidence_gate  qua tool registry; extraction  không biết gì về analytics .

## 15. Lộ trình triển khai (v1.3: ước tính 30 tuần cho backend lõi, nhóm 3–4 người; giao diện làm sau)

Nhóm gợi ý: 1 kỹ sư backend/kiến trúc, 1 kỹ sư OCR/ML, 1 kỹ sư Agent/RAG, 1 chuyên gia tài chính kiêm kiểm thử (bán thời gian).

<!-- Page 34 of 58 -->

| Phase | Tuần | Nội dung | Sản phẩm bàn giao | Tiêu chí hoàn thành |
| --- | --- | --- | --- | --- |
| 0. Nền tảng và dữ liệu | 1–3 | Chốt schema canonical, phân tầng dữ liệu, chế độ vận hành, định nghĩa chỉ số v1; danh sách nguồn chính thống và điều khoản sử dụng; kho báo cáo đã công bố đợt 1 (≥ 30, có ca scan khó); thử Groq và Google AI Studio gói miễn phí (hạn mức, danh sách model, khả năng gọi công cụ); thiết kế bộ ẩn danh | Đặc tả, schema, kho đợt 1, báo cáo đo hạn mức | Kiến trúc được duyệt; kho đợt 1 có nhãn đáp án đã duyệt |
| 1. OCR cục bộ và huấn luyện | 4–10 | Benchmark engine cục bộ trên kho; dùng VLM chỉ để sinh nhãn bạc trên tài liệu công khai; huấn luyện và hiệu chỉnh các thành phần nhỏ (phân loại trang, bảng, ánh xạ nhãn); pipeline S0– S5; chuẩn hóa số vi-VN | Báo cáo so sánh engine, pipeline cục bộ, mô hình nhỏ đã huấn luyện | ≥ 98% ô số đúng trước kiểm tra kế toán trên tập kiểm thử; qua cổng go/no-go |
| 2. Hiểu báo cáo và kho chuẩn | 11–15 | S6–S10, validator, sửa có ràng buộc, canonical store, kho phiên bản mẫu biểu, Review API và công cụ dòng lệnh duyệt tay | Kho dữ liệu chuẩn, Review API | ≥ 90% báo cáo trong kho đạt VERIFIED; ô sai không gắn cờ ≤ 0,1% |

<!-- Page 35 of 58 -->

| Phase | Tuần | Nội dung | Sản phẩm bàn giao | Tiêu chí hoàn thành |
| --- | --- | --- | --- | --- |
| 3. Phân tích | 16– 19 | Ratio Registry và kernel; 15 chỉ số lõi theo chính sách đã chốt; Applicability Gate (gồm nhận diện tổ chức tín dụng); Piotroski; Trend; kho ngưỡng chung | Kernel, registry, test tính tay | 100% khớp ca tính tay; cờ phải thu mã 130 đúng nguyên văn; chỉ số tham chiếu nợ vay xuất tự động |
| 4. Truy xuất, Gate và chế độ vận hành | 20– 23 | Chunking, index lai với embedding cục bộ, truy xuất trích xuất, Evidence Gate, hai chế độ, Verifier theo quy tắc, hậu kiểm số, bộ ẩn danh | Hỏi đáp trích xuất có trích dẫn, ABSTAIN và CAVEATS theo chế độ | Lớp số liệu: 0 số sai không gắn cờ; lớp truy vấn đạt mục tiêu từng chế độ (mục 19) |
| 5. LLM Gateway, Agent đơn, API | 24– 27 | Gateway Groq và Gemini (miễn phí), adapter OpenAI và DeepSeek (tắt); hai vị trí dùng model (mục 24); Agent đơn; API /v1, luồng sự kiện, tenant, tầng dữ liệu, job, bảo mật | Agent chạy đầu– cuối | Kịch bản đầu–cuối đạt; kiểm thử chứng minh không có đường gửi tài liệu ra ngoài |
| 6. Củng cố backend lõi | 28– 30 | Đánh giá toàn diện, red team, hiệu năng, mở rộng kho lên ≥ 100 báo cáo, tài liệu OpenAPI, runbook | Bản backend lõi | Đạt KPI mục 2 và mục 19; không còn lỗi BLOCK |

Sau Phase 6: Sector Pack và multi-agent theo ngành do bạn thiết kế (mục 22 và Báo cáo 2), rồi đến giao diện người dùng (mục 23). Ước tính này thô; OCR cục bộ và huấn luyện là phần khó dự đoán nhất và phụ thuộc cấu hình máy tính, nên cần hiệu chỉnh sau Phase 1.

Các cổng quyết định (go/no-go) ở cuối Phase 1 và Phase 2: nếu OCR chưa đạt ngưỡng thì dành thêm thời gian cho OCR thay vì chuyển sang Agent, vì mọi lớp sau đều phụ thuộc dữ liệu đúng.

<!-- Page 36 of 58 -->

## 16. Rủi ro và biện pháp giảm thiểu

| Rủi ro | Mức | Biện pháp |
| --- | --- | --- |
| Chất lượng scan kém làm OCR số sai | Cao | Đa engine, đọc lại bằng engine khác, đẳng thức, duyệt tay; cổng go/no-go sau Phase 1 |
| Mã số và mẫu biểu khác nhau giữa thông tư và doanh nghiệp | Cao | Kho phiên bản mẫu biểu; ánh xạ theo mã số kèm nhận diện nhãn; kiểm tra sau ánh xạ |
| Sai nguồn gốc (nguồn tài liệu bất nhất) bị nhầm là lỗi OCR | Trung bình | Tách “lỗi đọc” và “bất nhất của tài liệu”; gắn cờ, không tự sửa |
| LLM tự diễn giải và đưa số sai | Cao | Số chỉ từ công cụ; hậu kiểm số; Gate; đánh giá bằng câu hỏi bẫy |
| Hiểu sai ý nghĩa chỉ số cho doanh nghiệp đặc thù (holding, tài chính) | Cao | Applicability Gate, cờ NOT_MEANINGFUL, chặn nhóm ngành chưa hỗ trợ |
| Hạn mức và độ trễ của API miễn phí | Trung bình | Cache, hàng đợi ưu tiên, chuỗi dự phòng trả phí, chế độ khuôn mẫu |
| Chỉ thị độc hại trong tài liệu | Trung bình | Cách ly dữ liệu và chỉ thị, danh sách công cụ cố định, red team |
| Ngưỡng ngành không phù hợp | Trung bình | Bảng ngưỡng cấu hình; nêu rõ khi dùng ngưỡng chung |
| Quá phụ thuộc một nhà cung cấp model | Trung bình | LLM Gateway với chuỗi Groq, Gemini, rồi OpenAI hoặc DeepSeek trả phí; đánh giá định kỳ; chế độ suy giảm khi hết nhà cung cấp |
| Phạm vi lan rộng (thêm tính năng) | Trung bình | Phân hạng MoSCoW ở mục 11; chỉ nhận thêm sau Phase 5 |

**Rủi ro bổ sung:**

- **Gán nhầm tầng riêng tư:** tài liệu riêng tư bị coi là công khai. Biện pháp: mặc định riêng tư khi chưa rõ, chỉ admin được hạ tầng, kiểm thử tự động chặn đường gửi ra gói miễn phí.

- **Chế độ Hữu ích bị dùng cho quyết định quan trọng:** lớp số liệu không nới lỏng ở bất kỳ chế độ nào, và xuất báo cáo chính thức luôn kiểm tra ở mức Nghiêm ngặt.

<!-- Page 37 of 58 -->

- **Rò rỉ dữ liệu giữa tập huấn luyện và tập kiểm thử:** chia theo doanh nghiệp, đóng băng tập test, kiểm tra trùng lặp.

- **Multi-agent làm tăng độ trễ, chi phí, lỗi lan truyền:** triển khai theo giai đoạn, chỉ giữ khi vượt baseline Agent đơn (mục 22).

- **Định nghĩa chỉ số mở rộng sai:** mỗi chỉ số mới phải có ca kiểm thử tính tay và duyệt của chuyên gia tài chính trước khi vào Registry.

- **Tài liệu doanh nghiệp chưa niêm yết đa dạng và kém chuẩn hóa:** kho mẫu biểu mở rộng, trạng thái kiểm toán đi vào Evidence Gate, thêm kiểm tra riêng cho Excel và ảnh chụp.

## 17. Các quyết định đã chốt

| # | Chủ đề | Quyết định | Mô tả chi tiết |
| --- | --- | --- | --- |
| 1 | Đối tượng | Doanh nghiệp niêm yết là chính; chưa niêm yết và doanh nghiệp nhỏ và vừa khi khách hàng yêu cầu | Mục 2.2, 18 |
| 2 | Quyền riêng tư | Tài liệu không rời hạ tầng khi chạy thật; báo cáo niêm yết đã công bố là công khai, tài liệu chưa niêm yết và doanh nghiệp nhỏ và vừa riêng tư hết mức có thể | Mục 18, 24 |
| 3 | Cash Ratio | Cấu hình động; mặc định mã 110, bật mở rộng thì thêm mã 120 | Mục 20 |
| 4 | Vòng quay phải thu | Mặc định cố định mã 131; thiếu chi tiết hoặc người dùng chọn mã 130 thì phát cờ cảnh báo nguyên văn | Mục 20 |
| 5 | Tổng nợ | Tính song song hai cách; kết quả chính theo mẫu chuẩn; chỉ số tham chiếu nợ vay chịu lãi tự động xuất ở phần mở rộng | Mục 20 |
| 6 | Bộ chỉ số | 15 chỉ số lõi và Piotroski cho mọi doanh nghiệp, chưa phân ngành; mở rộng qua Ratio Registry | Mục 20, 24.8 |
| 7 | Chế độ vận hành | Nghiêm ngặt và Hữu ích; số liệu và chỉ số luôn 100%, truy vấn định tính ≥ 95%; ô mức C hiển thị kèm nhãn “chưa xác minh” ở chế độ Hữu ích | Mục 19 |

<!-- Page 38 of 58 -->

| # | Chủ đề | Quyết định | Mô tả chi tiết |
| --- | --- | --- | --- |
| 8 | Model API | Chỉ hai vị trí: nhận diện ý định và trích xuất tham số, viết câu trả lời từ kết quả tính toán; Groq và Google AI Studio gói miễn phí làm chính, OpenAI và DeepSeek trả phí làm dự phòng | Mục 12.5, 24 |
| 9 | Hỏi đáp nội dung văn bản báo cáo | Trích xuất cục bộ, không gửi đoạn trích cho model; tính đúng được đảm bảo, đổi lại ít trôi chảy; tóm tắt bằng model để sẵn dưới dạng cờ tắt | Mục 19.5, 24.4 |
| 10 | Ẩn danh | Chỉ thay tên doanh nghiệp, mã chứng khoán và định danh bằng ký hiệu; không cần mức ẩn danh bổ sung | Mục 24.2 |
| 11 | Tài nguyên tính toán | CPU hoặc máy ảo; GPU khi quá nặng | Mục 12.6 |
| 12 | Dữ liệu huấn luyện | Báo cáo đã công bố từ nguồn chính thống; tài liệu chưa niêm yết và doanh nghiệp nhỏ và vừa không dùng, xét lại khi sản phẩm hoàn thiện | Mục 21, 24.7 |
| 13 | Bối cảnh ngành | Chỉ liệt kê nguồn có trích dẫn | Mục 9.5, 24.1 |
| 14 | Ngân hàng và các ngành khác | Giữ giả định, làm thành báo cáo mở rộng riêng sau khi hoàn thành core | Báo cáo 2 |
| 15 | Sector Pack | Hợp đồng giao diện được định nghĩa ngay trong core để thêm ngành không phải sửa core; gói do bạn thiết kế sau | Mục 22, Báo cáo 2 |
| 16 | Multi-agent | Giai đoạn sau core, chiến lược single ở core | Mục 22, Báo cáo 2 |
| 17 | Phạm vi giai đoạn này | Backend hoàn chỉnh trước, giao diện sau | Mục 15, 23 |
| 18 | Duyệt tay | Chủ dự án duyệt | Mục 23 |

Không còn vấn đề mở ở mức quyết định. Các giả định cần xác minh khi mở rộng (đặc biệt về ngân hàng) được ghi ở Báo cáo 2.

## 18. Phân tầng dữ liệu và quyền riêng tư

Quy tắc nền: **chưa chắc chắn là công khai thì coi là riêng tư** (fail-closed). Hệ thống dùng ba tầng dữ liệu, mỗi tầng có chính sách xử lý rõ ràng.

<!-- Page 39 of 58 -->

### 18.1 Ba tầng dữ liệu

| Tầng | Đối tượng | Ghi chú |
| --- | --- | --- |
| Công khai (public) | Báo cáo tài chính đã công bố của doanh nghiệp niêm yết (công bố thông tin trên sàn hoặc website doanh nghiệp); tin tức và tài liệu ngành công khai | Câu hỏi đã ẩn danh và kết quả tính toán được phép gửi tới API ngoài, kể cả gói miễn phí; tài liệu thì không |
| Riêng tư (private) | Doanh nghiệp chưa niêm yết, doanh nghiệp nhỏ và vừa, tài liệu nội bộ, mọi tài liệu chưa xác định được là công khai | Mặc định cho mọi tài liệu không thuộc tầng công khai |
| Riêng tư tuyệt đối (strict private) | Khách hàng yêu cầu dữ liệu không rời hạ tầng của họ | Không gọi API ngoài (xem 18.3) |
|  |  |  |

### 18.2 Cách gán và kế thừa tầng

- **Gán lúc nạp** dựa vào (a) trạng thái niêm yết trong metadata của khách hàng hoặc mã chứng khoán trên báo cáo, (b) nguồn tài liệu (ví dụ URL công bố thông tin), (c) lựa chọn của khách hàng. Không xác định được thì là riêng tư.

- Ai cũng được **nâng** tầng; chỉ admin được **hạ** tầng.

- Tầng **kế thừa xuống mọi sản phẩm phái sinh**: trang, ảnh cắt ô, chunk, embedding, kết quả OCR, cache, trace, file xuất.

- Một yêu cầu dùng nhiều tài liệu thì áp dụng tầng **nghiêm nhất** trong số đó.

### 18.3 Chính sách xử lý theo tầng

| Khía cạnh | Công khai | Riêng tư | Riêng tư tuyệt đối |
| --- | --- | --- | --- |
| Tài liệu gốc, ảnh trang, văn bản báo cáo | Không rời hạ tầng | Không rời hạ tầng | Không rời hạ tầng |
| OCR, trích xuất, kiểm tra kế toán, tính toán, truy xuất | Cục bộ | Cục bộ | Cục bộ |

<!-- Page 40 of 58 -->

| Khía cạnh | Công khai | Riêng tư | Riêng tư tuyệt đối |
| --- | --- | --- | --- |
| API ngoài (nhận diện ý định, viết câu trả lời) | Được: câu hỏi đã ẩn danh, chỉ gửi kết quả cuối; gói miễn phí được phép | Chỉ khi tenant bật; ẩn danh bắt buộc; ưu tiên chế độ khuôn mẫu với dữ liệu nhạy cảm | Không gọi; ý định bằng bộ cục bộ, trả lời theo khuôn mẫu |
| Lưu trữ | Tiêu chuẩn | Mã hóa, tách theo tenant, thời hạn lưu cấu hình được, xóa theo yêu cầu | Như riêng tư, kèm kiểm soát truy cập chặt hơn và nhật ký truy cập |
| Cache | Dùng chung được | Theo tenant | Theo tenant, không ra ngoài hạ tầng |
| Dùng làm dữ liệu huấn luyện | Được, với báo cáo công bố từ nguồn chính thống | Hiện không; xét lại khi sản phẩm hoàn thiện, cần đồng ý bằng văn bản | Không |

### 18.4 Hệ quả thiết kế

- **Tài liệu không rời hạ tầng khi chạy thật** ở mọi tầng; chỉ câu hỏi đã ẩn danh và kết quả tính toán mới có thể tới API ngoài. Ngoại lệ duy nhất: giai đoạn phát triển và huấn luyện trên tài liệu công khai từ nguồn chính thống (mục 24.5, 24.7).

- **Bộ ẩn danh cục bộ** (mục 24.2): thay tên doanh nghiệp, mã chứng khoán, định danh bằng ký hiệu; bảng ánh xạ chỉ lưu cục bộ; khôi phục khi trả lời. Giới hạn: số liệu đặc trưng vẫn có thể giúp suy ra doanh nghiệp, nên tenant nhạy cảm dùng chế độ khuôn mẫu.

- Mọi lời gọi ra ngoài được ghi trace (nhà cung cấp, tầng, nội dung đã ẩn danh); kiểm thử tự động chứng minh không có đường nào gửi tài liệu hay văn bản báo cáo ra ngoài.

### 18.5 Đặc thù của doanh nghiệp chưa niêm yết và doanh nghiệp nhỏ và vừa

- **Mẫu biểu khác:** doanh nghiệp nhỏ và vừa thường dùng mẫu và mã số khác Thông tư 200 (cần xác minh khi dựng kho mẫu biểu); không hard-code mã.

- **Thường chưa kiểm toán:** trạng thái kiểm toán đi vào Evidence Gate; số liệu chưa kiểm toán luôn kèm cảnh báo.

- **Nhiều định dạng kém chuẩn hóa:** Excel nội bộ, báo cáo xuất từ phần mềm kế toán, ảnh chụp bằng điện thoại. Tiền xử lý ảnh mạnh hơn, kiểm tra riêng cho Excel (công thức, ô gộp, nhiều phiên bản), tỉ lệ duyệt tay cao hơn.

<!-- Page 41 of 58 -->

- **Thiếu thuyết minh:** nhiều chỉ số sẽ ở trạng thái MISSING_ITEM; hệ thống phải dùng CAVEATS hoặc ABSTAIN đúng chỗ thay vì đoán.

- **Không có dữ liệu ngành công khai để so sánh:** dùng ngưỡng từ kho báo cáo hoặc Sector Pack chung và nêu rõ nguồn so sánh.

## 19. Hai chế độ vận hành: Nghiêm ngặt và Hữu ích

### 19.1 Nguyên tắc: hai lớp tuyên bố với yêu cầu khác nhau

| Lớp | Gồm | Yêu cầu |
| --- | --- | --- |
| Lớp N: số liệu | Giá trị trích từ báo cáo, 15 chỉ số, Piotroski, điểm và xếp hạng | 100%: không có số sai nào được hiển thị mà không bị gắn cờ |
| Lớp Q: truy vấn | Câu hỏi định tính, giải thích, tóm tắt, so sánh diễn giải | ≥ 95% mệnh đề khẳng định được bằng chứng ủng hộ (chế độ Hữu ích) |

Yêu cầu 100% ở Lớp N đạt được **bằng thiết kế** (số chỉ đến từ kho chuẩn đã qua đẳng thức, hậu kiểm số, duyệt tay), không bằng hy vọng, và được đo trên bộ vàng. Cần nói thẳng một giới hạn: nếu chính tài liệu nguồn sai hoặc bất nhất (như số cổ phiếu ở mục 3.4), hệ thống không thể “đúng” hơn nguồn; nó phát hiện, gắn cờ và nêu rõ. Lớp N giống nhau ở hai chế độ, ngoại trừ cách xử lý ô mức C (đã chốt: hiển thị kèm nhãn “chưa xác minh” ở chế độ Hữu ích).

### 19.2 So sánh hai chế độ

| Khía cạnh | Nghiêm ngặt (không bao giờ sai) | Hữu ích (tối đa giá trị) |
| --- | --- | --- |
| Tinh thần | Thà từ chối còn hơn sai | Trả lời được càng nhiều càng tốt, kèm cảnh báo rõ |
| Lớp N: ô mức C (một engine, chưa đẳng thức) | Chặn, đưa vào hàng đợi duyệt | Chỉ hiện khi gắn nhãn “chưa xác minh” và không dùng để tính điểm tổng hay xếp hạng (đã chốt) |
| Lớp N: ô mức D | Chặn | Chặn |
| Lớp Q: mệnh đề khẳng định | Mỗi mệnh đề phải có bằng chứng trực tiếp; thiếu thì ABSTAIN | Cho phép trả lời một phần, suy luận có nêu giả định; thiếu thì CAVEATS thay vì ABSTAIN |

<!-- Page 42 of 58 -->

| Khía cạnh | Nghiêm ngặt (không bao giờ sai) | Hữu ích (tối đa giá trị) |
| --- | --- | --- |
| Ngưỡng Evidence Gate | Cao: đủ coverage, kỳ và scope khớp, nguồn đồng thuận | Vừa: chấp nhận thiếu phần phụ nếu phần cốt lõi đủ |
| Truy xuất | Top-k nhỏ, lọc chặt theo scope và kỳ | Top-k rộng hơn, viết lại câu hỏi, mở rộng truy vấn |
| Verifier | Hậu kiểm số và kiểm mọi mệnh đề bằng verifier độc lập | Hậu kiểm số bắt buộc; kiểm mệnh đề theo mẫu hoặc khi rủi ro cao |
| Nhãn Piotroski | Chỉ khi đủ cả 9 thành phần | Khi có ít nhất 7 trong 9 thành phần (mục 9.3) |
| Leo thang sang mô hình trả phí | Cho phép để phân xử khi admin bật | Chỉ khi hết hạn mức hoặc lỗi |
| Mục tiêu Lớp Q (đề xuất, hiệu chỉnh sau Phase 4) | ≥ 99% mệnh đề được ủng hộ; ABSTAIN thừa ≤ 15% | ≥ 95% mệnh đề được ủng hộ; ABSTAIN thừa ≤ 5%; độ phủ trả lời ≥ 90% |
| Mục tiêu Lớp N | 0 số sai không gắn cờ | 0 số sai không gắn cờ |
| Đổi lại | Chậm hơn, nhiều từ chối hơn | Nhanh hơn, nhiều cảnh báo hơn |

### 19.3 Cấu hình và áp dụng

- **Bốn cấp cấu hình:** hệ thống → tenant → khóa API → từng yêu cầu. Cấp dưới chỉ đặt được trong giới hạn do cấp trên cho phép (ví dụ admin khóa một tenant ở Nghiêm ngặt).

- **Mặc định đề xuất:** hỏi đáp tương tác dùng Hữu ích; xuất báo cáo chính thức và đánh giá sức khỏe tài chính (Assessment) luôn kiểm tra ở mức Nghiêm ngặt bất kể cài đặt.

- Chế độ đang dùng được ghi trong kết quả và trace; người dùng luôn thấy chế độ nào đã áp dụng.

- **Đổi chế độ không làm đổi bất kỳ số liệu nào đã tính**; chỉ đổi ngưỡng Gate, cách xử lý thiếu bằng chứng và mức kiểm tra.

### 19.4 Cách đo mục tiêu

- Tách câu trả lời thành **mệnh đề nguyên tử**; mỗi mệnh đề được gắn nhãn: có bằng chứng ủng hộ, không có bằng chứng, hoặc mâu thuẫn. Tỉ lệ ủng hộ = số mệnh đề ủng hộ ÷ số mệnh đề khẳng định (không tính mệnh đề đã nêu rõ là giả định).

<!-- Page 43 of 58 -->

- Chấm bằng verifier kết hợp chuyên gia chấm mẫu, trên bộ câu hỏi có đáp án, gồm cả câu bẫy.

- Để khẳng định “≥ 95%” một cách có ý nghĩa thống kê cần vài trăm mệnh đề trở lên; báo cáo kèm khoảng tin cậy chứ không chỉ một con số.

- Ngưỡng Gate được hiệu chỉnh trên bộ vàng để đạt mục tiêu của từng chế độ rồi đóng băng theo phiên bản.

### 19.5 Tác động của quy tắc “không gửi tài liệu ra ngoài”

Lớp Q gồm hai loại: (a) giải thích khái niệm, công thức, ý nghĩa của kết quả: dùng bảng định nghĩa và đáp số, model chỉ diễn đạt; (b) hỏi về nội dung văn bản báo cáo: trả lời **trích xuất** (đoạn nguyên văn kèm trang) từ truy xuất cục bộ, không tóm tắt bằng model ngoài (mục 24.4). Cách này giúp đạt mục tiêu “mệnh đề được bằng chứng ủng hộ” dễ hơn nhưng câu trả lời kém trôi chảy hơn. Tóm tắt bằng model cho tầng công khai đã được chốt là tắt và để sẵn dưới dạng cờ tính năng (mục 22).

## 20. Ratio Registry và chính sách chỉ số đã chốt

### 20.1 Ba chính sách đã chốt

| Chỉ số | Mặc định | Cấu hình hoặc kích hoạt | Cờ và đầu ra phụ |
| --- | --- | --- | --- |
| Chỉ số 3: Cash Ratio | Tử số = mã 110 (tiền và tương đương tiền) | Cấu hình động (hệ thống, tenant, yêu cầu): bật mở rộng thì tử số = 110 + 120 | Kết quả ghi rõ công thức đã dùng; khi bật mở rộng, cảnh báo thành phần mã 120 (gồm cả khoản không thanh khoản cao) |
| Chỉ số 8: vòng quay khoản phải thu | Cố định mã 131 (phải thu ngắn hạn của khách hàng) | Dùng mã 130 khi (a) dữ liệu thiếu chi tiết mã 131, hoặc (b) người dùng chủ động chọn | Cờ cảnh báo WARN, mã RECEIVABLES_BASIS_130 (chi tiết dưới) |
| Chỉ số 4 và 5: đòn bẩy (tổng nợ) | Kết quả chính theo Cách 1: tổng nợ phải trả (mã 300), đúng mẫu biểu chuẩn của thông tư kế toán | Ratio Kernel luôn tính song song cả hai cách | Chỉ số tham chiếu phụ theo Cách 2 (nợ vay chịu lãi) tự động có trong phần dữ liệu mở rộng |

<!-- Page 44 of 58 -->

### 20.2 Chi tiết

**Cash Ratio.** Hai biến thể được định nghĩa trong Registry; cờ cấu hình chọn biến thể áp dụng. Khi bật mở rộng, hệ thống có thể xuất song song giá trị mặc định để người dùng so sánh.

**Vòng quay khoản phải thu.** Quy tắc quyết định:

| Tình huống | Hành vi |
| --- | --- |
| Có mã 131 (kể cả 131 bằng 0 ghi tường minh) và người dùng không chọn mã 130 | Dùng 131, không cờ. Nếu 131 bằng 0 thì chỉ số là N/A vì không có phải thu khách hàng; không âm thầm chuyển sang 130 |
| Không có mã 131 trong dữ liệu (thiếu chi tiết) | Tự dùng mã 130 và phát cờ |
| Người dùng chủ động chọn mã 130 | Dùng 130 và phát cờ |

Nội dung cờ, nguyên văn: “Chỉ số vòng quay đang được tính dựa trên Tổng các khoản phải thu (130) thay vì Phải thu khách hàng (131)”. Cờ được đính vào kết quả của chỉ số, vào giải thích công khai của Agent và vào file xuất. Hệ thống phân biệt rõ *explicit_zero* (ghi 0 hoặc gạch ngang) với *missing* (không có dòng) để quyết định đúng.

**Tổng nợ của chỉ số đòn bẩy.**

| Loại | Chỉ số | Công thức | Vai trò |
| --- | --- | --- | --- |
| Chính (Cách 1) | Debt Ratio | Tổng nợ phải trả (300) ÷ Tổng tài sản (280) | Tham gia Assessment |
| Chính (Cách 1) | D/E | Tổng nợ phải trả (300) ÷ Vốn chủ sở hữu (400) | Tham gia Assessment |
| Tham chiếu phụ (Cách 2) | Debt Ratio nợ vay | Nợ vay chịu lãi ÷ Tổng tài sản | Chỉ xuất ra dữ liệu mở rộng, gắn nhãn “tham chiếu”, không tính điểm |
| Tham chiếu phụ (Cách 2) | D/E nợ vay | Nợ vay chịu lãi ÷ Vốn chủ sở hữu | Như trên |

Nợ vay chịu lãi = vay và nợ thuê tài chính ngắn hạn + dài hạn (và trái phiếu phát hành nếu có), lấy theo mã của đúng phiên bản mẫu biểu. Nếu thiếu chi tiết nợ vay thì chỉ các chỉ số tham chiếu phụ là N/A (MISSING_ITEM); kết quả chính vẫn tính bình thường.

*Ví dụ với báo cáo riêng quý 1/2026 của FPT:* Debt Ratio chính 0,235 và D/E chính 0,306; chỉ số tham chiếu nợ vay lần lượt khoảng 0,191 và 0,250 (nợ vay ngắn hạn 6.327,9 tỷ đồng, báo cáo không có vay dài hạn). Theo Thuyết minh 13, khoảng 4.664 tỷ đồng trong số này là vay

<!-- Page 45 of 58 -->

từ các công ty con trong tập đoàn, nên hệ thống nên kèm thêm cờ “vay từ bên liên quan” để người phân tích hiểu đúng bản chất.

### 20.3 Ratio Registry: mở rộng mà không sửa kernel

Mỗi chỉ số là một **định nghĩa khai báo** (dữ liệu), không phải mã trong kernel. Kernel chỉ là bộ thực thi nhỏ, kiểm thử kỹ, chạy biểu thức an toàn trên các mã chuẩn, không chạy mã tùy ý.

| Trường trong định nghĩa | Nội dung |
| --- | --- |
| id, tên, nhóm/trụ cột | Định danh và vị trí trong Assessment |
| Công thức | Biểu thức trên mã chuẩn (canonical_id), kèm biến thể (ví dụ Cách 1 và Cách 2) |
| Yêu cầu dữ liệu | Báo cáo nào, kỳ nào, scope nào, cơ sở số cuối kỳ hay bình quân |
| Điều kiện áp dụng | Quy tắc cho Applicability Gate (ví dụ tồn kho không đáng kể → N/A) |
| Tham số cấu hình | Ví dụ cờ mở rộng của Cash Ratio, chọn mã 131 hay 130 |
| Cờ cảnh báo | Điều kiện phát cờ và nội dung nguyên văn |
| Hướng tốt và dải ngưỡng | Cao tốt hay thấp tốt; ngưỡng mặc định và theo ngành |
| Trạng thái | core (15 chỉ số lõi, khóa), extended (đã duyệt), experimental (chưa tính điểm) |
| Phiên bản, nguồn định nghĩa | File chỉ số hoặc Sector Pack; kết quả luôn lưu phiên bản định nghĩa để tái lập |
| Ca kiểm thử bắt buộc | Ít nhất một ca tính tay trên báo cáo thật |

Quy trình thêm chỉ số: (1) viết định nghĩa, (2) thêm ca kiểm thử tính tay, (3) chuyên gia tài chính duyệt, (4) chạy hồi quy trên kho báo cáo để xem giá trị phân bố hợp lý, (5) phát hành ở trạng thái experimental, (6) chuyển sang extended và gắn trọng số trong Sector Pack khi đạt. **15 chỉ số lõi chỉ đổi qua quy trình phiên bản.** Chỉ số mở rộng không tự tham gia điểm tổng cho đến khi có trọng số.

Ứng viên mở rộng: DSO, DIO, DPO và chu kỳ chuyển đổi tiền; DuPont; EBITDA margin; Net debt/EBITDA; dòng tiền tự do; tăng trưởng doanh thu và lợi nhuận; Altman Z″; các chỉ số riêng ngành (ví dụ người mua trả tiền trước và tồn kho của bất động sản; NIM, NPL, CAR

<!-- Page 46 of 58 -->

của ngân hàng khi có mẫu biểu tương ứng).

## 21. Kho báo cáo: huấn luyện, đối chiếu và đánh giá

Việc bạn có thể cung cấp rất nhiều báo cáo là lợi thế lớn nhất của dự án. Cần làm rõ một điểm: “huấn luyện Agent” ở đây **không phải** tinh chỉnh (fine-tune) mô hình ngôn ngữ lớn. Kho báo cáo được dùng cho sáu việc, và phần lớn giá trị đến từ việc đo lường và hiệu chỉnh, không phải từ huấn luyện LLM.

### 21.1 Sáu cách dùng kho báo cáo

| # | Mục đích | Cách dùng |
| --- | --- | --- |
| 1 | Đánh giá | Tập kiểm thử đóng băng để đo OCR, validator, Ratio Kernel, RAG và Agent |
| 2 | Hiệu chỉnh OCR và bảng | Chọn tham số, tinh chỉnh mô hình layout và nhận dạng bảng nhỏ nếu đo được lợi ích; xây luật căn cột theo từng mẫu biểu |
| 3 | Ánh xạ mã số và nhãn | Học các biến thể nhãn tiếng Việt cho từng mã số, phát hiện mẫu biểu mới hoặc lệch mã |
| 4 | Hiệu chỉnh độ tin cậy | Đo xác suất đúng thực tế của các mức A–D và ngưỡng Evidence Gate |
| 5 | Benchmark và ngưỡng theo ngành | Tính phân vị từng chỉ số theo ngành cho Sector Pack (mục 22) |
| 6 | Câu hỏi và đáp án mẫu | Bộ câu hỏi đánh giá Agent, ví dụ few-shot; có thể tinh chỉnh mô hình nhỏ cho tác vụ hẹp (phân loại trang, ánh xạ nhãn) nếu có lợi ích đo được |

Kho cũng phục vụ **đối chiếu**: nhiều kỳ của cùng một doanh nghiệp cho phép kiểm tra chéo kỳ (số đầu kỳ bằng số cuối kỳ trước) và phát hiện báo cáo điều chỉnh lại số liệu.

### 21.2 Nguyên tắc dữ liệu

- **Chia tập theo doanh nghiệp**, không theo trang hay theo báo cáo, để tránh rò rỉ (cùng một doanh nghiệp xuất hiện ở cả huấn luyện và kiểm thử sẽ làm số đo đẹp giả tạo).

- **Ba tập:** huấn luyện, phát triển (dev), kiểm thử. Tập kiểm thử bị đóng băng và không dùng để chỉnh tham số.

- **Lấy mẫu phân tầng:** theo ngành, niêm yết hay chưa, loại báo cáo (riêng, hợp nhất), kỳ (quý, năm), chất lượng scan, năm, mẫu biểu, kiểm toán hay chưa.

<!-- Page 47 of 58 -->

- **Nhãn vàng và nhãn bạc:** nhãn vàng do chuyên gia duyệt ở cấp ô số; nhãn bạc là kết quả hệ thống tự đạt VERIFIED. Đánh giá chính thức chỉ dùng nhãn vàng; nhãn bạc dùng cho benchmark ngành và huấn luyện phụ.

- **Vòng phản hồi:** OCR → validator → hàng đợi duyệt → nhãn vàng → quay lại kho. Mỗi lần duyệt tay làm kho tốt hơn.

- **Quản trị:** quyền sử dụng của từng nguồn (tài liệu riêng tư hiện không dùng để huấn luyện; chỉ xét lại khi sản phẩm hoàn thiện và khách hàng đồng ý, mục 24.6), ẩn danh khi cần, tách theo tenant, phiên bản bộ dữ liệu, mô tả bộ dữ liệu (dataset card), loại bản trùng.

### 21.3 Khuyến nghị về quy mô và thứ tự

- Chất lượng và độ đa dạng của nhãn quan trọng hơn số lượng. Bắt đầu với khoảng 30 báo cáo đa dạng (đợt 1, Phase 0), tăng lên khoảng 100 có nhãn vàng ở cuối Phase 6; phần lớn hơn nữa dùng làm nhãn bạc cho benchmark ngành.

- Ưu tiên chọn các ca **khó**: scan nghiêng, hai cột kỳ, báo cáo hợp nhất nhiều trang, mẫu biểu lạ, doanh nghiệp holding, doanh nghiệp nhỏ và vừa; các ca dễ không giúp phát hiện điểm yếu.

## 22. Hướng phát triển và điểm mở rộng của core

Sector Pack, multi-agent theo ngành và các ngành cụ thể (Công nghệ, Ngân hàng, Logistics) được thiết kế và triển khai **sau khi core hoàn thành**; chi tiết nằm ở **Báo cáo 2: Hướng phát triển**. Mục này định nghĩa những gì core phải làm **ngay từ đầu** để các hướng đó được thêm vào mà **không phải sửa core**.

### 22.1 Nguyên tắc

- Mở rộng bằng **dữ liệu và cấu hình khai báo**, không bằng mã trong core.

- **Core dùng chính các điểm mở rộng này ngay từ ngày đầu:** gói ngành chung chạy qua giao diện Sector Pack, mẫu biểu doanh nghiệp thông thường chạy qua kho mẫu biểu. Nhờ đó đường mở rộng luôn được kiểm thử.

- Mọi định nghĩa mở rộng có phiên bản, ca kiểm thử bắt buộc và chạy hồi quy trên kho trước khi phát hành.

- Các bất biến không bị phá: số chỉ đến từ kho chuẩn và kernel; gói ngành không đổi giá trị chỉ số; tài liệu không rời hạ tầng khi chạy thật; Verifier là cổng cuối; fail-closed.

<!-- Page 48 of 58 -->

### 22.2 Các điểm mở rộng

| EP | Điểm mở rộng | Core cung cấp sẵn |
| --- | --- | --- |
| EP1 | Ratio Registry | Định nghĩa chỉ số khai báo; 15 chỉ số lõi; trạng thái experimental, extended, core |
| EP2 | Sector Pack Interface v1 | Gói chung generic@1 ; bộ nạp và kiểm tra gói (mục 22.3) |
| EP3 | Kho mẫu biểu | Mẫu doanh nghiệp thông thường; trường statement_family và template_id |
| EP4 | Kho quy tắc kiểm tra | Quy tắc khai báo gắn với mẫu biểu |
| EP5 | Luật áp dụng | Applicability Gate đọc luật khai báo từ Registry và gói |
| EP6 | Classifier plug-in | Điểm gọi bộ phân loại trang, ngành, mẫu biểu; hiện trả về gói chung cho ngành |
| EP7 | Agent Role Registry | Giao diện vai trò (mục 22.4); chiến lược điều phối single |
| EP8 | Tool Registry | Công cụ khai báo có schema và quyền |
| EP9 | LLM Gateway | Adapter nhà cung cấp, registry năng lực, tuyến theo loại tác vụ |
| EP10 | Evidence Source Connector | Giao diện nguồn bối cảnh có điểm tin cậy |
| EP11 | Cờ tính năng | Cờ theo tầng dữ liệu và tenant; mặc định tắt cho mọi tính năng gửi dữ liệu ra ngoài |
| EP12 | Hợp đồng API và sự kiện | API /v1, luồng sự kiện, endpoint ảnh cắt ô (mục 23.2) |

### 22.3 Hợp đồng Sector Pack Interface v1

| Trường | Nội dung |
| --- | --- |
| Định danh | pack_id, version, interface_version ( spack/1 ), status (draft, approved), min_core_version |
| Nhận diện ngành | Nhãn ngành và gợi ý cho bộ phân loại |
| Mẫu biểu yêu cầu | Danh sách template_id gói cần |
| Mở rộng dòng | Mã chuẩn bổ sung và ánh xạ theo mẫu biểu |

<!-- Page 49 of 58 -->

| Trường | Nội dung |
| --- | --- |
| Chỉ số | Danh sách chỉ số (lõi và mở rộng), vai trò (tính điểm, tham chiếu, ẩn), trọng số theo chỉ số và theo trụ cột |
| Ngưỡng và benchmark | Dải ngưỡng, nguồn, cỡ mẫu, ngày tính |
| Luật áp dụng ghi đè | Điều kiện N/A hoặc NOT_MEANINGFUL theo ngành |
| Cờ đỏ | Điều kiện khai báo trên chỉ số, dòng, xu hướng |
| Chính sách Piotroski | standard , variant hoặc not_applicable |
| Hướng dẫn diễn giải | Thuật ngữ, ràng buộc diễn đạt, danh sách “không được nói” cho vị trí 2 (mục 24.3) |
| Ca kiểm thử | Bộ ca bắt buộc |
| Nguồn gốc | Tác giả, ngày, nguồn dữ liệu |

Core thực thi các quy tắc sau với mọi gói:

- **Gói chung generic@1  đi kèm core** và là gói mặc định.

- Gói được nạp và kiểm tra khi khởi động: đúng schema, tham chiếu hợp lệ, ca kiểm thử đạt; gói lỗi không được nạp.

- **Gói không đổi giá trị chỉ số**; chỉ quyết định chỉ số nào tham gia, trọng số, ngưỡng, cờ và diễn giải.

- Biểu thức chỉ dùng ngôn ngữ biểu thức an toàn của Registry; không có mã tùy ý.

- Chọn gói theo bộ phân loại ngành (khi có) hoặc theo lựa chọn của người dùng; không chọn được thì dùng gói chung kèm cảnh báo.

- Kết quả luôn ghi pack_id@version  và ratio_def_version .

- Gói khai báo min_core_version ; core từ chối gói yêu cầu phiên bản cao hơn.

### 22.4 Hợp đồng Agent Role Interface

Mỗi vai trò khai báo: mục đích, công cụ được phép, tuyến model theo loại tác vụ, schema đầu vào và đầu ra, ngân sách (bước, token, thời gian), và rào chắn. Core chỉ triển khai chiến lược điều phối single  (một Orchestrator), nhưng **mọi lời gọi của Agent đã đi qua giao diện vai trò**, nên thêm vai trò hoặc chuyển sang chiến lược supervisor  là thay đổi cấu hình. **Verifier luôn là cổng cuối bắt buộc** ở mọi chiến lược.

<!-- Page 50 of 58 -->

### 22.5 Trường dữ liệu dành sẵn trong core

- statement_family  (mặc định corporate ) và template_id  trong thực thể Statement (mục 6.1).

- source_tier  (tầng dữ liệu) kế thừa xuống mọi sản phẩm phái sinh (mục 18).

- pack_id@version , ratio_def_version , chế độ vận hành và cờ trong mọi kết quả phân tích.

### 22.6 Các hướng phát triển sau core

Sector Pack Công nghệ, Logistics; ngân hàng (mẫu biểu, chỉ số và gói riêng); tự phân loại ngành; multi-agent theo ngành; chỉ số mở rộng; chứng khoán và bảo hiểm; doanh nghiệp nhỏ và vừa; tóm tắt bằng model cho văn bản công khai và bối cảnh ngành (cờ tắt); giao diện người dùng; GPU và triển khai tại chỗ; so sánh nhiều doanh nghiệp; IFRS. Với mỗi hướng, **Báo cáo 2** nêu cần gì, có đổi core không, thêm vào như thế nào và phần liên quan.

## 23. Backend trước, giao diện sau

### 23.1 Thế nào là “backend hoàn chỉnh”

Mọi chức năng dùng được hoàn toàn qua API và công cụ dòng lệnh, không cần giao diện để vận hành: nạp và OCR, kho chuẩn, validator, Review API, Ratio Registry và kernel, Piotroski, Trend, Assessment, RAG và Evidence Gate, hai chế độ vận hành, LLM Gateway, Agent, tenant và tầng riêng tư, job, bảo mật, quan sát, bộ đánh giá, export, cấu hình admin. Có tài liệu OpenAPI, script đánh giá và runbook.

### 23.2 Hợp đồng API ổn định cho giao diện về sau

- API có phiên bản (/v1), schema thống nhất, phân trang, khóa idempotency.

- **Luồng sự kiện** (SSE hoặc WebSocket) cho tiến độ job và cho câu trả lời của Agent, để giao diện sau này hiển thị theo thời gian thực mà không phải sửa backend.

- Endpoint trả **ảnh cắt ô kèm bbox** và giá trị ứng viên cho duyệt tay.

- Phần giải thích công khai (bằng chứng, công thức, giả định, cảnh báo, còn thiếu) trả về dạng có cấu trúc để giao diện tự dựng.

- Mã lỗi và khóa thông báo chuẩn hóa, hỗ trợ tiếng Việt và tiếng Anh; webhook thông báo khi job xong.

- Trường chế độ vận hành và tầng dữ liệu có trong mọi yêu cầu và phản hồi.

<!-- Page 51 of 58 -->

### 23.3 Công cụ thay thế giao diện trong giai đoạn này

- **Review API và công cụ dòng lệnh** duyệt tay: xuất ảnh cắt ô và giá trị ứng viên ra thư mục, nhận lại file quyết định.

- Cổng thử nghiệm API tự sinh từ OpenAPI.

- Script và notebook đánh giá; báo cáo Markdown, JSON, Excel.

### 23.4 Lộ trình

Lộ trình nằm ở **mục 15** (7 phase, khoảng 30 tuần cho backend lõi). Giao diện người dùng bắt đầu sau Phase 6 trên nền API đã ổn định.

## 24. Quyết định: model API chỉ ở hai vị trí, tài liệu không rời hạ tầng

Khi chạy thật, **tài liệu không được gửi ra API bên ngoài**; model API chỉ làm hai việc về ngôn ngữ.

### 24.1 Nguyên tắc và phân vai

- **Tài liệu gốc, ảnh trang và văn bản báo cáo không bao giờ rời hạ tầng khi chạy thật.** Ngoại lệ duy nhất: giai đoạn phát triển và huấn luyện, trên tài liệu công khai lấy từ nguồn chính thống (mục 24.5, 24.7).

- Model API chỉ xuất hiện ở **hai vị trí**; mọi việc còn lại chạy cục bộ.

| Thành phần | Việc | Dữ liệu được phép gửi ra ngoài |
| --- | --- | --- |
| FastAPI và các thành phần cục bộ | OCR và trích xuất, validator, kho chuẩn, Ratio Kernel, Piotroski, Trend, Assessment, truy xuất, Evidence Gate, Verifier theo quy tắc, tầng dữ liệu, bộ ẩn danh | Không gửi gì |
| Model API, vị trí 1 | Nhận diện ý định và trích xuất tham số (function calling) | Câu hỏi của người dùng, đã ẩn danh |
| Model API, vị trí 2 | Viết câu trả lời từ kết quả tính toán | Kết quả cuối (đáp số, trạng thái, cờ), đã ẩn danh nếu tầng yêu cầu; không gửi bảng thô |

Ranh giới: **model chỉ “hiểu” và “diễn đạt”; FastAPI chỉ “tính” và “quyết định”.** Model không tự tính số, không tự chuẩn hóa số, không thấy tài liệu.

<!-- Page 52 of 58 -->

Bối cảnh ngành từ tin tức công khai (mục 9.5): đã chốt chỉ **liệt kê nguồn có trích dẫn**, không dùng model để tóm tắt. Khả năng tóm tắt bằng model được để sẵn dưới dạng cờ tính năng tắt (mục 22; Báo cáo 2).

### 24.2 Vị trí 1: nhận diện ý định và trích xuất tham số

- **Luồng:** câu hỏi của người dùng → bộ ẩn danh cục bộ (thay tên doanh nghiệp, mã chứng khoán và định danh bằng ký hiệu như “Doanh nghiệp A”) → model API kèm danh sách công cụ → model trả về lệnh gọi hàm dạng JSON → FastAPI khôi phục tên thật cục bộ và thực thi công cụ.

- **Ví dụ:** câu hỏi “Tính giúp tôi ROE của công ty X năm 2025” cho lệnh {"action":"compute_ratios","ratio":"roe","company":"Doanh nghiệp A","period":"2025"} . Không có dữ liệu tài chính nào bị gửi đi; model chỉ nhận một câu hỏi và chỉ làm nhiệm vụ hiểu người dùng muốn gì.

- **Kiểm soát:** chỉ chấp nhận lệnh nằm trong danh mục công cụ, với schema chặt; tham số thiếu hoặc sai thì hỏi lại người dùng; model không được gọi công cụ ngoài danh mục.

- **Lưu ý về ví dụ P/E:** P/E cần giá thị trường, không có trong báo cáo tài chính và không thuộc 15 chỉ số lõi. Nếu người dùng hỏi, hệ thống trả MISSING_ITEM hoặc OUT_OF_DOMAIN, hoặc sau này thêm chỉ số vào Ratio Registry kèm một nguồn giá được duyệt.

- **Dự phòng:** tầng riêng tư tuyệt đối, hết hạn mức, hoặc mất kết nối thì dùng bộ nhận diện ý định cục bộ (luật và bộ phân loại nhỏ). Chấp nhận khả năng hiểu câu hỏi tự do thấp hơn.

### 24.3 Vị trí 2: soạn câu trả lời từ kết quả tính toán

- **Luồng:** FastAPI tính xong và gói thành “đáp số” (giá trị, đơn vị, kỳ, scope, trạng thái, cờ, mã công thức) → ẩn danh nếu tầng yêu cầu → model viết đoạn trả lời → **hậu kiểm cục bộ** → khôi phục tên thật → trả về người dùng.

- **Hậu kiểm:** mọi con số trong văn bản phải thuộc tập đáp số của lượt đó; không được thêm thực thể, kỳ hay khẳng định mới; trạng thái và cờ phải được giữ. Không qua thì thử lại; vẫn không qua thì trả lời bằng khuôn mẫu.

- **Ví dụ:** từ kết quả “ROE quý 1 = 7,22%, trạng thái bình thường”, model viết thành một đoạn nhận xét mạch lạc. Hai lưu ý: (a) ở giai đoạn lõi chưa có so sánh theo ngành, chỉ so với ngưỡng chung của file chỉ số; (b) lời nhận xét kiểu “định giá hấp dẫn” là khuyến nghị đầu tư, vốn nằm ngoài phạm vi (mục 2.2), nên prompt ràng buộc model chỉ mô tả và giải thích, không khuyến nghị mua hay bán.

- **Theo chế độ vận hành:** Nghiêm ngặt dùng khuôn mẫu cố định hoặc cho model chỉ diễn đạt lại dưới hậu kiểm chặt; Hữu ích cho model viết tự do hơn nhưng vẫn trong ràng buộc trên.

<!-- Page 53 of 58 -->

### 24.4 Hỏi đáp về nội dung văn bản báo cáo

Vì văn bản báo cáo không được gửi ra ngoài, câu hỏi về nội dung (chính sách kế toán, cơ cấu doanh nghiệp, giải thích một thuyết minh) được trả lời theo kiểu **trích xuất**: truy xuất cục bộ (embedding và reranking chạy cục bộ) trả đoạn nguyên văn kèm trang và vị trí, không tóm tắt bằng model ngoài. Đổi lại là câu trả lời ít trôi chảy hơn nhưng bám sát bằng chứng. Quyết định: không gửi đoạn trích cho model. Về chất lượng: tính đúng được đảm bảo theo thiết kế vì câu trả lời là văn bản gốc kèm trang và vị trí; thứ giảm đi là độ trôi chảy và khả năng tổng hợp nhiều đoạn. Cách cải thiện cục bộ: khuôn mẫu trình bày (tiêu đề mục, đoạn trích, nguồn), gom các đoạn liên quan theo thuyết minh, và đánh dấu đoạn trả lời trực tiếp câu hỏi. Tóm tắt bằng model cho tầng công khai được để sẵn như cờ tính năng tắt (mục 22; Báo cáo 2) để bật sau mà không sửa core.

### 24.5 OCR và trích xuất hoàn toàn cục bộ

Toàn bộ S0–S10 (mục 5) chạy cục bộ khi chạy thật. Hệ quả cần chấp nhận:

- **Không có VLM làm trọng tài** khi chạy thật. Độ tin cậy dựa vào text layer, nhiều engine OCR cục bộ, đẳng thức kế toán và duyệt tay. Với bản scan xấu, tỉ lệ ô vào hàng đợi duyệt có thể cao hơn; mục tiêu cuối vẫn là ô sai không gắn cờ ≤ 0,1%, đạt bằng gắn cờ nhiều hơn chứ không bằng đoán.

- **Phase 1 dài hơn** vì phải chọn engine cục bộ và huấn luyện các thành phần nhỏ (mục 15). Các mục tiêu độ chính xác OCR ở mục 2.1 giữ nguyên làm đích, nhưng chỉ được xác nhận sau khi benchmark ở Phase 1.

- **Dùng API lớn trong giai đoạn phát triển:** chỉ trên tài liệu công khai, để sinh nhãn bạc (VLM làm “giáo viên”), so sánh và tìm lỗi. Nhãn bạc phải qua đẳng thức kế toán và được duyệt mẫu; không thay thế đáp án vàng.

- **Tài nguyên tính toán:** OCR cục bộ và huấn luyện phụ thuộc cấu hình máy (CPU hay GPU); kế hoạch tài nguyên ở mục 12.6.

### 24.6 Nhà cung cấp, ẩn danh và chi phí

- **Groq và Google AI Studio gói miễn phí** là chính; **OpenAI và DeepSeek** trả phí làm dự phòng, mặc định tắt (mục 12.5). Vì chỉ gửi câu hỏi ngắn và kết quả ngắn, mức tiêu hao token thấp và hạn mức miễn phí khả thi hơn nhiều so với hướng đọc trang bằng VLM; vẫn phải đo thực tế ở Phase 0.

- Điều khoản của gói miễn phí có thể cho phép nhà cung cấp dùng nội dung để cải thiện sản phẩm và thay đổi theo thời gian: phải đọc điều khoản hiện hành, và coi mọi thứ gửi lên gói miễn phí như có thể bị lưu giữ. Đây là lý do bắt buộc ẩn danh và chỉ gửi kết quả cuối.

- **Giới hạn của ẩn danh:** số liệu đặc trưng vẫn có thể giúp suy ra doanh nghiệp. Với tenant nhạy cảm, bật chế độ khuôn mẫu (không gọi API).

<!-- Page 54 of 58 -->

### 24.7 Dữ liệu huấn luyện

- **Chỉ dùng báo cáo đã công bố** từ nguồn chính thống (sàn giao dịch, website doanh nghiệp, cơ quan quản lý); cần lập danh sách nguồn và kiểm tra điều khoản sử dụng. Tài liệu doanh nghiệp chưa niêm yết và doanh nghiệp nhỏ và vừa **hiện không dùng để huấn luyện**; chỉ xét lại khi sản phẩm hoàn thiện, với đồng ý bằng văn bản và ẩn danh.

- **Huấn luyện gì:** vì phần xử lý tài liệu chạy cục bộ nên huấn luyện là phần quan trọng: mô hình layout và bảng, bộ phân loại trang, ánh xạ nhãn sang mã số, bộ hiệu chỉnh độ tin cậy, bộ nhận diện ý định dự phòng cục bộ, và sau này bộ tự phân loại ngành. Tinh chỉnh chính model lớn không nằm trong kế hoạch.

- **Khoảng trống cần chấp nhận:** kho công khai thiếu kiểu tài liệu của doanh nghiệp nhỏ và vừa (Excel, ảnh chụp, mẫu khác). Giảm thiểu bằng dữ liệu tổng hợp (dựng báo cáo công khai thành bản scan nhiễu, ảnh chụp, Excel xuất) và pilot trong từng tenant khi khách đồng ý, kết quả không đưa vào kho chung. KPI cho nhóm này chỉ được xác nhận ở pilot.

### 24.8 Phạm vi chỉ số và ngành hiện tại

Giai đoạn lõi dùng **15 chỉ số và Piotroski F-Score cho mọi doanh nghiệp, chưa phân ngành**. Applicability Gate vẫn chạy (NOT_MEANINGFUL, N/A) và nhận diện tổ chức tín dụng để cảnh báo “không áp dụng” thay vì tính ra những con số vô nghĩa. Sector Pack và multi-agent theo ngành làm sau khi lõi hoàn thành (mục 22).

## Phụ lục A. Ca vàng đầu tiên: BCTC riêng quý 1/2026 của FPT

Các số dưới đây tính tay từ số liệu trong file (đơn vị tỷ đồng, làm tròn), dùng làm **đáp án kiểm thử** cho Ratio Kernel và làm ví dụ về việc cổng áp dụng hoạt động. Giá trị theo *kỳ quý*, chưa quy năm.

| # | Chỉ số | Giá trị | Nhận xét của hệ thống |
| --- | --- | --- | --- |
| 1 | Current Ratio | 1,41 (10.626 ÷ 7.545) | Hợp lệ |
| 2 | Quick Ratio | 1,41 | Hợp lệ (tồn kho không đáng kể) |
| 3 | Cash Ratio | 0,30 (2.231 ÷ 7.545) | Hợp lệ theo định nghĩa file; nếu cộng cả tiền gửi có kỳ hạn (6.359 tỷ) thì 1,14, hai con số khác nhau nên phải nêu rõ chính sách |
| 4 | Debt Ratio | 0,235 | Hợp lệ |
| 5 | D/E | 0,306 | Hợp lệ |

<!-- Page 55 of 58 -->

| # | Chỉ số | Giá trị | Nhận xét của hệ thống |
| --- | --- | --- | --- |
| 6 | Interest Coverage | 19,5 (EBIT ≈ 1.937 ÷ lãi vay ≈ 99) | Tính được nhưng EBIT chủ yếu từ cổ tức công ty con: cờ cảnh báo |
| 7 | Vòng quay hàng tồn kho | — | N/A: doanh nghiệp dịch vụ, tồn kho chỉ 0,8 tỷ |
| 8 | Vòng quay khoản phải thu (phải thu khách hàng) | ≈ 1,01 lần/quý | NOT_MEANINGFUL: doanh thu là phí quản lý nội bộ tập đoàn |
| 9 | Vòng quay tổng tài sản | ≈ 0,005 lần/quý | NOT_MEANINGFUL |
| 10 | Biên lợi nhuận gộp | 80,3% (quý 1/2025: 82,5%) | Hợp lệ nhưng là biên của dịch vụ nội bộ |
| 11 | Biên lợi nhuận ròng | ≈ 1.089% | NOT_MEANINGFUL: lợi nhuận 1.828 tỷ trên doanh thu 168 tỷ do cổ tức |
| 12 | ROA | 5,53% theo quý | Không so ngưỡng của file khi chưa quy năm; cờ phụ thuộc cổ tức |
| 13 | ROE | 7,22% theo quý | Như trên |
| 14 | OCF / Nợ ngắn hạn | −0,053 | Dòng tiền HĐKD âm 402 tỷ; lưu ý cổ tức nhận về ghi ở dòng tiền đầu tư, nên báo cáo riêng của holding có xu hướng cho OCF âm |
| 15 | OCF / Tổng tài sản | −1,22% | Như trên |

**Piotroski cho cùng tài liệu (chế độ cùng quý năm trước):** chỉ có đủ dữ liệu cho F1 (đạt), F2 (không đạt, CFO âm), F4 (không đạt, CFO nhỏ hơn lợi nhuận), F7 (đạt, vốn góp không đổi trong quý), F8 (không đạt, biên gộp giảm từ 82,5% xuống 80,3%). F3, F5, F6, F9 cần bảng cân đối ngày 31/03/2025 hoặc tương đương nên là UNAVAILABLE. Kết quả hiển thị đúng: **điểm hiện có 2, 4 thành phần chưa đủ dữ liệu, khoảng khả dĩ 2 đến 6, chưa đủ để gán nhãn**. Nếu cho phép so với ngày 31/12/2025 (chế độ liền kề, nêu rõ không phải năm trước) thì F6 không đạt vì Current Ratio giảm từ 1,47 xuống 1,41.

**Ca kiểm thử bẫy rút ra từ tài liệu:** (a) hỏi số liệu hợp nhất, kỳ trả lời đúng là ABSTAIN; (b) hỏi vòng quay hàng tồn kho, kỳ vọng N/A; (c) đọc nhầm một chữ số của mã 280 thì đẳng thức 280 = 440 phải phát hiện; (d) số cổ phiếu ngày 31/12/2025 không khớp vốn góp, kỳ vọng cờ bất nhất nguồn thay vì tự sửa.

<!-- Page 56 of 58 -->

## Phụ lục B. Ánh xạ mã số theo mẫu biểu của tài liệu mẫu

Chỉ liệt kê các mã chính. Bộ ánh xạ thực tế phải được **gắn với phiên bản mẫu biểu**: một số mã trong file (ví dụ vay và nợ thuê tài chính ngắn hạn ở mã 321, dự phòng phải trả ngắn hạn ở mã 322) có vẻ lệch một mã so với mẫu cũ thường gặp, nên không được hard-code theo trí nhớ mà phải xác minh khi dựng kho phiên bản mẫu biểu.

| Báo cáo | Mã chính |
| --- | --- |
| B01 Tài sản | 100 Tài sản ngắn hạn (110 Tiền và tương đương tiền, 120 Đầu tư tài chính ngắn hạn, 130 Phải thu ngắn hạn gồm 131 phải thu khách hàng, 132 trả trước cho người bán, 135 phải thu khác, 136 dự phòng; 140 Hàng tồn kho; 160 Tài sản ngắn hạn khác); 200 Tài sản dài hạn (210 phải thu dài hạn, 220 tài sản cố định gồm 221 hữu hình và 227 vô hình, 250 xây dựng cơ bản dở dang, 260 đầu tư tài chính dài hạn gồm 261 công ty con, 262 liên doanh liên kết, 263 góp vốn đơn vị khác, 264 dự phòng, 265 đầu tư nắm giữ đến ngày đáo hạn; 270 tài sản dài hạn khác); 280 Tổng tài sản |
| B01 Nguồn vốn | 300 Nợ phải trả (310 nợ ngắn hạn gồm 311 phải trả người bán, 314 thuế phải nộp, 316 chi phí phải trả, 320 phải trả ngắn hạn khác, 321 vay và nợ thuê tài chính ngắn hạn; 330 nợ dài hạn); 400 Vốn chủ sở hữu (411 vốn góp, 412 thặng dư vốn, 420 lợi nhuận sau thuế chưa phân phối gồm 420a đầu kỳ và 420b kỳ này); 440 Tổng nguồn vốn |
| B02 | 01 Doanh thu bán hàng và cung cấp dịch vụ; 02 Các khoản giảm trừ; 10 Doanh thu thuần; 11 Giá vốn; 20 Lợi nhuận gộp; 22 Doanh thu hoạt động tài chính; 23 Chi phí tài chính (24 Trong đó chi phí đi vay: mục ghi nhớ, không cộng); 25 Chi phí bán hàng; 26 Chi phí quản lý doanh nghiệp; 30 Lợi nhuận thuần từ HĐKD; 31 Thu nhập khác; 32 Chi phí khác; 40 Lợi nhuận khác; 50 Tổng lợi nhuận kế toán trước thuế; 51 Thuế TNDN hiện hành; 52 Thuế TNDN hoãn lại; 60 Lợi nhuận sau thuế |

<!-- Page 57 of 58 -->

| Báo cáo | Mã chính |
| --- | --- |
| B03 | 01 Lợi nhuận trước thuế; 02 Khấu hao; 03 Các khoản dự phòng; 04 Chênh lệch tỷ giá chưa thực hiện; 05 Lãi/lỗ từ đầu tư; 06 Chi phí đi vay; 08 Lợi nhuận trước thay đổi vốn lưu động; 09–12 thay đổi vốn lưu động; 14 Chi phí đi vay đã trả; 17 Tiền chi khác cho HĐKD; 20 Lưu chuyển tiền thuần từ HĐKD; 21–27 các dòng đầu tư; 30 từ HĐ đầu tư; 33, 34, 36 các dòng tài chính; 40 từ HĐ tài chính; 50 Lưu chuyển thuần trong kỳ; 60 Tiền đầu kỳ; 61 Ảnh hưởng tỷ giá; 70 Tiền cuối kỳ |

*Kết thúc báo cáo tiền dự án. Bước tiếp theo đề xuất: bắt đầu Phase 0 (mục 15); hướng phát triển sau core nằm ở Báo cáo 2.*

<!-- Page 58 of 58 -->
