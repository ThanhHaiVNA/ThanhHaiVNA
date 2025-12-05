from __future__ import annotations
from typing import Dict, Any, List

import google.generativeai as genai

from config import CHAT_MODEL_NAME
from rag_index import retrieve_top_k, build_context_snippet
from symptoms import find_symptom_matches, build_symptom_match_block
from prompts import SYSTEM_PROMPT


def answer_with_rag(
    query: str,
    index: Dict[str, Any],
    disease_name: Dict[int, str],
    symptom_dict: Dict[int, Dict[str, str]],
) -> str:
    # 1) Gợi ý bệnh theo triệu chứng
    matches = find_symptom_matches(
        user_text=query,
        disease_name=disease_name,
        symptom_dict=symptom_dict,
        min_score=0.9,
        max_results=5,
    )
    symptom_block = build_symptom_match_block(matches)

    # 2) RAG: retrieve tài liệu
    retrieved = retrieve_top_k(query, index, k=4)
    context_docs = build_context_snippet(retrieved)

    full_context = symptom_block + context_docs

    user_prompt = f"""CÂU HỎI CỦA NGƯỜI DÙNG:
{query}

NGỮ CẢNH (CONTEXT – TRÍCH TỪ CƠ SỞ DỮ LIỆU EXCEL VÀ GỢI Ý TRIỆU CHỨNG NẾU CÓ):
{full_context}

YÊU CẦU:
- Chỉ dựa vào NGỮ CẢNH để trả lời, không dùng kiến thức bên ngoài.
- Không chẩn đoán, không kê đơn, không đưa liều dùng.
- Không hướng dẫn tự ý thay đổi hay ngừng thuốc/thảo dược.
- Nếu CONTEXT không có đủ thông tin, phải nói rõ “Không đủ thông tin trong CSDL hiện tại”.
- Được phép nhắc đến “gợi ý bệnh dựa trên tương đồng triệu chứng” nếu block tương ứng xuất hiện,
  nhưng luôn khẳng định đây KHÔNG phải là chẩn đoán.
- Trả lời bằng tiếng Việt, giọng điệu thân thiện, dễ hiểu.
"""  # noqa: E501

    model = genai.GenerativeModel(CHAT_MODEL_NAME)
    resp = model.generate_content([SYSTEM_PROMPT, user_prompt])

    chunks: List[str] = []
    if resp.candidates:
        for c in resp.candidates:
            if not c.content:
                continue
            for p in c.content.parts:
                if hasattr(p, "text"):
                    chunks.append(p.text)
    return "\n".join(chunks).strip()
