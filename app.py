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
  
  // Đọc 6 cột đầu tiên từ dòng 3 của sheet DM_CHUAN
  var range = sheetDM.getRange(3, 1, lastRow - 2, 6);
  var values = range.getValues();
  
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Thiết lập tiêu đề chuẩn tuyệt đối cho KHO_PHAN_BO
  sheetKho.clear();
  sheetKho.appendRow(["VỀ TRANG CHỦ", "TÌM KIẾM -->", "", "", "", "", "", "", ""]);
  sheetKho.appendRow([
    "Mã dự án", "Mã thiết bị / SKU", "Tên dự án", 
    "Tên thiết bị / Hàng hóa", "Số lượng", "Đơn vị tính", 
    "Đội nhận thiết bị", "Địa điểm vận chuyển lắp đặt", "Trạng thái Giao Nhận"
  ]);
  
  // Đọc sheet DANH_SACH_DU_AN để tra cứu Tên dự án từ Mã dự án
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
  
  // Ép chuẩn chỉ số mảng ứng với từng cột của DM_CHUAN:
  for (var i = 0; i < values.length; i++) {
    var maDuAn  = String(values[i][0]).trim(); // Cột A
    var maTB    = String(values[i][1]).trim(); // Cột B
    var tenTB   = String(values[i][2]).trim(); // Cột C: Tên thiết bị / Hàng hóa
    var donVi   = String(values[i][3]).trim(); // Cột D: Đơn vị tính
    var soLuong = values[i][4];                // Cột E: Số lượng
    var doiNhan = String(values[i][5]).trim(); // Cột F: Đội nhận / Xã
    
    if (maTB && soLuong !== "") {
      items.push({
        maDuAn: maDuAn,
        maTB: maTB,
        tenTB: tenTB,     // Lưu chuẩn Tên thiết bị
        donVi: donVi,     // Lưu chuẩn Đơn vị tính
        soLuong: soLuong  // Lưu chuẩn Số lượng
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
  
  // Đẩy dữ liệu sang KHO_PHAN_BO đúng từng vị trí cột đã chốt:
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var tenDuAn = mapDA[item.maDuAn] || item.maDuAn;
      
      sheetKho.appendRow([
        item.maDuAn,    // Cột A: Mã dự án
        item.maTB,      // Cột B: Mã thiết bị / SKU
        tenDuAn,        // Cột C: Tên dự án (quy chiếu từ DANH_SACH_DU_AN)
        item.tenTB,     // Cột D: Tên thiết bị / Hàng hóa (Lấy từ Cột C DM_CHUAN)
        item.soLuong,   // Cột E: Số lượng (Lấy từ Cột E DM_CHUAN)
        item.donVi,     // Cột F: Đơn vị tính (Lấy từ Cột D DM_CHUAN)
        currentUnit,    // Cột G: Đội nhận thiết bị / xã (Lấy từ Cột F DM_CHUAN)
        "",             // Cột H: Địa điểm (để trống)
        ""              // Cột I: Trạng thái Giao Nhận (để trống cho Admin xác nhận)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Phân bổ thành công " + count + " dòng! Đã khớp chuẩn tuyệt đối các cột.");
}
