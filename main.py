import sys

from config import EXCEL_PATH, init_genai
from kb_builder import build_kb_from_excel
from rag_index import build_index
from chat_rag import answer_with_rag
from prompts import EXAMPLE_QUESTIONS


def main() -> None:
    print("=== Chatbot Dược – Bệnh – Thảo dược (RAG từ datasjet.xlsx + GỢI Ý TRIỆU CHỨNG ≥90%) ===\n")  # noqa: E501
    print(f"📂 Đang đọc dữ liệu từ file Excel: {EXCEL_PATH}")

    # 1) Khởi tạo Gemini
    try:
        init_genai()
    except Exception as e:
        print("❌ Lỗi cấu hình GenAI:", e)
        sys.exit(1)

    # 2) Build KB từ Excel
    try:
        kb_docs, disease_name, symptom_dict = build_kb_from_excel(EXCEL_PATH)
    except Exception as e:
        print("❌ Lỗi build KB:", e)
        sys.exit(1)

    # 3) Build index
    index = build_index(kb_docs)

    # 4) Demo câu hỏi mẫu
    print("🧪 Một vài câu hỏi mẫu (prompt) bạn có thể thử:")
    for q in EXAMPLE_QUESTIONS:
        print("  -", q)
    print("\nGõ câu hỏi của bạn (tiếng Việt). Gõ 'exit' để thoát.\n")

    # 5) Loop chat
    while True:
        try:
            q = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThoát.")
            break

        if not q:
            continue
        if q.lower() in ("exit", "quit", "q"):
            print("Thoát.")
            break

        print("🤖 AI đang suy nghĩ...\n")
        try:
            ans = answer_with_rag(q, index, disease_name, symptom_dict)
        except Exception as e:
            print("❌ Lỗi khi gọi API:", repr(e))
            continue

        print("AI:", ans)
        print("-" * 60)


if __name__ == "__main__":
    main()
