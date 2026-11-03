# Bằng chứng đính chính FPT — 02/11/2026

Nguồn duy nhất: [PDF gốc](../../../data/public_reports/20260424_-_FPT_-_BCTC_rieng_Quy_1_nam_2026_1777344035.pdf), SHA256 `11c9709914cdc5f1561f47045283598c359f7466f94e5ffbc21893e28b0315fa`. Không sửa PDF, không dùng số tính ngược làm số đọc.

Render cục bộ bằng Windows.Data.Pdf, yêu cầu400dpi; Windows xuất raster thực tế5848×4135 ở trang6 và4135×5848 ở trang8/9/25. Tên400dpi là cấu hình yêu cầu, không suy DPI thực từ tên. Crops là phép cắt pixel nguyên từ raster bằng System.Drawing.Bitmap.Clone, không resize/sharpen/OCR hoặc tạo ảnh bằng model. Tọa độ dưới đây là pixel trên raster, gốc trái trên, bbox `[x1,y1,x2,y2]` với cạnh phải/dưới loại trừ.

| Crop | Trang vật lý | Bbox | Giá trị đã xem trực tiếp |
| --- | --- | --- | --- |
| [B02 nhãn/cột](b02-rows20-30.png) |6|[680,1150,5630,2450]|Mã20/22/23/24/25/26/30 và cột Q1/2026, Q1/2025, YTD |
| [B02 cận chữ số](b02-code23-digits.png) |6|[3070,1850,4390,2350]|97.623.991.644;99.309.404.980;1.837.469.291.998 |
| [Thuyết minh18](note18-finance-costs.png) |25|[660,720,3760,1480]|(1.685.413.336), tổng97.623.991.644; kỳ trước(1.533.326.629) |
| [CF04](cf04-current-prior.png) |8|[650,1050,3850,2150]|(1.685.263.219); kỳ trước(1.498.048.003) |
| [CF61](cf61-current-prior.png) |9|[650,1100,3850,2450]|(150.117); kỳ trước(35.278.716) |

Ảnh toàn trang giữ để đối chiếu nhãn/kỳ. Hash raster/crops và các giá trị đọc nằm trong [evidence.json](evidence.json). Đây là bằng chứng đính chính các ô được chỉ định, không phải annotation đầy đủ hoặc phê duyệt gold corpus.

Đẳng thức B02-30 xác nhận chéo số đọc. Chênh TM18/CF04 kỳ này bằng150.117 nhưng kỳ trước còn residual90đ sau phép tương tự; **giữ WARN, bridge chưa được chứng minh/phê duyệt**.
