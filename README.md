# Medical RAG Chatbot (Excel + Gemini + Symptom Matching)

Dự án này tách code của bạn thành nhiều **module nhỏ** để dễ quản lý và test:

## Cấu trúc thư mục

```text
project/
│
├─ config.py          # Cấu hình API key, tên model, đường dẫn Excel
├─ excel_utils.py     # Hàm đọc Excel an toàn + helper chuyển kiểu dữ liệu
├─ kb_builder.py      # Đọc các sheet trong datasjet.xlsx và build danh sách documents (KB)
├─ rag_index.py       # Tạo embedding, build index, hàm retrieve_top_k
├─ symptoms.py        # Match triệu chứng và build block gợi ý
├─ prompts.py         # SYSTEM_PROMPT và các câu hỏi mẫu
├─ chat_rag.py        # Hàm answer_with_rag() – ghép context + gọi Gemini
└─ main.py            # Chương trình CLI để chat
```

> **Lưu ý:** File `datasjet.xlsx` cần nằm cùng cấp với `main.py` (tức là trong cùng thư mục `project/`).

---

## 1. Chuẩn bị môi trường

```bash
cd project

# Tạo venv (khuyến khích)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Cài thư viện cần thiết
pip install google-generativeai pandas numpy openpyxl
```

---

## 2. Cấu hình API key

Bạn có 2 cách:

### Cách 1 – dùng biến môi trường (khuyến khích)

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
# Windows (PowerShell):
# $env:GEMINI_API_KEY="YOUR_API_KEY"
```

### Cách 2 – sửa trực tiếp trong `config.py`

```python
API_KEY = "YOUR_API_KEY"
```

---

## 3. Đặt file Excel

Đảm bảo file:

```text
datasjet.xlsx
```

nằm cùng thư mục với `main.py` (thư mục `project/`).

---

## 4. Chạy chatbot

```bash
python main.py
```

Màn hình sẽ hiện:

- Thông báo đọc Excel và build KB.
- Tạo vector index.
- In ra một vài **câu hỏi mẫu** để bạn thử.
- Sau đó bạn có thể gõ câu hỏi (tiếng Việt). Gõ `exit` để thoát.

---

## 5. Test từng phần (nếu muốn)

Bạn có thể import từng module để test riêng:

```python
from config import EXCEL_PATH, init_genai
from kb_builder import build_kb_from_excel
from rag_index import build_index
from symptoms import find_symptom_matches
from chat_rag import answer_with_rag

init_genai()
docs, disease_name, symptom_dict = build_kb_from_excel(EXCEL_PATH)
index = build_index(docs)

matches = find_symptom_matches("dau dau, so mui, hoi sot", disease_name, symptom_dict)
print(matches)

answer = answer_with_rag(
    "Em bi dau dau, nghe mui, hoi dau hong va co sot",
    index,
    disease_name,
    symptom_dict,
)
print(answer)
```

---

## 6. Ghi chú quan trọng

- Tất cả logic build KB đều nằm trong **`kb_builder.py`** (copy nguyên từ script gốc của bạn).
- Luồng chạy chính:
  1. `build_kb_from_excel()` → list `docs`
  2. `build_index(docs)` → index có `embeddings`
  3. `answer_with_rag(query, index, disease_name, symptom_dict)`

Nếu bạn muốn chỉnh sửa prompt, hãy mở `prompts.py` và sửa biến `SYSTEM_PROMPT`.
