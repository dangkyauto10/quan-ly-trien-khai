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
  
  // Đọc dữ liệu từ dòng 3, lấy 6 cột (A đến F)
  var range = sheetDM.getRange(3, 1, lastRow - 2, 6);
  var values = range.getValues();
  
  // Mở hoặc tạo sheet KHO_PHAN_BO
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
    sheetKho.appendRow(["Mã dự án", "Mã thiết bị / SKU", "Tên dự án", "Tên thiết bị / Hàng hóa", "Số lượng", "Đơn vị tính", "Đội nhận thiết bị", "Địa điểm vận chuyển lắp đặt", "Trạng thái Giao Nhận"]);
  }
  
  // Sheet DANH_SACH_DU_AN để tra cứu tên dự án
  var sheetDA = ss.getSheetByName("DANH_SACH_DU_AN");
  
  var items = [];
  var unitsSet = {};
  
  // 1. Thu thập danh mục thiết bị và các đơn vị nhận từ Col F
  for (var i = 0; i < values.length; i++) {
    var maDuAn  = String(values[i][0]).trim(); // Col A: Mã dự án
    var maTB    = String(values[i][1]).trim(); // Col B: Mã SKU
    var tenTB   = String(values[i][2]).trim(); // Col C: Tên thiết bị
    var donVi   = String(values[i][3]).trim(); // Col D: Đơn vị tính
    var soLuong = values[i][4];                // Col E: Số lượng
    var doiNhan = String(values[i][5]).trim(); // Col F: Đội nhận / Xã
    
    if (maTB && soLuong !== "") {
      items.push({
        maDuAn: maDuAn,
        maTB: maTB,
        tenTB: tenTB,
        donVi: donVi,
        soLuong: soLuong
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
  
  // Hàm tra cứu tên dự án an toàn từ DANH_SACH_DU_AN
  function getProjectName(mDa) {
    if (!sheetDA) return mDa;
    var daData = sheetDA.getDataRange().getValues();
    for (var r = 0; r < daData.length; r++) {
      var code = String(daData[r][0]).trim();
      if (code === mDa) {
        var name = String(daData[r][1]).trim();
        if (name) return name;
      }
    }
    return mDa;
  }
  
  var count = 0;
  
  // 2. Ghi dữ liệu sang KHO_PHAN_BO: Mỗi đơn vị nhận đủ trọn bộ items với đúng số lượng
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var tenDuAn = getProjectName(item.maDuAn);
      
      sheetKho.appendRow([
        item.maDuAn,    // Col A: Mã dự án
        item.maTB,      // Col B: Mã thiết bị / SKU
        tenDuAn,        // Col C: Tên dự án (quy chiếu chuẩn từ DANH_SACH_DU_AN)
        item.tenTB,     // Col D: Tên thiết bị / Hàng hóa
        item.soLuong,   // Col E: Số lượng
        item.donVi,     // Col F: Đơn vị tính
        currentUnit,    // Col G: Đội nhận thiết bị / xã
        "",             // Col H: Địa điểm (để trống)
        ""              // Col I: Trạng thái Giao Nhận (để trống cho Admin xác nhận)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Phân bổ thành công " + count + " dòng! Mỗi đơn vị đã nhận đủ trọn bộ thiết bị với số lượng chuẩn xác.");
}
