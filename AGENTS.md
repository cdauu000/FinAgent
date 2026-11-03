# FinAgent: quy tắc cố định cho mọi phiên làm việc

## Nguồn sự thật
- Đặc tả đầy đủ nằm ở docs/bao-cao-chinh.md (Báo cáo chính v2.0). Hướng phát triển sau core nằm ở docs/bao-cao-2-huong-phat-trien.md. Định nghĩa 15 chỉ số và ngưỡng nằm ở docs/15_financial_ratios.md.
- Khi code và đặc tả mâu thuẫn, đặc tả thắng. Khi đặc tả mơ hồ hoặc thiếu, KHÔNG tự đoán: ghi vào docs/ASSUMPTIONS.md (mục, câu hỏi, lựa chọn an toàn nhất đã chọn) và đánh dấu TODO(verify) trong mã.
- Báo cáo mẫu: samples/FPT_BCTC_rieng_Q1_2026.pdf (báo cáo RIÊNG của công ty mẹ, quý 1/2026). Đáp án tính tay ở Phụ lục A của Báo cáo chính là bộ kiểm thử vàng đầu tiên.

## Bất biến không được vi phạm (kiểm thử phải chứng minh)
1. Mọi con số hiển thị đến từ kho chuẩn hoặc Ratio Kernel. LLM không bao giờ sinh, tính hay chuẩn hóa số.
2. Tài liệu gốc, ảnh trang, văn bản báo cáo KHÔNG BAO GIỜ gửi ra API bên ngoài khi chạy thật. Model API chỉ có hai vị trí: (a) nhận diện ý định và trích xuất tham số từ câu hỏi đã ẩn danh, (b) viết câu trả lời từ kết quả tính toán đã ẩn danh. Ngoại lệ duy nhất: tập lệnh phát triển và huấn luyện trên tài liệu công khai.
3. Fail-closed: thiếu bằng chứng thì ABSTAIN hoặc CAVEATS, không bao giờ đoán. Ba trạng thái: ANSWER, ANSWER_WITH_CAVEATS, ABSTAIN.
4. Không có số sai nào được hiển thị mà không bị gắn cờ. Ô OCR có mức tin cậy A, B, C, D; mức D bị chặn; mức C chỉ hiện kèm nhãn “chưa xác minh” ở chế độ Hữu ích.
5. Sector Pack không đổi giá trị chỉ số. Core chỉ chạy gói chung generic@1 nhưng PHẢI chạy qua giao diện Sector Pack v1 và các điểm mở rộng EP1 đến EP12 (mục 22 của Báo cáo chính).
6. Verifier là cổng cuối bắt buộc: mọi số trong câu trả lời phải thuộc tập đáp số của lượt đó.
7. Mặc định riêng tư (fail-closed): tài liệu không xác định được là công khai thì coi là riêng tư.

## Phạm vi
- LÀM: backend hoàn chỉnh theo Báo cáo chính (Phase 0 đến 6).
- KHÔNG LÀM: giao diện người dùng; Sector Pack theo ngành; multi-agent; chỉ số ngân hàng; bất kỳ hướng nào của Báo cáo 2 ngoài việc dành sẵn điểm mở rộng.

## Công nghệ
Python 3.11+, FastAPI, Pydantic v2, PostgreSQL (dev có thể dùng docker compose), hàng đợi job có hai chế độ in-memory và Redis, pytest, ruff, mypy (strict cho module analytics, validation, store). Khóa API chỉ qua biến môi trường; có .env.example; không commit bí mật. Kiểm thử không được phụ thuộc mạng: mọi nhà cung cấp LLM có bản giả (mock).

## Quy ước
- Mã, tên biến, commit: tiếng Anh. Tài liệu, thông báo cho người dùng: tiếng Việt, có khóa i18n để thêm tiếng Anh.
- Số tiền lưu bằng VND nguyên (Decimal hoặc integer), không dùng float cho số liệu tài chính.
- Mỗi module có interface rõ ràng (Protocol/ABC), schema Pydantic, test hợp đồng.
- Mỗi giá trị chỉ số lưu: công thức, phiên bản định nghĩa, đầu vào kèm provenance, cờ cảnh báo, mức tin cậy.
- Cờ cảnh báo vòng quay phải thu dùng đúng nguyên văn: “Chỉ số vòng quay đang được tính dựa trên Tổng các khoản phải thu (130) thay vì Phải thu khách hàng (131)”.

## Cách làm việc
- Làm theo phase (mục 15 của Báo cáo chính), không nhảy phase. Mỗi phase kết thúc khi đạt tiêu chí hoàn thành của phase đó và mọi kiểm thử đạt.
- Test trước hoặc cùng lúc với mã. Không tắt, bỏ qua hay làm yếu một kiểm thử để cho qua.
- Không bịa số đo. Mọi chỉ tiêu (độ chính xác OCR, recall ABSTAIN, hallucination rate…) chỉ được báo cáo từ lần chạy thật của harness trong eval/, kèm cỡ mẫu và lệnh tái lập.
- Cuối mỗi phase: cập nhật docs/PROGRESS.md (đã làm, kết quả kiểm thử, số đo, sai lệch so với đặc tả, giả định mới) rồi dừng chờ xác nhận ở các cổng go/no-go (sau Phase 1 và Phase 2).

## Điều chỉnh do chủ dự án duyệt ngày02/11/2026

Quyết định trực tiếp của người dùng thắng mô tả cũ. Đọc trạng thái hiện hành trong PLAN/ARCHITECTURE/ASSUMPTIONS/PROGRESS. Alias nguồn trong CLAUDE chưa tồn tại; đường dẫn thực theo bảng nguồn READING_NOTES.

- B02-23=97.623.991.644, TM18 FX=(1.685.413.336), evidence tại docs/evidence/fpt_q1_2026. CF04/TM18 giữ WARN, bridge chưa duyệt. Không sửa oracle theo output.
- Gateway theo D-GW-1–8/A53–A60 đã duyệt: value-blind composer, typed refs/local renderer, mask user numbers, enum clarification, run-random tokens, không streaming/hedging; training_use/retention, tenant fairness/separate runtime-dev keys. Mặc định không history; SSE chỉ progress/result_ref, GET answer sau verified.
- Chưa có keys: không gọi provider. Không copy quota/terms mục20 thiết kế vào registry. Private artifacts30ngày không phải provider retention bound.
- Assessment generic v0 chỉ là cơ sở; vẫn POLICY_UNAPPROVED đến khi chủ dự án duyệt kết quả corpus run. OCF14 score một lần ở cashflow, bands overlap/gap UNCLASSIFIED, Piotroski/Trend weights0; caps/disclaimer theo A25–A28.
- Corpus Phase0≥30 manifest nguồn/ngày/điều khoản/hash +≥10 gold approved do chủ dự án cung cấp; không tự thu thập ngoài danh sách nguồn cho phép bằng văn bản, không nhân mẫu bằng copy/synthetic.
- Phase0 theo thứ tự PLAN; **DỪNG tại P0.05 sau draft schemas/snapshot tests để chủ dự án xem trước frozen**. Chưa qua cổng thì không P0.06–P0.11. Kết thúc Phase0 lại dừng trước Phase1.
- Dùng .venv workspace; không cài global tool/plugin/MCP, không Git/Codex hooks hoặc pre-commit install. Pre-commit chỉ manual/CI. Không spawn sub-agent, không runtime multi-agent.
- Chạy checks thật, thiếu service ghi NOT_RUN; không hạ KPI. Cập nhật PROGRESS khi bàn giao.

## Cổng schema sau review R1–R7

Chủ dự án đã xác nhận **freeze** cho14 nhóm và A61. Baseline ở schemas/frozen/manifest.json; cùng major chỉ thêm DTO hoặc trường tùy chọn. Mọi finite enum hiện closed, **extensible=[]**; thêm giá trị enum xử lý đầy đủ là breaking. Canonical/1 được sửa breaking qua ADR/hash/diff trước first real write P2.01; sau đó strict version/ADR/migration/full snapshots. Các nhóm khác strict frozen ngay.

P0.06–P0.11 đã được cho phép; Phase0 chưa đủ corpus thì không tuyên bố hoàn thành. Mọi loader registry đĩa/DB phải qua registry.bundle, có test không bypass; lỗi sau freeze thêm ca sai vào tests/fixtures/schema_review_cases.json. A61 là biên kỹ thuật, chạm dữ liệu thật báo/xin duyệt, không cắt/bỏ. Chỉ xử lý reports thật trong data/public_reports, không thu thập/copy/synthetic để đạt30/10. P0.10 chỉ đọc official docs; account/live/token-copy NOT_RUN tới khi có quyền/khóa, không threshold tự đặt. Không sửa Git global config/quyền.git. **Dừng trước Phase1 chờ xác nhận**, không hỏi lại freeze.

## Ngoại lệ Phase1a ngày03/11/2026

Chủ dự án chỉ cho P1.01 (ingestion/BlobStore/file+URL/job memory), phân loại/render/xoay/deskew P1.02, S5 normalization P1.05 và harness thời gian/memory/trace, manifest/crop candidates từ data/public_reports. Phase0 INCOMPLETE/NO_GO vẫn giữ, không mở Phase1 đầy đủ. Không P1.03 tuning/P1.04 engine benchmark hoặc selection/P1.06 train/P1.07 teacher/P1.08 KPI/GO gate. Không báo OCR accuracy, không gọi provider. Live/token-copy/Docker/Postgres/Redis/hosted CI giữ NOT_RUN. Không packages/global settings/hooks/Git config/ACL. Hoàn tất phần được phép cập nhật PROGRESS và **dừng chờ corpus≥30 complete manifests,≥10 gold approved và xác nhận mới**. PLAN§3.1/A64 nêu chi tiết và giới hạn;14 frozen schemas không đổi.
