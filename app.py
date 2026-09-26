function doGet(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName("DANH SÁCH ĐIỂM");
    if (!sheet) {
      sheet = ss.getSheets()[0]; // Nếu không tìm thấy tên thì lấy sheet đầu tiên
    }
    
    // Lấy toàn bộ dữ liệu Cột D (bắt đầu từ dòng 3 trở đi)
    var lastRow = sheet.getLastRow();
    var danhSachDiem = [];
    
    if (lastRow >= 3) {
      var values = sheet.getRange(3, 4, lastRow - 2, 1).getValues();
      for (var i = 0; i < values.length; i++) {
        var tenDiem = String(values[i][0]).trim();
        if (tenDiem !== "" && danhSachDiem.indexOf(tenDiem) === -1) {
          danhSachDiem.push(tenDiem);
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
