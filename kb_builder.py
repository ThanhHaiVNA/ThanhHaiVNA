from __future__ import annotations
from typing import List, Dict, Any, Tuple

import pandas as pd

from excel_utils import (
    safe_read_sheet,
    _str,
    _safe_int,
    _id_from_code_prefix,
    safe_get_col,
)


def build_kb_from_excel(
    xlsx_path: str
) -> Tuple[List[Dict[str, Any]], Dict[int, str], Dict[int, Dict[str, str]]]:
    """    Đọc các sheet trong datasjet.xlsx và build KB_DOCS cho RAG.

    Trả về:
        - docs: list document (list[dict]) để làm RAG
        - disease_name: dict id_benh -> tên bệnh
        - symptom_dict: dict id_benh -> {symptoms, link}
    """
    docs: List[Dict[str, Any]] = []
    doc_id = 1

    # --------------------------------------------------------
    # 3.1. BỆNH, TRIỆU CHỨNG, NHÓM BỆNH
    # --------------------------------------------------------
    dim_benh = safe_read_sheet(xlsx_path, "dim_benh", header=None)
    trieu_chung = safe_read_sheet(xlsx_path, "trieu_chung", header=None)
    nhombenh = safe_read_sheet(xlsx_path, "nhombenh", header=None)
    map_nhombenh_benh = safe_read_sheet(xlsx_path, "map_nhombenh_benh", header=None)

    if dim_benh is None:
        raise RuntimeError("❌ Thiếu sheet dim_benh trong Excel.")

    # disease_id -> name
    dim_benh = dim_benh.iloc[:, :2]
    dim_benh.columns = [0, 1]
    disease_name: Dict[int, str] = {}
    for _, r in dim_benh.iterrows():
        did = _safe_int(r[0])
        if did is None:
            continue
        disease_name[did] = _str(r[1])

    # disease_id -> {symptoms, link}
    symptom_dict: Dict[int, Dict[str, str]] = {}
    if trieu_chung is not None:
        trieu_chung = trieu_chung.iloc[:, :3]
        trieu_chung.columns = [0, 1, 2]
        for _, r in trieu_chung.iterrows():
            did = _safe_int(r[0])
            if did is None:
                continue
            symptom_dict[did] = {
                "symptoms": _str(r[1]),
                "link": _str(r[2]),
            }

    # group_id -> group_name
    group_name: Dict[int, str] = {}
    if nhombenh is not None:
        nhombenh = nhombenh.iloc[:, :2]
        nhombenh.columns = [0, 1]
        for _, r in nhombenh.iterrows():
            gid = _safe_int(r[0])
            if gid is None:
                continue
            group_name[gid] = _str(r[1])

    # disease_groups: disease_id -> [group_name...]
    disease_groups: Dict[int, List[str]] = {did: [] for did in disease_name.keys()}
    if map_nhombenh_benh is not None:
        map_nhombenh_benh = map_nhombenh_benh.iloc[:, :2]
        map_nhombenh_benh.columns = [0, 1]
        for _, r in map_nhombenh_benh.iterrows():
            gid = _safe_int(r[0])
            did = _safe_int(r[1])
            if gid is None or did is None:
                continue
            gname = group_name.get(gid, f"Nhóm {gid}")
            if did in disease_groups:
                disease_groups[did].append(gname)

    # --------------------------------------------------------
    # 3.2. THUỐC TÂY: CORE + DƯỢC LỰC + DƯỢC ĐỘNG + TÍNH CHẤT
    # --------------------------------------------------------
    dim_thuoctay = safe_read_sheet(xlsx_path, "dim_thuoctay", header=None)
    tht_cochetacdong = safe_read_sheet(xlsx_path, "thuoctay_cochetacdong", header=None)
    tht_duocluchoc = safe_read_sheet(xlsx_path, "thuoctay_duocluchoc", header=None)
    tht_thoigiantacdung = safe_read_sheet(xlsx_path, "thuoctay_thoigiantacdung", header=None)
    tht_duocdonghoc = safe_read_sheet(xlsx_path, "thuoctay_duocdonghoc", header=None)
    tht_dacdiemhoahoc = safe_read_sheet(xlsx_path, "thuoctay_dacdiemhoahoc", header=None)
    tht_dacdiemnguongoc = safe_read_sheet(xlsx_path, "thuoctay_dacdiemnguongoc", header=None)
    tht_doctinh = safe_read_sheet(xlsx_path, "thuoctay_doctinh", header=None)
    tht_tinhchatlyhoa = safe_read_sheet(xlsx_path, "thuoctay_tinhchatlyhoa", header=None)

    drug_core: Dict[int, Dict[str, Any]] = {}
    drug_mech: Dict[int, List[str]] = {}
    drug_pk: Dict[int, List[str]] = {}
    drug_chem: Dict[int, List[str]] = {}
    drug_origin: Dict[int, List[str]] = {}
    drug_toxic: Dict[int, List[str]] = {}
    drug_time: Dict[int, List[str]] = {}
    drug_physchem: Dict[int, List[str]] = {}

    # Core: dim_thuoctay
    if dim_thuoctay is not None:
        dim_thuoctay = dim_thuoctay.iloc[:, :6]
        dim_thuoctay.columns = [0, 1, 2, 3, 4, 5]
        for _, r in dim_thuoctay.iterrows():
            did = _safe_int(r[0])
            if did is None:
                continue
            drug_core[did] = {
                "drug_name": _str(r[1]),
                "active": _str(r[2]),
                "brands": _str(r[3]),
                "active_short": _str(r[4]),
                "warnings": _str(r[5]),
            }

    # Cơ chế tác động (PD): thuoctay_cochetacdong
    if tht_cochetacdong is not None:
        tht_cochetacdong.columns = list(range(tht_cochetacdong.shape[1]))
        for _, r in tht_cochetacdong.iterrows():
            drug_id = _safe_int(safe_get_col(r, 1))
            if drug_id is None:
                continue
            mech_code = _str(safe_get_col(r, 2))
            action = _str(safe_get_col(r, 3))
            mech = _str(safe_get_col(r, 4))
            text = f"- Cơ chế {mech_code}: {action}. Giải thích: {mech}"
            drug_mech.setdefault(drug_id, []).append(text)

    # Dược lực học lâm sàng + cảnh báo (không dùng cột liều): thuoctay_duocluchoc
    if tht_duocluchoc is not None:
        tht_duocluchoc.columns = list(range(tht_duocluchoc.shape[1]))
        for _, r in tht_duocluchoc.iterrows():
            code = safe_get_col(r, 1)
            drug_id = _id_from_code_prefix(code)
            if drug_id is None:
                continue
            effect = _str(safe_get_col(r, 2))
            note = _str(safe_get_col(r, 4))
            if effect or note:
                text = f"- Tác dụng lâm sàng: {effect}. Ghi chú an toàn/đặc điểm: {note}"
                drug_mech.setdefault(drug_id, []).append(text)

    # Thời gian tác dụng: thuoctay_thoigiantacdung
    if tht_thoigiantacdung is not None:
        tht_thoigiantacdung.columns = list(range(tht_thoigiantacdung.shape[1]))
        for _, r in tht_thoigiantacdung.iterrows():
            code = safe_get_col(r, 1)
            drug_id = _id_from_code_prefix(code)
            if drug_id is None:
                continue
            onset = _str(safe_get_col(r, 2))
            duration = _str(safe_get_col(r, 3))
            text = f"- Thời gian khởi phát tác dụng: {onset}. Thời gian duy trì tác dụng: {duration}"  # noqa: E501
            drug_time.setdefault(drug_id, []).append(text)

    # Dược động học: thuoctay_duocdonghoc
    if tht_duocdonghoc is not None:
        tht_duocdonghoc.columns = list(range(tht_duocdonghoc.shape[1]))
        for _, r in tht_duocdonghoc.iterrows():
            drug_id = _safe_int(safe_get_col(r, 0))
            if drug_id is None:
                continue
            absorption = _str(safe_get_col(r, 1))
            distribution = _str(safe_get_col(r, 2))
            metabolism = _str(safe_get_col(r, 3))
            elimination = _str(safe_get_col(r, 4))
            text = (
                f"- Hấp thu: {absorption}\n"
                f"- Phân bố: {distribution}\n"
                f"- Chuyển hóa: {metabolism}\n"
                f"- Thải trừ: {elimination}"
            )
            drug_pk.setdefault(drug_id, []).append(text)

    # Đặc điểm hóa học: thuoctay_dacdiemhoahoc
    if tht_dacdiemhoahoc is not None:
        tht_dacdiemhoahoc.columns = list(range(tht_dacdiemhoahoc.shape[1]))
        for _, r in tht_dacdiemhoahoc.iterrows():
            drug_id = _safe_int(safe_get_col(r, 0))
            if drug_id is None:
                continue
            text = (
                f"- Đặc điểm hóa học: {_str(safe_get_col(r, 1))}\n"
                f"- Độ tan: {_str(safe_get_col(r, 2))}\n"
                f"- Độ bền/ổn định: {_str(safe_get_col(r, 3))}\n"
                f"- Ghi chú thêm: {_str(safe_get_col(r, 4))}"
            )
            drug_chem.setdefault(drug_id, []).append(text)

    # Nguồn gốc, bản chất: thuoctay_dacdiemnguongoc
    if tht_dacdiemnguongoc is not None:
        tht_dacdiemnguongoc.columns = list(range(tht_dacdiemnguongoc.shape[1]))
        for _, r in tht_dacdiemnguongoc.iterrows():
            drug_id = _safe_int(safe_get_col(r, 0))
            if drug_id is None:
                continue
            text = (
                f"- Nguồn gốc/hóa dược: {_str(safe_get_col(r, 1))}\n"
                f"- Quy trình/ứng dụng: {_str(safe_get_col(r, 2))}\n"
                f"- Dạng dùng điển hình: {_str(safe_get_col(r, 3))}\n"
                f"- Ghi chú: {_str(safe_get_col(r, 4))}"
            )
            drug_origin.setdefault(drug_id, []).append(text)

    # Độc tính & cảnh báo: thuoctay_doctinh
    if tht_doctinh is not None:
        tht_doctinh.columns = list(range(tht_doctinh.shape[1]))
        for _, r in tht_doctinh.iterrows():
            drug_id = _safe_int(safe_get_col(r, 0))
            if drug_id is None:
                continue
            text = (
                f"- Độc tính/biến cố: {_str(safe_get_col(r, 1))}\n"
                f"- Nhóm đối tượng cần thận trọng: {_str(safe_get_col(r, 2))}\n"
                f"- Tương tác/ghi chú khác: {_str(safe_get_col(r, 3))}"
            )
            drug_toxic.setdefault(drug_id, []).append(text)

    # Tính chất lý – hóa: thuoctay_tinhchatlyhoa
    if tht_tinhchatlyhoa is not None:
        tht_tinhchatlyhoa.columns = list(range(tht_tinhchatlyhoa.shape[1]))
        for _, r in tht_tinhchatlyhoa.iterrows():
            drug_id = _safe_int(safe_get_col(r, 0))
            if drug_id is None:
                continue
            mp_low = _str(safe_get_col(r, 1))
            mp_high = _str(safe_get_col(r, 2))
            pka = _str(safe_get_col(r, 3))
            logp = _str(safe_get_col(r, 4))
            text = (
                f"- Nhiệt độ nóng chảy (ước tính): {mp_low}–{mp_high}\n"
                f"- pKa: {pka}; logP (tính thân dầu/nước): {logp}"
            )
            drug_physchem.setdefault(drug_id, []).append(text)

    # --------------------------------------------------------
    # 3.3. THẢO DƯỢC: CORE + DƯỢC LỰC + DƯỢC ĐỘNG + TÍNH CHẤT
    # --------------------------------------------------------
    dim_thaoduoc = safe_read_sheet(xlsx_path, "dim_thaoduoc", header=None)
    thd_cochetacdong = safe_read_sheet(xlsx_path, "thaoduoc_cochetacdong", header=None)
    thd_duocluchoc = safe_read_sheet(xlsx_path, "thaoduoc_duocluchoc", header=None)
    thd_thoigiantacdung = safe_read_sheet(xlsx_path, "thaoduoc_thoigiantacdung", header=None)
    thd_duocdonghoc = safe_read_sheet(xlsx_path, "thaoduoc_duocdonghoc", header=None)
    thd_dacdiemhoahoc = safe_read_sheet(xlsx_path, "thaoduoc_dacdiemhoahoc", header=None)
    thd_dacdiemnguongoc = safe_read_sheet(xlsx_path, "thaoduoc_dacdiemnguongoc", header=None)
    thd_doctinh = safe_read_sheet(xlsx_path, "thaoduoc_doctinh", header=None)
    thd_tinhchatlyhoa = safe_read_sheet(xlsx_path, "thaoduoc_tinhchatlyhoa", header=None)

    herb_core: Dict[int, Dict[str, Any]] = {}
    herb_mech: Dict[int, List[str]] = {}
    herb_pk: Dict[int, List[str]] = {}
    herb_chem: Dict[int, List[str]] = {}
    herb_origin: Dict[int, List[str]] = {}
    herb_toxic: Dict[int, List[str]] = {}
    herb_time: Dict[int, List[str]] = {}
    herb_physchem: Dict[int, List[str]] = {}

    # Core: dim_thaoduoc
    if dim_thaoduoc is not None:
        dim_thaoduoc.columns = list(range(dim_thaoduoc.shape[1]))
        for _, r in dim_thaoduoc.iterrows():
            herb_id = _safe_int(safe_get_col(r, 0))
            if herb_id is None:
                continue

            herb_core[herb_id] = {
                "herb_name": _str(safe_get_col(r, 1)),
                "formula": _str(safe_get_col(r, 2)),
                "usage": _str(safe_get_col(r, 3)),
                # KHÔNG dùng col4 (liều)
                "warning": (
                    _str(safe_get_col(r, 5)) + " " + _str(safe_get_col(r, 8))
                ).strip(),
                "contra": _str(safe_get_col(r, 6)),
                "reference": _str(safe_get_col(r, 7)),
            }

    # Cơ chế tác động: thaoduoc_cochetacdong
    if thd_cochetacdong is not None:
        thd_cochetacdong.columns = list(range(thd_cochetacdong.shape[1]))
        for _, r in thd_cochetacdong.iterrows():
            herb_id = _safe_int(safe_get_col(r, 1))
            if herb_id is None:
                continue
            mech_code = _str(safe_get_col(r, 2))
            action = _str(safe_get_col(r, 3))
            mech = _str(safe_get_col(r, 4))
            text = f"- Cơ chế {mech_code}: {action}. Giải thích (theo mô tả): {mech}"
            herb_mech.setdefault(herb_id, []).append(text)

    # Dược lực học hỗ trợ lâm sàng: thaoduoc_duocluchoc
    if thd_duocluchoc is not None:
        thd_duocluchoc.columns = list(range(thd_duocluchoc.shape[1]))
        for _, r in thd_duocluchoc.iterrows():
            code = safe_get_col(r, 1)
            herb_id = _id_from_code_prefix(code)
            if herb_id is None:
                continue
            eff1 = _str(safe_get_col(r, 2))
            eff2 = _str(safe_get_col(r, 3))
            eff3 = _str(safe_get_col(r, 4))
            joined = "; ".join([x for x in (eff1, eff2, eff3) if x])
            if joined:
                text = f"- Tác dụng dược lực hỗ trợ: {joined}"
                herb_mech.setdefault(herb_id, []).append(text)

    # Thời gian tác dụng: thaoduoc_thoigiantacdung
    if thd_thoigiantacdung is not None:
        thd_thoigiantacdung.columns = list(range(thd_thoigiantacdung.shape[1]))
        for _, r in thd_thoigiantacdung.iterrows():
            code = safe_get_col(r, 1)
            herb_id = _id_from_code_prefix(code)
            if herb_id is None:
                continue
            onset = _str(safe_get_col(r, 2))
            duration = _str(safe_get_col(r, 3))
            text = f"- Thời gian bắt đầu cảm nhận tác dụng: {onset}. Thời gian duy trì: {duration}"  # noqa: E501
            herb_time.setdefault(herb_id, []).append(text)

    # Dược động học: thaoduoc_duocdonghoc
    if thd_duocdonghoc is not None:
        thd_duocdonghoc.columns = list(range(thd_duocdonghoc.shape[1]))
        for _, r in thd_duocdonghoc.iterrows():
            herb_id = _safe_int(safe_get_col(r, 0))
            if herb_id is None:
                continue
            abs_ = _str(safe_get_col(r, 1))
            dist = _str(safe_get_col(r, 2))
            elim = _str(safe_get_col(r, 3))
            note = _str(safe_get_col(r, 4))
            text = (
                f"- Hấp thu & phân bố: {abs_}\n"
                f"- Thời gian/tính chất tác dụng: {dist}\n"
                f"- Đặc điểm thải trừ/tích lũy: {elim}\n"
                f"- Ghi chú thêm: {note}"
            )
            herb_pk.setdefault(herb_id, []).append(text)

    # Đặc điểm hóa học: thaoduoc_dacdiemhoahoc
    if thd_dacdiemhoahoc is not None:
        thd_dacdiemhoahoc.columns = list(range(thd_dacdiemhoahoc.shape[1]))
        for _, r in thd_dacdiemhoahoc.iterrows():
            herb_id = _safe_int(safe_get_col(r, 0))
            if herb_id is None:
                continue
            text = (
                f"- Thành phần hóa học chính: {_str(safe_get_col(r, 1))}\n"
                f"- Độ tan: {_str(safe_get_col(r, 2))}\n"
                f"- Ổn định với nhiệt/điều kiện: {_str(safe_get_col(r, 3))}\n"
                f"- Cách bảo quản: {_str(safe_get_col(r, 4))}"
            )
            herb_chem.setdefault(herb_id, []).append(text)

    # Đặc điểm nguồn gốc: thaoduoc_dacdiemnguongoc
    if thd_dacdiemnguongoc is not None:
        thd_dacdiemnguongoc.columns = list(range(thd_dacdiemnguongoc.shape[1]))
        for _, r in thd_dacdiemnguongoc.iterrows():
            herb_id = _safe_int(safe_get_col(r, 0))
            if herb_id is None:
                continue
            text = (
                f"- Bộ phận dùng: {_str(safe_get_col(r, 1))}\n"
                f"- Vùng trồng/điều kiện: {_str(safe_get_col(r, 2))}\n"
                f"- Thời điểm thu hái: {_str(safe_get_col(r, 3))}\n"
                f"- Dạng sử dụng: {_str(safe_get_col(r, 4))}"
            )
            herb_origin.setdefault(herb_id, []).append(text)

    # Độc tính, thận trọng: thaoduoc_doctinh
    if thd_doctinh is not None:
        thd_doctinh.columns = list(range(thd_doctinh.shape[1]))
        for _, r in thd_doctinh.iterrows():
            herb_id = _safe_int(safe_get_col(r, 0))
            if herb_id is None:
                continue
            text = (
                f"- Độc tính/triệu chứng không mong muốn: {_str(safe_get_col(r, 1))}\n"  # noqa: E501
                f"- Nhóm đối tượng cần thận trọng: {_str(safe_get_col(r, 2))}\n"
                f"- Ghi chú về dữ liệu an toàn: {_str(safe_get_col(r, 3))}"
            )
            herb_toxic.setdefault(herb_id, []).append(text)

    # Tính chất lý – hóa & cảm quan: thaoduoc_tinhchatlyhoa
    if thd_tinhchatlyhoa is not None:
        thd_tinhchatlyhoa.columns = list(range(thd_tinhchatlyhoa.shape[1]))
        for _, r in thd_tinhchatlyhoa.iterrows():
            herb_id = _safe_int(safe_get_col(r, 0))
            if herb_id is None:
                continue
            text = (
                f"- Vị, tính: {_str(safe_get_col(r, 1))}\n"
                f"- Đặc điểm tinh dầu/kết cấu: {_str(safe_get_col(r, 2))}\n"
                f"- Màu sắc & cảm quan: {_str(safe_get_col(r, 3))}\n"
                f"- Độ ổn định/ảnh hưởng môi trường: {_str(safe_get_col(r, 4))}"
            )
            herb_physchem.setdefault(herb_id, []).append(text)

    # --------------------------------------------------------
    # 3.4. MAP BỆNH – THUỐC TÂY / THẢO DƯỢC + SURVEY
    # --------------------------------------------------------
    map_benh_thuoctay = safe_read_sheet(xlsx_path, "map_benh_thuoctay", header=None)
    map_benh_thaoduoc_survey = safe_read_sheet(xlsx_path, "map_benh_thaoduoc_survey", header=None)

    disease_to_drugs: Dict[int, List[int]] = {did: [] for did in disease_name.keys()}
    disease_to_herbs: Dict[int, List[int]] = {did: [] for did in disease_name.keys()}

    # map_benh_thuoctay
    if map_benh_thuoctay is not None:
        map_benh_thuoctay.columns = list(range(map_benh_thuoctay.shape[1]))
        for _, r in map_benh_thuoctay.iterrows():
            did = _safe_int(safe_get_col(r, 0))
            drug_id = _safe_int(safe_get_col(r, 1))
            if did is None or drug_id is None:
                continue
            author = _str(safe_get_col(r, 2))
            title = _str(safe_get_col(r, 3))
            url = _str(safe_get_col(r, 4))

            if did in disease_to_drugs:
                disease_to_drugs[did].append(drug_id)

            dname = disease_name.get(did, f"Bệnh ID {did}")
            dinfo = drug_core.get(drug_id, {})
            ddrug_name = dinfo.get("drug_name", f"Thuốc ID {drug_id}")
            active = dinfo.get("active", "")
            brands = dinfo.get("brands", "")
            warnings = dinfo.get("warnings", "")
            sym = symptom_dict.get(did, {})

            mech_text = "\n".join(drug_mech.get(drug_id, [])[:3])
            pk_text = "\n".join(drug_pk.get(drug_id, [])[:1])
            time_text = "\n".join(drug_time.get(drug_id, [])[:1])

            text = (
                f"Bệnh trong CSDL: {dname} (ID {did}).\n"
                f"Triệu chứng gợi ý (nếu có): {sym.get('symptoms', '')}\n\n"
                f"Thuốc tây liên quan trong CSDL: {ddrug_name} (ID {drug_id}).\n"
                f"Hoạt chất chính: {active}.\n"
                f"Biệt dược thường gặp: {brands}.\n"
                f"Cảnh báo & thận trọng (tóm tắt): {warnings}.\n\n"
                f"Một số thông tin dược lực/dược động (tóm lược):\n"
                f"{mech_text}\n"
                f"{pk_text}\n"
                f"{time_text}\n\n"
                f"Tài liệu tham khảo liên quan:\n"
                f"- Tác giả/nhóm nghiên cứu: {author}\n"
                f"- Tiêu đề: {title}\n"
                f"- Link: {url}\n"
            )

            docs.append({
                "id": doc_id,
                "title": f"{dname} - Thuốc tây: {ddrug_name}",
                "type": "disease_drug",
                "text": text,
            })
            doc_id += 1

            lit_text = (
                f"Tài liệu tham khảo về thuốc tây trong bối cảnh bệnh {dname}.\n"
                f"Tác giả/nguồn: {author}\n"
                f"Tiêu đề: {title}\n"
                f"Link: {url}\n"
            )
            docs.append({
                "id": doc_id,
                "title": f"Tài liệu thuốc tây: {title}",
                "type": "literature",
                "text": lit_text,
            })
            doc_id += 1

    # map_benh_thaoduoc_survey
    if map_benh_thaoduoc_survey is not None:
        map_benh_thaoduoc_survey.columns = list(range(map_benh_thaoduoc_survey.shape[1]))
        for _, r in map_benh_thaoduoc_survey.iterrows():
            did = _safe_int(safe_get_col(r, 0))
            herb_id = _safe_int(safe_get_col(r, 1))
            if did is None or herb_id is None:
                continue
            author = _str(safe_get_col(r, 3))
            title = _str(safe_get_col(r, 4))
            url = _str(safe_get_col(r, 5))

            if did in disease_to_herbs:
                disease_to_herbs[did].append(herb_id)

            dname = disease_name.get(did, f"Bệnh ID {did}")
            hinfo = herb_core.get(herb_id, {})
            herb_name = hinfo.get("herb_name", f"Thảo dược ID {herb_id}")
            formula = hinfo.get("formula", "")
            usage = hinfo.get("usage", "")
            h_warning = hinfo.get("warning", "")
            h_contra = hinfo.get("contra", "")
            h_ref = hinfo.get("reference", "")
            sym = symptom_dict.get(did, {})

            mech_text = "\n".join(herb_mech.get(herb_id, [])[:3])
            pk_text = "\n".join(herb_pk.get(herb_id, [])[:1])
            time_text = "\n".join(herb_time.get(herb_id, [])[:1])

            text = (
                f"Bệnh trong CSDL: {dname} (ID {did}).\n"
                f"Triệu chứng gợi ý (nếu có): {sym.get('symptoms', '')}\n\n"
                f"Thảo dược/bài thuốc liên quan trong CSDL: {herb_name} (ID {herb_id}).\n"
                f"Công thức/bài thuốc: {formula}.\n"
                f"Cách dùng (mô tả chung, không dùng để tự kê đơn): {usage}.\n"
                f"Cảnh báo & lưu ý: {h_warning}.\n"
                f"Chống chỉ định: {h_contra}.\n"
                f"Nguồn tham khảo gốc của bài thuốc (nếu có): {h_ref}.\n\n"
                f"Một số thông tin dược lực/dược động (tóm lược):\n"
                f"{mech_text}\n"
                f"{pk_text}\n"
                f"{time_text}\n\n"
                f"Tài liệu khảo sát/ tham khảo cụ thể:\n"
                f"- Tác giả/nguồn: {author}\n"
                f"- Tiêu đề: {title}\n"
                f"- Link: {url}\n"
            )

            docs.append({
                "id": doc_id,
                "title": f"{dname} - Thảo dược: {herb_name}",
                "type": "disease_herb",
                "text": text,
            })
            doc_id += 1

            lit_text = (
                f"Tài liệu tham khảo về thảo dược trong bối cảnh bệnh {dname}.\n"
                f"Tác giả/nguồn: {author}\n"
                f"Tiêu đề: {title}\n"
                f"Link: {url}\n"
            )
            docs.append({
                "id": doc_id,
                "title": f"Tài liệu thảo dược: {title}",
                "type": "literature",
                "text": lit_text,
            })
            doc_id += 1

    # --------------------------------------------------------
    # 3.5. DOC TỔNG QUAN BỆNH
    # --------------------------------------------------------
    for did, dname in disease_name.items():
        groups = ", ".join(sorted(set(disease_groups.get(did, [])))) or "Chưa phân nhóm"
        sym = symptom_dict.get(did, {})
        drug_list = disease_to_drugs.get(did, [])
        herb_list = disease_to_herbs.get(did, [])

        summary_drugs = ", ".join(
            sorted({drug_core.get(didrug, {}).get("drug_name", f"Thuốc ID {didrug}") for didrug in drug_list})  # noqa: E501
        )
        summary_herbs = ", ".join(
            sorted({herb_core.get(hid, {}).get("herb_name", f"Thảo dược ID {hid}") for hid in herb_list})  # noqa: E501
        )

        text = (
            f"Bệnh: {dname} (ID {did}).\n"
            f"Nhóm bệnh (theo cơ quan/hệ thống) trong CSDL: {groups}.\n"
            f"Triệu chứng gợi ý được mô tả: {sym.get('symptoms', '')}\n"
            f"Link tham khảo chi tiết (nếu có): {sym.get('link', '')}\n\n"
            f"Các thuốc tây được liên kết trong CSDL (liệt kê tên): {summary_drugs or 'Chưa có dữ liệu'}\n"  # noqa: E501
            f"Các thảo dược/bài thuốc được liên kết trong CSDL (liệt kê tên): {summary_herbs or 'Chưa có dữ liệu'}\n"  # noqa: E501
        )

        docs.append({
            "id": doc_id,
            "title": f"Tổng quan bệnh: {dname}",
            "type": "disease",
            "text": text,
        })
        doc_id += 1

    # --------------------------------------------------------
    # 3.6. DOC CHI TIẾT TỪNG THUỐC TÂY
    # --------------------------------------------------------
    for drug_id, info in drug_core.items():
        mech_text = "\n".join(drug_mech.get(drug_id, []))
        pk_text = "\n".join(drug_pk.get(drug_id, []))
        chem_text = "\n".join(drug_chem.get(drug_id, []))
        origin_text = "\n".join(drug_origin.get(drug_id, []))
        toxic_text = "\n".join(drug_toxic.get(drug_id, []))
        time_text = "\n".join(drug_time.get(drug_id, []))
        physchem_text = "\n".join(drug_physchem.get(drug_id, []))

        text = (
            f"Thuốc tây trong CSDL: {info['drug_name']} (ID {drug_id}).\n"
            f"Hoạt chất chính: {info['active']}.\n"
            f"Biệt dược phổ biến (nếu có): {info['brands']}.\n"
            f"Tên hoạt chất rút gọn (nếu có): {info['active_short']}.\n"
            f"Cảnh báo & thận trọng tóm tắt: {info['warnings']}.\n\n"
            f"— Đặc điểm dược lực học (cơ chế, tác dụng):\n{mech_text}\n\n"
            f"— Dược động học (ADME):\n{pk_text}\n\n"
            f"— Đặc điểm hóa học:\n{chem_text}\n\n"
            f"— Nguồn gốc & bào chế:\n{origin_text}\n\n"
            f"— Độc tính & nhóm thận trọng:\n{toxic_text}\n\n"
            f"— Thời gian khởi phát & kéo dài tác dụng:\n{time_text}\n\n"
            f"— Tính chất lý – hóa (nhiệt độ nóng chảy, pKa, logP…):\n{physchem_text}\n"
        )

        docs.append({
            "id": doc_id,
            "title": f"Thuốc tây: {info['drug_name']}",
            "type": "drug",
            "text": text,
        })
        doc_id += 1

    # --------------------------------------------------------
    # 3.7. DOC CHI TIẾT TỪNG THẢO DƯỢC
    # --------------------------------------------------------
    for herb_id, info in herb_core.items():
        mech_text = "\n".join(herb_mech.get(herb_id, []))
        pk_text = "\n".join(herb_pk.get(herb_id, []))
        chem_text = "\n".join(herb_chem.get(herb_id, []))
        origin_text = "\n".join(herb_origin.get(herb_id, []))
        toxic_text = "\n".join(herb_toxic.get(herb_id, []))
        time_text = "\n".join(herb_time.get(herb_id, []))
        physchem_text = "\n".join(herb_physchem.get(herb_id, []))

        text = (
            f"Thảo dược/bài thuốc trong CSDL: {info['herb_name']} (ID {herb_id}).\n"
            f"Công thức/bài thuốc (theo mô tả): {info['formula']}.\n"
            f"Cách dùng (mô tả chung, KHÔNG dùng để tự kê đơn): {info['usage']}.\n"
            f"Cảnh báo và lưu ý: {info['warning']}.\n"
            f"Chống chỉ định: {info['contra']}.\n"
            f"Nguồn tham khảo bài thuốc: {info['reference']}.\n\n"
            f"— Đặc điểm dược lực học (theo YHCT và mô tả hiện đại):\n{mech_text}\n\n"
            f"— Dược động học (hấp thu, phân bố, thải trừ…):\n{pk_text}\n\n"
            f"— Đặc điểm hóa học:\n{chem_text}\n\n"
            f"— Nguồn gốc & bộ phận dùng:\n{origin_text}\n\n"
            f"— Độc tính & nhóm thận trọng:\n{toxic_text}\n\n"
            f"— Thời gian khởi phát & kéo dài tác dụng:\n{time_text}\n\n"
            f"— Tính chất lý – hóa & cảm quan:\n{physchem_text}\n"
        )

        docs.append({
            "id": doc_id,
            "title": f"Thảo dược: {info['herb_name']}",
            "type": "herb",
            "text": text,
        })
        doc_id += 1

    # --------------------------------------------------------
    # 3.8. DISCLAIMER CHUNG
    # --------------------------------------------------------
    disclaimer_text = (
        "Tất cả thông tin về bệnh, thuốc tây và thảo dược trong cơ sở dữ liệu này "  # noqa: E501
        "chỉ mang tính chất tham khảo, dùng cho mục đích giáo dục và hỗ trợ tra cứu.\n"  # noqa: E501
        "Thông tin không phải là đơn thuốc, không thay thế cho chẩn đoán hoặc điều trị trực tiếp.\n"  # noqa: E501
        "Người dùng cần tham khảo ý kiến bác sĩ hoặc nhân viên y tế trước khi bắt đầu, thay đổi "  # noqa: E501
        "hoặc ngừng bất kỳ thuốc hay thảo dược nào."
    )
    docs.append({
        "id": doc_id,
        "title": "Disclaimer y khoa chung",
        "type": "disclaimer",
        "text": disclaimer_text,
    })
    doc_id += 1

    print(f"✅ Đã build KB từ Excel với tổng cộng {len(docs)} documents.")
    return docs, disease_name, symptom_dict
