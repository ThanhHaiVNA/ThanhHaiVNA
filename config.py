import os
import google.generativeai as genai

# === CẤU HÌNH CƠ BẢN ===
API_KEY = os.getenv("GEMINI_API_KEY", "")  # hoặc điền thẳng API key vào đây nếu muốn
CHAT_MODEL_NAME = "models/gemma-3-12b-it"
EMBED_MODEL_NAME = "models/text-embedding-004"

# File Excel
EXCEL_PATH = "datasjet.xlsx"


def init_genai() -> None:
    """Khởi tạo cấu hình cho thư viện google-generativeai."""
    if not API_KEY:
        raise RuntimeError(
            "Chưa cấu hình API_KEY. Hãy set biến môi trường GEMINI_API_KEY "
            "hoặc sửa trực tiếp trong config.API_KEY."
        )
    genai.configure(api_key=API_KEY)
