function dongBoVanChuyenSangLapDatTuDong() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sVC = ss.getSheetByName("VAN_CHUYEN") || ss.getSheetByName("KHO_PHAN_BO");
  var sLD = ss.getSheetByName("LAP_DAT");
  
  if (!sVC || !sLD) return;
  
  var lastRowVC = sVC.getLastRow();
  if (lastRowVC < 3) return;
  
  // Đọc toàn bộ các cột từ A đến I (9 cột) bắt đầu từ dòng 3
  var dataVC = sVC.getRange(3, 1, lastRowVC - 2, 9).getValues();
  
  // Làm sạch dữ liệu cũ bên LAP_DAT để cập nhật đồng bộ
  var lastRowLD = sLD.getLastRow();
  if (lastRowLD >= 3) {
    sLD.getRange(3, 1, lastRowLD - 2, sLD.getLastColumn()).clearContent();
  }
  
  var rowsLD = [];
  var nowStr = Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss");
  
  for (var i = 0; i < dataVC.length; i++) {
    var maDA = (dataVC[i][0] || "").toString().trim();       // Cột A: Mã dự án (DA880)
    var tenTB = dataVC[i][3];                               // Cột D: Tên thiết bị
    var soLuong = dataVC[i][4];                             // Cột E: Số lượng
    var doiNhan = dataVC[i][6];                             // Cột G: Đội nhận thiết bị (VHH, KTV 003...)
    var diemGiao = (dataVC[i][7] || "").toString().trim();   // Cột H: Địa điểm vận chuyển lắp đặt
    var trangThai = (dataVC[i][8] || "").toString().trim().toLowerCase(); // Cột I: Trạng thái Giao Nhận
    
    // KHI CỘT I ĐẠT TRẠNG THÁI "ĐÃ GIAO HÀNG" (HOẶC "ĐÃ GIAO") THÌ TỰ ĐỘNG SINH VIỆC
    if (maDA !== "" && diemGiao !== "" && (trangThai === "đã giao hàng" || trangThai === "đã giao")) {
      var maCV = "CV-" + (100001 + rowsLD.length);
      
      rowsLD.push([
        maCV,                         // Cột A: Mã công việc
        maDA,                         // Cột B: Mã dự án (DA880)
        doiNhan || "KTV",             // Cột C: Đội nhận / KTV phụ trách
        soLuong,                      // Cột D: Số lượng thiết bị
        diemGiao,                     // Cột E: Địa điểm lắp đặt
        "Chờ lắp đặt",                // Cột F: Tình trạng thực hiện
        nowStr,                       // Cột G: Thời gian nhận bàn giao
        "https://maps.google.com"     // Cột H: Link Google Maps
      ]);
    }
  }
  
  // Ghi tự động sang LAP_DAT
  if (rowsLD.length > 0) {
    sLD.getRange(3, 1, rowsLD.length, rowsLD[0].length).setValues(rowsLD);
  }
  
  SpreadsheetApp.flush();
}
