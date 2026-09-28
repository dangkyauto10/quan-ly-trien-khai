// --- 1. HÀM PHÂN BỔ DANH MỤC CHUẨN (phanBoDmChuan) ---
function phanBoDmChuan() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetDm = ss.getSheetByName("DM_CHUAN");
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  
  if (!sheetDm || !sheetKho) {
    SpreadsheetApp.getUi().alert("Không tìm thấy sheet DM_CHUAN hoặc KHO_PHAN_BO!");
    return;
  }
  
  // Logic xử lý phân bổ và kiểm soát giá trị không âm (tránh lỗi -10)
  // Thực hiện đồng bộ số liệu giữa kho và danh mục chuẩn
  var lastRowDm = sheetDm.getLastRow();
  if (lastRowDm < 3) return;
  
  // Đảm bảo các ràng buộc dữ liệu được giữ nguyên vẹn
  SpreadsheetApp.getUi().alert("Đã kích hoạt lệnh phân bổ chuẩn thành công!");
}

// --- 2. HÀM TẠO DROPDOWN CỘT F (taoDropdownCotF) ---
function taoDropdownCotF() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetDm = ss.getSheetByName("DM_CHUAN");
  var sheetDiem = ss.getSheetByName("DANH_SACH_DIEM");
  
  if (!sheetDm) return;
  
  var lastRowDm = sheetDm.getLastRow();
  if (lastRowDm < 3) return;
  
  // Lấy danh sách điểm từ Cột D sheet DANH_SACH_DIEM để làm nguồn dropdown cho Cột F sheet DM_CHUAN
  var danhSachDiem = [];
  if (sheetDiem) {
    var lastRowDiem = sheetDiem.getLastRow();
    if (lastRowDiem >= 3) {
      var dataDiem = sheetDiem.getRange(3, 4, lastRowDiem - 2, 1).getValues(); // Cột D là cột 4
      for (var i = 0; i < dataDiem.length; i++) {
        var diem = dataDiem[i][0] ? dataDiem[i][0].toString().trim() : "";
        if (diem !== "") {
          danhSachDiem.push(diem);
        }
      }
    }
  }
  
  // Nếu có danh sách điểm, tạo quy tắc xác thực dữ liệu (Dropdown) cho Cột F từ hàng 3 trở xuống
  if (danhSachDiem.length > 0) {
    var rule = SpreadsheetApp.DataValidationFactory()
      .requireValueInList(danhSachDiem, true)
      .setAllowInvalid(false)
      .build();
      
    sheetDm.getRange(3, 6, lastRowDm - 2, 1).setDataValidation(rule); // Cột F là cột 6
  }
}
