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
  
  // Mở sheet KHO_PHAN_BO
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Tự động quy chiếu Tên dự án từ sheet DANH_SACH_DU_AN dựa vào Mã dự án (Col A)
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
  
  var items = [];
  var unitsSet = {};
  
  // 1. Thu thập toàn bộ các dòng hàng hóa hợp lệ (TB-01 đến TB-05) và danh sách các đơn vị ở cột F
  for (var i = 0; i < values.length; i++) {
    var maDuAn    = values[i][0]; // Cột A: Mã dự án
    var maTB      = values[i][1]; // Cột B: SKU
    var tenTB     = values[i][2]; // Cột C: Tên thiết bị
    var donVi     = values[i][3]; // Cột D: Đơn vị tính
    var soLuong   = values[i][4]; // Cột E: Số lượng
    var doiNhan   = values[i][5]; // Cột F: Đội nhận / Xã
    
    // Lưu lại thông tin mặt hàng nếu có mã thiết bị và số lượng
    if (maTB && soLuong !== "") {
      items.push({
        maDuAn: maDuAn,
        maTB: maTB,
        tenTB: tenTB,
        donVi: donVi,
        soLuong: soLuong
      });
    }
    
    // Thu thập các đơn vị/xã xuất hiện ở cột F (mỗi dòng cột F có thể là một xã hoặc cách nhau bằng dấu phẩy)
    if (doiNhan) {
      var splitUnits = String(doiNhan).split(",");
      for (var u = 0; u < splitUnits.length; u++) {
        var uName = splitUnits[u].trim();
        if (uName) {
          unitsSet[uName] = true;
        }
      }
    }
  }
  
  var units = Object.keys(unitsSet);
  
  if (items.length === 0 || units.length === 0) {
    SpreadsheetApp.getUi().alert("❌ Chưa có đủ danh mục thiết bị hoặc chưa điền đơn vị nhận ở cột F!");
    return;
  }
  
  var count = 0;
  
  // 2. PHÂN BỔ CHUẨN XÁC: MỖI XÃ / ĐƠN VỊ ĐỀU NHẬN ĐƯỢC ĐẦY ĐỦ TRỌN BỘ CÁC MẶT HÀNG TỪ ITEMS
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var tenDuAn = mapDA[item.maDuAn] || "";
      
      sheetKho.appendRow([
        item.maDuAn,    // Cột A: Mã dự án
        item.maTB,      // Cột B: Mã SKU
        tenDuAn,        // Cột C: Tên dự án (quy chiếu tự động từ DANH_SACH_DU_AN)
        item.tenTB,     // Cột D: Tên thiết bị / Hàng hóa
        item.soLuong,   // Cột E: Số lượng (y hệt nhau cho mỗi xã)
        item.donVi,     // Cột F: Đơn vị tính
        currentUnit,    // Cột G: Đội nhận thiết bị / xã
        "",             // Cột H: Địa điểm (để trống)
        ""              // Cột I: Trạng thái Giao Nhận (để trống cho AD xác nhận)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Đã phân bổ thành công " + count + " dòng! Mỗi xã/đơn vị đã nhận đầy đủ trọn bộ các mặt hàng với số lượng chuẩn xác.");
}
