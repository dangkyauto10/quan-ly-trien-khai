function phanBoDmChuan() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetDM = ss.getSheetByName("DM_CHUAN");
  if (!sheetDM) {
    sheetDM = ss.getActiveSheet();
  }
  
  var lastRow = sheetDM.getLastRow();
  if (lastRow < 3) {
    SpreadsheetApp.getUi().alert("Chưa có dữ liệu để thực hiện phân bổ!");
    return;
  }
  
  // Đọc từ cột A đến cột F (6 cột) từ dòng 3
  var range = sheetDM.getRange(3, 1, lastRow - 2, 6);
  var values = range.getValues();
  
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Xóa và thiết lập tiêu đề chuẩn xác cho KHO_PHAN_BO
  sheetKho.clear();
  sheetKho.appendRow(["VỀ TRANG CHỦ", "TÌM KIẾM -->", "", "", "", "", "", "", ""]);
  sheetKho.appendRow([
    "Mã dự án", "Mã thiết bị / SKU", "Tên dự án", 
    "Tên thiết bị / Hàng hóa", "Số lượng", "Đơn vị tính", 
    "Đội nhận thiết bị", "Địa điểm vận chuyển lắp đặt", "Trạng thái Giao Nhận"
  ]);
  
  // Đọc sheet DANH_SACH_DU_AN để lấy Tên dự án từ Mã dự án
  var sheetDA = ss.getSheetByName("DANH_SACH_DU_AN");
  var mapDA = {};
  if (sheetDA) {
    var daData = sheetDA.getDataRange().getValues();
    for (var r = 0; r < daData.length; r++) {
      var mDa = String(daData[r][0]).trim(); // Cột A
      var tDa = String(daData[r][1]).trim(); // Cột B
      if (mDa && mDa !== "Mã dự án") {
        mapDA[mDa] = tDa;
      }
    }
  }
  
  var items = [];
  var unitsSet = {};
  
  // Ánh xạ tường minh từng cột từ DM_CHUAN:
  // values[i][0] -> Cột A: Mã dự án
  // values[i][1] -> Cột B: Mã SKU
  // values[i][2] -> Cột C: Tên thiết bị / Hàng hóa
  // values[i][3] -> Cột D: Đơn vị tính
  // values[i][4] -> Cột E: Số lượng
  // values[i][5] -> Cột F: Đội nhận / Xã
  for (var i = 0; i < values.length; i++) {
    var maDuAn  = String(values[i][0]).trim();
    var maTB    = String(values[i][1]).trim();
    var tenTB   = String(values[i][2]).trim();
    var donVi   = String(values[i][3]).trim();
    var soLuong = values[i][4];
    var doiNhan = String(values[i][5]).trim();
    
    if (maTB && soLuong !== "") {
      items.push({
        maDuAn: maDuAn,
        maTB: maTB,
        tenTB: tenTB,     // Lưu chính xác Tên thiết bị
        donVi: donVi,     // Lưu chính xác Đơn vị tính
        soLuong: soLuong  // Lưu chính xác Số lượng
      });
    }
    
    if (doiNhan && doiNhan !== "nan") {
      var parts = doiNhan.split(",");
      for (var p = 0; p < parts.length; p++) {
        var uName = parts[p].trim();
        if (uName) {
          unitsSet[uName] = true;
        }
      }
    }
  }
  
  var units = Object.keys(unitsSet);
  if (items.length === 0 || units.length === 0) {
    SpreadsheetApp.getUi().alert("❌ Chưa có đủ dữ liệu thiết bị hoặc chưa điền đơn vị nhận ở cột F!");
    return;
  }
  
  var count = 0;
  
  // Đẩy sang KHO_PHAN_BO với thứ tự cột được gán cứng, không bao giờ lệch:
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var tenDuAn = mapDA[item.maDuAn] || item.maDuAn;
      
      sheetKho.appendRow([
        item.maDuAn,    // Cột A: Mã dự án
        item.maTB,      // Cột B: Mã thiết bị / SKU
        tenDuAn,        // Cột C: Tên dự án
        item.tenTB,     // Cột D: Tên thiết bị / Hàng hóa
        item.soLuong,   // Cột E: Số lượng
        item.donVi,     // Cột F: Đơn vị tính
        currentUnit,    // Cột G: Đội nhận thiết bị / xã
        "",             // Cột H: Địa điểm vận chuyển lắp đặt (để trống)
        ""              // Cột I: Trạng thái Giao Nhận (để trống)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Phân bổ thành công " + count + " dòng! Đã khóa cứng chuẩn vị trí từng cột.");
}
