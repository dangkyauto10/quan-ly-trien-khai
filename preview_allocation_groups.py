"""Read-only selection of tender location groups for multi-SKU allocations.

The text pasted from a tender contract is never treated as an instruction.
Only exact, unambiguous active project location names/codes are accepted.
"""
from collections import defaultdict
from io import BytesIO
from pathlib import Path
import unicodedata
import re

from openpyxl import load_workbook


def normalized(value):
    raw = unicodedata.normalize("NFKD", str(value or "")).casefold()
    raw = "".join(c for c in raw if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", raw).strip()


def match_contract_locations(project, all_points, contract_lines):
    """Match newline-separated names/codes against exact project catalog.

    Return (ordered_ids, issues), never fuzzy-guess ambiguous or unknown names.
    """
    catalog = {}
    refs = defaultdict(set)
    for p in all_points:
        pid = str(p.get("Mã điểm", "")).strip()
        if p.get("Mã dự án") != project or not pid or p.get("Trạng thái") != "Hoạt động":
            continue
        if pid in catalog:
            return [], [f"Trùng mã điểm trong danh mục dự án: {pid}."]
        catalog[pid] = p
        for label in (pid, p.get("Tên xã/phường/đơn vị", "")):
            key = normalized(label)
            if key:
                refs[key].add(pid)
    found, seen, issues = [], set(), []
    for idx, text in enumerate(contract_lines, 1):
        line = str(text or "").strip()
        if not line:
            continue
        key = normalized(line)
        matched = sorted(refs.get(key, []))
        if not matched:
            issues.append(f"Dòng {idx}: không tìm thấy địa điểm '{line}' trong dự án.")
        elif len(matched) != 1:
            issues.append(f"Dòng {idx}: '{line}' trùng tên {len(matched)} địa điểm; hãy dùng Mã điểm.")
        elif matched[0] in seen:
            issues.append(f"Dòng {idx}: '{line}' đã được chọn trước đó.")
        else:
            found.append(matched[0])
            seen.add(matched[0])
    if not found:
        issues.append("Chưa chọn được địa điểm hợp lệ.")
    return found, issues


def read_contract_locations_excel(filename, data):
    """Read first Excel column from a named/ID location list, never execute formulas."""
    if Path(filename).suffix.lower() != ".xlsx":
        raise ValueError("Chỉ hỗ trợ Excel .xlsx.")
    if not data or len(data) > 5_000_000:
        raise ValueError("Danh sách Excel trống hoặc lớn hơn 5 MB.")
    workbook = load_workbook(BytesIO(data), read_only=True, data_only=True)
    try:
        ws = workbook.active
        rows = ws.iter_rows(min_row=1, max_row=2001, max_col=min(ws.max_column, 12), values_only=True)
        header = next(rows, None)
        if not header:
            raise ValueError("Excel không có dữ liệu.")
        col = None
        for j, v in enumerate(header):
            if normalized(v) in {"ma điem", "ten xa/phuong/đon vi", "ten đia điem",
                                 "ten xa/phuong/don vi", "ten dia diem"}:
                col = j
                break
        if col is None:
            # Simple one-column name lists without a header are supported.
            if sum(v is not None and str(v).strip() != "" for v in header) == 1:
                col = next(j for j, v in enumerate(header) if v is not None and str(v).strip())
                rows = iter([header] + list(rows))
            else:
                raise ValueError("Cần cột 'Mã điểm' hoặc 'Tên xã/phường/đơn vị'.")
        result = []
        for row in rows:
            value = row[col] if col < len(row) else None
            if value is not None and str(value).strip():
                result.append(str(value).strip())
        if not result:
            raise ValueError("File không có địa điểm nào.")
        return result
    finally:
        workbook.close()


def preview_basket(skus, quantities, selected_count):
    """Readable tender-basket math; never treats allocation as a stock movement."""
    if selected_count < 0 or int(selected_count) != selected_count:
        raise ValueError("Số điểm không hợp lệ.")
    from preview_bulk_allocation import quantity
    return {sku: quantity(quantities.get(sku, 0)) * selected_count for sku in skus}
