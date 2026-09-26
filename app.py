// HÀM ĐỌC TỰ ĐỘNG TOÀN BỘ CỘT D GỬI SANG APP
function doGet(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    // Tìm đúng sheet DANH SÁCH ĐIỂM
    var sheet = ss.getSheetByName("DANH SÁCH ĐIỂM");
    if (!sheet) {
      sheet = ss.getSheets()[0];
    }
    
    var lastRow = sheet.getLastRow();
    var danhSachDiem = [];
    
    // Đọc từ dòng 3 của Cột D (Cột số 4) đến hết bảng
    if (lastRow >= 3) {
      var values = sheet.getRange(3, 4, lastRow - 2, 1).getValues();
      for (var i = 0; i < values.length; i++) {
        var val = String(values[i][0]).trim();
        if (val !== "" && danhSachDiem.indexOf(val) === -1) {
          danhSachDiem.push(val);
        }
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      total: danhSachDiem.length,
      data: danhSachDiem
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
