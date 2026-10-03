function dongBoTonKhoNhapKho() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheetKho = ss.getSheetByName("KHO_PHAN_BO");
  var sheetNhap = ss.getSheetByName("NHAP_KHO");
  if (!sheetKho || !sheetNhap) {
    ss.toast("Không tìm thấy sheet KHO_PHAN_BO hoặc NHAP_KHO!", "Lỗi", 3);
    return;
  }
  
  // 1. Quét dữ liệu đã phân bổ từ KHO_PHAN_BO
  var khoData = sheetKho.getDataRange().getValues();
  var phanBoMap = {};
  
  for (var r = 2; r < khoData.length; r++) {
    var mDa = String(khoData[r][0]).trim();
    var mSku = String(khoData[r][1]).trim();
    var slPb = parseFloat(khoData[r][4]) || 0;
    if (mSku) {
      var key = mDa + "_" + mSku;
      phanBoMap[key] = (phanBoMap[key] || 0) + slPb;
    }
  }
  
  // 2. Quét sheet NHAP_KHO và tính toán lại tồn kho (Tổng nhập - Đã phân bổ)
  var nhapData = sheetNhap.getDataRange().getValues();
  var tonKhoValues = [];
  
  for (var r = 2; r < nhapData.length; r++) {
    var row = nhapData[r];
    var mDaNhap = String(row[0]).trim();
    var mSkuNhap = String(row[1]).trim();
    var tongNhap = parseFloat(row[4]) || 0; // Cột E: Tổng nhập thầu
    
    if (mSkuNhap) {
      var lookupKey = mDaNhap + "_" + mSkuNhap;
      var daPb = phanBoMap[lookupKey] || 0;
      var tonKho = tongNhap - daPb; // Nếu KHO_PHAN_BO trống, daPb = 0 => Tồn kho = Tổng nhập
      tonKhoValues.push([tonKho]);
    } else {
      tonKhoValues.push([""]);
    }
  }
  
  // 3. Cập nhật lại Cột F của NHAP_KHO
  if (tonKhoValues.length > 0) {
    sheetNhap.getRange(3, 6, tonKhoValues.length, 1).setValues(tonKhoValues);
    ss.toast("✅ Đã đồng bộ lại toàn bộ tồn kho vào NHAP_KHO thành công!", "Thành công", 4);
  }
}
