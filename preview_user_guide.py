"""Public, read-only handbook for TDV PREVIEW field participants.

This page uses no Google Sheets/Drive, login, or backend writes.
Every exercise is an illustrative, local Streamlit interaction only.
"""
GUIDE_URL = "https://quan-ly-trien-khai-qfzumkrq7escxbxpv9v9tr.streamlit.app/?guide=1"

TOPICS = (
    "📝 Đăng ký tham gia",
    "🔐 Đăng nhập & icon điện thoại",
    "🚚 Đội VC – báo giao hàng",
    "🔧 Đội KTV – báo lắp đặt",
    "📦 VC + LĐ và hàng tập kết",
    "📊 Lãnh đạo / ADMIN",
    "🧪 Thực hành thử (không lưu dữ liệu)",
)

READY_EXAMPLES = {
    "Chưa có hàng VC giao": False,
    "VC đã giao một phần": False,
    "VC đã giao đủ từng SKU tận xã": True,
    "KTV đã ký nhận đủ từng SKU tại điểm tập kết": True,
    "Thiếu biên bản hoặc chưa xác minh số lượng": False,
}


def can_demo_install(receipt, photo, gps):
    return bool(READY_EXAMPLES.get(receipt, False) and photo and gps)


def render_guide():
    """Show phone-friendly guide within the same Streamlit app at ?guide=1."""
    import streamlit as st

    st.markdown(
        "<style>"
        ".tdv-guide-title {color:#173A73;font-weight:800;font-size:1.43rem;"
        "line-height:1.4;margin:0.3rem 0}"
        ".tdv-guide-intro {background:#F2F7FC;border:1px solid #DDE9F4;"
        "padding:13px;border-radius:14px;line-height:1.6}"
        "</style>",
        unsafe_allow_html=True
    )
    back, share = st.columns([1, 1])
    with back:
        if st.button("← Về app", key="guide_back_home", use_container_width=True):
            st.query_params.clear()
            st.rerun()
    with share:
        st.link_button("🔗 Mở link hướng dẫn", GUIDE_URL,
                       use_container_width=True)
    st.markdown('<div class="tdv-guide-title">📖 HƯỚNG DẪN SỬ DỤNG</div>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="tdv-guide-intro">Dành cho người đăng ký đội trưởng, '
        'đội vận chuyển (VC), kỹ thuật lắp đặt (KTV) và người được cấp quyền '
        'xem báo cáo. Chọn nội dung cần làm để đọc từng bước. '
        '<strong>Trang hướng dẫn và thực hành không lưu dữ liệu.</strong></div>',
        unsafe_allow_html=True)
    st.caption("QUẢN LÝ DỰ ÁN • BẢN THỬ NGHIỆM. "
               "Có thể gửi riêng link hướng dẫn cho người mới qua Zalo.")

    topic = st.selectbox("📌 Tôi muốn xem hướng dẫn", TOPICS,
                         key="guide_topic_choice")
    if topic == TOPICS[0]:
        st.markdown("#### 1. Đăng ký tham gia dự án")
        st.info("Hiện biểu mẫu công khai dùng để đăng ký **đội trưởng**. "
                "Thành viên trong đội do đội trưởng quản lý; gửi đăng ký "
                "không tạo tài khoản báo cáo ngay.")
        with st.expander("Bước 1 • Mở đăng ký", expanded=True):
            st.write("Mở trang app, chọn **📝 Đăng ký tham gia** tại "
                     "**CHỌN CHỨC NĂNG**. Chọn đúng **Dự án đăng ký**.")
        with st.expander("Bước 2 • Điền hồ sơ", expanded=True):
            st.write("Điền **Họ và tên**, **Điện thoại liên hệ (Zalo)**; "
                     "chọn các xã/đơn vị thuộc **khu vực đã hợp đồng**, "
                     "hoặc ghi địa bàn bổ sung; chọn **Chuyên môn / Nhiệm vụ** "
                     "và **Phương tiện**. Kiểm tra kỹ trước khi gửi.")
        with st.expander("Bước 3 • Gửi và chờ duyệt", expanded=True):
            st.write("Bấm **GỬI ĐĂNG KÝ** một lần; chờ thông báo "
                     "**đã nhận hồ sơ**. ADMIN kiểm tra và duyệt, "
                     "sau đó **cấp mật khẩu riêng và gán nhiệm vụ**. "
                     "Chưa có tài khoản/nhiệm vụ thì chưa báo cáo được.")
        st.warning("Không gửi lại nhiều lần nếu chưa chắc hồ sơ đã lưu. "
                   "Hỏi ADMIN khi hồ sơ trùng hoặc chờ lâu.")

    elif topic == TOPICS[1]:
        st.markdown("#### 2. Đăng nhập và lưu biểu tượng app")
        with st.expander("Đăng nhập bằng HỌ TÊN", expanded=True):
            st.write("Sau khi được ADMIN cấp tài khoản, bấm "
                     "**👷 ĐỘI TRƯỞNG – BÁO CÁO** → nhập **họ tên đã đăng ký** "
                     "và **mật khẩu riêng** → bấm **VÀO BÁO CÁO**. "
                     "Mã đội nội bộ không cần nhớ.")
            st.caption("Nếu trùng họ tên hoặc chưa được cấp tài khoản, "
                       "hãy nhờ ADMIN xử lý; không thử tài khoản người khác.")
        with st.expander("Ghi nhớ đăng nhập 30 ngày"):
            st.write("Có thể tích **Ghi nhớ đăng nhập trên thiết bị này "
                     "(30 ngày)** nếu chức năng được ADMIN cấu hình. "
                     "Chỉ dùng trên điện thoại cá nhân; khi chọn ĐĂNG XUẤT "
                     "sẽ xóa phiên ghi nhớ.")
        iphone, android = st.tabs(["🍎 iPhone", "🤖 Android"])
        with iphone:
            st.write("Mở app bằng **Safari** (không ở trình duyệt nhúng Zalo) "
                     "→ bấm **Chia sẻ** → **Thêm vào Màn hình chính** "
                     "→ bấm **Thêm**. Từ lần sau chạm biểu tượng để mở.")
        with android:
            st.write("Mở app bằng **Chrome** → bấm **⋮** → chọn "
                     "**Thêm vào màn hình chính** hoặc **Cài đặt và tạo "
                     "lối tắt** → **Thêm**.")
        st.caption("Biểu tượng trên màn hình chính là lối tắt/web app; "
                   "việc thêm cần chính người dùng xác nhận.")

    elif topic == TOPICS[2]:
        st.markdown("#### 3. Đội VC – giao hàng và báo cáo")
        with st.expander("Trước khi đi", expanded=True):
            st.write("Đăng nhập đội trưởng → chọn **📋 Báo cáo nhiệm vụ** "
                     "→ mở **📝 2. BÁO CÁO GIAO HÀNG / LẮP ĐẶT** "
                     "→ chọn **Điểm được giao để báo cáo**. "
                     "Chỉ báo các điểm được ADMIN phân công.")
        with st.expander("Tại điểm giao", expanded=True):
            st.write("Đối chiếu **SKU và số lượng** trên app với hàng giao thực. "
                     "Nếu giao đúng đủ theo các nhiệm vụ của điểm, "
                     "chọn **Đã giao hàng**, chụp 1–10 ảnh làm chứng cứ. "
                     "Báo cáo VC hiện không bắt buộc GPS.")
        with st.expander("Gửi báo cáo", expanded=True):
            st.write("Bấm **✅ GỬI BÁO CÁO** một lần rồi kiểm tra thông báo "
                     "lưu thành công. Không bấm gửi liên tục nếu báo lỗi "
                     "đồng bộ; báo ADMIN đối soát.")
        st.warning("Phiên bản này chưa có mẫu báo cáo giao thiếu theo "
                   "số lượng thực nhận từng SKU. Nếu **giao thiếu, giao sai "
                   "hoặc hàng hỏng**, KHÔNG chọn 'Đã giao hàng' đủ; "
                   "báo ADMIN đối soát trước.")

    elif topic == TOPICS[3]:
        st.markdown("#### 4. Đội KTV – kiểm tra hàng và lắp đặt")
        with st.expander("Bước 1 • Xem điểm sẵn sàng lắp", expanded=True):
            st.write("Đăng nhập đội trưởng → **📋 Báo cáo nhiệm vụ** "
                     "→ bấm mở **📦 1. KIỂM TRA HÀNG VC / TẬP KẾT**. "
                     "Tìm xã, chọn **Sẵn sàng lắp** hoặc "
                     "**Sẵn sàng lắp (tập kết)**, xem **SKU**, "
                     "số VC giao tận xã và số KTV ký nhận tại tập kết.")
        with st.expander("Bước 2 • Đi lắp từng xã", expanded=True):
            st.write("Đọc địa điểm được giao, bấm **Xem địa điểm trên Google "
                     "Maps** nếu cần. Nếu chưa xác minh GPS điểm đến, "
                     "kiểm tra kỹ địa chỉ thật trước khi di chuyển. "
                     "Chỉ lắp tại xã được phân công.")
        with st.expander("Bước 3 • Báo đã lắp xong", expanded=True):
            st.write("Mở **📝 2. BÁO CÁO GIAO HÀNG / LẮP ĐẶT** "
                     "→ chọn điểm → **Đã lắp đặt**. Khi hàng thực tế đủ "
                     "và lắp xong, tải **1–10 ảnh hiện trường**, "
                     "cho phép **check-in GPS** trên điện thoại "
                     "rồi bấm **✅ GỬI BÁO CÁO**.")
        st.warning("Không báo 'Đã lắp đặt' khi chưa có đủ hàng "
                   "đã giao tại xã hoặc chứng từ KTV nhận đủ ở điểm "
                   "tập kết. Báo cáo KTV phải có **ảnh và GPS**.")

    elif topic == TOPICS[4]:
        st.markdown("#### 5. Vận chuyển kết hợp lắp đặt / nhận tại tập kết")
        with st.expander("Đội vừa VC vừa lắp đặt", expanded=True):
            st.write("Với đội **VC + LĐ**, phải báo **Giao hàng** trước, "
                     "sau khi hàng được xác nhận đủ mới báo **Lắp đặt**; "
                     "hai bước ghi riêng. Chưa có chế độ một nút báo "
                     "hoàn thành cả hai công việc.")
        with st.expander("VC giao gộp cho KTV tại một điểm", expanded=True):
            st.write("Ví dụ một đội KTV nhận nhiều xã vùng Đồng Văn – Yên "
                     "Minh – Quản Bạ tại **một điểm tập kết**: VC và KTV "
                     "**kiểm đếm, ký biên bản giấy**. ADMIN vào "
                     "**📦 Bàn giao tập kết** để ghi từng xã/từng SKU "
                     "theo biên bản và ảnh chữ ký.")
        with st.expander("KTV nhận rồi lắp theo địa bàn", expanded=True):
            st.write("KTV xem các xã có trạng thái **Sẵn sàng lắp (tập kết)**. "
                     "Mỗi xã được báo lắp xong **riêng**, kèm ảnh và GPS. "
                     "Bàn giao tập kết được theo dõi riêng, **không có "
                     "nghĩa VC đã giao tận từng xã**.")
        st.warning("Nếu số thực nhận thiếu so với biên bản, mất chứng từ "
                   "hoặc giao trùng, liên hệ ADMIN để đối soát; "
                   "không xác nhận đủ trên app.")

    elif topic == TOPICS[5]:
        st.markdown("#### 6. Lãnh đạo và ADMIN")
        with st.expander("Lãnh đạo xem tiến độ", expanded=True):
            st.write("Bấm **📊 LÃNH ĐẠO – XEM BÁO CÁO** → nhập **mật khẩu "
                     "Lãnh đạo** → **XEM BÁO CÁO**. Có thể chọn "
                     "ghi nhớ 30 ngày trên thiết bị cá nhân. "
                     "Lãnh đạo chỉ **xem**, không sửa được dự án.")
        with st.expander("Báo cáo phân biệt ba việc", expanded=True):
            st.write("**VC giao tận xã**, **KTV nhận hàng tại điểm tập kết**, "
                     "và **địa điểm đã lắp xong** là ba chỉ tiêu khác nhau. "
                     "Bấm **CẬP NHẬT SỐ LIỆU** khi cần số liệu mới.")
        with st.expander("ADMIN xét duyệt và cấp quyền", expanded=True):
            st.write("ADMIN đăng nhập → mở **👥 Đăng ký & quản lý đội** "
                     "→ duyệt hồ sơ → mở mục **🔐 CẤP / ĐẶT LẠI "
                     "MẬT KHẨU ĐỘI TRƯỞNG** → chọn tên người đã duyệt "
                     "→ xác nhận **CẤP MẬT KHẨU**. Mật khẩu mạnh "
                     "chỉ hiện một lần: ADMIN sao chép và gửi riêng "
                     "cho người nhận (không đăng nhóm Zalo). "
                     "Sau đó gán địa bàn. Quyền xem **📊 Báo cáo tiến độ** "
                     "toàn dự án chỉ dành cho ADMIN và LÃNH ĐẠO.")
        st.info("Đội trưởng không xem báo cáo tiến độ tổng hợp của các đội khác.")

    else:
        st.markdown("#### 🧪 Thực hành thử – KHÔNG ghi Google Sheets")
        st.caption("Các tên, điểm và số lượng bên dưới chỉ là ví dụ. "
                   "Bấm thử thoải mái: không gửi hồ sơ, không tải ảnh "
                   "và không đổi trạng thái nhiệm vụ thật.")
        mode=st.selectbox("Chọn bài thử",[
            "Đăng ký hồ sơ minh họa",
            "Đội VC – kiểm tra trước khi báo giao",
            "Đội KTV – kiểm tra điều kiện báo lắp"],key="guide_demo_mode")
        if mode=="Đăng ký hồ sơ minh họa":
            st.text_input("Họ tên minh họa",value="Nguyễn Văn A (ví dụ)",
                          key="guide_demo_name")
            st.selectbox("Chuyên môn (thử)",[
                "Vận chuyển / Giao nhận","KTV lắp đặt",
                "Vận chuyển & Lắp đặt"],key="guide_demo_specialty")
            st.selectbox("Địa bàn (thử)",[
                "Đồng Văn","Yên Minh","Quản Bạ"],key="guide_demo_region")
            if st.button("🧪 GIẢ LẬP GỬI ĐĂNG KÝ",key="guide_demo_register"):
                st.success("Đây là kết quả MÔ PHỎNG. "
                           "Không có hồ sơ nào được gửi. Khi đăng ký thật, "
                           "quay lại app và chọn 'Đăng ký tham gia'.")
        elif mode=="Đội VC – kiểm tra trước khi báo giao":
            location=st.selectbox("Điểm giả lập",[
                "Xã A (ví dụ)","Xã B (ví dụ)"],key="guide_demo_vc_site")
            enough=st.checkbox("Đã kiểm đếm giao đủ tất cả SKU",
                               key="guide_demo_vc_enough")
            photo=st.checkbox("Đã chụp ảnh giao hàng",
                              key="guide_demo_vc_photo")
            if st.button("🧪 KIỂM TRA GIẢ LẬP",key="guide_demo_vc"):
                if enough and photo:
                    st.success("Ví dụ hợp lệ: đủ hàng và có ảnh. "
                               "Trong app thật phải chọn nhiệm vụ "
                               "được giao rồi bấm GỬI BÁO CÁO.")
                else:
                    st.warning("Chưa đủ điều kiện báo giao xong. "
                               "Không đánh dấu Đã giao hàng nếu chưa đủ "
                               "hàng thực tế hoặc thiếu ảnh.")
        else:
            scenario=st.selectbox("Tình trạng hàng (thử)",list(READY_EXAMPLES),
                                  key="guide_demo_stock")
            photo=st.checkbox("Đã có ảnh lắp đặt",key="guide_demo_ld_photo")
            gps=st.checkbox("Đã check-in GPS",key="guide_demo_ld_gps")
            if st.button("🧪 KIỂM TRA GIẢ LẬP",key="guide_demo_ld"):
                if can_demo_install(scenario,photo,gps):
                    st.success("Ví dụ đã đủ điều kiện mở bước báo lắp xong. "
                               "Trong thực tế vẫn phải lắp xong, xác nhận "
                               "đúng điểm/SKU và gửi báo cáo thật.")
                else:
                    st.warning("Chưa đủ điều kiện báo lắp xong: "
                               "cần hàng được nhận đủ, ảnh và GPS.")
    st.divider()
    st.caption("Cần trợ giúp? Liên hệ ADMIN phụ trách dự án. "
               "Không chia sẻ mật khẩu hay mã truy cập riêng với người khác.")
    st.code(GUIDE_URL,language=None)
