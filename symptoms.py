from __future__ import annotations
from typing import Dict, Any, List
import re


def _normalize_tokens(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^0-9a-zA-ZÀ-ỹà-ỹ\s]", " ", text)
    tokens = [t for t in text.split() if t]
    return set(tokens)


def find_symptom_matches(
    user_text: str,
    disease_name: Dict[int, str],
    symptom_dict: Dict[int, Dict[str, str]],
    min_score: float = 0.9,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """So khớp triệu chứng đơn giản dựa trên trùng lặp token."""
    user_tokens = _normalize_tokens(user_text)
    if not user_tokens:
        return []

    matches: List[Dict[str, Any]] = []
    for did, info in symptom_dict.items():
        sym_text = info.get("symptoms", "")
        if not sym_text.strip():
            continue
        sym_tokens = _normalize_tokens(sym_text)
        if not sym_tokens:
            continue
        inter = user_tokens.intersection(sym_tokens)
        score = len(inter) / max(1, len(sym_tokens))
        if score >= min_score:
            matches.append({
                "disease_id": did,
                "disease_name": disease_name.get(did, f"Bệnh ID {did}"),
                "score": score,
                "symptoms": sym_text,
                "link": info.get("link", ""),
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:max_results]


def build_symptom_match_block(matches: List[Dict[str, Any]]) -> str:
    if not matches:
        return ""

    lines: List[str] = []
    lines.append("[Gợi ý dựa trên trùng khớp triệu chứng]")
    lines.append(
        "Hệ thống so khớp mô tả triệu chứng của người dùng với mô tả triệu chứng trong CSDL. "  # noqa: E501
        "Các bệnh sau có mức độ TƯƠNG ĐỒNG TRIỆU CHỨNG cao (0–1, càng gần 1 càng giống, ở đây chỉ lấy ≥ 0.9):"  # noqa: E501
    )
    for m in matches:
        lines.append(
            f"- Bệnh: {m['disease_name']} (điểm tương đồng ~ {m['score']:.2f}). "  # noqa: E501
            f"Triệu chứng trong CSDL: {m['symptoms']}"
        )
    lines.append(
        "Đây chỉ là gợi ý về MỨC ĐỘ TƯƠNG ĐỒNG TRIỆU CHỨNG giữa mô tả của người dùng và CSDL, "  # noqa: E501
        "không phải chẩn đoán. Chẩn đoán cần bác sĩ thăm khám trực tiếp."
    )
    return "\n".join(lines) + "\n\n"
