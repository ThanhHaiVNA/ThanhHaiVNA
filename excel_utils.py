from __future__ import annotations
from typing import Any

import pandas as pd


def safe_read_sheet(
    xlsx_path: str,
    sheet_name: str,
    header: int | None = None
) -> pd.DataFrame | None:
    """Đọc một sheet từ Excel an toàn, thử khớp lowercase nếu tên gốc lỗi."""
    import openpyxl

    try:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=header)
        return df
    except Exception as e:
        print(f"⚠️ Lỗi đọc sheet '{sheet_name}' (thử trực tiếp): {e}")

    try:
        book = openpyxl.load_workbook(xlsx_path, read_only=True)
        all_sheets = book.sheetnames
        print(f"ℹ️ Các sheet tìm thấy trong file '{xlsx_path}': {all_sheets}")

        target = sheet_name.lower().strip()
        matched_name = None
        for s in all_sheets:
            if s.lower().strip() == target:
                matched_name = s
                break

        if matched_name is not None:
            print(
                f"✅ Tìm thấy sheet khớp lowercase: '{matched_name}' (thay cho '{sheet_name}'). Thử đọc lại..."
            )
            try:
                df = pd.read_excel(xlsx_path, sheet_name=matched_name, header=header)
                return df
            except Exception as e2:
                print(f"⚠️ Vẫn lỗi khi đọc sheet '{matched_name}': {e2}")
                return None
        else:
            print(
                f"❌ Không tìm thấy sheet nào khớp với '{sheet_name}' (kể cả so sánh lowercase)."
            )
            return None

    except Exception as e:
        print(f"⚠️ Lỗi khi mở workbook '{xlsx_path}': {e}")
        return None


def _str(x: Any) -> str:
    """Chuyển về str, tránh lỗi NaN/None."""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()


def _safe_int(x: Any) -> int | None:
    """Chuyển về int an toàn, lỗi thì trả None."""
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        return int(x)
    except Exception:
        try:
            return int(float(x))
        except Exception:
            return None


def _id_from_code_prefix(code: Any) -> int | None:
    """Lấy phần trước dấu chấm làm ID (vd '1.1' -> 1)."""
    s = _str(code)
    if not s:
        return None
    parts = s.split(".")
    return _safe_int(parts[0])


def safe_get_col(r: pd.Series, idx: int) -> Any:
    """Lấy giá trị cột theo index, nếu không có thì trả về None."""
    if idx in r.index:
        return r[idx]
    return None
