# QUẢN LÝ DỰ ÁN — PREVIEW 2026-10-22

Đây là nhánh thử nghiệm. **Không đổi app chạy chính**, không merge vào main trước khi V nghiệm thu.

## Các liên kết
- Google Sheets PREVIEW: https://docs.google.com/spreadsheets/d/1gQZhu0bBE3yDR-R_cRw6YpUkOvgmdtWiaDn27_L3JRE/edit
- Google Sheets GỐC: https://docs.google.com/spreadsheets/d/129gDm3V1Gean0E9JvUXkf3euh7KGIeGwzREBFiboOc4/edit
- BACKUP Sheet: https://docs.google.com/spreadsheets/d/16WBAovGBQIV5YNFt_5IU5QdiMd3-tgVpVHiGvomqESI/edit
- GitHub backup: backup-001-20261022
- GitHub phát triển: preview-20261022

## Cấu trúc & quyền
- ADMIN: quản lý dự án, điểm, nhập hàng, phân bổ, đội, duyệt đăng ký, thống kê.
- LÃNH ĐẠO: chỉ xem thống kê + tìm đường.
- ĐỘI TRƯỞNG: chỉ báo cáo các mã nhiệm vụ gán đúng mã đội trong VAN_CHUYEN hoặc LAP_DAT; được tìm đường.
- THÀNH VIÊN: chỉ tìm đường (không được báo cáo).
- Khách chưa đăng nhập: đăng ký / tìm đường, không xem báo cáo và thống kê.

## Điều kiện báo cáo
- VC: bắt buộc ảnh, không bắt buộc GPS.
- KTV: bắt buộc ảnh + GPS.
- Giao & lắp: đội phải có đủ hai loại nhiệm vụ tại điểm, yêu cầu ảnh + GPS.
- Mỗi báo cáo lưu dấu thời gian máy chủ, Map, ảnh và mã báo cáo. Các nhiệm vụ được cập nhật trạng thái; nếu lỗi phải đối soát (không tuyên bố thành công giả).

## Những bước bắt buộc TRƯỚC khi chạy thử
1. Thu hồi/thay khóa Google Service Account và ImgBB cũ đã lộ trên repository công khai; KHÔNG dùng lại những khóa này.
2. Tạo Service Account mới với quyền tối thiểu; không commit JSON key lên GitHub.
3. Admin chia sẻ riêng Google Sheets PREVIEW và một thư mục ảnh Drive PREVIEW cho email Service Account mới với quyền Editor.
4. Cài dependencies trong \`requirements-preview.txt\`.
5. Trong Streamlit Cloud tạo một APP PREVIEW RIÊNG từ branch \`preview-20261022\`, entrypoint \`preview_app.py\`. Không đổi cấu hình app đang chạy.
6. Dùng ví dụ trong \`secrets.preview.example.toml\` để nhập **bí mật trong Streamlit Cloud Secrets**, không ghi thật vào repository.
7. Tạo một bộ tài khoản Admin, Lãnh đạo, Đội trưởng VC, Đội trưởng KTV, Thành viên. Mật khẩu/mã PIN phải lưu dạng PBKDF2 SHA256 với salt sinh ngẫu nhiên.
8. Kiểm thử \`KIEM_THU\` T01–T12 trên Preview; test hai đội A/B để chắc chắn A không báo cáo việc của B.
9. Chỉ sau V duyệt mới cân nhắc chuyển app và dữ liệu sản xuất sang phiên bản mới.

## Hạn chế chưa nghiệm thu
- Không có connector trực tiếp điều khiển Streamlit Cloud app, nên chưa tạo được URL PREVIEW.
- Kết nối Google Service Account mới chưa được V cấp (và không được dùng khóa cũ), nên chưa chạy test ghi dữ liệu/ảnh thực.
- Chưa kiểm thử đồng thời nhiều Admin phân bổ; việc ghi đa sheet không có giao dịch atomic. Cần bước đối soát trước vận hành.
- Báo cáo chọn SL thực tế hiện lấy mặc định theo số phân bổ; các trường thiếu/lệch và phục hồi giao dịch cần nghiệm thu thêm.
- Chức năng "làm sạch" dữ liệu nghiệp vụ đã cố ý KHÔNG đưa vào bản thử để tránh xóa nhầm. Phải chốt chính sách reset riêng.
- Google Sheets gốc, API Apps Script hiện tại, app production không được thay đổi.


## Ghi nhớ đăng nhập trên thiết bị riêng (bản PREVIEW)
- Tài khoản tự chọn ô **Ghi nhớ đăng nhập trên thiết bị này (30 ngày)** ở màn hình đăng nhập.
- **Bắt buộc** đặt riêng trong Streamlit Secrets: `remember_login_secret = "<chuỗi ngẫu nhiên tối thiểu 32 ký tự>"`.
- Không sử dụng PIN, khóa Google Service Account, hoặc mật khẩu dùng chung để làm khóa ký. Không chia sẻ Secrets/chụp ảnh vùng này.
- Cookie có chữ ký HMAC-SHA256, HTTPS Secure, SameSite=Strict và thời hạn 30 ngày; chỉ lưu tên tài khoản, thời hạn, dấu vân tay kiểm tra phiên, **không chứa PIN/mật khẩu**.
- Không chọn trên máy dùng chung; bấm Đăng xuất sẽ xóa cookie của thiết bị này.
- Thay đổi PIN/hash, quyền vai trò, mã đội hoặc khóa ký phiên sẽ làm cookie ghi nhớ cũ mất hiệu lực khi kiểm tra.
- Đây là lưu đăng nhập tùy chọn trong PREVIEW, cần kiểm thử thực tế trên Android/iOS/Chrome, đặc biệt việc tự khôi phục phiên sau tải lại trang.
