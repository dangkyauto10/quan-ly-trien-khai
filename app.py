function phanBoDmChuan() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  var lastRow = sheet.getLastRow();
  
  if (lastRow < 3) {
    SpreadsheetApp.getUi().alert("Chưa có dữ liệu để thực hiện phân bổ!");
    return;
  }
  
  // Đọc dữ liệu từ dòng 3 của sheet DM_CHUAN (lấy 6 cột đầu: A đến F)
  var range = sheet.getRange(3, 1, lastRow - 2, 6);
  var values = range.getValues();
  var count = 0;
  
  // Mở sheet KHO_PHAN_BO
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Đọc sheet DANH_SACH_DU_AN để tự động quy chiếu Mã dự án (Col A) ra Tên dự án (Col B)
  var sheetDA = ss.getSheetByName("DANH_SACH_DU_AN");
  var mapDA = {};
  if (sheetDA) {
    var lastRowDA = sheetDA.getLastRow();
    if (lastRowDA >= 3) {
      var dataDA = sheetDA.getRange(3, 1, lastRowDA - 2, 2).getValues();
      for (var d = 0; d < dataDA.length; d++) {
        var mDa = String(dataDA[d][0]).trim();
        var tDa = String(dataDA[d][1]).trim();
        if (mDa) {
          mapDA[mDa] = tDa;
        }
      }
    }
  }
  
  for (var i = 0; i < values.length; i++) {
    var maDuAn    = values[i][0]; // Cột A DM_CHUAN -> Cột A Kho
    var maTB      = values[i][1]; // Cột B DM_CHUAN -> Cột B Kho
    var tenTB     = values[i][2]; // Cột C DM_CHUAN -> Cột D Kho (Tên thiết bị)
    var donVi     = values[i][3]; // Cột D DM_CHUAN -> Cột F Kho (Đơn vị tính)
    var soLuong   = values[i][4]; // Cột E DM_CHUAN -> Cột E Kho (Số lượng)
    var doiNhan   = values[i][5]; // Cột F DM_CHUAN -> Cột G Kho (Phân bổ đơn vị/xã)
    
    // Kiểm tra điều kiện hợp lệ
    if (maTB && soLuong !== "" && doiNhan !== "") {
      // Tự động quy chiếu Tên dự án từ DANH_SACH_DU_AN vào Cột C Kho phân bổ
      var tenDuAn = mapDA[maDuAn] || "";
      
      // Ghi dữ liệu chuẩn tuyệt đối vào KHO_PHAN_BO theo đúng yêu cầu:
      sheetKho.appendRow([
        maDuAn,       // Cột A: Mã dự án
        maTB,         // Cột B: Mã thiết bị / SKU
        tenDuAn,      // Cột C: Tên dự án (quy chiếu từ DANH_SACH_DU_AN)
        tenTB,        // Cột D: Tên thiết bị / Hàng hóa
        soLuong,      // Cột E: Số lượng
        donVi,        // Cột F: Đơn vị tính
        doiNhan,      // Cột G: Đội nhận thiết bị / xã
        "",           // Cột H: Địa điểm (để trống)
        ""            // Cột I: Trạng thái Giao Nhận (để trống cho AD xác nhận)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Đã phân bổ thành công " + count + " dòng! Các cột đã khớp chuẩn xác 100%.");
}
