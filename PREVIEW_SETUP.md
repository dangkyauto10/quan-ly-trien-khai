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


## Phân bổ hàng loạt đa SKU — PREVIEW
- Mở `📦 Phân bổ`, chọn `Hàng loạt – định mức chung + ngoại lệ`.
- SKU tự nhận từ `NHAP_KHO` của dự án. Mỗi SKU có định mức chung riêng.
- Mặc định chọn tất cả địa điểm hoạt động của dự án; bỏ bớt nếu chỉ cần phân bổ một phần.
- Chọn các địa điểm ngoại lệ rồi sửa **từng SKU** trong bảng, hoặc tải file Excel .xlsx với `Mã điểm` và các cột có tiêu đề là mã SKU chính xác. Ô Excel trống giữ định mức chung; ô `0` nghĩa là không cấp SKU đó.
- Phần `Đối soát` hiện tổng dự kiến và tồn còn lại theo SKU, kèm toàn bộ ma trận và nút tải Excel xem trước.
- Chỉ sau khi ADMIN đánh dấu xác nhận, ứng dụng mới đọc lại dữ liệu trực tiếp và đối chiếu kho. Một lần gọi Google Sheets `spreadsheets.batchUpdate` ghi đồng thời `DM_CHUAN`, `KHO_PHAN_BO`, `VAN_CHUYEN`, `LAP_DAT`, `TIEN_DO` và `NHAT_KY_HE_THONG`.
- `DM_CHUAN` giữ **nhật ký phân bổ chuẩn hóa (mỗi địa điểm × SKU một dòng)**, còn ma trận đa SKU cho phép chỉnh và xem trước ở app/Excel. Không thay đổi tiêu đề cột của các sheet đã có.
- Một SKU tại cùng địa điểm không được phân bổ lại bằng chức năng này. Nếu cần cấp bổ sung SKU đã có, phải có quy trình bổ sung riêng.
- Không cho ghi vượt tồn kho, số lượng âm, trùng điểm/SKU, hoặc vượt 1.800 dòng/đợt. Với dự án rất lớn có thể chọn địa điểm theo nhiều đợt khác nhau.
- Kiểm thử thực tế tối thiểu: 2 bộ TB-TEST01, chọn 1 địa điểm và phân bổ 1 bộ, đối chiếu 6 sheet; khi đã nghiệm thu thì kiểm tra các bộ SKU phức tạp trên dữ liệu giả trước khi dùng thật.
- Trước khi xác nhận, yêu cầu **chỉ một Admin thao tác phân bổ mỗi lúc**, vì Google Sheets không phải cơ sở dữ liệu khóa giao dịch đồng thời. Nếu xảy ra lỗi không rõ kết quả, không bấm lại liên tục; đối chiếu mã đợt trong các sheet.

## Phân bổ theo bộ định mức và nhóm điểm theo hồ sơ thầu (PREVIEW)
- Mỗi nhóm địa điểm nhận cùng một bộ mặt hàng / định mức trên mỗi điểm.
- ADMIN nhập SL/điểm cho từng SKU; SKU không cấp để 0.
- Chọn các điểm cùng định mức bằng ô tìm tên/mã điểm, dán danh sách mỗi dòng một điểm, nạp Excel cột Mã điểm/Tên xã/phường/đơn vị, hoặc chọn tất cả điểm chưa phân bổ.
- Chỉ nhận tên/mã điểm đang hoạt động đúng dự án, không trùng; tên sai, trùng tên hoặc ngoại dự án không được tự đoán.
- Bảng đối soát tính SL/điểm × số điểm; hiển thị SKU, ĐVT, tổng cần, tồn khả dụng, ngoại lệ và ma trận chi tiết.
- Thay đổi SKU/định mức/nhóm địa điểm thì xác nhận cũ mất hiệu lực.
- DM_CHUAN hiện là nhật ký phân bổ, KHÔNG phải danh mục định mức độc lập lấy từ hồ sơ thầu. ADMIN cần đối chiếu bản gốc trước khi ghi.
- Giới hạn 3.000 dòng điểm×SKU/đợt trong PREVIEW; nhiều hơn thì chia nhóm, không cho vượt tồn hoặc phân bổ trùng.
- Phân bổ khởi tạo nhiệm vụ VC/LĐ chứ chưa phải xuất kho hay đã giao hàng. Chỉ một ADMIN phân bổ tại một thời điểm; dữ liệu PREVIEW cần nghiệm thu trước sản xuất.

## Truy cập nhanh cho LÃNH ĐẠO — chỉ mật khẩu (PREVIEW)

- Trang chưa đăng nhập có nút lớn **📊 LÃNH ĐẠO – XEM BÁO CÁO**. Bấm nút → nhập **Mật khẩu Lãnh đạo** → vào thẳng báo cáo tiến độ chỉ đọc, không gõ mã tài khoản, không chọn chức năng.
- Trên form có dấu tích **Ghi nhớ đăng nhập trên thiết bị này (30 ngày)**. Chỉ sử dụng thiết bị cá nhân; dùng cơ chế cookie ký HMAC hiện có, KHÔNG ghi PIN/mật khẩu trong cookie.
- Cần tối thiểu một tài khoản riêng `[accounts.leader_preview]` với `role = "LANH_DAO"`, salt và PBKDF2 hash mạnh trong **Streamlit Secrets**. Không tạo quyền LÃNH ĐẠO bằng cách dùng tài khoản ADMIN, không nhúng mã PIN hay hash vào repository.
- Nếu chỉ có **một** tài khoản LANH_DAO trong Secrets, app tự tìm đúng tài khoản; nếu có nhiều tài khoản lãnh đạo, cấu hình thêm `leader_login_username = "leader_preview"` tại Secrets để chọn tài khoản dùng trên nút. Không có tài khoản hợp lệ thì nút chỉ thông báo cần cấu hình, không cấp quyền.
- Ghi nhớ chỉ hoạt động khi đã có `remember_login_secret` đủ dài; việc đổi mật khẩu, salt, vai trò hoặc khóa ký sẽ vô hiệu cookie cũ.
- Thử sai mật khẩu bị giới hạn theo cơ chế đăng nhập hiện có. LÃNH ĐẠO không có tùy chọn nhập kho, phân bổ, gán đội, duyệt hồ sơ hoặc báo cáo thay đội trưởng.
- Có nút **ĐĂNG XUẤT** xóa cookie ghi nhớ; app sẽ yêu cầu mật khẩu ở lần tiếp theo.
- Cần kiểm tra riêng trên iPhone/Android và máy tính: nhập mật khẩu một lần, bật Ghi nhớ, đóng tab và mở lại phải vào thẳng báo cáo; khi đăng xuất phải yêu cầu mật khẩu lại. Không coi CI là đã kiểm thử trình duyệt thực.



## Bàn giao TẬP KẾT cho đội KTV (PREVIEW, Hà Giang cũ)

- Có **hai hình thức giao**: (a) VC giao thẳng tận xã/đơn vị; (b) VC tập kết gộp hàng của nhiều xã theo địa bàn hợp đồng, KTV ký nhận tại một địa điểm đã thống nhất. Địa bàn có thể dùng địa danh hành chính cũ, ví dụ Đồng Văn / Yên Minh / Quản Bạ; phải chọn chính xác các xã/đơn vị theo hợp đồng, không suy diễn chỉ từ tên huyện cũ.
- ADMIN mở **📦 Bàn giao tập kết**, chọn dự án, đội trưởng KTV, nhiều xã thuộc những nhiệm vụ LĐ đã gán; phần mềm cộng tất cả SKU và SL theo định mức từng xã (KHO_PHAN_BO và LAP_DAT). Chưa có đội hoặc chưa gán địa bàn thì chưa lập biên bản.
- ADMIN nhập vị trí tập kết, người VC giao, số biên bản giấy, tải ảnh có **chữ ký bên giao và bên nhận KTV**, xác nhận kiểm đếm đủ. Nếu thiếu SL, chưa ghi trạng thái đủ; chia chuyến hoặc đối soát sau. Không chấp nhận ghi đúp các SKU đã tập kết hoặc đã giao tận xã/đã lắp.
- Sau nút xác nhận, một giao dịch PREVIEW ghi nhật ký **BAN_GIAO_TAP_KET**, mỗi xã × SKU một dòng với chung mã biên bản/ảnh và tên người KTV nhận. Bảng này KHÔNG xóa hay thay đổi KHO_PHAN_BO, VAN_CHUYEN, LAP_DAT. Đây là nhật ký giao tập kết, chưa phải phiếu xuất kho hay chứng nhận lắp xong.
- KTV mở **👷 ĐỘI TRƯỞNG – BÁO CÁO**, chọn nhóm **📦 1. KIỂM TRA HÀNG VC / TẬP KẾT** để xem chỉ các xã được gán cho mình, SL VC giao tận xã và SL KTV đã nhận tại điểm tập kết được tách riêng. Trạng thái **Sẵn sàng lắp (tập kết)** nghĩa là biên bản ký nhận đủ SL của từng SKU trong hợp đồng; **KHÔNG** khẳng định đã giao tận xã.
- KTV đi đến từng xã, mở **📝 2. BÁO CÁO GIAO HÀNG / LẮP ĐẶT**: chọn xã, nhập ảnh+GPS theo quy định. App chặn xác nhận LĐ nếu không có VC giao trực tiếp đủ hoặc biên bản tập kết đủ đã ghi. Khi đã báo LĐ, tiến độ Lãnh đạo tính riêng VC giao tận xã, KTV nhận ở điểm tập kết, và xã đã lắp xong.
- Bố cục điện thoại: mỗi nhóm thành phần bấm mở/thu gọn, bảng trong vùng cuộn, không dàn dài 135–500 địa điểm trên cùng một trang. Tên đội trưởng hiện cho người dùng, mã đội chỉ lưu nội bộ để xác thực quyền.
- **Bắt buộc nghiệp vụ**: biên bản giấy ký cả hai bên mới là chứng cứ nhận hàng. Nếu thiếu, mất, sửa chứng từ hoặc thực nhận lệch định mức phải đối soát, không giả tạo trạng thái hoàn tất. Khi vận hành thật cần thêm phiếu xuất kho vật lý, sổ hàng KTV chuyển từ điểm tập kết tới từng xã và xử lý bồi hoàn/thiếu hàng.
- PREVIEW mới chỉ qua unit test/compile GitHub Actions. Chưa nghiệm thu trực tiếp trên iPhone/Android hay luồng ảnh ký nhận ngoài thực địa; tuyệt đối không đổi PRODUCTION.


## Biểu tượng app trên màn hình điện thoại (PREVIEW)

- Trên trang công khai có phần thu gọn **📲 ĐƯA APP RA MÀN HÌNH ĐIỆN THOẠI**; ngay sau khi người dùng tự gửi đăng ký thành công, phần hướng dẫn được mở sẵn (iPhone và Android ở hai thẻ riêng).
- iPhone: mở URL app bằng **Safari** (không dùng trình duyệt nhúng Zalo), chọn **Chia sẻ → Thêm vào Màn hình chính → Thêm**; bật **Mở dưới dạng ứng dụng web** nếu khả dụng. Android: mở bằng **Chrome → ⋮ → Cài đặt và tạo lối tắt / Thêm vào màn hình chính → Tạo lối tắt / Thêm** (tên menu tùy phiên bản).
- Chỉ chính người dùng có thể xác nhận việc thêm biểu tượng; app không có quyền tự động cài biểu tượng sau đăng ký. Biểu tượng tạo ra là lối tắt web hoặc web app tùy hệ điều hành, **không phải app phát hành qua App Store/Google Play**. Hiện logo/tên khi ghim từ Streamlit Cloud có thể vẫn chịu định dạng/biểu tượng mặc định, cần kiểm thử trên thiết bị thật trước khi hứa logo riêng.
- Lối tắt không có nghĩa đã duyệt hay có quyền báo cáo. ADMIN vẫn duyệt, cấp mật khẩu và gán nhiệm vụ. Tài khoản đã cấp có thể chọn **Ghi nhớ đăng nhập (30 ngày)** trên thiết bị cá nhân, không lưu mật khẩu trong cookie.
- Chỉ cập nhật mã nguồn PREVIEW và hướng dẫn sau khi đăng ký. Không thay đổi dữ liệu dự án, quyền, Secrets, đường dẫn hay app production.

## 📖 Hướng dẫn sử dụng công khai + thực hành thử trên điện thoại

- Màn hình đầu PREVIEW có nút nhỏ **📖 Hướng dẫn sử dụng** ngay dưới tiêu đề TV. Mọi vai trò đều mở được, kể cả người **chưa đăng nhập**. Bấm mở trang hướng dẫn ngay bên trong app, có nút **← Về app**.
- Đường dẫn chia sẻ độc lập: https://quan-ly-trien-khai-qfzumkrq7escxbxpv9v9tr.streamlit.app/?guide=1 (gửi riêng vào nhóm Zalo hoặc mã QR ngoài app nếu cần). Không tạo website mới, không yêu cầu đăng nhập. Đây là đường dẫn của **bản PREVIEW**, không phải production.
- Sau khi người dùng gửi đăng ký thành công, app cũng hiện nút **📖 XEM HƯỚNG DẪN & THỰC HÀNH THỬ**, cạnh hướng dẫn ghim biểu tượng điện thoại.
- Nội dung đúng luồng chức năng hiện tại: **đội trưởng đăng ký → ADMIN duyệt, cấp tài khoản, gán địa bàn → đội trưởng vào theo họ tên + mật khẩu → VC báo giao đủ kèm ảnh → KTV xem hàng VC/tập kết đủ từng SKU → KTV báo lắp từng điểm kèm ảnh/GPS**. Có hướng dẫn cho VC+LĐ, biên bản giấy có chữ ký tại điểm tập kết, Lãnh đạo đọc báo cáo, ghim app lên màn hình chính.
- Mục **🧪 Thực hành thử** có 3 bài: gửi đăng ký giả lập, VC kiểm tra đủ hàng/ảnh, KTV kiểm tra hàng/ảnh/GPS. Mọi nút thực hành chỉ chạy local Streamlit, **không đọc/ghi Google Sheets**, không lưu ảnh hay sửa DA880. Đây không phải môi trường sandbox để gửi báo cáo thật; muốn báo cáo thật phải ra màn hình đội trưởng sau khi đã có quyền.
- Người dùng mới tham khảo tài liệu khi chưa duyệt, không tự cấp quyền. Mục hướng dẫn không cho xem dữ liệu tổng hợp ADMIN/LÃNH ĐẠO hoặc dữ liệu riêng của đội khác.
- Chưa có thử nghiệm UI thực tế trên Safari iPhone/Chrome Android. CI kiểm tra cấu trúc/không có backend write, nhưng V vẫn cần nghiệm thu khả năng bấm cuộn và font trên thiết bị.


## 🔐 ADMIN cấp mật khẩu Đội trưởng ngay trong app (PREVIEW)

- **Trình tự:** Đội trưởng gửi đăng ký → ADMIN mở **👥 Đăng ký & quản lý đội** để duyệt hồ sơ → mở **🔐 CẤP / ĐẶT LẠI MẬT KHẨU ĐỘI TRƯỞNG** → chọn **họ tên + dự án + chuyên môn** của người được duyệt → đánh dấu xác nhận gửi riêng → bấm **CẤP MẬT KHẨU**. ADMIN sao chép mật khẩu mạnh 18 ký tự **chỉ hiện một lần**, gửi riêng cho đội trưởng; KHÔNG đăng ảnh/chụp nhóm, không dùng chung mã.
- KTV/VC trên điện thoại bấm **👷 ĐỘI TRƯỞNG – BÁO CÁO**, nhập **họ và tên đã duyệt + mật khẩu riêng**; không cần biết mã đội/mã tài khoản ngẫu nhiên. Sau khi đăng nhập được phép xem/báo cáo **chỉ các nhiệm vụ đã gán đúng mã đội**; việc cấp mật khẩu không tự gán địa điểm, hàng hóa hay nhiệm vụ.
- Nếu quên mã, ADMIN chọn người đã có tài khoản và bấm **ĐẶT LẠI MẬT KHẨU**. Mã cũ và cookie ghi nhớ bằng mật khẩu cũ tự mất hiệu lực khi tra lại vân tay hash (độ trễ cache dữ liệu Preview khoảng 15 giây). Ghi nhớ 30 ngày cần Secret ký phiên đã cấu hình.
- Tạo bảng TAI_KHOAN_DOI chỉ trên Google Sheets PREVIEW. **KHÔNG lưu mật khẩu nguyên văn**: chỉ ghi mã tài khoản nội bộ, mã đội, dự án, DOI_TRUONG, salt ngẫu nhiên, PBKDF2-HMAC-SHA256 hash (390000 vòng), trạng thái, thời gian và ADMIN thao tác. Mật khẩu không ghi trong GitHub, nhật ký app, Sheets, cookie.
- Giữ tài khoản **ADMIN và LÃNH ĐẠO** riêng trong **Streamlit Secrets**, **không thể tự cấp quyền ADMIN/LANH_DAO** qua bảng tài khoản. Dữ liệu bảng cần đúng mã đội hoạt động, dự án, vai trò và định dạng hash; các hàng bất hợp lệ/trùng tự từ chối. Nếu đội đã có tài khoản trong Secrets thì ADMIN không được cấp thêm tài khoản Sheet để tránh xung đột.
- **QUAN TRỌNG BẢO MẬT:** Bảng TAI_KHOAN_DOI phải do ADMIN và Service Account có quyền, **không chia sẻ quyền Editor Google Sheets cho đội trưởng/thành viên**; người chỉnh sửa bảng hash có thể giả mạo tài khoản đội trưởng dù không biết mật khẩu gốc. Việc dùng Google Sheet làm nơi lưu xác thực phù hợp **chỉ trong PREVIEW**; khi đưa vào vận hành thật cần kho tài khoản và quy trình quản lý định danh bảo mật hơn.
- Nếu cùng họ tên ở hai hồ sơ đang hoạt động, chặn cấp mật khẩu mới cho đến khi ADMIN xác minh và xử lý trùng tên. Không cho đội trưởng tự nhập mã đội để đoán quyền. Khi bản ghi cấp mật khẩu thất bại hoặc không rõ kết quả, **không gửi mã**; ADMIN kiểm tra trạng thái trên app trước khi thử lại.
- Chưa tích hợp gửi mật khẩu qua Zalo/SMS tự động, chưa có trang đổi mật khẩu tự phục vụ. ADMIN gửi mã **bằng tin riêng** và cần nghiệm thu luồng trên điện thoại với đội trưởng trước vận hành.


## 🔐 Đội trưởng TỰ ĐẶT MẬT KHẨU khi đăng ký (PREVIEW)

- **Luồng mới:** Đội trưởng mở **📝 Đăng ký tham gia**, nhập họ tên/số điện thoại/dự án/địa bàn, rồi tự nhập **Mật khẩu tự chọn** và **Nhập lại mật khẩu**. Gợi ý dùng một cụm từ dễ nhớ **10–128 ký tự có chữ và số**, tránh tên, số điện thoại và các chuỗi dễ đoán. Khi xác nhận, app **không ghi mật khẩu nguyên văn** vào bất kỳ bảng nào.
- Trong **cùng một lần ghi Google Sheets**, hệ thống tạo bản ghi DANG_KY_THANH_VIEN trạng thái Chờ duyệt và MAT_KHAU_DANG_KY gồm mã hồ sơ/dự án + salt ngẫu nhiên + mã băm PBKDF2-SHA256 (390.000 vòng) + trạng thái Chờ duyệt. Chưa có tài khoản đăng nhập và chưa gán nhiệm vụ.
- ADMIN vào **👥 Đăng ký & quản lý đội**, chọn **Đã duyệt** sau khi đối chiếu hồ sơ. Cùng một lệnh Sheets, app tạo/ghép đội, tạo tài khoản DOI_TRUONG trong bảng TAI_KHOAN_DOI với **mã băm do chính người dùng đã tạo**, cập nhật hồ sơ Đã duyệt và dọn salt/hash khỏi bản chờ, đánh dấu Đã kích hoạt. Sau đó ADMIN gán địa bàn; người dùng đăng nhập bằng **họ tên + mật khẩu đã chọn**. ADMIN không cần gửi mật khẩu riêng.
- Nếu chọn **Từ chối**, mã băm trong MAT_KHAU_DANG_KY được xóa, đánh dấu Đã từ chối, không tạo tài khoản. Nếu hash chờ bị thiếu/trùng/sai dự án, trạng thái không thể kích hoạt và cần ADMIN đối soát; không cấp quyền mặc định.
- **Hồ sơ cũ trước tính năng** hoặc đăng ký hộ không có mật khẩu chờ vẫn được duyệt bình thường nhưng ADMIN phải dùng mục **CẤP / ĐẶT LẠI MẬT KHẨU**. Người dùng muốn thay mật khẩu sau đó phải nhờ ADMIN; chưa có tự đặt lại.
- **Quyền:** tài khoản ADMIN và LÃNH ĐẠO chỉ từ Streamlit Secrets; bảng tự đăng ký tuyệt đối không thể tạo quyền này. Cần giữ Google Sheet chứa mã băm chỉ cho ADMIN và service account, không cấp Editor/view nếu không có nhu cầu. Đây là triển khai thử trên PREVIEW, chưa phải hệ thống quản lý định danh phù hợp cho production.
- **Lối tắt điện thoại:** trang đăng ký có mục bấm hướng dẫn 2 bước: iPhone (Zalo → Safari → Chia sẻ → Thêm vào màn hình chính); Android (Zalo → Chrome → ⋮ → Cài đặt và tạo lối tắt → Thêm). Các bước do chính chủ điện thoại xác nhận; website không thể tự cài icon.
- Chưa nghiệm thu thực tế trên điện thoại và chưa có chức năng tự gửi tin nhắn xác minh số điện thoại. ADMIN **phải kiểm tra người đăng ký** trước khi duyệt. Tuyệt đối không gửi hay lưu mật khẩu rõ trong ảnh Zalo, trong Sheets hoặc nhật ký GitHub.

### Bổ sung PREVIEW: mật khẩu tự chọn dễ nhớ (10 ký tự) và nhập hộ

- Khi đội trưởng đăng ký mới trên điện thoại, nhập mật khẩu **tự chọn từ 10–128 ký tự, có chữ và số**, nhập lần hai để xác nhận. Mật khẩu bị từ chối nếu quá ngắn, trùng họ tên/số điện thoại hoặc chứa các mẫu dễ đoán. Hệ thống không ép dùng mã ngẫu nhiên 18 ký tự.
- Với người **đã đăng ký / đã được duyệt trước phiên bản này**, không cho nộp lại hồ sơ để đổi mật khẩu. ADMIN vào **👥 Đăng ký & quản lý đội → 🔐 CẤP / ĐẶT LẠI MẬT KHẨU**, chọn người, chọn **Đội trưởng đề nghị / ADMIN nhập hộ** (hoặc **Hệ thống tự tạo**), nhập mật khẩu theo đề nghị hai lần rồi xác nhận. Mật khẩu cũ và phiên ghi nhớ cũ bị vô hiệu hóa sau thay đổi.
- Chỉ mã băm/salt được lưu ở TAI_KHOAN_DOI. Mật khẩu rõ không gửi lên Google Sheets, không ghi nhật ký, không nhúng mã nguồn. Giữ kiểm tra quyền ADMIN và trạng thái đội đã duyệt.


## Tự thu hồi quyền/địa bàn khi xóa hồ sơ đăng ký đội trưởng (PREVIEW)

- Bảng LIEN_KET_DANG_KY_DOI ghi **Mã đăng ký → Mã đội → Dự án** trong **cùng giao dịch xét duyệt** khi app TẠO một đội mới từ hồ sơ. Đội đã có sẵn/tạo tay, hoặc hồ sơ cũ thiếu mã dự án, KHÔNG được suy đoán liên kết và không bị xóa tự động. Điều này tránh xóa nhầm 7 đội thử nghiệm còn trong QUAN_LY_DOI khi V xóa sạch DANG_KY_THANH_VIEN trước ngày bổ sung chức năng.
- Khi một hồ sơ đã duyệt có liên kết bị xóa khỏi DANG_KY_THANH_VIEN trực tiếp bằng Google Sheets, **người dùng đội đó bị từ chối đăng nhập ở lần xác thực tiếp theo**. ADMIN mở/tải lại PREVIEW sẽ tự đối chiếu bản ghi liên kết và thực hiện gỡ các quan hệ, không cần nhấn nút xóa riêng.
- Trường hợp chưa có báo cáo thực: QUAN_LY_DOI đổi Trạng thái sang Đã gỡ (không hard-delete dòng để giữ lịch sử), TAI_KHOAN_DOI đổi sang Đã gỡ, các nhiệm vụ VAN_CHUYEN/LAP_DAT còn Chưa giao/Chưa lắp và chưa có chứng từ sẽ được xóa **Mã đội VC/Mã đội KTV** (trả về Chờ phân công). Số lượng SKU tại mỗi điểm vẫn còn trong nhiệm vụ để giao cho đội mới.
- Trường hợp có báo cáo, phiếu giao/lắp, hoặc biên bản KTV đã ký tại điểm tập kết: tài khoản bị khóa, đội chuyển Cần đối soát; nhiệm vụ chưa thực hiện được thu hồi, nhưng nhiệm vụ đã làm và chứng từ **KHÔNG bị xóa hay đổi số lượng**.
- KHO_PHAN_BO là **phân bổ HÀNG CHO XÃ theo hợp đồng**, không phải cho đội trưởng. Xóa người phụ trách **không được hoàn kho** hay xóa định mức phân bổ của xã, không đổi NHAP_KHO, BAO_CAO_TRIEN_KHAI hoặc chứng cứ giao nhận; chỉ thay đổi phân công nhiệm vụ.
- Đối soát tự động là **event-driven theo lượt mở/tải lại app ADMIN**, chưa có trigger Google Sheets độc lập chạy ngay tức thì khi một ô/row bị xóa lúc app không hoạt động. Tối đa khoảng 15 giây TTL cache ở bước đăng nhập; khi ADMIN mở app có đọc trực tiếp Sheets và thực hiện batch update. Nếu Google Sheets mất kết nối, phải kiểm tra lại sau, không hứa gỡ tức thì.
- Bảng DANG_KY_THANH_VIEN đã được người dùng phục hồi từ lịch sử, hiện có 9 hồ sơ (6 đã duyệt, 3 từ chối). Ngày 23/10/2026 đã **đối chiếu lại chính xác 5 liên kết cũ** bằng mã hồ sơ + mã đội + dự án + họ tên + điện thoại + chuyên môn + ghi chú `Duyệt từ <mã đăng ký>` và lưu vào LIEN_KET_DANG_KY_DOI. Không xóa đội hay nhiệm vụ trong bước này. Hai đội còn lại không đủ dữ liệu gắn liên kết chắc chắn (trong đó một hồ sơ cũ thiếu mã dự án), nên tiếp tục được giữ để đối soát khi dọn TEST. Không dùng thao tác xóa toàn bộ hàng để đặt lại nhân sự.
- Chỉ PREVIEW được cập nhật; không ghi vào sheet production. CI kiểm thử gắn mã đội, thu hồi quyền, thu hồi nhiệm vụ chưa làm, bảo toàn chứng từ và số liệu kho. Cần V nghiệm thu trên bản thử với một đăng ký mới có liên kết.



## Kiểm thử nghiệp vụ vòng đời đội trưởng — TEST ONLY, 23/10/2026

**Nguyên tắc:** Dữ liệu thử để phát hiện lỗi giao việc, trách nhiệm hàng, chứng từ và quyền truy cập. Dữ liệu TEST không phải hồ sơ thật; sau kiểm thử mới đặt lại. Trong kiểm thử, vẫn phải giữ chứng từ ký nhận đã phát sinh cho mục đích đối soát.

**Màn hình ADMIN mới:** 👥 Đăng ký & quản lý đội → 🔎 XEM ẢNH HƯỞNG KHI XÓA ĐỘI TRƯỞNG. Chọn đội đã liên kết hồ sơ, xem điểm/SKU có thể trả chờ phân công, điểm KTV đang giữ hàng, điểm VC đã bàn giao tập kết, và chứng từ cũ chưa xác định VC. Màn này chỉ xem, không xóa.

**Ma trận nghiệp vụ chấp nhận:**
- Chưa giao/nhận/lắp: xóa hồ sơ có liên kết → khóa quyền đội, bỏ mã đội khỏi nhiệm vụ VC/LD chưa thực hiện → ADMIN giao lại mà không nhập kho/phân bổ lần hai.
- VC đã giao một phần hoặc có báo cáo: giữ nhiệm vụ và chứng từ đã ghi, chuyển Cần đối soát; không coi như giao đủ.
- VC đã giao đủ tận xã: giữ chứng cứ giao tận xã; không giao VC lại cho cùng SKU.
- VC giao gộp cho KTV tại tập kết: biên bản phải có mã đội VC và mã đội KTV, khớp nhiệm vụ VC của từng xã/SKU; KHÔNG tính là giao tận xã.
- KTV đã nhận hàng tập kết: không tự bỏ nhiệm vụ lắp tại SKU đang giữ hàng; cần bàn giao hàng thực tế và đối soát chứng từ rồi mới đổi KTV.
- Biên bản tập kết cũ không có mã đội VC: giữ nhiệm vụ VC tương ứng để đối soát; không đoán đội VC chỉ từ tên người ký rồi giao lại.
- Đã lắp xong: giữ tiến độ và ảnh/GPS, chỉ thu hồi quyền đội và công việc còn dang dở.
- Chưa duyệt/từ chối: không có tài khoản hoạt động để thu hồi; không cấp quyền trước duyệt.
- Trùng tên / 500 điểm × 5 SKU / đổi mật khẩu: kiểm tra xung đột, số lượng, quyền theo dự án.

**Bảng ký nhận tập kết PREVIEW** bổ sung cột U "Mã đội VC giao" sau 20 cột cũ. Phiếu mới chỉ lưu khi ADMIN chọn đúng đội VC hoạt động và mọi dòng VC ở các xã/SKU được giao cho đúng đội đó, chưa báo hoàn tất và số lượng khớp định mức. Từ chối trường hợp thiếu nhiệm vụ, thuộc VC khác, đã giao một phần hoặc sai SL. Các biên bản cũ thiếu mã VC không tự được điền; cần kiểm tra trước khi tái phân công.

**Giới hạn kiểm thử:** Dọn liên kết xảy ra khi ADMIN mở/làm mới app, không có trigger tự chạy ở Google Sheets. Hoàn thành TEST cần lưu snapshot rồi mới dọn dữ liệu. Chưa có nghiệp vụ xuất kho vật lý và chuyển giao tồn hàng từ KTV cũ sang KTV mới hoàn chỉnh; đây là một bước bàn giao riêng, không suy diễn từ trạng thái phân bổ.
