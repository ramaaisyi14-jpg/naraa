import os
import re
import random
import logging
import asyncio
import tempfile
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
import database
import ai_engine
import tts_engine
import scheduler_engine
import keep_alive

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class NaraTelegramBot:
    def __init__(self):
        self.app = None

    def run(self):
        # Validate config
        missing = config.validate_config()
        if missing:
            logger.warning(f"⚠️ PERHATIAN: Variabel environment berikut belum diset di .env: {', '.join(missing)}")

        # Initialize Supabase
        database.init_supabase()

        # Start Keep-Alive Web Server
        keep_alive.keep_alive()

        # Build Telegram Application
        if not config.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN kosong. Bot tidak dapat dijalankan.")
            return

        self.app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

        # Register Command Handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("vn", self.cmd_vn))
        self.app.add_handler(CommandHandler("ingatkan", self.cmd_ingatkan))
        self.app.add_handler(CommandHandler("memory", self.cmd_memory))

        # Register Text Message Handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))

        # Initialize Scheduler for proactive messages & reminders
        scheduler_engine.init_scheduler(self)

        logger.info("🌸 Bot Telegram Nara Virtual AI siap berjalan!")
        self.app.run_polling()

    # --- Sync Helpers for Scheduler ---
    def send_message_sync(self, chat_id: int, text: str):
        """Kirim pesan teks dari background thread scheduler dengan pemecahan bubble."""
        if not self.app or not self.app.bot:
            return
        asyncio.run_coroutine_threadsafe(
            self._send_split_bubbles(chat_id, text),
            self.app.loop
        )

    def send_photo_sync(self, chat_id: int, photo_url: str, caption: str = ""):
        """Kirim foto PAP dari background thread scheduler."""
        if not self.app or not self.app.bot:
            return
        asyncio.run_coroutine_threadsafe(
            self.app.bot.send_photo(chat_id=chat_id, photo=photo_url, caption=caption),
            self.app.loop
        )

    async def _send_split_bubbles(self, chat_id: int, reply_text: str):
        """Helper untuk memecah balasan menjadi bubble chat terpisah secara santai & tidak agresif."""
        reply_text = ai_engine.clean_quotes(reply_text)
        
        # Split ke baris-baris mentah
        raw_lines = [ai_engine.clean_quotes(b) for b in re.split(r'\n+', reply_text) if ai_engine.clean_quotes(b)]
        if not raw_lines:
            raw_lines = [reply_text]

        # Gabungkan baris agar santai & tidak agresif (kebanyakan 1 bubble)
        bubbles = []
        current_bubble = ""
        
        for line in raw_lines:
            if current_bubble and (len(current_bubble) + len(line) < 140):
                current_bubble += " " + line
            else:
                if current_bubble:
                    bubbles.append(current_bubble)
                current_bubble = line
        
        if current_bubble:
            bubbles.append(current_bubble)

        # Maksimal 2 bubble untuk balasan santai
        if len(bubbles) > 2:
            bubbles = [bubbles[0], " ".join(bubbles[1:])]

        for i, bubble in enumerate(bubbles):
            if i > 0:
                await self.app.bot.send_chat_action(chat_id=chat_id, action="typing")
                delay = min(max(len(bubble) * 0.03, 0.6), 1.8)
                await asyncio.sleep(delay)
            
            await self.app.bot.send_message(chat_id=chat_id, text=bubble)

    # --- Command Handlers ---
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        database.get_or_create_user(user.id, name=user.first_name, username=user.username or "")
        
        welcome_text = (
            f"eh halo {user.first_name}! 👋\n"
            f"ak Nara. seneng deh akhirnya km ngechat ak 🥰\n"
            f"km bisa ngobrol apa aja sma ak, minta PAP selfie, bikin pengingat, atau dengerin pesan suara ak.\n"
            f"ketik /help kalo mau liat daftar perintah ya!"
        )
        await self._send_split_bubbles(update.effective_chat.id, welcome_text)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "🌸 **Daftar Fitur & Perintah Nara:**\n\n"
            "💬 **Chat Biasa:** Langsung ketik pesan apa saja (misal: *lagi ngapain nar?*, *pap dong*, *aku capek bgt*).\n"
            "🎙️ `/vn [teks]` - Kirim pesan suara (Voice Note) dari Nara.\n"
            "⏰ `/ingatkan [waktu] [pesan]` - Minta Nara mengingatkan sesuatu.\n"
            "   *Contoh:* `/ingatkan 10m minum obat` atau `/ingatkan 19:30 makan malam`\n"
            "🧠 `/memory` - Lihat fakta-fakta yang diingat Nara tentang kamu.\n"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def _send_voice_note_reply(self, update: Update, reply_text: str) -> bool:
        """Helper untuk membuat dan mengirim Voice Note dengan penanganan file & exception yang aman."""
        speech_text = tts_engine.clean_text_for_tts(reply_text)
        if not speech_text:
            speech_text = reply_text

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".ogg")
        os.close(tmp_fd)

        try:
            success = await tts_engine.text_to_speech(speech_text, tmp_path)
            if success and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, "rb") as audio_file:
                    caption_text = ai_engine.clean_quotes(reply_text)
                    if len(caption_text) > 1000:
                        caption_text = caption_text[:997] + "..."
                    await update.message.reply_voice(voice=audio_file, caption=caption_text)
                return True
            else:
                logger.warning("Gagal membuat file voice note audio, fallback ke pesan teks.")
                await self._send_split_bubbles(update.effective_chat.id, reply_text)
                return False
        except Exception as e:
            logger.error(f"Error mengirim Voice Note: {e}")
            await self._send_split_bubbles(update.effective_chat.id, reply_text)
            return False
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    async def cmd_vn(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Membuat dan mengirimkan Voice Note dari Nara."""
        user = update.effective_user
        text_arg = " ".join(context.args) if context.args else ""
        
        if not text_arg:
            reply_text, _ = ai_engine.generate_nara_response(user.id, user.first_name, "Kirim voice note sapaan manis buat aku")
        else:
            reply_text = text_arg

        reply_text = ai_engine.clean_quotes(reply_text)
        await self._send_voice_note_reply(update, reply_text)

    async def cmd_ingatkan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Memproses request reminder dari user."""
        user = update.effective_user
        args = context.args
        
        if len(args) < 2:
            await update.message.reply_text("Format salah ya 🙏 Contoh: `/ingatkan 10m Minum obat` atau `/ingatkan 19:30 Makan malam`", parse_mode="Markdown")
            return
            
        time_str = args[0].lower()
        reminder_text = " ".join(args[1:])
        
        now = datetime.now()
        rem_datetime = None

        # Format 1: Relative minutes e.g., 10m, 30m, 2h
        rel_match = re.match(r"^(\d+)([mh])$", time_str)
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2)
            if unit == "m":
                rem_datetime = now + timedelta(minutes=amount)
            elif unit == "h":
                rem_datetime = now + timedelta(hours=amount)

        # Format 2: Absolute time e.g., 19:30 or 07:00
        if not rem_datetime and ":" in time_str:
            try:
                parts = time_str.split(":")
                hour = int(parts[0])
                minute = int(parts[1])
                rem_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if rem_datetime <= now:
                    rem_datetime += timedelta(days=1)
            except ValueError:
                pass

        if not rem_datetime:
            await update.message.reply_text("Format waktu tidak valid. Gunakan format seperti `10m` (10 menit) atau `19:30` (jam 7 malam).", parse_mode="Markdown")
            return

        iso_time = rem_datetime.isoformat()
        database.add_reminder(user.id, reminder_text, iso_time)
        
        formatted_time = rem_datetime.strftime("%H:%M")
        await update.message.reply_text(f"Sip! Nanti jam {formatted_time} Nara ingatkan: *{reminder_text}* ya! ❤️", parse_mode="Markdown")

    async def cmd_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        memories = database.get_user_memories(user.id)
        
        if not memories:
            await update.message.reply_text("Nara belum mencatat fakta khusus tentang kamu. Sering-sering ngobrol sama Nara ya! 😊")
            return

        mem_list = "\n".join([f"• {m}" for m in memories])
        msg = f"🧠 **Hal-hal yang Nara ingat tentang {user.first_name}:**\n\n{mem_list}"
        await update.message.reply_text(msg, parse_mode="Markdown")

    # --- Text Message Handler ---
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_text = update.message.text.strip()
        chat_id = update.effective_chat.id
        
        # Make sure user exists in Supabase
        database.get_or_create_user(user.id, name=user.first_name, username=user.username or "")

        # Indicate typing state
        await update.message.chat.send_action("typing")

        # Generate Nara AI Response + check for PAP URL
        reply_text, pap_image_url = ai_engine.generate_nara_response(user.id, user.first_name, user_text)

        # Check if user explicitly asked for Voice Note in text
        if is_vn_requested(user_text):
            sent_vn = await self._send_voice_note_reply(update, reply_text)
            if sent_vn:
                if pap_image_url:
                    await update.message.chat.send_action("upload_photo")
                    try:
                        await update.message.reply_photo(photo=pap_image_url, caption="📸 PAP dari Nara ✨")
                    except Exception as e:
                        logger.error(f"Gagal mengirim gambar PAP: {e}")
                return

        # Send Text Reply as SPLIT CHAT BUBBLES dynamically
        await self._send_split_bubbles(chat_id, reply_text)

        # If Nara decided to send PAP selfie, send photo!
        if pap_image_url:
            await update.message.chat.send_action("upload_photo")
            try:
                await update.message.reply_photo(photo=pap_image_url, caption="📸 PAP dari Nara ✨")
            except Exception as e:
                logger.error(f"Gagal mengirim gambar PAP: {e}")

def is_vn_requested(user_text: str) -> bool:
    """Mengecek apakah pengguna meminta pesan suara/voice note dalam pesan teks."""
    if not user_text:
        return False
    text_lower = user_text.lower().strip()
    
    # Kata kunci langsung
    if text_lower in ["vn", "vn dong", "minta vn", "kirim vn", "voice note", "voicenote", "pesan suara", "rekaman suara"]:
        return True
        
    # Pattern regex untuk menangkap variasi pengucapan natural
    patterns = [
        r"\b(vn|voicenote|voice\s*note|pesan\s*suara|rekaman\s*suara)\b",
        r"\b(suara|ngomong|bicara|omong)\s*(dong|ya|lagi|langsung|kamu|mu|nya)\b",
        r"\b(pake|pakai|kirim|minta|cobaa?|dengera?|dengar)\s*(suara|vn|voice\s*note)\b",
        r"\b(mana|denger|dengar)\s*(suara|vn|voice\s*note)",
    ]
    return any(re.search(p, text_lower) for p in patterns)

if __name__ == "__main__":
    bot = NaraTelegramBot()
    bot.run()

