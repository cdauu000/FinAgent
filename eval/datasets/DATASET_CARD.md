# Corpus FinAgent tại cuối lượt Phase 0

Chỉ kiểm kê các tệp thật trong `data/public_reports/`. Hiện có một PDF FPT, SHA256 `11c9709914cdc5f1561f47045283598c359f7466f94e5ffbc21893e28b0315fa`; không tải thêm, sao chép, dựng báo cáo tổng hợp hoặc dùng fixture để đạt hạn ngạch.

[Manifest](manifest.json) ghi path/hash/nguồn owner_supplied, entity/group FPT, scope riêng, kỳ Q1/2026,28 trang và missing fields. Ngày2026-04-24 từ tên file chỉ là **filename_date_hint**, không phải source_date đã xác minh. Chưa có URL công bố gốc/ngày có chứng cứ/terms review; effective tier giữ private. Không suy quyền training/teacher từ tên thư mục public_reports.

Hiện **1 report có entry;0 manifest đầy đủ nguồn/ngày/điều khoản;0 full-gold approval**. Chưa đạt≥30 manifest và≥10 nhãn vàng Phase0. Ngành và nhãn native/scan/hybrid/độ khó theo trang còn unknown; không bịa strata để đạt đa dạng.

[Nhãn FPT dự thảo](fpt-q1-2026-draft.json) có80 quan sát số theo TEST_PLAN§3.1 đã đối chiếu từ PDF ở Bước0. Các ô giữ kỳ so sánh stock31/12/2025 khác flowQ1/2025, mã dạng string và số VND dạng string. B02-23 current/prior có hai bbox chọn trên [crop thật](../../docs/evidence/fpt_q1_2026/b02-code23-digits.png), tọa độ pixel của raster400DPI trang vật lý6. Các ô khác chưa có bbox nên giữ null; chưa đủ gold OCR, chưa có approver_ref. Chỉ một subset bbox không thay full-document approval.

Giữ SOURCE_INCONSISTENCY cổ phiếu2025, CLASSIFICATION_DIFFERENCE_UNRESOLVED TM18/CF04 và SOURCE_FORMULA_LABEL_INCOMPLETE. Không sửa97.623.991.644, không coi150.117 là bridge đã chứng minh; kỳ trước còn residual90 đồng. Không ghi dữ liệu canonical thật vào DB trong Phase0, nên cửa sổ canonical/1 chưa đóng.

[Split](split.json) đặt FPT vào visible_regression, không phải test holdout. Chưa có train/dev/test entities; group phải cùng split khi bổ sung dữ liệu. Duplicate hash, path escape, hash mismatch, group leakage và gold approval/geometry không hợp lệ bị chặn bởi corpus tooling. Cohort hash ràng buộc cả manifest và bytes nhãn để thay nhãn không giữ nguyên cohort.

Corpus/gold/split DTO mới là additive tooling contracts; [JSON Schemas dự thảo](../../schemas/tooling/split-1.validation.json) nằm ở schemas/tooling, chưa thuộc14 nhóm đóng băng. Split được kiểm với entry/group/holdout và bind bytes vào cohort hash; cần review đầy đủ trước official corpus release. Harness không train, không gửi teacher, không chạy OCR/analytics để gán số đo. Unit fixtures không đi vào manifest/cỡ mẫu thật.
