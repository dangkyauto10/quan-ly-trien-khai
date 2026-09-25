/**
 * HỆ THỐNG ĐIỀU HƯỚNG TỰ ĐỘNG - KHÔNG BỊ TỰ ĐÓNG TRANG
 */
function onSelectionChange(e) {
  if (!e || !e.range) return;
  
  var sheet = e.range.getSheet();
  var sheetName = sheet.getName();

  // CHỈ THỰC HIỆN KHI BẤM TRÊN MÀN HÌNH "TRANG_CHU"
  // Khi đã nhảy sang sheet con, dừng lại ngay lập tức -> KHÔNG BAO GIỜ TỰ ĐÓNG
  if (sheetName !== "TRANG_CHU") return;

  var val = e.range.getValue().toString().trim().toUpperCase();
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var mapSheet = {
    "DỰ ÁN": "DANH_SACH_DU_AN",
    "TIẾN ĐỘ": "TIEN_DO",
    "NHẬP KHO": "NHAP_KHO",
    "KHO PHÂN BỔ": "KHO_PHAN_BO",
    "PHÂN BỔ": "KHO_PHAN_BO",
    "VẬN CHUYỂN": "VAN_CHUYEN",
    "LẮP ĐẶT": "LAP_DAT",
    "BÁO CÁO": "BAO_CAO_TRIEN_KHAI",
    "DANH SÁCH ĐIỂM": "DANH_SACH_DIEM",
    "ĐIỂM": "DANH_SACH_DIEM",
    "QUẢN LÝ ĐỘI": "QUAN_LY_DOI",
    "ĐĂNG KÝ THÀNH VIÊN": "DANG_KY_THANH_VIEN",
    "THÀNH VIÊN": "THANH_VIEN"
  };

  var targetName = "";
  for (var key in mapSheet) {
    if (val.indexOf(key) !== -1) {
      targetName = mapSheet[key];
      break;
    }
  }

  if (targetName !== "") {
    var targetSheet = ss.getSheetByName(targetName);
    // Dự phòng trường hợp tên sheet là DU_AN
    if (!targetSheet && targetName === "DANH_SACH_DU_AN") {
      targetSheet = ss.getSheetByName("DU_AN");
    }

    if (targetSheet) {
      // 1. Mở sheet được chọn
      targetSheet.showSheet();
      ss.setActiveSheet(targetSheet);

      // 2. Ẩn tất cả các sheet khác, chỉ để lại đúng 2 tab: TRANG_CHU và Sheet đang xem
      var allSheets = ss.getSheets();
      for (var i = 0; i < allSheets.length; i++) {
        var s = allSheets[i];
        var sName = s.getName();
        if (sName !== targetSheet.getName() && sName !== "TRANG_CHU") {
          s.hideSheet();
        }
      }
    }
  }
}

/**
 * Tạo thêm Menu "🏠 ĐIỀU HÀNH" trên thanh công cụ để về Trang Chủ bất kỳ lúc nào
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🏠 ĐIỀU HÀNH')
    .addItem('Quay về TRANG CHỦ', 'veTrangChu')
    .addToUi();
}

function veTrangChu() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var home = ss.getSheetByName("TRANG_CHU");
  if (home) {
    home.showSheet();
    ss.setActiveSheet(home);
  }
}
