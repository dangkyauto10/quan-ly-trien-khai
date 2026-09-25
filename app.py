# Hỗ trợ nhận diện chính xác tham số view trên mọi trình duyệt
params = st.query_params
raw_view = params.get("view", "hientruong")

# Xử lý trường hợp tham số bị trả về dưới dạng list [ 'dangky' ]
if isinstance(raw_view, list):
    view_mode = raw_view[0] if len(raw_view) > 0 else "hientruong"
else:
    view_mode = str(raw_view)
