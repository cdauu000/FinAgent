# Báo cáo 2: Hướng phát triển FinAgent sau khi hoàn thành core

*Đi kèm Báo cáo chính (Phiên bản 2.0) · 28/10/2026 · Chỉ ý tưởng và thiết kế, chưa viết code*

## 1. Mục đích và cách đọc

Báo cáo chính mô tả toàn bộ dự án và core của hệ thống. Báo cáo này trả lời bốn câu hỏi cho từng hướng phát triển sau core: **cần những gì, có phải đổi core không, thêm vào như thế nào, và các phần liên quan bị ảnh hưởng ra sao.**

- Mục 2 nêu nguyên tắc mở rộng. Mục 3 liệt kê các điểm mở rộng mà core dành sẵn. Mục 4 là bảng tổng hợp mọi hướng.

- Mục 5 đến 10 chi tiết từng hướng. Mục 11 là quy trình khi bắt buộc đổi core. Mục 12 là lộ trình gợi ý. Phụ lục là các danh sách kiểm tra.

- Những điều tôi chưa xác minh được (đặc biệt về ngân hàng) được đánh dấu **[GIẢ ĐỊNH]**. Theo yêu cầu của bạn, các giả định này được giữ lại ở đây, không đưa vào báo cáo chính, để kiểm tra khi bắt đầu mở rộng.

## 2. Nguyên tắc mở rộng không sửa core

1. **Mở rộng bằng dữ liệu và cấu hình khai báo**, không bằng mã trong core.

2. **Core dùng chính các điểm mở rộng ngay từ ngày đầu.** Gói ngành chung (generic) chạy qua giao diện Sector Pack; mẫu biểu doanh nghiệp thông thường chạy qua kho mẫu biểu. Nhờ đó đường mở rộng luôn được kiểm thử, không phải “đường chưa ai đi”.

3. **Phiên bản hóa và tương thích ngược:** mọi định nghĩa mới có phiên bản, ca kiểm thử bắt buộc, và chạy hồi quy trên kho báo cáo trước khi phát hành.

4. **Các bất biến không bao giờ bị mở rộng phá vỡ:** số chỉ đến từ kho chuẩn và kernel; Sector Pack không đổi giá trị chỉ số; tài liệu không rời hạ tầng khi chạy thật; Verifier là cổng cuối; fail-closed khi thiếu bằng chứng.

5. **Chỉ được đổi core khi** (a) cần kiểu dữ liệu mà mô hình canonical không biểu diễn được, (b) cần phép toán ngoài ngôn ngữ biểu thức an toàn của Registry, (c) cần thay đổi một bất biến, hoặc (d) cần giao thức agent ngoài schema thông điệp hiện có. Khi đó áp dụng quy trình ở mục 11.

## 3. Các điểm mở rộng (EP) của core

Bảng này đối chiếu với mục 22 của Báo cáo chính.

<!-- Page 1 of 17 -->

| EP | Điểm mở rộng | Thêm gì | Cách thêm |
| --- | --- | --- | --- |
| EP1 | Ratio Registry | Chỉ số mới, biến thể công thức | Viết định nghĩa khai báo + ca tính tay; trạng thái experimental → extended |
| EP2 | Sector Pack Interface v1 | Gói ngành: trọng số, ngưỡng, cờ đỏ, luật áp dụng, chỉ số bổ sung | Thêm tệp gói đúng schema; nạp và kiểm tra khi khởi động |
| EP3 | Kho mẫu biểu (Statement Template Registry) | Mẫu biểu mới (ngân hàng, doanh nghiệp nhỏ và vừa, IFRS…) | Thêm ánh xạ mã số → mã chuẩn, nhận diện mẫu, nhãn tiếng Việt/Anh |
| EP4 | Kho quy tắc kiểm tra (Validation Rule Registry) | Đẳng thức và quy tắc hợp lý riêng cho mẫu biểu | Thêm quy tắc khai báo gắn với template_id |
| EP5 | Luật áp dụng (Applicability Rules) | Điều kiện N/A hoặc NOT_MEANINGFUL theo loại doanh nghiệp | Khai báo trong Registry hoặc trong gói ngành |
| EP6 | Classifier plug-in | Bộ phân loại trang, ngành, mẫu biểu | Thêm mô hình tuân theo giao diện: đầu vào tài liệu, đầu ra nhãn + độ tin cậy + bằng chứng |
| EP7 | Agent Role Registry và chiến lược điều phối | Vai trò agent mới; chuyển từ single sang supervisor | Khai báo vai trò: công cụ được phép, tuyến model, schema vào/ra, ngân sách |
| EP8 | Tool Registry | Công cụ mới cho Agent | Khai báo công cụ có schema và quyền; kernel hoặc truy vấn phía sau |
| EP9 | LLM Gateway: adapter và tuyến tác vụ | Nhà cung cấp, model, loại tác vụ mới | Thêm adapter, cập nhật registry năng lực và chuỗi định tuyến |
| EP10 | Evidence Source Connector | Nguồn mới cho bối cảnh ngành và tin tức | Thêm connector có điểm tin cậy nguồn |
| EP11 | Cờ tính năng (feature flags) | Bật hoặc tắt khả năng theo tầng dữ liệu và tenant | Khai báo cờ, mặc định tắt, ràng buộc theo tầng |

<!-- Page 2 of 17 -->

| EP | Điểm mở rộng | Thêm gì | Cách thêm |
| --- | --- | --- | --- |
| EP12 | Hợp đồng API và sự kiện | Giao diện người dùng, tích hợp ngoài | Dùng API /v1 và luồng sự kiện sẵn có |

## 4. Bảng tổng hợp các hướng phát triển

| # | Hướng | Cần gì | Core có đổi không | Thêm bằng cách nào | Ưu tiên |
| --- | --- | --- | --- | --- | --- |
| D1 | Sector Pack Công nghệ | Chuyên gia tài chính, kho báo cáo ngành, thuật ngữ | Không | EP2, EP1, EP5 | Cao (nhẹ nhất) |
| D2 | Sector Pack Logistics | Như D1, thêm hồ sơ con nặng/nhẹ tài sản | Không | EP2, EP1, EP5 | Cao |
| D3 | Ngân hàng | Mẫu biểu tổ chức tín dụng, báo cáo mẫu, nguồn NPL/CAR, chuyên gia | Dự kiến không (xem mục 6.4) | EP3, EP4, EP1, EP2, EP5 | Cao, nặng nhất |
| D4 | Tự phân loại ngành | Kho báo cáo có nhãn ngành, huấn luyện | Không | EP6 | Cao (cần cho D1 đến D3) |
| D5 | Multi-agent | Gói ngành, định nghĩa vai trò, ngân sách gọi model | Không | EP7, EP8, EP9 | Trung bình |
| D6 | Chỉ số mở rộng | Định nghĩa, ca tính tay, duyệt chuyên gia | Không | EP1 | Cao, làm liên tục |
| D7 | Chứng khoán, bảo hiểm | Như D3 cho từng loại | Dự kiến không | EP3, EP4, EP1, EP2 | Thấp |
| D8 | Doanh nghiệp nhỏ và vừa, dữ liệu riêng tư | Mẫu biểu riêng, Excel và ảnh chụp, đồng ý dữ liệu, pilot | Không (có thể thêm bước tiền xử lý ảnh) | EP3, EP4, EP6 | Trung bình |
| D9 | Tóm tắt bằng model cho văn bản báo cáo công khai | Quyết định bật, kiểm soát tầng | Không | EP11, EP9 | Thấp |
| D10 | Tóm tắt bối cảnh ngành bằng model | Nguồn tin cậy, kiểm tra trích dẫn | Không | EP10, EP11, EP9 | Thấp |
| D11 | Giao diện người dùng | Thiết kế UI, API ổn định | Không | EP12 | Cao sau core |
| D12 | Hạ tầng: GPU, triển khai tại chỗ, VLM nội bộ | Máy, mô hình trọng số mở | Không (adapter) | EP9, EP6 | Theo nhu cầu |

<!-- Page 3 of 17 -->

| # | Hướng | Cần gì | Core có đổi không | Thêm bằng cách nào | Ưu tiên |
| --- | --- | --- | --- | --- | --- |
| D13 | So sánh nhiều doanh nghiệp, benchmark ngành | Kho đủ lớn, định nghĩa nhóm so sánh | Không | EP8, kho chuẩn | Trung bình |
| D14 | Báo cáo IFRS hoặc tiếng Anh | Mẫu biểu, nhãn | Không | EP3 | Thấp |

## 5. D1, D2: Sector Pack theo ngành

### 5.1 Cần gì

- **Người thiết kế gói** (bạn) và một chuyên gia tài chính của ngành để duyệt trọng số, ngưỡng, cờ đỏ.

- **Kho báo cáo theo ngành:** khuyến nghị tối thiểu khoảng 20 đến 30 báo cáo đã công bố của doanh nghiệp trong ngành (nhiều kỳ, nhiều doanh nghiệp) để tính phân vị và thử gói.

- **Danh sách thuật ngữ và dòng đặc thù** của ngành trong báo cáo.

- **Bộ ca kiểm thử riêng:** câu hỏi và đáp án mẫu theo ngành.

### 5.2 Có đổi core không

**Không.** Giao diện Sector Pack v1 (Báo cáo chính mục 22.3) đã nằm trong core, và gói chung chạy qua đúng giao diện này. Thêm một ngành là thêm một tệp gói.

### 5.3 Thêm vào như thế nào

1. Viết hồ sơ ngành: đặc điểm báo cáo, chỉ số quan trọng, chỉ số N/A, cờ đỏ.

2. Khai báo chỉ số bổ sung (nếu có) trong Ratio Registry ở trạng thái experimental, kèm ca tính tay.

3. Tính benchmark từ kho: phân vị từng chỉ số theo ngành, ghi nguồn và ngày.

4. Soạn gói theo schema Sector Pack v1: trọng số trụ cột và chỉ số, ngưỡng, luật áp dụng ghi đè, cờ đỏ, hướng dẫn diễn giải, ca kiểm thử.

5. Cấu hình bộ phân loại ngành (D4) để nhận ra ngành; trong lúc chưa có thì chọn gói thủ công.

6. Nạp gói ở chế độ nháp; chạy kiểm tra schema và ca kiểm thử; chạy hồi quy trên kho; so sánh kết quả với gói chung.

7. Chuyên gia duyệt; phát hành; ghi pack_id@phiên bản .

<!-- Page 4 of 17 -->

### 5.4 Giả thuyết khởi điểm cho hai ngành (cần chuyên gia xác nhận)

| Hạng mục | Công nghệ | Logistics |
| --- | --- | --- |
| Đặc điểm | Biên gộp cao, ít tồn kho (trừ phân phối phần cứng), doanh thu chưa thực hiện, phụ thuộc khách hàng lớn | Hai mô hình: nặng tài sản (vận tải, cảng, kho bãi, đội tàu hay xe) và nhẹ tài sản (giao nhận); chi phí nhiên liệu, khấu hao và đòn bẩy lớn ở mô hình nặng tài sản |
| Chỉ số trọng tâm | Biên gộp, biên ròng, ROE, OCF; DSO (mở rộng) | ICR, D/E, Current Ratio, OCF, vòng quay tài sản, vòng quay phải thu; EBITDA margin, Net debt/EBITDA, vòng quay tài sản cố định, dòng tiền tự do (mở rộng) |
| N/A hoặc kém ý nghĩa | Vòng quay hàng tồn kho (trừ phân phối phần cứng) | Vòng quay hàng tồn kho; biên gộp khó so sánh giữa hai mô hình |
| Cờ đỏ | Phải thu tăng nhanh hơn doanh thu; doanh thu chưa thực hiện biến động mạnh | Vay ngắn hạn tài trợ tài sản dài hạn; dòng tiền tự do âm kéo dài do chi đầu tư; phụ thuộc nhiên liệu và tỷ giá; tập trung khách hàng |
| Dữ liệu cần thêm | Doanh thu chưa thực hiện, phân đoạn | Thuyết minh tài sản cố định, thuê tài chính, vay theo kỳ hạn, phân đoạn |
| Hồ sơ con | Phần mềm và dịch vụ so với phân phối phần cứng | Nặng tài sản so với nhẹ tài sản |

### 5.5 Phần liên quan bị ảnh hưởng

- **Ratio Registry:** thêm chỉ số bổ sung ở trạng thái extended khi gói dùng.

- **Applicability Gate:** nhận luật ghi đè từ gói.

- **Assessment:** trọng số và ngưỡng lấy từ gói; kết quả ghi pack_id@phiên bản ; điểm và độ tin cậy vẫn tách biệt.

- **Agent, vị trí 2:** phần hướng dẫn diễn giải và danh sách “không được nói” của gói được đưa vào prompt soạn câu trả lời; hậu kiểm số không đổi.

- **Kiểm thử:** thêm bộ ca theo ngành; kiểm tra tự động giá trị chỉ số không đổi khi đổi gói.

### 5.6 Rủi ro

- Ngưỡng ngành tính từ kho nhỏ hoặc lệch (ít doanh nghiệp, một giai đoạn kinh tế): ghi cỡ mẫu, ngày và cảnh báo khi dưới ngưỡng cỡ mẫu.

<!-- Page 5 of 17 -->

- Doanh nghiệp đa ngành: chọn gói theo cơ cấu doanh thu; khi không rõ thì gói chung kèm cảnh báo.

## 6. D3, D7: Ngân hàng (và chứng khoán, bảo hiểm)

### 6.1 Vì sao khác

Báo cáo của tổ chức tín dụng có bản chất khác doanh nghiệp thông thường: tài sản chủ yếu là cho vay khách hàng và chứng khoán đầu tư, nguồn vốn chủ yếu là tiền gửi của khách hàng, thu nhập chính là chênh lệch lãi suất, và đòn bẩy rất cao là bình thường. Vì vậy phần lớn 15 chỉ số lõi (Current, Quick, Cash, các vòng quay, OCF trên nợ ngắn hạn) không có ý nghĩa; Debt Ratio và D/E không so được với ngưỡng doanh nghiệp thông thường; ROA và ROE vẫn dùng được. Trong core, Applicability Gate đã nhận diện tổ chức tín dụng để cảnh báo “không áp dụng” thay vì tính ra con số vô nghĩa.

### 6.2 Các giả định giữ lại [GIẢ ĐỊNH]

Theo yêu cầu của bạn, các giả định sau được giữ nguyên và chỉ kiểm tra khi bắt đầu làm gói ngân hàng.

| # | Giả định | Cách xác minh |
| --- | --- | --- |
| A1 | Báo cáo của tổ chức tín dụng dùng mẫu biểu và mã số riêng, khác mẫu doanh nghiệp thông thường | Lấy văn bản quy định và ít nhất 5 báo cáo ngân hàng thật; lập bảng mã số thực tế |
| A2 | NIM, CIR, NPL, bao phủ dự phòng, LDR, CASA, chi phí tín dụng tính được từ báo cáo tài chính và thuyết minh | Với từng chỉ số, chỉ ra dòng nguồn cụ thể trong báo cáo thật; ghi chỉ số nào không tính được |
| A3 | CAR thường nằm ở tài liệu công bố khác, không nằm trong báo cáo tài chính | Kiểm tra từng ngân hàng mẫu; nếu thiếu thì chỉ số là MISSING_ITEM |
| A4 | Tỉ lệ nợ xấu lấy từ thuyết minh phân loại nợ (nhóm nợ xấu theo quy định hiện hành) | Chuyên gia ngân hàng xác nhận định nghĩa nhóm nợ và công thức |
| A5 | Piotroski F-Score không phù hợp ngân hàng (thiết kế gốc cho doanh nghiệp phi tài chính), nên mặc định N/A | Chuyên gia quyết định có dùng biến thể hay không |
| A6 | Báo cáo hợp nhất của ngân hàng có cấu trúc tương tự báo cáo riêng ở mức khung | Đối chiếu báo cáo thật |

<!-- Page 6 of 17 -->

| # | Giả định | Cách xác minh |
| --- | --- | --- |
| A7 | Công thức chuẩn của từng chỉ số ngân hàng (bình quân hay cuối kỳ, tử số và mẫu số cụ thể) cần chuyên gia chốt | Chuyên gia duyệt định nghĩa và ca tính tay |

### 6.3 Cần gì

- Văn bản quy định mẫu biểu và phân loại nợ áp dụng; chuyên gia ngân hàng.

- Ít nhất 5 đến 10 báo cáo ngân hàng đã công bố (riêng và hợp nhất, nhiều kỳ) làm bộ vàng; nhãn đáp án ở cấp ô số cho các bảng chính.

- Danh sách chỉ số ngân hàng cần có và nguồn dữ liệu của từng chỉ số.

### 6.4 Core có đổi không

**Dự kiến không**, nếu ba điều kiện sau đúng (cần kết luận ở bước khảo sát, không giả định trước):

1. Mô hình canonical biểu diễn được các dòng của ngân hàng bằng *dữ liệu*: core đã dành sẵn trường statement_family  (mặc định corporate ) và template_id ; dòng mới như cho vay khách hàng, tiền gửi của khách hàng, thu nhập lãi chỉ là thêm mã chuẩn, không phải thêm kiểu dữ liệu.

2. Các đẳng thức của mẫu ngân hàng biểu diễn được trong Validation Rule Registry (cha bằng tổng con, tổng tài sản bằng tổng nguồn vốn, liên báo cáo).

3. Các chỉ số ngân hàng biểu diễn được bằng ngôn ngữ biểu thức của Registry (tỉ số, bình quân hai điểm, tổng có điều kiện).

Nếu một trong ba điều kiện sai, đi theo quy trình đổi core ở mục 11. Phần có nhiều khả năng cần xem xét nhất là điều kiện 3 (ví dụ chỉ số cần gộp theo nhóm nợ ở thuyết minh).

### 6.5 Thêm vào như thế nào

1. **Khảo sát (1 đến 2 tuần):** thu thập báo cáo mẫu, kiểm tra các giả định A1 đến A7, quyết định nhóm chỉ số.

2. **Kho mẫu biểu (EP3):** thêm mẫu ngân hàng: nhận diện mẫu, ánh xạ mã số sang mã chuẩn, nhãn tiếng Việt, hỗ trợ nhiều phiên bản.

3. **Quy tắc kiểm tra (EP4):** khai báo các đẳng thức riêng, quy tắc hợp lý (ví dụ cho vay không âm, dự phòng mang dấu âm).

4. **Chỉ số (EP1):** khai báo NIM, CIR, NPL, bao phủ dự phòng, LDR, CASA, chi phí tín dụng, tăng trưởng tín dụng ở trạng thái experimental, kèm ca tính tay; ROA và ROE dùng lại định nghĩa lõi.

<!-- Page 7 of 17 -->

5. **Luật áp dụng (EP5):** khai báo 15 chỉ số lõi nào là N/A hoặc NOT_MEANINGFUL cho ngân hàng.

6. **Sector Pack ngân hàng (EP2):** trọng số, ngưỡng từ kho, cờ đỏ (nợ xấu tăng, bao phủ dự phòng giảm, LDR sát giới hạn, phụ thuộc vốn ngắn hạn thị trường), hướng dẫn diễn giải.

7. **Huấn luyện bộ đọc bảng (EP6, phần OCR):** tinh chỉnh layout và bảng cho mẫu ngân hàng bằng báo cáo công khai; bảng ngân hàng thường dài và nhiều cấp.

8. **Kiểm thử và phát hành:** chạy hồi quy; đối chiếu chỉ số với bảng tính tay của chuyên gia; chuyển chỉ số sang extended; phát hành gói.

### 6.6 Danh sách chỉ số ngân hàng đề xuất (công thức cần chuyên gia chốt, theo A7)

| Chỉ số | Ý tưởng công thức | Dữ liệu |
| --- | --- | --- |
| NIM | Thu nhập lãi thuần ÷ tài sản sinh lãi bình quân | KQKD; thuyết minh tài sản sinh lãi |
| CIR | Chi phí hoạt động ÷ tổng thu nhập hoạt động | KQKD |
| NPL | Dư nợ nhóm nợ xấu ÷ tổng dư nợ cho vay | Thuyết minh phân loại nợ |
| Bao phủ dự phòng | Dự phòng rủi ro tín dụng ÷ nợ xấu | Cân đối, thuyết minh |
| LDR | Dư nợ cho vay ÷ tiền gửi huy động (theo cách tính chuyên gia chốt) | Cân đối, thuyết minh |
| CASA | Tiền gửi không kỳ hạn ÷ tổng tiền gửi | Thuyết minh |
| Chi phí tín dụng | Chi phí dự phòng ÷ dư nợ cho vay bình quân | KQKD, cân đối |
| Tăng trưởng tín dụng | Thay đổi dư nợ cho vay so với kỳ so sánh | Cân đối hai kỳ |
| CAR | Lấy từ nguồn công bố khác nếu có | Ngoài báo cáo tài chính (A3) |

### 6.7 Phần liên quan bị ảnh hưởng

- **Canonical model:** thêm mã chuẩn của họ bank ; không đổi cấu trúc bảng.

- **OCR và trích xuất:** mẫu bảng mới; cần dữ liệu huấn luyện công khai từ các ngân hàng.

- **Assessment:** trụ cột khác (chất lượng tài sản, hiệu quả, thanh khoản, vốn); định nghĩa trong gói, không sửa Assessment.

<!-- Page 8 of 17 -->

- **Agent:** danh sách công cụ không đổi; prompt vị trí 2 và danh sách “không được nói” theo gói.

- **Piotroski:** mặc định N/A cho họ bank .

### 6.8 Chứng khoán và bảo hiểm (D7)

Cùng quy trình 6.5 với mẫu biểu, chỉ số và gói riêng. Làm sau ngân hàng, tái dùng nguyên khung. Mỗi loại cần bộ giả định và bước khảo sát riêng như mục 6.2.

### 6.9 Rủi ro

- Công thức chỉ số ngân hàng phụ thuộc quy định thay đổi theo thời gian: lưu phiên bản định nghĩa và ngày hiệu lực.

- Dữ liệu thiếu (CAR, một số nhóm nợ): dùng MISSING_ITEM, tuyệt đối không ước lượng.

- Bảng ngân hàng dài, nhiều cấp, dễ sai khi nối trang: thêm ca kiểm thử chuyên cho nối bảng.

## 7. D4: Tự phân loại ngành

### 7.1 Mục tiêu và cần gì

Tự nhận ra doanh nghiệp thuộc ngành nào để chọn đúng Sector Pack. Cần **kho báo cáo đã công bố có nhãn ngành** (nhãn do bạn gán hoặc lấy từ nguồn chính thống), tối thiểu vài chục doanh nghiệp mỗi ngành mục tiêu, và danh sách ngành.

### 7.2 Core có đổi không

Không. Bộ phân loại tuân theo giao diện Classifier plug-in (EP6): đầu vào là tài liệu đã trích xuất, đầu ra là nhãn, độ tin cậy và đoạn căn cứ. Core đã có điểm gọi bộ phân loại khi chọn gói; hiện tại điểm này trả về gói chung.

### 7.3 Thiết kế

- **Chạy cục bộ**, huấn luyện trên báo cáo công khai; không gửi văn bản báo cáo ra API ngoài.

- **Đặc trưng:** mô tả ngành nghề trong Thuyết minh, cơ cấu doanh thu và chi phí, đặc trưng cấu trúc báo cáo (ví dụ ngân hàng nhận ra qua dòng cho vay khách hàng, tiền gửi của khách hàng, thu nhập lãi), từ khóa và các dòng đặc thù.

- **Kết hợp luật và mô hình:** luật cấu trúc cho các họ báo cáo khác hẳn (ngân hàng, chứng khoán, bảo hiểm), mô hình học cho phân loại giữa các ngành phi tài chính.

<!-- Page 9 of 17 -->

- **Đầu ra:** tối đa vài nhãn kèm tỉ trọng cho doanh nghiệp đa ngành, độ tin cậy, đoạn căn cứ. Dưới ngưỡng thì dùng gói chung kèm cảnh báo; người dùng được ghi đè nhãn.

### 7.4 Thêm vào như thế nào và đánh giá

1. Chốt danh sách ngành và cây phân cấp (theo cách tự phân loại, không bám chuẩn bên ngoài).

2. Gắn nhãn kho; chia tập theo doanh nghiệp.

3. Huấn luyện, hiệu chỉnh ngưỡng tin cậy trên tập phát triển.

4. Đo trên tập kiểm thử đóng băng: độ chính xác, độ chính xác theo ngành, tỉ lệ rơi về gói chung; đặt chỉ tiêu cụ thể sau khi có số đo đầu tiên.

5. Gắn vào điểm chọn gói; chạy song song với chọn thủ công một thời gian rồi mới chuyển sang tự động.

## 8. D5: Multi-agent theo ngành

### 8.1 Khi nào đáng làm

Core dùng một Orchestrator với danh mục công cụ và Verifier theo quy tắc. Multi-agent chỉ đáng làm khi đo được lợi ích so với cấu hình đơn: diễn giải theo ngành tốt hơn, kiểm tra độc lập tốt hơn, hoặc chạy song song hiệu quả. Cái giá: độ trễ, số lần gọi model (đáng kể khi dùng gói miễn phí có hạn mức), lỗi lan truyền, khó gỡ lỗi.

### 8.2 Core có đổi không

Không, vì core đã đưa mọi lời gọi của Agent qua giao diện **Agent Role Interface** (EP7) và chiến lược điều phối mặc định là single . Chuyển sang supervisor  là thay cấu hình và thêm định nghĩa vai trò.

### 8.3 Các vai trò đề xuất

| Agent | Trách nhiệm | Công cụ được phép | Không được làm |
| --- | --- | --- | --- |
| Supervisor | Phân loại ý định, chọn gói ngành, phân việc, hợp nhất, quyết định cuối theo chế độ vận hành | Danh mục điều phối | Tự tính số |
| Financial Analyst | Chạy chỉ số, Trend, Piotroski theo gói | compute_*, get_statement | Đổi định nghĩa chỉ số |

<!-- Page 10 of 17 -->

| Agent | Trách nhiệm | Công cụ được phép | Không được làm |
| --- | --- | --- | --- |
| Sector Specialist (một cấu hình mỗi ngành) | Diễn giải theo trọng tâm ngành, cờ đỏ đặc thù | Công cụ phân tích, dữ liệu của gói | Đổi giá trị chỉ số hay trọng số ngoài gói |
| Reconciliation | Đối chiếu giữa báo cáo và giữa kỳ, giải thích chênh lệch | Validator, get_statement | Ghi đè số |
| Extraction QA | Xử lý hàng đợi ô nghi ngờ, đề xuất sửa bằng engine OCR cục bộ | Công cụ OCR, Review API (chỉ đề xuất) | Ghi trực tiếp vào kho đã VERIFIED |
| Risk and Audit | Cờ đỏ chất lượng lợi nhuận, bên liên quan, ý kiến kiểm toán | Công cụ phân tích, search_evidence | Đổi điểm cơ bản |
| Context | Liệt kê bối cảnh ngành từ nguồn công khai có trích dẫn | Connector nguồn | Ảnh hưởng điểm số |
| Verifier | Cổng cuối: hậu kiểm số, kiểm thực thể, nhãn trạng thái; có quyền chặn | Chỉ đọc đáp số và bằng chứng | Sinh số |
| Report Composer | Soạn câu trả lời và báo cáo, xuất file | Export | Thêm số ngoài tập đáp số |

### 8.4 Giao thức phối hợp

- Giao tiếp bằng thông điệp có schema, qua kho bằng chứng dùng chung; **không truyền số bằng văn bản tự do**; mọi thông điệp mang evidence_id.

- Ngân sách chung về bước, token, thời gian; số vòng trao đổi tối đa; điều kiện dừng rõ.

- Tầng dữ liệu và chế độ vận hành áp dụng cho mọi agent; agent không gọi nhà cung cấp vi phạm tầng.

- Mỗi agent ghi trace; trace nối thành cây theo yêu cầu.

- Nguồn số duy nhất vẫn là kho chuẩn và kernel.

<!-- Page 11 of 17 -->

### 8.5 Ba giai đoạn và điều kiện giữ

| Giai đoạn | Cấu hình | Điều kiện sang giai đoạn kế |
| --- | --- | --- |
| A (core) | single : Orchestrator + công cụ + Verifier theo quy tắc, chưa phân ngành | Đạt mục tiêu chế độ vận hành |
| B | supervisor : Supervisor + Financial Analyst + Sector Specialist cho 2 đến 3 ngành đã có gói | Vượt baseline giai đoạn A |
| C | Thêm Reconciliation, Risk and Audit, Extraction QA; thêm ngành; chạy song song | Theo nhu cầu và ngân sách |

**Điều kiện giữ multi-agent:** trên bộ đánh giá phải vượt baseline Agent đơn về tỉ lệ mệnh đề được ủng hộ và độ phù hợp theo ngành do chuyên gia chấm, trong khi độ trễ và chi phí không quá khoảng 2 lần (ngưỡng đề xuất). Nếu không đạt thì giữ cấu hình đơn.

### 8.6 Thêm vào như thế nào

1. Khai báo từng vai trò (mục đích, công cụ, tuyến model, schema vào/ra, ngân sách).

2. Khai báo giao thức thông điệp và cây trace.

3. Chuyển chiến lược sang supervisor  cho một nhóm ngành thử nghiệm bằng cờ.

4. Chạy A/B trên bộ đánh giá: có và không có multi-agent, có và không có gói ngành.

5. Theo dõi chi phí và hạn mức: cache, model nhỏ cho agent phụ, hàng đợi ưu tiên.

### 8.7 Phần liên quan bị ảnh hưởng

LLM Gateway (nhiều lời gọi hơn, hạn mức), hàng đợi ưu tiên, trace và quan sát, bộ đánh giá Agent, và chế độ suy giảm (khi hết hạn mức phải quay về single  hoặc khuôn mẫu).

## 9. D6: Chỉ số mở rộng

### 9.1 Cần gì và core có đổi không

Cần định nghĩa chỉ số, ca tính tay trên báo cáo thật, và chuyên gia duyệt. **Core không đổi** vì Ratio Registry (EP1) được thiết kế cho việc này; quy trình thêm chỉ số nằm ở Báo cáo chính mục 20.3 (viết định nghĩa, ca tính tay, chuyên gia duyệt, hồi quy trên kho, experimental rồi extended, gắn trọng số trong gói).

<!-- Page 12 of 17 -->

### 9.2 Danh sách ứng viên

| Chỉ số | Cần dữ liệu | Core có đổi không |
| --- | --- | --- |
| DSO, DIO, DPO, chu kỳ chuyển đổi tiền | Doanh thu, giá vốn, phải thu, tồn kho, phải trả người bán (bình quân hai điểm) | Không |
| DuPont (ROE phân rã) | Biên ròng, vòng quay tài sản, đòn bẩy tài chính | Không |
| EBITDA margin, Net debt/EBITDA | EBIT, khấu hao (mã 02 của lưu chuyển tiền tệ), vay trừ tiền | Không |
| Dòng tiền tự do | OCF và chi mua sắm tài sản (mã 21) | Không |
| Tăng trưởng doanh thu, lợi nhuận | Hai kỳ cùng loại, cùng scope | Không |
| Altman Z″ | Vốn lưu động, lợi nhuận giữ lại, EBIT, vốn chủ, nợ; ngưỡng cần kiểm chứng cho thị trường Việt Nam | Không |
| Beneish M-score | Tám biến số trên hai năm; dễ cho kết quả sai nếu dữ liệu thiếu | Không, nhưng có độ rủi ro diễn giải cao |
| P/E, P/B, EPS theo giá thị trường | Giá cổ phiếu và số cổ phiếu lưu hành không có trong báo cáo tài chính | Có thêm thực thể dữ liệu thị trường (xem mục 11); nguồn giá qua connector EP10 |

Lưu ý: hệ thống hiện không có dữ liệu giá. Nếu người dùng hỏi P/E, core trả MISSING_ITEM hoặc OUT_OF_DOMAIN; đây là lý do P/E nằm ở nhóm “có thêm thực thể”.

## 10. Các hướng còn lại

### 10.1 D8: Doanh nghiệp nhỏ và vừa, và dùng dữ liệu riêng tư để huấn luyện

- **Cần:** mẫu biểu riêng của doanh nghiệp nhỏ và vừa (cần xác minh văn bản và mã số), bộ tiền xử lý ảnh chụp điện thoại, hỗ trợ Excel nội bộ nhiều biến thể, pilot trong tenant, đồng ý bằng văn bản của khách hàng.

- **Core có đổi không:** không. Mẫu biểu qua EP3 và EP4; bộ tiền xử lý ảnh là một adapter trong lớp OCR; trạng thái chưa kiểm toán đã có trong Evidence Gate.

<!-- Page 13 of 17 -->

- **Dùng tài liệu riêng tư để huấn luyện (hiện tắt):** bật bằng cờ theo tenant và theo tài liệu, chỉ sau khi sản phẩm hoàn thiện. Cần cơ chế đồng ý (opt-in) bằng văn bản, ẩn danh dữ liệu, tách khỏi kho chung theo tenant, quyền rút và xóa dữ liệu, mô tả bộ dữ liệu (dataset card). Việc đổi cờ là cấu hình, không phải đổi core.

- **Phần liên quan:** phân tầng dữ liệu (mục 18 báo cáo chính), quản trị kho (mục 21), tham vấn pháp lý.

### 10.2 D9: Tóm tắt bằng model cho văn bản báo cáo công khai

- **Hiện trạng:** tắt; câu hỏi về nội dung văn bản trả lời bằng trích xuất.

- **Thêm vào:** bật cờ public_snippet_summarization  chỉ cho tầng công khai; thêm tuyến tác vụ trong LLM Gateway (EP9); giới hạn số đoạn và độ dài; hậu kiểm: câu tóm tắt chỉ được chứa thực thể và số có trong đoạn gửi đi; Verifier kiểm mệnh đề; chế độ Nghiêm ngặt vẫn dùng trích xuất.

- **Core đổi không:** không.

- **Phần liên quan:** cập nhật chính sách tầng (mục 18.3), bộ đánh giá lớp truy vấn, chi phí và hạn mức.

### 10.3 D10: Tóm tắt bối cảnh ngành bằng model

- **Hiện trạng:** chỉ liệt kê nguồn có trích dẫn, không dùng model tóm tắt.

- **Thêm vào:** connector nguồn mới (EP10) với danh sách nguồn tin cậy và điểm tin cậy; cờ tính năng; tuyến tác vụ tóm tắt (EP9); kiểm tra trích dẫn; ràng buộc cứng giữ nguyên: bối cảnh ngành không đổi điểm cơ bản.

- **Core đổi không:** không.

### 10.4 D11: Giao diện người dùng

- **Cần:** thiết kế giao diện và API đã ổn định. Core đã chuẩn bị hợp đồng API có phiên bản, luồng sự kiện, endpoint ảnh cắt ô kèm bbox, giải thích công khai có cấu trúc và khóa thông báo hai ngôn ngữ (Báo cáo chính mục 23.2).

- **Các màn hình đề xuất:** tải tài liệu và trạng thái xử lý; duyệt tay (ảnh cắt cạnh giá trị); hỏi đáp có trích dẫn; chỉ số, Piotroski và Assessment kèm cờ và giả định; cấu hình (chế độ, chính sách chỉ số); quản trị.

- **Core đổi không:** không. Việc phát sinh nên được ghi nhận như yêu cầu bổ sung API (thêm trường tùy chọn, không phá /v1).

### 10.5 D12: Hạ tầng (GPU, triển khai tại chỗ, VLM nội bộ)

- **GPU:** thêm worker GPU theo nhu cầu cho các job nặng; engine adapter đã hỗ trợ cả CPU và GPU (Báo cáo chính mục 12.6). Không đổi core.

<!-- Page 14 of 17 -->

- **Triển khai tại chỗ:** đóng gói container, cấu hình tách tenant; mở khóa tầng riêng tư tuyệt đối khi có mô hình nội bộ.

- **LLM và VLM nội bộ:** thêm adapter cho mô hình trọng số mở qua LLM Gateway (EP9). Khi có VLM nội bộ có thể đưa vào như bộ đọc thứ hai trong pipeline OCR, vẫn qua đẳng thức và Verifier; cờ runtime_vlm  mặc định tắt. Đổi cờ này phải đi kèm quyết định chính sách về tầng dữ liệu.

### 10.6 D13: So sánh nhiều doanh nghiệp và benchmark ngành

- **Cần:** kho đủ lớn trong từng ngành, định nghĩa nhóm so sánh, kiểm tra khả năng so sánh (cùng scope, cùng kỳ, cùng mẫu biểu).

- **Thêm vào:** công cụ mới như compare_companies  và get_peer_benchmark  (EP8), đọc từ kho chuẩn; kết quả luôn nêu cỡ mẫu và ngày tính.

- **Core đổi không:** không. Lớp phân tích vốn đã chỉ đọc từ kho chuẩn.

### 10.7 D14: IFRS hoặc báo cáo tiếng Anh

Thêm mẫu biểu qua EP3, nhãn hai ngôn ngữ, đẳng thức qua EP4. Cần ánh xạ giữa khái niệm IFRS và các mã chuẩn; một số khoản mục có thể không có mã chuẩn tương ứng, khi đó thêm mã chuẩn mới (dữ liệu, không phải mã). Không đổi core.

## 11. Quy trình khi buộc phải đổi core

Chỉ dùng khi một trong bốn điều kiện ở mục 2 xảy ra. Các tình huống có thể gặp: thêm thực thể dữ liệu thị trường (P/E, P/B); mở rộng ngôn ngữ biểu thức (nhóm theo nhãn, tổng có điều kiện); thêm loại sự kiện API; thêm kiểu thông điệp agent.

1. **Đánh giá:** xác nhận bằng văn bản rằng không thể làm bằng EP hiện có; ghi điều kiện nào trong bốn điều kiện đang đúng.

2. **Ghi quyết định kiến trúc (ADR) ngắn:** vấn đề, các phương án, tác động, rủi ro.

3. **Chọn cách ít xâm lấn nhất:** thêm trường hoặc thực thể *tùy chọn*; phiên bản hóa schema; không đổi nghĩa của trường cũ.

4. **Tương thích ngược:** giữ API /v1, thêm trường tùy chọn; nếu bắt buộc phá thì mở /v2 và có thời gian chuyển tiếp; viết kịch bản di chuyển dữ liệu.

5. **Kiểm thử:** chạy toàn bộ bộ vàng; **giá trị của 15 chỉ số lõi và các chỉ số đã phát hành phải giữ nguyên** trước và sau thay đổi; chạy bộ câu hỏi bẫy và kiểm thử bảo mật.

6. **Phát hành bằng cờ**, theo dõi, rồi mới bật mặc định.

7. **Cập nhật tài liệu** (hai báo cáo, OpenAPI, runbook).

<!-- Page 15 of 17 -->

## 12. Lộ trình mở rộng gợi ý

Thứ tự dưới đây dựa trên phụ thuộc giữa các hướng. Ước tính thô, phụ thuộc vào chuyên gia và dữ liệu có sẵn; cần hiệu chỉnh sau mỗi đợt.

| Đợt | Nội dung | Phụ thuộc | Ước tính |
| --- | --- | --- | --- |
| E1 | D4 tự phân loại ngành (nền); D1 Công nghệ (gói nhẹ nhất, kiểm chứng đường Sector Pack); D6 nhóm chỉ số cơ bản (chu kỳ chuyển đổi tiền, EBITDA, dòng tiền tự do) | Core hoàn thành; kho có nhãn ngành | 6 đến 8 tuần |
| E2 | D2 Logistics; D13 benchmark ngành; D11 giao diện bản đầu (song song) | E1; kho đủ lớn mỗi ngành | 8 đến 10 tuần |
| E3 | D3 Ngân hàng: khảo sát 1 đến 2 tuần, rồi triển khai | Kết luận khảo sát (mục 6.4) | 8 đến 12 tuần |
| E4 | D5 Multi-agent giai đoạn B | Có ít nhất 2 đến 3 gói ngành; bộ đánh giá Agent | 4 đến 6 tuần |
| E5 | D8, D9, D10, D12, D14, D7 theo nhu cầu và quyết định chính sách | Tùy hướng | Theo nhu cầu |

Quy tắc chung: mỗi đợt kết thúc bằng hồi quy trên bộ vàng, cập nhật bộ đánh giá và cập nhật hai báo cáo.

## Phụ lục. Danh sách kiểm tra

### A. Thêm một ngành

1. Hồ sơ ngành và chuyên gia duyệt. 2. Kho báo cáo của ngành (khuyến nghị 20 đến 30). 3. Ratio Registry: chỉ số bổ sung, ca tính tay. 4. Benchmark từ kho. 5. Tệp Sector Pack theo schema v1. 6. Cập nhật bộ phân loại ngành. 7. Bộ ca kiểm thử ngành. 8. Hồi quy trên kho và so với gói chung. 9. Chuyên gia duyệt, phát hành pack_id@phiên bản .

### B. Thêm một mẫu biểu mới

1. Nhận diện mẫu và phiên bản. 2. Ánh xạ mã số sang mã chuẩn (thêm mã chuẩn nếu cần).

3. Nhãn tiếng Việt và tiếng Anh. 4. Đẳng thức và quy tắc hợp lý trong Validation Rule Registry. 5. Luật áp dụng cho 15 chỉ số lõi. 6. Dữ liệu huấn luyện công khai cho bộ đọc bảng. 7. Bộ vàng và hồi quy. 8. Cập nhật Piotroski (N/A hoặc biến thể được duyệt).

<!-- Page 16 of 17 -->

### C. Thêm một chỉ số

1. Định nghĩa khai báo (công thức, dữ liệu, điều kiện áp dụng, cờ, ngưỡng, hướng tốt). 2. Ca tính tay trên báo cáo thật. 3. Chuyên gia duyệt. 4. Hồi quy phân bố giá trị trên kho. 5. experimental, rồi extended. 6. Gắn trọng số trong gói ngành nếu muốn tính điểm.

### D. Thêm một nhà cung cấp hoặc model

1. Adapter đúng giao diện LLM Gateway (chat, JSON theo schema, gọi công cụ, lỗi). 2. Cập nhật registry năng lực (ảnh, schema, gọi công cụ, ngữ cảnh, giới hạn). 3. Đọc và ghi lại điều khoản dữ liệu hiện hành. 4. Thêm vào chuỗi định tuyến của từng tác vụ, mặc định tắt. 5. Chạy bộ kiểm thử tương đương (parity) và bộ vàng. 6. Đặt ngân sách và cờ.

### E. Bật một cờ tính năng

1. Xác định tầng dữ liệu được phép. 2. Kiểm tra chính sách ẩn danh và hậu kiểm. 3. Chạy bộ đánh giá liên quan. 4. Bật cho một tenant thử, theo dõi trace và chi phí. 5. Mở rộng dần; luôn có thể tắt ngay.

*Kết thúc Báo cáo 2. Các giả định đánh dấu [GIẢ ĐỊNH] cần được kiểm tra khi bắt đầu hướng tương ứng.*

<!-- Page 17 of 17 -->
