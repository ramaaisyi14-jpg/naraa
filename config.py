import os
from dotenv import load_dotenv

# Load variables from .env or fallback to .env.example
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists(".env.example"):
    load_dotenv(".env.example")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
PORT = int(os.getenv("PORT", "8080"))

# Validation helper
def validate_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN or "7123456789" in TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GEMINI_API_KEY or "AIzaSyxxx" in GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not SUPABASE_URL or "your-project-id" in SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY or SUPABASE_KEY.endswith("l-5ZRQGh4jvUsHQuXGVZIsIDAN_ekLAnjpWMJtGASak_placeholder"):
        missing.append("SUPABASE_KEY")
    
    return missing
