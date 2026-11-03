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