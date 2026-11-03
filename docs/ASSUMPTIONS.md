# Giả định, xung đột và lựa chọn an toàn — Bước 0

Cập nhật02/11/2026. Nguồn: Báo cáo chính v2.0, Báo cáo2, CLAUDE.md, chỉ số/PDF và toàn bộ [LLM_GATEWAY_DESIGN.md](LLM_GATEWAY_DESIGN.md), kể cả mục20. **Bước0 đã được duyệt cùng điều chỉnh02/11/2026**; xem trạng thái từng A-ID. Duyệt cơ sở không phải duyệt tham số chưa đo, frozen schemas hoặc corpus-run Assessment.

Khi viết mã sau này, chỗ còn mở mang `TODO(verify): Axx`; kết quả ghi `assumption_ids` và phiên bản policy. Không dùng TODO để bỏ kiểm tra hoặc cho qua cổng. Trạng thái VERIFIED ở tài liệu này chỉ nói bằng chứng đã đọc; không phải trạng thái Statement của sản phẩm.

## 0. Quyết định Gateway đã duyệt, không phải giả định

| ID | Quyết định ngày02/11/2026 |
| --- | --- |
| D-GW-1 | Composer mù giá trị: chỉ claim_id, nhãn khái niệm, status, band cục bộ, quan hệ định tính, warning codes, mã kỳ/scope; không financial values |
| D-GW-2 | AnswerDraft gồm prose/claim_ref/warning_ref/entity_ref; prose cấm chữ số và tên, renderer cục bộ chèn số/cảnh báo nguyên văn |
| D-GW-3 | Che số tài chính user gõ trước khi gửi; verify_user_claim chỉ tham chiếu placeholder, giá trị đọc cục bộ |
| D-GW-4 | Clarification enum ENTITY/PERIOD/SCOPE/RATIO/AMBIGUOUS_REQUEST; câu hỏi từ local template |
| D-GW-5 | Token random mỗi run; tenant-stable chỉ khi admin chấp nhận |
| D-GW-6 | Không streaming, không hedging |
| D-GW-7 | Thay data_use bằng training_use=none_verified/may_use/unknown và retention=none_verified/limited(days)/indefinite/unknown; unknown xấu nhất. Private chỉ training_use=none_verified và verified retention≤tenant private.max_retention_days |
| D-GW-8 | Quota công bằng theo tenant; khóa runtime tách khóa phát triển |

Những đoạn nguồn cũ mâu thuẫn được thay thế trong hồ sơ dẫn xuất, không sửa tệp thiết kế gốc. Không triển khai ngoại lệ with_values. Không coi model/provider miễn phí là bằng chứng về training/retention. Mục20 là nguồn thứ cấp đọc01/11/2026, không chép số quota/điều khoản từ đó vào registry/hồ sơ; P0.10 phải xác minh nguồn chính thức + tài khoản thật + terms và checked_at. Các phần live chưa có quyền/keys ghi NOT_RUN.

## 1. Nguồn, mẫu biểu, OCR

| ID | Nguồn / điểm chưa rõ | Lựa chọn an toàn dự kiến | Xác minh / mốc |
| --- | --- | --- | --- |
| A01 | Tên tệp trong CLAUDE/yêu cầu khác tên thực tế | Dẫn tệp tiếng Việt hiện có và PDF trong `data/public_reports`; không tạo bản sao/đổi nguồn | VERIFIED đường dẫn/hash; manifest corpus Phase0 giữ tên thật |
| A02 | Chưa có repo Git/mã/test; không có lệnh build hiện hữu | Bước0 chỉ docs; Phase0 mới scaffold và định nghĩa lệnh, không báo test đã chạy | VERIFIED cây workspace; khởi tạo repo local khi triển khai, không publish |
| A03 | §2.2/PLB không cung cấp đủ mã theo thông tư/phiên bản, mẫu FPT khác mẫu cũ | Registry khóa `(family, template_id, template_version, statement_type, code)`; mapping FPT theo PDF/hash, không giả nhận là mọi TT200; mẫu không biết → review/ABSTAIN | PARTIALLY VERIFIED mã321/322/22/24; Phase0 lập catalog từ nguồn chính thống hiện hành |
| A04 | B02 §7 nói “dòng21,24 thì theo mẫu đầy đủ” trong khi PLB dùng22/24 memo | Mỗi template khai báo chính xác danh mục toán hạng và dấu; không cộng24 lần nữa; template khác không dùng lại phương trình theo trí nhớ | VERIFIED PDF6; Phase0/2 test template riêng |
| A05 | “Hỗ trợ VAS/SME/song ngữ” rộng hơn số mẫu sẵn có; Báo cáo2 hoãn SME mở rộng | Core corporate + generic có tiếng Việt/Anh, nhận format SME nhưng chặn normalization khi thiếu template đã duyệt; chưa làm pack/IFRS/ngân hàng | Phase0 ghi ma trận supported/unsupported; không tuyên bố full template coverage |
| A06 | §5.3 viết “bất đồng thuận nhiều engine” đứng trên một engine, trái §5.4 D | Hiểu là lỗi diễn đạt; bất đồng luôn D, không ưu tiên majority để che xung đột. A chỉ sau kiểm format/layout và không có BLOCK liên quan | CONFLICTING; kiểm thử ở Phase1/2 |
| A07 | S4 nói ≥2 lượt độc lập; native sạch chỉ cần text layer theo A | Native sạch dùng parser/native đối chiếu layout; ô từ OCR phải ≥2 engine/đường đọc độc lập, rerun cùng engine không gọi là đồng thuận độc lập | Phase1 benchmark và corpus card |
| A08 | A chỉ cần một đẳng thức, nhưng đẳng thức có thể cùng sai hoặc triệt tiêu | A là hạng bằng chứng, không chứng minh đúng tuyệt đối; mọi rule áp dụng vẫn chạy; bất đồng/BLOCK hạ xuống D; đo lỗi không cờ độc lập bằng gold | Phase1/2 test lỗi bù trừ và chữ số hoán vị |
| A09 | Ngưỡng triage/native sạch và confidence chưa định lượng | Không đặt ngưỡng “đã hiệu chỉnh” giả; native chất lượng không rõ → OCR/review. Đề xuất ngưỡng chỉ đóng băng trên dev sau benchmark | Phase1 không dùng FPT test để tune |
| A10 | S9 “nghiệm duy nhất” chưa quy định phạm vi tìm kiếm | Chỉ ứng viên thật từ đúng ô, cùng unit/period; mọi BLOCK liên quan đạt; nhiều/không nghiệm →review. Không sinh ứng viên bằng phép trừ tổng hoặc sửa source inconsistency | Phase2 property/ambiguity tests |

## 2. Canonical và validation

| ID | Nguồn / điểm chưa rõ | Lựa chọn an toàn dự kiến | Xác minh / mốc |
| --- | --- | --- | --- |
| A11 | §6 LineItem có một value nhưng bảng nhiều kỳ/cột/đại lượng | Một LineItem là một observation cho một period/measure; giữ bảng, ô, column role. Amount VND integer, ratio Decimal, count integer, percent Decimal; không ép cổ phiếu thành VND | Phase0 schema/contract; Phase2 lưu thực |
| A12 | §6 “cấm trộn stock/flow” nhưng ratio cần cả hai | Cấm hoán đổi ý nghĩa thời gian; cho phép join tường minh flow[t0,t1] với stock cuối hoặc bình quân đầu/cuối đúng t0/t1 theo RatioDefinition | Phase0 time schema, Phase3 mutation tests |
| A13 | Q1=YTD; các quý sau không có quy tắc tách YTD | Giữ hai provenance cùng fact tương đương nếu cùng khoảng và khớp; không cộng đôi. Q2=YTD6m−Q1 chỉ khi đúng scope/version và có đủ dữ liệu, tạo derived fact có lineage; không giả số đầu kỳ | Phase2/3 |
| A14 | Restatement có nhiều version, chọn bản nào chưa rõ | Bản mới không ghi đè; selector cố định revision trong snapshot/run. Khác nguồn chưa xác nhận điều chỉnh →CONFLICTING_SOURCES, không tự dùng latest | Phase2; review có optimistic concurrency |
| A15 | §7 thiếu giá trị cụ thể “chênh lớn/nhỏ có lý giải” | Exact VND tolerance0; rounded±1 display unit theo rule. Sai khác exact cùng nghĩa →BLOCK; chỉ WARN khi có bridge phân loại/rounding evidence đã duyệt, không đặt % dung sai toàn cục | Phase2, không cần hỏi lại tolerance0 vốn đã quy định |
| A16 | VERIFIED/PARTIAL chưa định nghĩa rule thiếu đầu vào | Rule có PASS/FAIL/NOT_EVALUATED/NOT_APPLICABLE. Thiếu essential/core identity →PARTIAL hoặc REJECTED theo nguyên nhân; không gọi missing=PASS. Chỉ snapshot phần độc lập có provenance được phục vụ | Phase2; không đưa REJECTED vào canonical analysis |
| A17 | Ô được duyệt tay nâng hạng như thế nào | Giữ OCR gốc; correction tạo revision mới, reviewer/ảnh/lý do. Xác nhận nhìn đúng nguồn khác với phán quyết nguồn đúng. Gắn `human_verified` cùng kiểm rule, không xóa source flag | Phase2 Review API/CLI |
| A18 | Tax rate hợp lệ, revenue/assets không âm có ngoại lệ chưa liệt kê | Chỉ WARN có điều kiện và nguồn; không hard-code thuế20% làm kiểm tuân thủ pháp luật; không ép dự phòng/hao mòn hoặc net financial cost sang dương | Phase0 template/rule catalog; Phase2 |

## 3. Công thức, applicability và chấm điểm

| ID | Nguồn / điểm chưa rõ | Lựa chọn an toàn dự kiến | Xác minh / mốc |
| --- | --- | --- | --- |
| A19 | Precision, làm tròn và số tài chính lớn chưa chốt | VND integer/SQL NUMERIC không float; ratio Decimal precision38, ROUND_HALF_UP chỉ khi hiển thị; API decimal string. So sánh/chấm điểm bằng giá trị chưa làm tròn | Đề xuất Phase0; test boundary/serialization Phase3 |
| A20 | “Gần0”, tồn kho “không đáng kể”, “holding chủ yếu cổ tức” chưa có ngưỡng | **ĐÃ DUYỆT cơ sở02/11/2026**. Denominator≤0 →N/A. Với denominator dương không tự gọi gần0 nếu chưa có rule. Cơ sở inventory/tài sản<0,1% **và** bằng chứng dịch vụ; holding cần riêng + bằng chứng phí nội bộ/đầu tư + cổ tức chiếm>50% LNTT dương; mọi điều kiện versioned/evidence-linked, không nhánh tên FPT | Chỉ tinh chỉnh trên dev, không FPT Phase0/3; thiếu bằng chứng không khẳng định loại hình |
| A21 | “Quy năm” §9.1/9.2 chưa cho phép nhân/chọn ngày rõ ràng | **ĐÃ DUYỆT cơ sở02/11/2026**. Mặc định kỳ thực, không áp ngưỡng năm cho flow/stock. Biến thể annualized tách ID/basis: quý×4,6tháng×2,YTD×12/số tháng khi đủ tháng tài chính; không quy năm margins/ICR/stock ratios; TTM chỉ đủ bốn quý không chồng | Đã duyệt Phase0; luôn cảnh báo mùa vụ |
| A22 | §9.2 cho cuối kỳ khi thiếu bình quân; zero131 ở§20.2 chưa nói hai mốc | Nếu131 cuối kỳ explicit0 thì N/A đúng§20; nếu thiếu131 thực sự mới fallback130 cho cả basis tương thích. Thiếu đầu kỳ →biến thể closing CAVEATS, không tráo thành average. Input C chưa đủ chuẩn tính ratio mặc định, useful chỉ hiện raw chưa xác minh; không chấm | Phase3; test zero/missing/C riêng |
| A23 | ROA/ROE cuối kỳ và bình quân; consolidated parent equity/LNST mã nào | Chính closing như ca vàng; average riêng. Consolidated ROE dùng parent profit/parent equity cùng quyền lợi; thiếu chi tiết thì N/A thay vì NI toàn tập đoàn /equity công ty mẹ. Không thay mã400 trong mọi mẫu bằng parent equity ngầm | Phase0 template/Phase3 |
| A24 | Nợ vay gồm lease/bond có thể cộng trùng; thiếu dòng dài hạn | Dùng tập canonical components không giao nhau theo template. Missing không=0; chỉ suy zero có công thức/provenance từ bảng hoàn chỉnh được đối chiếu, gọi `derived_zero`, không `explicit_zero` | Phase2/3; FPT330 đã đủ337+338 nên không suy mọi330 là vay |
| A25 | Ngưỡng chồng/hở | ĐÃ DUYỆT generic v0: UNCLASSIFIED và không chấm; không ưu tiên risk cutoff để lấp overlap/gap. Giữ source/boundaries/inclusive flags | POLICY_UNAPPROVED tới khi chủ dự án duyệt kết quả chạy trên kho |
| A26 | Mapping/weights/grade/caps | ĐÃ DUYỆT generic v0 làm cơ sở: tốt100/trung bình50/yếu0;5trụ đều20%, ratios trong trụ đều;grade≥75 tốt/≥50 trung bình. Equity âm cap yếu;OCF kỳ âm và ICR<1,5 cap trung bình;chưa VERIFIED/thiếu coverage không grade; kéo dài chỉ khi Trend đủ kỳ | Disclaimer bắt buộc: quy ước theo file chỉ số, chưa phải mô hình kiểm chứng hoặc khuyến nghị đầu tư. Giữ POLICY_UNAPPROVED tới corpus run được chủ dự án duyệt |
| A27 | Piotroski/Trend modifiers | ĐÃ DUYỆT trọng số hai thành phần đều0 cho tới khi chủ dự án duyệt lại; vẫn compute/hiển thị đầy đủ availability/basis | Không tự bật khi đổi pack/model hoặc đủ dữ liệu |
| A28 | Coverage/OCF14 | Giữ ceil(2n/3) trong trụ sau N/A loại và≥3trụ mới tổng;NOT_MEANINGFUL/C/UNCLASSIFIED không chấm, giảm coverage. ĐÃ DUYỆT OCF14 hiển thị liquidity/cashflow nhưng chỉ score một lần ở cashflow, loại khỏi scoring membership liquidity; công bố rõ tác động | Báo absolute15/pack-adjusted coverage, không double count; POLICY_UNAPPROVED tới corpus run được duyệt |
| A29 | Piotroski§9.3 ≥7 nhãn, §19 strict9; basis ROA/F5/band nhãn chưa đủ | Ưu tiên mode-specific: strict9/useful≥7; annual default, same_quarter_yoy/TTM explicit. Đề xuất F1/F3 opening-assets basis, F5 average-assets/long-term debt330 theo định nghĩa; thiếu mốc phù hợp →UNAVAILABLE. Không đặt nhãn mạnh/yếu nếu chưa duyệt band | Phase0 định nghĩa từng F, Phase3 tests; không suy quý trước là cùng quý năm trước |
| A30 | F7 FPT pass trong PL A nhưng bảng cổ phiếu tăng do sai cột nguồn | F7 vốn góp theo roll-forward TM14 PDF23 không phát hành trong quý →1, basis=`contributed_capital_rollforward`; đồng thời warn bảng cổ phiếu PDF24 mâu thuẫn, không dùng bảng này để chứng minh F7. Nếu không có roll-forward đáng tin →UNAVAILABLE | VERIFIED căn cứ PDF, test F7=1 **và** warning còn nguyên |

## 4. Gate, Agent và đầu ra

| ID | Nguồn / điểm chưa rõ | Lựa chọn an toàn dự kiến | Xác minh / mốc |
| --- | --- | --- | --- |
| A31 | Kiểm numeric membership chưa đủ binding, và composer cũ nhận final values | **Phần egress đã được D-GW-1/2 thay thế:** AnswerSet/value/unit/evidence chỉ local, outbound chỉ value-blind descriptors. OutputValidator kiểm typed draft/required refs trước renderer; Verifier kiểm output sau render theo value+unit+entity+kỳ/scope/variant/evidence | Phase4; chi tiết manifest/prose guard bổ sung A53, không phát bytes trước receipt |
| A32 | Sơ đồ§4 đặt Verifier trước Composer; SSE có thể rò nội dung | **D-GW-2/6 thay thế đường soạn/stream:** Gate → OutputValidator sau composer → local renderer/identity restore → Verifier; không streaming/hedging. A60 đề xuất SSE chỉ progress/result_ref, không còn các đoạn answer đã verified như bản cũ | Phase4/5; export strict tái kiểm, mọi sink cần receipt |
| A33 | Gate chưa có trọng số, top-k, recency, mức risk Q cụ thể | Essential coverage1, period/scope exact là hard predicates; useful thiếu phụ mới caveat. Khởi điểm retrieval strict k5/useful k10, nguồn tin TTL90ngày chỉ là proposal theo connector; strict kiểm mọi claim local, useful cũng kiểm mọi claim ở core | Phase4 hiệu chỉnh dev; source date missing/stale rõ, không giả confidence xác suất |
| A34 | Số bước/token/timeouts/retry budget chưa có | Đề xuất max8 tool calls/run,2 lần/tool,deadline15s tương tác,2 retries transient trong deadline,1 compose retry rồi template; trả trace lý do hết budget. Tác vụ batch deadline riêng | Phase0 cấu hình; Phase5/6 hiệu chỉnh bằng số đo |
| A35 | Hội thoại đổi context, một câu hỏi làm rõ nhưng schema/context outbound chưa kín | D-GW-3/4/5: enum clarification, local template một câu gộp; context version/ACL, che số/retokenize mỗi run, chỉ user history sạch. Không assistant answers/tool results, không tin số user như fact hoặc tự chọn latest | Phase5 T14/T28; giới hạn history còn proposal A54 |
| A36 | §11 optional và§23 “backend hoàn chỉnh”/Excel có khác phạm vi | Core có tất cả Must-have và module§23, Excel export tối thiểu có formula/provenance; không thêm DSO/DuPont/Altman/peer benchmark/UI/cảnh báo theo lịch. Related-party chỉ flags và evidence cần cho ca vàng | Phase5/6, scope traceability trong PLAN |

## 5. Vận hành, tài nguyên, dữ liệu, privacy, mở rộng

| ID | Nguồn / điểm chưa rõ | Lựa chọn an toàn dự kiến | Xác minh / mốc |
| --- | --- | --- | --- |
| A37 | CSDL/index/blob/worker được nêu nhiều lựa chọn | **ĐÃ DUYỆT cơ sở02/11/2026**. Cơ sở PostgreSQL+pgvector, BM25 cục bộ trong retrieval adapter, đĩa local blob dev; memory/Redis qua cùng protocol, không thêm OpenSearch/Qdrant/Celery mặc định. Phiên bản package pin sau xác minh Phase0, không cài ở Bước0 | Đã duyệt dependencies dự án; không cài global |
| A38 | Limit file/page/URL, macro scanner optional chưa số | **ĐÃ DUYỆT cơ sở02/11/2026**. Cơ sở50MiB/300trang,20MiB URL body,3redirects,15s fetch,archive expansion ratio100 và200MiB; chặn active content/macros, XML external entities. Scanner chưa có phải hiện trạng thái; policy yêu cầu scanner thì fail-closed | Phase0 config, Phase1/5 security/load; đây là limit dự thảo |
| A39 | Events/retry/idempotency/tenant đồng tài liệu chưa đủ giao thức | SSE event_id+sequence+replay cursor; at-least-once, consumer dedupe. Hash khóa theo tenant+pipeline, không lộ dedup cross-tenant; stage atomic và retry-safe. Review409 khi revision thay đổi | Phase0/2/5 |
| A40 | Corpus | Chủ dự án cung cấp≥30 public reports có manifest nguồn/ngày/điều khoản/hash,≥10 gold approved ở Phase0; gold còn lại Phase1–2;Phase6≥100 gold. Chỉ thu thập thêm theo danh sách cho phép bằng văn bản | Hiện1 PDF, chưa đủ corpus/gold approved. Không copy/synthetic/silver để đạt chỉ tiêu; thiếu→INCOMPLETE |
| A41 | KPI N100% so OCR lỗi không cờ≤0,1%; Q thresholds ghi “đề xuất”; coverage chưa có mẫu số cụ thể | Hai mẫu số khác: cell extraction≤0,1%, answer N=0 sai không cờ (cứng). Giữ Q99/95 và false-abstain15/5/coverage90 làm target. Coverage dùng cohort in-domain đóng băng, báo thêm answerable-only; không đổi cơ cấu câu hỏi sau đo. Đo trước/sau review riêng | Phase1/2/4/6; chốt cohort trước calibration |
| A42 | FPT đã biết đáp án; chia dataset/CI/CI confidence sample chưa số | FPT là visible golden regression; test tổng quát giữ doanh nghiệp khác. Official eval chỉ gold approved, holdout entity/group; đề xuất≥300 claims Q/mode,≥100 câu thiếu và≥100 đủ, báo Wilson95% + bootstrap cluster. N ít vẫn báo thật, không xác nhận KPI toàn bộ | Phase0 dataset design; Phase6 evaluation |
| A43 | Keys/model/account evidence | Chủ dự án chưa cấp keys; không gọi provider. P0.10 đọc official docs/terms ghi checked_at; live/account limits/terms account-specific NOT_RUN tới khi có keys/quyền. Quota sources manual_console/probe/header_hint; không lấy§20 làm registry evidence, routes do số đo | Runtime/dev keys tách; eligibility training_use/retention theo D-GW-7. Public docs không chứng minh account terms/quota |
| A44 | Query guard cũ chỉ che tên và đoạn report, composer có final values | **Được D-GW-1/3/5 thay thế:** che mọi số tài chính user gõ thành local placeholders, verify_user_claim local lookup; token random mỗi run. Không chắc sạch →local; composer không nhận final values/tables/notes/provenance/name, không with_values | Phase0 contracts, Phase4/5 canary số user/composer/history; A53 chi tiết guard |
| A45 | Public dựa ticker/niêm yết có thể gán nhầm, cache public dùng chung được | Ticker riêng không chứng minh công bố chính thống; default private, chỉ public khi có evidence/được admin xác nhận. Cache ban đầu tenant-separated cả public; không hạ privacy theo nguồn yếu; tier merge max | Phase0/5 |
| A46 | Retention/xóa/mã hóa/webhook/trace payload chưa chi tiết | **ĐÃ DUYỆT cơ sở02/11/2026**. Retention configurable; cơ sở private30ngày cho artifacts vận hành, purge cả derivative/index/cache, backup expiry phải có runbook. TLS+storage encryption bắt buộc deployment profile; chưa cấu hình →readinessfail. Logs không full prompts/answers/secrets; audit chỉ hash/refs và secure local access. Webhook opt-in chỉid/status, ACL+SSRF, không dùng Codex hook | Phase0 policy và Phase5/6 implementation; không gọi production ready khi còn thiếu |
| A47 | EP11/D9 bật cờ gửi snippet trái§24; Gateway cũ chứa local/dev capability | Runtime Gateway chỉ external intent/compose; local inference qua LocalModelPort, dev teacher tách factory/imports/keys/budget. Image/PDF/embedding không thuộc Gateway runtime. Flags chưa triển khai bị từ chối, không bypass egress; không ship local VLM/multi-agent mới trong core | Phase0/5 contracts và runtime import/key tests; mở rộng cần yêu cầu riêng |
| A48 | “Không sửa core” quá mạnh nếu phép toán/type/message tương lai khác | Dựng đủ12 EP dùng thật, DSL số học/avg/aggregation có điều kiện trên facts typed, role messages evidence_refs+trace tree. Không ship supervisor/bank. Chỉ cam kết tương thích trong hợp đồng; trường hợp vượt schema theo Báo cáo2§11 | Phase0/3/5 extension conformance tests |

## 6. Ba bổ sung từ PDF và nghĩa nợ vay

| ID | Nguồn / điểm chưa rõ | Lựa chọn an toàn dự kiến | Xác minh / mốc |
| --- | --- | --- | --- |
| A49 | PDF9 nhãn `70=50+60` nhưng có61 âm150.117; §7 đúng có61 | Rule định nghĩa đầy đủ50+60+61=70; giữ nhãn nguồn và INFO `SOURCE_FORMULA_LABEL_INCOMPLETE`; không sửa số theo nhãn in thiếu | VERIFIED PDF9 và phép cộng; test Phase2 |
| A50 | §7E interest≤finance_cost không đúng FPT:24>23; hồ sơ trước đọc sai mã23 | [Crop PDF6](evidence/fpt_q1_2026/b02-code23-digits.png) xác nhận23=97.623.991.644; [TM18 PDF25](evidence/fpt_q1_2026/note18-finance-costs.png) xác nhận99.309.404.980−1.685.413.336=tổng23. Vẫn WARN heuristic24>23, không BLOCK/hạ trust số đúng; FPT-E13 bắt mutation một chữ số bằng đẳng thức30 | VERIFIED từng chữ số trên crop02/11/2026; lỗi97.623.971.644 của hồ sơ đã sửa, không chỉnh oracle theo kernel |
| A51 | CF04 vàTM18 chênh150.117, trùng trị tuyệt đối CF61 kỳ này; không đủ chứng minh bridge | [CF04](evidence/fpt_q1_2026/cf04-current-prior.png)/[TM18](evidence/fpt_q1_2026/note18-finance-costs.png)/[CF61](evidence/fpt_q1_2026/cf61-current-prior.png): kỳ trước delta35.278.626 khác35.278.716 đúng90đ. Giữ hai concepts và CLASSIFICATION_DIFFERENCE_UNRESOLVED/WARN; không tăng tolerance0/sửa số/đóng issue khi bridge chưa duyệt | VERIFIED số và chênh lệch, UNVERIFIED nguyên nhân/bridge; đính chính170.117 là lỗi đọc hồ sơ, Phase2 giữ WARN |
| A52 | Trái phiếu/lease, trường mở rộng canonical và DSL chưa cho metadata chuẩn | Fact có dimensions typed (counterparty, debt_type, maturity, gross/net), concept registry xác định không trùng; tổng có điều kiện trên facts đã normalize. Unknown debt components chỉ reference N/A; không suy vay dài hạn bằng toàn330 | Phase0 schemas; Phase2 mapping, Phase3 ref ratios |

## 7. Gateway — đã duyệt cơ sở, tham số chờ đo

Các ID này chỉ giải quyết chi tiết còn thiếu; không mở rộng D-GW-1–8 thành quyết định mới và không hạ KPI. Không chốt provider quota/terms/route hoặc tham số tuning chưa đo.

| ID | Điểm chưa đủ / nguồn | Lựa chọn an toàn đề xuất | Trạng thái / xác minh |
| --- | --- | --- | --- |
| A53 | Typed draft phải chống tráo nhãn và ngôn ngữ lách số/tên; phân biệt năm/quý với tiền/count | **ĐÃ DUYỆT cơ sở02/11/2026**. ReferenceManifest value-free có required claims/warnings/status/render slots; local renderer bind atomic claim (label/value/unit/period/scope). Unicode digits/names/numbers-in-words guard, vocabulary hạn chế và template khi chưa chứng minh an toàn. Chỉ typed period rõ mới giữ năm/quý; số mơ hồ →local | Tham số chờ đo P6.04; P0.09/P4.04–05/T05/T26–29/GW01–04. Không tuyên bố regex chứng minh mọi prose |
| A54 | Conversation context | ĐÃ DUYỆT không gửi history mặc định; chỉ query hiện tại guard/mask và SessionSelection giả danh. Không assistant answers/tool results; run-random tokens | P0.05 draft có history rỗng; P5.03/GW05 thực thi; không tự bật N>0 |
| A55 | G7 yêu cầu fairness nhưng chưa định thuật toán/weights/burst | **ĐÃ DUYỆT cơ sở02/11/2026**. Redis atomic reservation cho account/model + tenant allocation; cơ sở fair queue có weights/burst cấu hình, tenant thiếu allocation không được dùng toàn shared bucket. Tham số theo quotas đo thật và tenant policy, chưa tự gán trọng số/hạn mức; local nếu hết deadline | Tham số chờ đo P6.04 thuật toán/tham số; atomicity/account key/fairness là yêu cầu thiết kế đã nhận. P5.01/P6.04/GW07 |
| A56 | Private max_retention_days thiếu config; evidence terms cũ/hết hạn chưa có TTL | **ĐÃ DUYỆT cơ sở02/11/2026**. Thiếu bound hoặc evidence không đủ/hết hạn theo review policy →local; không ngầm đặt ngày lưu hay expiry interval. Terms evidence có checked_at/scope/refs, chỉ nguồn chính thức/account review chứng minh; unknown fail theo D-GW-7 | Tham số chờ đo P6.04 xử lý missing/expiry; không lấy retention artifacts nội bộ A46 làm provider bound. P0.10/GW11 |
| A57 | G13 chưa có định nghĩa chi tiết/chất lượng threshold theo model | **ĐÃ DUYỆT cơ sở02/11/2026**. K19=drafts bị OutputValidator reject / responses đã validate theo model (first/all attempts riêng); K20=provider-routed requests cuối dùng template / requests đã chọn external route, breakdown chain/model/reason, thêm forced-local/all requests. Renderer faults/forced-private tách khỏi provider failures | Tham số chờ đo P6.04 phép đo; **ngưỡng PENDING_APPROVAL sau baseline**, không tự đặt. P5.08/P6.05/GW13, không thay K01–K18 |
| A58 | Token random làm cache cross-run nguy hiểm; worker crash sau upstream accept chưa rõ idempotency | **ĐÃ DUYỆT cơ sở02/11/2026**. Chưa reuse composer draft cross-run khi chưa có safe remapping; trong run journal reservation/outcome và revalidate quyền/terms/refs. Upstream outcome uncertain →không blind resend, local fallback/typed uncertain, không hứa exactly-once provider billing | Tham số chờ đo P6.04; P5.01/P6.04, fault/cache/retokenization tests |
| A59 | Hàng GatewayOutcome ở thiết kế§4 bị cắt sau source=provider | **ĐÃ DUYỆT cơ sở02/11/2026**. Hoàn chỉnh DTO source=provider/local, typed result, degraded, fallback_reason, trace_ref/versions; không raw response/map. Fallback ports inject và giữ nghiệp vụ ở caller | Tham số chờ đo P6.04 schema; P0.05/P5.01 conformance, source file giữ nguyên |
| A60 | SSE | ĐÃ DUYỆT chỉ progress metadata/result_ref; GET nội dung sau verified. Không provider/draft/token/partial-answer streaming hoặc hedging | P5.05/GW10; không hỏi lại |

## 8. A61 đã duyệt và đóng băng theo lệnh freeze

| ID | Khoảng trống | Đề xuất trong draft | Trạng thái |
| --- | --- | --- | --- |
| A61 | Biên schema sau review R1–R7 | R1: ent_/num_ +8 ký tự theo run; UUID128 local. R2: JSON int safe range, số lớn dùng canonical string. R3: trần text riêng. R4: fraction/scale/ROUND_HALF_UP. R5: depth32/nodes1024/width100. Chi tiết bên dưới giữ nguyên trị số đã trình | **ĐÃ DUYỆT bằng chữ freeze ngày02/11/2026**, là biên kỹ thuật schema, không phải ngưỡng tài chính. Nếu chạm dữ liệu thật phải báo/xin duyệt, không cắt hoặc bỏ dữ liệu |

Chi tiết A61 dưới đây đã được chủ dự án duyệt. [SCHEMA_REVIEW_SUMMARY](SCHEMA_REVIEW_SUMMARY.md) giữ hồ sơ lần trình; [manifest frozen](../schemas/frozen/manifest.json) là baseline hiện hành:

- **APPROVED — lexical/token:** Identifier≤160, NonEmpty≤4096 ký tự Unicode. Token dùng alphabet Crockford32 `0123456789abcdefghjkmnpqrstvwxyz`, suffix8 ký tự (40 bit ngẫu nhiên, không phải ID bảo mật), `secrets.choice`; UUID128 local không nằm trong alias. Kiểm full token và suffix với câu hỏi gốc sau NFKC/casefold, kiểm suffix đã cấp trong run cho cả hai loại; va chạm thì bỏ candidate, thử lại tối đa32 lần rồi local-only. Không dùng lại token có va chạm. Không có stable token theo tenant mặc định. Đây mới là allocator cục bộ, chưa phải query guard/anonymizer đầy đủ.
- **APPROVED — trần văn bản riêng:** PageText1.000.000, ChunkText64.000, CitationText64.000, ExportText10.000.000 ký tự Unicode; không tính byte/token model. Page.native_text và SourceCell/Reading.raw_text dùng PageText; EvidenceChunk.text dùng ChunkText; SourceQuote.text dùng CitationText; TextExportContent.content dùng ExportText. Vượt trần báo lỗi để review/chia nội dung ở phase tương ứng, không cắt ngầm. Test cả4097, đúng trần và trần+1. File nhị phân XLSX/blob không phải chuỗi ExportText.
- **R2/R4:** bare JSON int chỉ nhận từ−9.007.199.254.740.991 đến9.007.199.254.740.991; tiền/count lớn hơn cần canonical string, giữ integer nội bộ. Metadata integer cũng có safe bound và giới hạn riêng không bị nới. Không nhận float/bool cho financial values, không exponent text. Ratio wire ví dụ `{"kind":"ratio","value":"0.1250","representation":"fraction","scale":4,"rounding_mode":"ROUND_HALF_UP","display_kind":"percent"}`: scale là số chữ số sau dấu chấm của phân số đã lưu, không phải hệ số nhân100; thiếu scale được suy chính xác, scale khai sai bị chặn. Metadata làm tròn công bố quy ước, DTO không tự làm tròn hay quy năm; kernel/formatter thực thi tại phase tương ứng.
- **APPROVED — AST:** depth≤32 (root=1), tổng≤1024 node occurrences cho một formula; rule chia budget1024 cho cả hai vế, không1024 mỗi vế; aggregate≤100 inputs/node như trước. Đếm cả node lá/lặp, không dedup để né trần; iterative preflight chặn cycle trước Pydantic. Chưa có số đo corpus chứng minh đủ, không lấy FPT để tuning.
- **R6/compat theo chỉ đạo chủ dự án:** SHA256 mỗi validation/serialization snapshot, compat_policy và số ca đúng/sai thực thi theo nhóm. Sau `freeze`: cùng bản chính chỉ thêm DTO/trường tùy chọn; breaking phải nâng bản chính kèm ADR, migration và chạy lại toàn bộ snapshot. Không tự freeze bằng test/generate; chưa tạo ADR/migration trong lần sửa draft này.
- **P0.10:** prompt tổng hợp chép alias và scorer cục bộ đã chuẩn bị; model measurement **NOT_RUN**, không có threshold hoặc kết quả model giả. Chỉ đo khi qua cổng và có keys/quyền; báo exact-case/token-position counts, task/model/version và raw-response evidence an toàn.

## 9. Trạng thái sau phê duyệt Bước0

Chủ dự án đã duyệt Bước0 và các điều chỉnh02/11/2026. A20 chỉ tinh chỉnh trên dev, không FPT; A21 annualized là biến thể phụ riêng; A37 PostgreSQL/pgvector/localBM25, không OpenSearch/Qdrant/Celery; A38 limits đã duyệt cơ sở; A46 private artifacts30ngày, không phải provider retention bound.

Cổng schema P0.05 đã qua bằng lệnh freeze; A61 đã duyệt. Phase0 được làm tiếp P0.06–P0.11, nhưng vẫn INCOMPLETE nếu corpus hoặc kiểm chứng môi trường chưa đủ. Cần xác nhận riêng trước Phase1, corpus-run Assessment và ngưỡng K19/K20. Không hỏi lại quyết định đã trả lời, không tự thu thập thêm corpus.

Không hooks/plugin/MCP/global packages; pre-commit chỉ manual/CI, không install hooks. Không provider calls khi chưa có khóa/quyền. Không chuyển Phase1 chưa có xác nhận; không đổi Git global config hoặc quyền.git.

## 10. Điều kiện freeze do chủ dự án duyệt

| ID | Quyết định áp dụng ngay |
| --- | --- |
| D-SCH-1 |14 nhóm frozen; cùng major chỉ thêm DTO hoặc trường tùy chọn. Enum mà consumer xử lý đầy đủ (error/event/effect/task/status và các finite enum khác) thêm giá trị là breaking, phải nâng version. Chỉ enum khai báo extensible kèm fallback đã kiểm mới được mở rộng cùng major |
| D-SCH-2 | Canonical/1 có cửa sổ sửa breaking qua ADR trước lần lưu canonical thật đầu tiên P2.01; giữ hash trước/sau và diff. Từ first-write áp dụng strict major/ADR/migration/full snapshot policy. Các nhóm khác frozen ngay. [Lifecycle](../schemas/lifecycle/canonical-1.json) hiện chưa có first-write; corpus manifest/nhãn dự thảo không phải canonical persistence |
| D-SCH-3 | Tất cả đường nạp registry từ đĩa/DB phải qua registry.bundle; mọi task loader có inventory, gate tests và kiểm không bypass trước hoàn thành |
| D-SCH-4 | Mỗi lỗi/lỗ hổng sau freeze thêm ca sai vào tests/fixtures/schema_review_cases.json, ghi rõ tầng validator. Archive tại freeze bất biến; current regression cases tăng độc lập |
| D-SCH-5 | A61 approved là biên kỹ thuật. Chạm dữ liệu thật báo/xin duyệt, không truncate/discard |
| D-SCH-6 | Token-copy live NOT_RUN tới khi chủ dự án đặt khóa; không tự đặt ngưỡng |

| A-ID mới | Lựa chọn kỹ thuật / giới hạn | Trạng thái |
| --- | --- | --- |
| A62 | **Danh sách enum extensible hiện tại: rỗng**. Mọi enum/Literal hữu hạn trong14 nhóm đều closed vì chưa có fallback được khai báo và kiểm. Các Identifier refs/catalog keys mở không được coi là enum extensible ngầm | Cách áp dụng fail-closed của D-SCH-1; không thêm giá trị enum trong lượt này |
| A63 | Guard P0.09 dùng từ vựng câu hỏi được cho phép, local entity aliases, selector kỳ/scope tường minh; unknown/document/injection/number format mơ hồ →local-only. Đây là implementation bảo thủ cho Phase0, chưa đo coverage, chưa thay local intent/OutputValidator/Verifier ở Phase4–5 | IMPLEMENTED_OFFLINE; hiệu chỉnh trên dev và đánh giá KPI ở phase tương ứng, không tự hạ target. Corpus/gold/eval DTO mới là additive, chưa thuộc14 nhóm frozen |

## 11. Ngoại lệ Phase1a và A64

**ĐÃ DUYỆT phạm vi ngày03/11/2026:** chỉ P1.01, phần phân loại/render/xoay/deskew của P1.02, S5 của P1.05 và công cụ manifest/crop/operation trace không cần corpus. Phase0 vẫn INCOMPLETE/NO_GO, chưa mở Phase1. Không OCR engine selection/benchmark/training/teacher/KPI/go-no-go1. Kết thúc dừng chờ đủ corpus và xác nhận mới. P0.10 đã đọc official Groq/Google ngày02/11/2026 theo hồ sơ nguồn; không cần khóa để đọc docs, account/live vẫn NOT_RUN.

| ID | Chỗ chưa đủ / lựa chọn an toàn | Trạng thái |
| --- | --- | --- |
| A64 | Giới hạn kỹ thuật Phase1a chưa có calibration: router cần≥80 ký tự body aligned và image fraction<0,2 để đi text; thiếu/native reader unavailable→unknown/OCR-needed, không lấy chữ ký làm body. Archive≤10.000 entries; raster≤100 triệu pixels; deskew candidate±5° bước0,25°, tối đa khoảng100.000 điểm mẫu; không tự quyết hướng180°. Helper render timeout90s mỗi lời gọi, chưa là deadline toàn job. Memory job mặc định3 attempts, lease60s và tối đa3.600s; DNS tối đa8 thao tác OS tồn đọng, caller chờ trong deadline A38. Projection score là tín hiệu hình học chưa calibration, không phải confidence/OCR accuracy | **PROPOSED, IMPLEMENTED_OFFLINE** để kiểm hành vi; không phải ngưỡng tài chính/KPI và không phải phê duyệt tuning. Chưa tinh chỉnh trên FPT/dev. Chạm giới hạn dữ liệu thật báo lỗi/review, không cắt/bỏ hoặc nâng trần ngầm |

Windows.Data.Pdf/System.Drawing là adapter render/hình học có sẵn, không là OCR engine được chọn. Không cài thư viện native PDF/OCR; native extraction NOT_RUN vì không có library. Cần parser/engine adapter ở phần Phase1 chưa được mở. WinRT Page.Size và DestinationWidth là DIP; host LogicalDpi đọc cục bộ, bù kích thước rồi đối chiếu PNG IHDR thực với sai số lượng tử≤ceil(LogicalDpi/96/2) pixel. Transform dùng **kích thước PNG thực**, không gán pixel theo nominal DPI. Space `upright_pdf_dip` đã tính intrinsic rotation của WinRT; native parser tương lai phải chuyển đúng coordinate space, không ghép bbox raw PDF72pt ngầm. Tham khảo chính thức: [PdfPage](https://learn.microsoft.com/en-us/uwp/api/windows.data.pdf.pdfpage?view=winrt-26100), [DestinationWidth](https://learn.microsoft.com/en-us/uwp/api/windows.data.pdf.pdfpagerenderoptions.destinationwidth?view=winrt-26100), [Matrix](https://learn.microsoft.com/en-us/dotnet/api/system.drawing.drawing2d.matrix?view=windowsdesktop-9.0); checked_at03/11/2026.

Profiler chạy tuần tự, không nesting/concurrent tracemalloc: wall/process CPU, Python allocation peak, RSS trước/sau và peak working set của helper nếu có. Đây không phải peak RSS toàn pipeline, CPU của process con, ingest latency25 trang hoặc bất kỳ KPI nào. LocalBlobStore chỉ dev/local disk, không được báo production encryption/purge mọi derivative; memory journal/queue mất khi restart. Scanner hiện UNAVAILABLE; byte scan PDF chỉ heuristic, không thay antivirus hoặc chứng minh PDF an toàn đầy đủ; policy đòi scanner phải fail-closed. Các giới hạn này không hạ tiêu chí production/Phase1.
