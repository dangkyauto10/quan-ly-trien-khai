/**
 * TỰ ĐỘNG MỞ SHEET & ẨN CÁC SHEET KHÁC (ĐÃ FIX LỖI CHẶN LIÊN KẾT)
 */
function onSelectionChange(e) {
  if (!e || !e.range) return;
  
  var sheet = e.range.getSheet();
  var sheetName = sheet.getName();

  // Chỉ hoạt động khi click chuột trên TRANG_CHU
  if (sheetName !== "TRANG_CHU") return;

  var val = e.range.getValue().toString().trim().toUpperCase();
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Bảng đối chiếu chính xác tên ô và tên Sheet thực tế
  var mapSheet = {
    "DỰ ÁN": "DANH_SACH_DU_AN",
    "TIẾN ĐỘ": "TIEN_DO",
    "NHẬP KHO": "NHAP_KHO",
    "PHÂN BỔ": "KHO_PHAN_BO",
    "VẬN CHUYỂN": "VAN_CHUYEN",
    "LẮP ĐẶT": "LAP_DAT",
    "BÁO CÁO": "BAO_CAO_TRIEN_KHAI",
    "DANH SÁCH ĐIỂM": "DANH_SACH_DIEM",
    "ĐIỂM": "DANH_SACH_DIEM",
    "QUẢN LÝ ĐỘI": "QUAN_LY_DOI",
    "ĐĂNG KÝ THÀNH VIÊN": "DANG_KY_THANH_VIEN"
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
    if (!targetSheet && targetName === "DANH_SACH_DU_AN") {
      targetSheet = ss.getSheetByName("DU_AN");
    }

    if (targetSheet) {
      // 1. Mở sheet đích trước
      targetSheet.showSheet();
      ss.setActiveSheet(targetSheet);

      // 2. Ẩn tất cả các sheet khác (chỉ giữ lại TRANG_CHU và Sheet đang mở)
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
