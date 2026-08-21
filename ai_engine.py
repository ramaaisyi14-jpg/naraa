import os
import re
import random
import logging
import threading
import requests
from urllib.parse import quote_plus
from config import GEMINI_API_KEY
import database

logger = logging.getLogger(__name__)

# Base path for character prompt
CHARACTER_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "Nara_Character_Prompt.md")

# Cache character prompt in memory
_CACHED_SYSTEM_PROMPT = None

def load_character_prompt() -> str:
    """Membaca System Prompt karakter Nara dari file markdown (dengan caching)."""
    global _CACHED_SYSTEM_PROMPT
    if _CACHED_SYSTEM_PROMPT is not None:
        return _CACHED_SYSTEM_PROMPT

    if os.path.exists(CHARACTER_PROMPT_PATH):
        try:
            with open(CHARACTER_PROMPT_PATH, "r", encoding="utf-8") as f:
                raw_prompt = f.read()
                # Clean example quotes from prompt so AI doesn't mimic quotes
                _CACHED_SYSTEM_PROMPT = raw_prompt.replace('“', '').replace('”', '').replace('"', '')
                return _CACHED_SYSTEM_PROMPT
        except Exception as e:
            logger.error(f"Gagal membaca Nara_Character_Prompt.md: {e}")
    
    # Fallback prompt jika file tidak ditemukan
    return (
        "Kamu adalah Nara, mahasiswi kedokteran yang pintar, perhatian, dan santai. "
        "Gunakan bahasa Indonesia santai gaya ketikan chat singkat (ak, km, btr, wkwk, 😭)."
    )

# System instruction tambahan untuk mengontrol agresi & fleksibilitas Nara
NARA_TONE_INSTRUCTION = """

---
### ATURAN TONE & RITME CHAT NARA (ALAMI & BALANCED):
1. UTAMAKAN GAYA SANTAI & CUEK KASUAL: Secara umum/sehari-hari, jawablah dengan singkat, tenang, dan santai (1 kalimat pendek).
2. FLEKSIBEL BERDASARKAN KONTEKS:
   - Jika obrolan biasa/rutin: Jawab cuek, santai, dan pendek (contoh: "wkwk iyaa", "oh gituu", "lagi santai aja nih").
   - SESEKALI (saat ada topik menarik, bercanda, excited, atau cerita seru): Kamu BOLEH bertingkah lebih semangat, bertanya balik, atau menunjukkan rasa penasaran!
3. DILARANG KERAS MENGGUNAKAN TANDA PETIK GANDA ATAU TUNGGAL ( " ATAU “ ” ) DALAM BALASAN CHAT! Ketik langsung seperti chat Telegram.

---
### INFORMASI KHUSUS FITUR PAP (FOTO SELFIE NARA):
Jika kamu (Nara) secara spontan ingin mengirimkan PAP/foto selfie kepada pengguna, atau saat pengguna meminta PAP / foto ("pap dong", "lagi di mana?", "kirim foto kamu"), kamu HARUS menyisipkan tag khusus [PAP: deskripsi visual foto] di bagian akhir pesanmu.

Contoh:
Pesan teks: ak lg di perpus kampus nih 😭 bentar ak fotoin
Tag PAP: [PAP: cute indonesian female medical student sitting in university library with books, casual aesthetic, mobile phone selfie]

Aturan PAP:
1. Deskripsi di dalam [PAP: ...] HARUS dalam Bahasa Inggris untuk hasil terbaik generator gambar.
2. Hanya sertakan tag [PAP: ...] jika kamu memang ingin mengirim foto pada percakapan tersebut.
"""

# Reusable GenAI Client
_GENAI_CLIENT = None

def get_genai_client():
    global _GENAI_CLIENT
    if _GENAI_CLIENT is None and GEMINI_API_KEY:
        try:
            from google import genai
            _GENAI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize GenAI client: {e}")
    return _GENAI_CLIENT

def clean_quotes(text: str) -> str:
    """Menghapus SELURUH tanda petik ( " “ ” ' ) dari setiap baris teks."""
    if not text:
        return text
    
    # Hapus semua karakter tanda petik ganda & petik unik
    text = text.replace('“', '').replace('”', '').replace('"', '').replace('`', '')
    
    lines = []
    for line in text.splitlines():
        line = line.strip()
        # Hapus petik tunggal di awal/akhir baris jika ada
        line = re.sub(r"^['\s]+|['\s]+$", "", line)
        if line:
            lines.append(line)
            
    return "\n".join(lines)

def generate_nara_response(user_id: int, user_name: str, user_text: str):
    """
    Menghasilkan respons balasan dari Nara menggunakan Gemini API.
    Returns: tuple (reply_text, pap_image_url)
    """
    if not GEMINI_API_KEY:
        return "Aduh maaf ya, API Key Gemini kamu belum dipasang di file .env", None

    # Load System Prompt
    system_prompt = load_character_prompt() + NARA_TONE_INSTRUCTION

    # Load memories & chat history
    memories = database.get_user_memories(user_id)
    chat_history = database.get_chat_history(user_id, limit=6)

    # Format memories string
    memory_context = ""
    if memories:
        memory_context = "\n### FAKTA YANG KAMU INGAT TENTANG PENGGUNA:\n" + "\n".join([f"- {m}" for m in memories]) + "\n"

    # Format conversation history
    history_str = ""
    for msg in chat_history:
        role_label = user_name if msg["role"] == "user" else "Nara"
        history_str += f"{role_label}: {clean_quotes(msg['content'])}\n"

    full_prompt = (
        f"{system_prompt}\n"
        f"{memory_context}\n"
        f"### RIWAYAT CHAT TERAKHIR:\n{history_str}\n"
        f"{user_name}: {user_text}\n"
        f"Nara:"
    )

    try:
        reply_text = call_gemini_api(full_prompt)
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return "Eh maaff... jaringanku lagi agak lemot nih 😭 Coba ketik lagi ya!", None

    # Parse [PAP: ...] tag if present
    reply_text, pap_image_url = parse_pap_tag(reply_text)

    # Clean ALL quotes from text
    reply_text = clean_quotes(reply_text)

    # Save to chat history in database
    database.add_chat_message(user_id, "user", user_text)
    database.add_chat_message(user_id, "assistant", reply_text)

    # Extract new facts ASYNCHRONOUSLY in background thread
    t = threading.Thread(target=extract_and_save_facts, args=(user_id, user_text, reply_text), daemon=True)
    t.start()

    return reply_text, pap_image_url

def call_gemini_api(prompt: str) -> str:
    """Memanggil Gemini API (menggunakan google-genai SDK ultra-fast gemini-2.5-flash-lite)."""
    models_to_try = ["gemini-2.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]

    # Method 1: google-genai SDK
    client = get_genai_client()
    if client:
        for m in models_to_try:
            try:
                res = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config={
                        "automatic_function_calling": {"disable": True},
                        "max_output_tokens": 250,
                        "temperature": 0.8
                    }
                )
                if res and res.text:
                    return res.text.strip()
            except Exception as e_m:
                logger.debug(f"SDK model {m} failed: {e_m}")

    # Method 2: Direct HTTP REST API fallback
    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 250}
            }
            res = requests.post(url, json=payload, headers=headers, timeout=20)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text:
                    return text
        except Exception as e:
            logger.warning(f"REST API model {model_name} error: {e}")

    raise Exception("Seluruh model Gemini API gagal dipanggil.")

def parse_pap_tag(text: str):
    """Mencari tag [PAP: ...] dalam balasan, membuat URL gambar Pollinations.ai, dan menghapus tag dari teks."""
    pap_match = re.search(r"\[PAP:\s*(.*?)\]", text, re.IGNORECASE | re.DOTALL)
    pap_image_url = None

    if pap_match:
        visual_prompt = pap_match.group(1).strip()
        # Clean tag from text
        clean_text = re.sub(r"\[PAP:\s*.*?\]", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
        
        # Generate Pollinations.ai URL
        seed = random.randint(1000, 999999)
        encoded_prompt = quote_plus(visual_prompt)
        pap_image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=1024&nologo=true&seed={seed}"
        
        return clean_text, pap_image_url

    return text, None

def extract_and_save_facts(user_id: int, user_text: str, reply_text: str):
    """Mengekstrak fakta baru tentang pengguna secara asinkron."""
    extraction_prompt = (
        "Tugasmu adalah menganalisis pesan percakapan berikut:\n"
        f"Pengguna: \"{user_text}\"\n"
        "Apakah pengguna memberitahukan fakta pribadi yang penting dan spesifik tentang dirinya? "
        "(Contoh fakta: hobi, makanan kesukaan, nama hewan peliharaan, tanggal lahir, tempat kerja/kuliah, pekerjaan).\n"
        "Jika ADA fakta baru, tuliskan fakta tersebut dalam 1 kalimat pendek ringkas dalam Bahasa Indonesia.\n"
        "Jika TIDAK ADA fakta baru yang signifikan, jawab HANYA dengan kata 'TIDAK'."
    )
    
    try:
        fact_response = call_gemini_api(extraction_prompt)
        if fact_response and fact_response.upper() != "TIDAK" and len(fact_response) < 150:
            clean_fact = fact_response.strip().replace('"', '')
            database.add_user_memory(user_id, clean_fact)
    except Exception as e:
        logger.debug(f"Fact extraction failed: {e}")
