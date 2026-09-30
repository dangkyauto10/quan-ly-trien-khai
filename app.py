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
  
  // Đọc dữ liệu từ cột A đến cột F (6 cột đầu tiên) bắt đầu từ dòng 3
  var range = sheetDM.getRange(3, 1, lastRow - 2, 6);
  var values = range.getValues();
  
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Thiết lập lại tiêu đề chuẩn cho KHO_PHAN_BO
  sheetKho.clear();
  sheetKho.appendRow(["VỀ TRANG CHỦ", "TÌM KIẾM -->", "", "", "", "", "", "", ""]);
  sheetKho.appendRow([
    "Mã dự án", "Mã thiết bị / SKU", "Tên dự án", 
    "Tên thiết bị / Hàng hóa", "Số lượng", "Đơn vị tính", 
    "Đội nhận thiết bị", "Địa điểm vận chuyển lắp đặt", "Trạng thái Giao Nhận"
  ]);
  
  // Đọc sheet DANH_SACH_DU_AN để tra cứu Tên dự án chuẩn từ Mã dự án
  var sheetDA = ss.getSheetByName("DANH_SACH_DU_AN");
  var mapDA = {};
  if (sheetDA) {
    var daData = sheetDA.getDataRange().getValues();
    for (var r = 0; r < daData.length; r++) {
      var mDa = String(daData[r][0]).trim(); // Cột A: Mã dự án
      var tDa = String(daData[r][1]).trim(); // Cột B: Tên dự án
      if (mDa && mDa !== "Mã dự án") {
        mapDA[mDa] = tDa;
      }
    }
  }
  
  var items = [];
  var unitsSet = {};
  
  // Duyệt qua từng dòng của DM_CHUAN với chỉ số mảng chính xác:
  // Index 0 = Cột A (Mã dự án)
  // Index 1 = Cột B (Mã SKU)
  // Index 2 = Cột C (Tên thiết bị / Hàng hóa)
  // Index 3 = Cột D (Đơn vị tính)
  // Index 4 = Cột E (Số lượng)
  // Index 5 = Cột F (Đội nhận / Xã)
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
  
  var count = 0;
  
  // Ghi dữ liệu sang KHO_PHAN_BO với thứ tự cột chuẩn xác 100%:
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var tenDuAn = mapDA[item.maDuAn] || item.maDuAn;
      
      sheetKho.appendRow([
        item.maDuAn,    // Cột A: Mã dự án
        item.maTB,      // Cột B: Mã thiết bị / SKU
        tenDuAn,        // Cột C: Tên dự án (lấy từ DANH_SACH_DU_AN)
        item.tenTB,     // Cột D: Tên thiết bị / Hàng hóa (chuẩn từ Cột C DM_CHUAN)
        item.soLuong,   // Cột E: Số lượng (chuẩn từ Cột E DM_CHUAN)
        item.donVi,     // Cột F: Đơn vị tính (chuẩn từ Cột D DM_CHUAN)
        currentUnit,    // Cột G: Đội nhận thiết bị / xã (chuẩn từ Cột F DM_CHUAN)
        "",             // Cột H: Địa điểm (để trống)
        ""              // Cột I: Trạng thái Giao Nhận (để trống cho Admin xác nhận)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Phân bổ thành công " + count + " dòng! Tất cả các cột đã về đúng vị trí tắp lự.");
}
