import os
import threading
import logging
import gradio as gr
import bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_telegram_bot():
    """Menjalankan bot Telegram Nara di background thread."""
    try:
        logger.info("🌸 Menjalankan Nara Telegram Bot di background thread...")
        nara_bot = bot.NaraTelegramBot()
        nara_bot.run()
    except Exception as e:
        logger.error(f"Error pada Telegram Bot: {e}")

# Run Telegram bot in a daemon background thread
bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
bot_thread.start()

# Build Gradio Interface for Hugging Face Space UI
with gr.Blocks(title="Nara Virtual AI Bot", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🌸 Nara - VirtualMate AI Telegram Bot
        
        **Status:** 🟢 Bot Telegram Nara aktif & berjalan 24/7 di background!
        
        ### 💬 Cara Menggunakan:
        1. Buka aplikasi **Telegram** kamu.
        2. Cari bot Nara kamu dan ketik `/start`.
        3. Mulai chat, minta PAP selfie, atau kirim voice note!
        """
    )
    
    status_output = gr.JSON(
        value={
            "bot_name": "Nara Virtual AI",
            "status": "Online 24/7",
            "platform": "Hugging Face Gradio Space"
        },
        label="System Status"
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
