function phanBoDmChuan() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getActiveSheet();
  var lastRow = sheet.getLastRow();
  
  if (lastRow < 3) {
    SpreadsheetApp.getUi().alert("Chưa có dữ liệu để thực hiện phân bổ!");
    return;
  }
  
  // Quét đúng vùng dữ liệu nguồn từ dòng 3
  var range = sheet.getRange(3, 1, lastRow - 2, 9);
  var values = range.getValues();
  var count = 0;
  
  // Trỏ tới sheet KHO_PHAN_BO
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
    sheetKho.appendRow(["Mã dự án", "Mã thiết bị / SKU", "Tên dự án", "Tên thiết bị / Hàng hóa", "Số lượng", "Đơn vị tính", "Đội nhận thiết bị", "Địa điểm", "Thời gian"]);
  }
  
  for (var i = 0; i < values.length; i++) {
    var maDuAn    = values[i][0]; // Cột A: Mã dự án (lấy từ danh sách dự án)
    var maTB      = values[i][1]; // Cột B: Mã thiết bị / SKU
    var tenDA     = values[i][2]; // Cột C: Tên dự án
    var tenTB     = values[i][3]; // Cột D: Tên thiết bị / Hàng hóa (chuẩn sheet Nhập kho)
    var soLuong   = values[i][4]; // Cột E: Số lượng
    var donVi     = values[i][5]; // Cột F: Đơn vị tính
    var doiNhan   = values[i][6]; // Cột G: Đội nhận thiết bị
    var diaDiem   = values[i][7]; // Cột H: Địa điểm vận chuyển lắp đặt
    
    // Kiểm tra điều kiện hợp lệ để ghi nhận sang Kho phân bổ
    if (maTB && tenTB && soLuong !== "") {
      sheetKho.appendRow([maDuAn, maTB, tenDA, tenTB, soLuong, donVi, doiNhan, diaDiem, new Date()]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Đã phân bổ chính xác " + count + " dòng vào Kho phân bổ đúng cấu trúc!");
}
