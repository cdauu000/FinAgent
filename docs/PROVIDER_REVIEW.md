# P0.10 — nguồn chính thức, chưa xác minh tài khoản/live

`checked_at=2026-11-02T10:53:39Z`. Chỉ đọc tài liệu công khai chính thức bằng web; không đăng nhập, không đọc khóa, không gọi inference/probe. [Hồ sơ máy đọc được](../eval/providers/official-review-2026-11-02.json) ghi URL, nguồn, trạng thái và giới hạn chứng cứ. Không lấy số hoặc điều khoản từ LLM_GATEWAY_DESIGN§20.

| Nguồn chính thức đã đọc | Điều rút ra cho thiết kế, không phải kết quả account/probe |
| --- | --- |
| [Groq Rate Limits](https://console.groq.com/docs/rate-limits) | Phạm vi quota gắn tổ chức; trang limits tài khoản mới xác nhận áp dụng thực tế. Không chép bảng số công khai vào registry |
| [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs) | Hỗ trợ cấu trúc tùy model/mode; phải probe từng model/task. Local validation vẫn bắt buộc theo FinAgent |
| [Groq Your Data](https://console.groq.com/docs/your-data) | Retention phụ thuộc tính năng, xử lý reliability/abuse và Data Controls; không suy cấu hình account của chủ dự án |
| [Groq Services Agreement](https://console.groq.com/docs/legal/services-agreement) | Đây là thỏa thuận cloud service; Terms of Use của website không thay thế nó. Chưa xác nhận thỏa thuận áp dụng cho account nào |
| [Groq DPA](https://console.groq.com/docs/legal/customer-data-processing-addendum) | Điều khoản xử lý/xóa dữ liệu cần đọc cùng thỏa thuận dịch vụ; chưa thể biến thành retention bound của route cụ thể |
| [Gemini Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits) | Quota gắn project, thay đổi theo model/tier; active limits nằm trong AI Studio. Không gán số hạn mức từ tài liệu cho account chưa biết |
| [Gemini Structured Output](https://ai.google.dev/gemini-api/docs/structured-output) | Hỗ trợ một phần JSON Schema; có giới hạn không được backend model thực thi, cần kiểm cục bộ. Chưa gán structured_strategy cho model chưa probe |
| [Gemini Additional Terms](https://ai.google.dev/gemini-api/terms) | Cách dùng dữ liệu khác nhau theo dịch vụ paid/unpaid và điều kiện account/region. Chưa gán training_use/retention verified cho tenant |
| [Google API Terms](https://developers.google.com/terms) | Điều khoản chung được Gemini Additional Terms dẫn chiếu; việc đọc không chứng minh account đã chấp nhận hoặc đủ điều kiện |

Không trích nguyên văn điều khoản, không chốt tư vấn pháp lý hoặc eligibility từ các bản tóm tắt này. Các trang public có thể cập nhật; khi có account phải kiểm lại scope/model/region/plan, điều khoản áp dụng và thời điểm.

- Official-document review: **READ**, có checked_at/URL. Không coi là capability/terms verification cho model/account.
- Account limits, Data Controls, account-specific terms: **NOT_RUN** — chưa có quyền/khóa; không thử đăng nhập.
- Live structured conformance, token-copy, latency, chất lượng, usage/cost: **NOT_RUN**; không threshold tự đặt.
- Registry model thực: **0 entries**; training_use/retention của route vẫn unknown, provider order chưa xác định. `config/registries/models.json` và prompts là empty draft qua loader tập trung; không được dùng làm route production.
- Runtime/dev keys chỉ có tên biến riêng trong `.env.example`; không fallback sang khóa phát triển. Private thiếu chứng cứ hiện hành hoặc retention bound thì local-only; strict-private luôn local.

Khi có khóa/quyền sau này, P0.10/P6.04 tiếp tục phần còn thiếu, ghi quota source manual_console/probe/header_hint riêng. Header là hint; synthetic probe thành công không chứng minh trần quota, điều khoản, khả năng giữ bí mật hoặc chất lượng trên toàn bộ báo cáo.
