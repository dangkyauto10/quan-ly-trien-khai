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
  
  // Đọc dữ liệu từ dòng 3 của DM_CHUAN (lấy 6 cột: A đến F)
  var range = sheetDM.getRange(3, 1, lastRow - 2, 6);
  var values = range.getValues();
  
  // Mở hoặc tạo sheet KHO_PHAN_BO
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Xóa sạch dữ liệu cũ trong KHO_PHAN_BO (giữ lại dòng tiêu đề 1 và 2) và ghi lại tiêu đề chuẩn
  sheetKho.clear();
  sheetKho.appendRow(["VỀ TRANG CHỦ", "TÌM KIẾM -->", "", "", "", "", "", "", ""]);
  sheetKho.appendRow([
    "Mã dự án", "Mã thiết bị / SKU", "Tên dự án", 
    "Tên thiết bị / Hàng hóa", "Số lượng", "Đơn vị tính", 
    "Đội nhận thiết bị", "Địa điểm vận chuyển lắp đặt", "Trạng thái Giao Nhận"
  ]);
  
  // Đọc sheet DANH_SACH_DU_AN để lập bảng tra cứu Mã dự án -> Tên dự án
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
  
  // Thu thập dữ liệu từ DM_CHUAN
  for (var i = 0; i < values.length; i++) {
    var maDuAn  = String(values[i][0]).trim(); // Col A: Mã dự án
    var maTB    = String(values[i][1]).trim(); // Col B: Mã SKU
    var tenTB   = String(values[i][2]).trim(); // Col C: Tên thiết bị / Hàng hóa
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
  
  var count = 0;
  
  // Ghi dữ liệu sang KHO_PHAN_BO với ánh xạ cột chính xác tuyệt đối
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var tenDuAn = mapDA[item.maDuAn] || item.maDuAn; // Lấy tên dự án từ danh sách, nếu không thấy lấy mã
      
      sheetKho.appendRow([
        item.maDuAn,    // Cột A: Mã dự án
        item.maTB,      // Cột B: Mã thiết bị / SKU
        tenDuAn,        // Cột C: Tên dự án (quy chiếu chuẩn)
        item.tenTB,     // Cột D: Tên thiết bị / Hàng hóa
        item.soLuong,   // Cột E: Số lượng
        item.donVi,     // Cột F: Đơn vị tính
        currentUnit,    // Cột G: Đội nhận thiết bị / xã
        "",             // Cột H: Địa điểm vận chuyển lắp đặt (để trống)
        ""              // Cột I: Trạng thái Giao Nhận (để trống cho Admin xác nhận)
      ]);
      count++;
    }
  }
  
  SpreadsheetApp.getUi().alert("✅ Phân bổ thành công " + count + " dòng! Tất cả các cột đã chuẩn khớp 100%.");
}
