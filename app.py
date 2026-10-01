// ==========================================
// 1. HÀM PHÂN BỔ CHÍNH (Nối tiếp dữ liệu dồn đợt 1, đợt 2... không mất dữ liệu cũ)
// ==========================================
function phanBoDmChuan() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetDM = ss.getSheetByName("DM_CHUAN");
  if (!sheetDM) return;
  
  var lastRowDM = sheetDM.getLastRow();
  if (lastRowDM < 3) {
    SpreadsheetApp.getUi().alert("Sheet DM_CHUAN không có dữ liệu để phân bổ!");
    return;
  }
  
  var rangeDM = sheetDM.getRange(3, 1, lastRowDM - 2, 6);
  var valuesDM = rangeDM.getValues();
  
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) {
    sheetKho = ss.insertSheet("KHO_PHAN_BO");
  }
  
  // Thiết lập chuẩn giao diện hàng 1 và hàng 2 (Ô E1 là ô tìm kiếm màu vàng)
  if (sheetKho.getLastRow() < 2) {
    sheetKho.getRange(1, 1).setValue("VỀ TRANG CHỦ");
    sheetKho.getRange(1, 4).setValue("TÌM KIẾM -->");
    sheetKho.getRange(1, 5).setBackground("#ffff00");
    sheetKho.getRange(2, 1).setValue("Mã dự án");
    sheetKho.getRange(2, 2).setValue("Mã thiết bị / SKU");
    sheetKho.getRange(2, 3).setValue("Tên dự án");
    sheetKho.getRange(2, 4).setValue("Tên thiết bị / Hàng hóa");
    sheetKho.getRange(2, 5).setValue("Số lượng");
    sheetKho.getRange(2, 6).setValue("Đơn vị tính");
    sheetKho.getRange(2, 7).setValue("Đội nhận thiết bị");
    sheetKho.getRange(2, 8).setValue("Địa điểm vận chuyển lắp đặt");
    sheetKho.getRange(2, 9).setValue("Trạng thái Giao Nhận");
  }
  
  var sheetDA = ss.getSheetByName("DANH_SACH_DU_AN");
  var mapDA = {};
  if (sheetDA) {
    var daData = sheetDA.getDataRange().getValues();
    for (var r = 0; r < daData.length; r++) {
      var mDa = String(daData[r][0]).trim();
      var tDa = String(daData[r][1]).trim();
      if (mDa && mDa !== "Mã dự án" && mDa !== "Mã đội") {
        mapDA[mDa] = tDa;
      }
    }
  }
  
  var items = [];
  var units = [];
  
  for (var i = 0; i < valuesDM.length; i++) {
    var maDuAn  = String(valuesDM[i][0]).trim();
    var maTB    = String(valuesDM[i][1]).trim();
    var tenTB   = String(valuesDM[i][2]).trim();
    var donVi   = String(valuesDM[i][3]).trim();
    var soLuong = valuesDM[i][4];
    var doiNhan = String(valuesDM[i][5]).trim();
    
    if (maTB && soLuong !== "") {
      items.push({
        maDuAn: maDuAn ? maDuAn : "DA880",
        maTB: maTB,
        tenTB: tenTB,
        donVi: donVi,
        soLuong: soLuong
      });
    }
    
    if (doiNhan && doiNhan.toLowerCase() !== "nan") {
      var parts = doiNhan.split(",");
      for (var p = 0; p < parts.length; p++) {
        var uClean = parts[p].trim();
        if (uClean && units.indexOf(uClean) === -1) {
          units.push(uClean);
        }
      }
    }
  }
  
  if (items.length === 0) return;
  if (units.length === 0) { units = [""]; }
  
  var rowsToAppend = [];
  for (var u = 0; u < units.length; u++) {
    var currentUnit = units[u];
    for (var it = 0; it < items.length; it++) {
      var item = items[it];
      var m_da = item.maDuAn;
      var t_da = mapDA[m_da] || m_da;
      
      rowsToAppend.push([
        m_da, item.maTB, t_da, item.tenTB, item.soLuong, item.donVi, "", currentUnit, ""
      ]);
    }
  }
  
  if (rowsToAppend.length > 0) {
    var nextRow = sheetKho.getLastRow() + 1;
    if (nextRow < 3) nextRow = 3;
    sheetKho.getRange(nextRow, 1, rowsToAppend.length, rowsToAppend[0].length).setValues(rowsToAppend);
  }
  
  tinhToanTonKhoNhapKho();
  SpreadsheetApp.getActiveSpreadsheet().toast("Phân bổ thành công và đã cập nhật tồn kho!", "Thông báo", 3);
}

// ==========================================
// 2. HÀM TÍNH TOÁN TỒN KHO (CHỐT CHẶN AN TOÀN TUYỆT ĐỐI KHÔNG BỊ DỰ NỢ RÁC)
// ==========================================
function tinhToanTonKhoNhapKho() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetNhap = ss.getSheetByName("NHAP_KHO");
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  
  if (!sheetNhap) return;
  
  var lastRowNhap = sheetNhap.getLastRow();
  if (lastRowNhap < 3) return;
  
  var phanBoMap = {};
  var hasActiveData = false;
  
  if (sheetKho) {
    var lastRowKho = sheetKho.getLastRow();
    if (lastRowKho >= 3) {
      var khoData = sheetKho.getRange(3, 1, lastRowKho - 2, 9).getValues();
      
      for (var k = 0; k < khoData.length; k++) {
        var mDA = String(khoData[k][0]).trim();        // Cột A: Mã dự án
        var mSKU = String(khoData[k][1]).trim();       // Cột B: Mã SKU
        var soLuongPhanBo = parseFloat(khoData[k][4]); // Cột E: Số lượng
        
        // KIỂM TRA CỰC KỲ KHẮT KHE: Chỉ khi SKU có chữ thật VÀ số lượng là số dương khác 0
        if (mSKU !== "" && mSKU !== "null" && !isNaN(soLuongPhanBo) && soLuongPhanBo > 0) {
          hasActiveData = true;
          var key = mDA + "_" + mSKU;
          phanBoMap[key] = (phanBoMap[key] || 0) + soLuongPhanBo;
        }
      }
    }
  }
  
  var nhapData = sheetNhap.getRange(3, 1, lastRowNhap - 2, 5).getValues();
  var tonKhoValues = [];
  
  for (var n = 0; n < nhapData.length; n++) {
    var mDA_nhap = String(nhapData[n][0]).trim();
    var mSKU_nhap = String(nhapData[n][1]).trim();
    var tongNhapThau = parseFloat(nhapData[n][4]) || 0; // Cột E: Tổng nhập thầu
    
    if (mSKU_nhap !== "") {
      var lookupKey = mDA_nhap + "_" + mSKU_nhap;
      
      // Nếu không có dữ liệu phân bổ hợp lệ -> Tồn kho trả về đúng 100% Tổng nhập thầu
      var daPhanBo = hasActiveData ? (phanBoMap[lookupKey] || 0) : 0;
      var tonKho = tongNhapThau - daPhanBo;
      
      tonKhoValues.push([tonKho]);
    } else {
      tonKhoValues.push([""]);
    }
  }
  
  if (tonKhoValues.length > 0) {
    sheetNhap.getRange(3, 6, tonKhoValues.length, 1).setValues(tonKhoValues);
  }
}

// ==========================================
// 3. HÀM TÌM KIẾM, CHECK TRÙNG VÀ ĐỒNG BỘ TỒN KHO TẠI Ô E1
// ==========================================
function timKiemHoacKiemTraTrungLap() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  if (!sheetKho) return;
  
  var keyword = String(sheetKho.getRange(1, 5).getValue()).trim().toLowerCase();
  var lastRow = sheetKho.getLastRow();
  
  tinhToanTonKhoNhapKho();
  
  if (lastRow < 3) {
    SpreadsheetApp.getActiveSpreadsheet().toast("Sheet KHO_PHAN_BO đang trống. Đã đồng bộ tồn kho NHAP_KHO về 100%!", "Thông báo", 3);
    return;
  }
  
  var range = sheetKho.getRange(3, 1, lastRow - 2, 9);
  var values = range.getValues();
  
  if (keyword !== "") {
    for (var i = 0; i < values.length; i++) {
      var rowIndex = i + 3;
      var rowText = "";
      for (var c = 0; c < values[i].length; c++) {
        rowText += " " + String(values[i][c]).trim().toLowerCase();
      }
      
      if (rowText.indexOf(keyword) !== -1) {
        sheetKho.showRows(rowIndex);
        sheetKho.getRange(rowIndex, 1, 1, 9).setBackground("#d9ead3");
      } else {
        sheetKho.hideRows(rowIndex);
      }
    }
    return;
  }
  
  for (var i = 0; i < values.length; i++) {
    sheetKho.showRows(i + 3);
    sheetKho.getRange(i + 3, 1, 1, 9).setBackground(null);
  }
  
  var trackingMap = {};
  var duplicateRows = [];
  
  for (var i = 0; i < values.length; i++) {
    var maDA = String(values[i][0]).trim();
    var maSKU = String(values[i][1]).trim();
    var doiNhan = String(values[i][7]).trim().toLowerCase();
    
    if (maSKU !== "" && doiNhan !== "") {
      var uniqueKey = maDA + "_" + maSKU + "_" + doiNhan;
      var currentLine = i + 3;
      
      if (!trackingMap[uniqueKey]) {
        trackingMap[uniqueKey] = [];
      }
      trackingMap[uniqueKey].push(currentLine);
    }
  }
  
  for (var key in trackingMap) {
    if (trackingMap[key].length > 1) {
      var rows = trackingMap[key];
      for (var r = 0; r < rows.length; r++) {
        duplicateRows.push(rows[r]);
        sheetKho.getRange(rows[r], 1, 1, 9).setBackground("#f4cccc");
      }
    }
  }
  
  if (duplicateRows.length > 0) {
    SpreadsheetApp.getUi().alert("Phát hiện " + duplicateRows.length + " dòng bị trùng lặp ở các dòng: " + duplicateRows.join(", ") + ". Đã tô đỏ và đồng bộ tồn kho!");
  } else {
    SpreadsheetApp.getActiveSpreadsheet().toast("Đã đồng bộ tồn kho và kiểm tra trùng lặp thành công!", "Thông báo", 3);
  }
}
