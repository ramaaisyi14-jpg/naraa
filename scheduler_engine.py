import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import database
import ai_engine

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()

def init_scheduler(bot_instance):
    """Menginisialisasi scheduler untuk pengingat & sapaan proaktif."""
    
    # 1. Routine check for due reminders every 30 seconds
    scheduler.add_job(
        check_and_send_reminders,
        'interval',
        seconds=30,
        args=[bot_instance],
        id='reminder_job',
        replace_existing=True
    )
    
    # 2. Morning Proactive Greeting (07:00 WIB)
    scheduler.add_job(
        send_proactive_greeting,
        'cron',
        hour=7,
        minute=0,
        args=[bot_instance, "morning"],
        id='morning_greeting_job',
        replace_existing=True
    )

    # 3. Evening Proactive Check-in (21:30 WIB)
    scheduler.add_job(
        send_proactive_greeting,
        'cron',
        hour=21,
        minute=30,
        args=[bot_instance, "evening"],
        id='evening_greeting_job',
        replace_existing=True
    )

    scheduler.start()
    logger.info("APScheduler pengingat & chat proaktif berhasil dijalankan!")

def check_and_send_reminders(bot_instance):
    """Mengecek database untuk reminder yang sudah jatuh tempo dan mengirimkannya."""
    try:
        now_iso = datetime.now().isoformat()
        due_reminders = database.get_due_reminders(now_iso)
        
        for rem in due_reminders:
            user_id = rem["user_id"]
            text = rem["reminder_text"]
            rem_id = rem["id"]
            
            message_to_send = f"⏰ **Pengingat dari Nara:**\n\n{text}\n\n*Jangan lupa ya! ❤️*"
            
            # Send message via Telegram bot
            try:
                bot_instance.send_message_sync(user_id, message_to_send)
                database.mark_reminder_sent(rem_id)
                logger.info(f"Berhasil mengirim reminder {rem_id} ke user {user_id}")
            except Exception as e:
                logger.error(f"Gagal mengirim reminder ke {user_id}: {e}")
    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {e}")

def send_proactive_greeting(bot_instance, greeting_type: str):
    """Mengirim sapaan proaktif otomatis di pagi/malam hari dari Nara."""
    try:
        users = database.get_all_active_users()
        for u in users:
            user_id = u["user_id"]
            user_name = u.get("name", "Sayang")
            
            if greeting_type == "morning":
                prompt = f"Ini jam 07:00 pagi. Buat sapaan pagi singkat yang manis, perhatian, dan menyemangati untuk {user_name}. Ingatkan sarapan/minum air."
            else:
                prompt = f"Ini jam 21:30 malam. Tanyakan kabar harinya {user_name} secara perhatian, ingatkan istirahat/tidur."
                
            reply_text, pap_url = ai_engine.generate_nara_response(user_id, user_name, prompt)
            
            # Send proactive text message
            bot_instance.send_message_sync(user_id, reply_text)
            
            # Send PAP photo if generated
            if pap_url:
                bot_instance.send_photo_sync(user_id, pap_url)
                
            logger.info(f"Berhasil mengirim sapaan proaktif ({greeting_type}) ke {user_id}")
    except Exception as e:
        logger.error(f"Error in send_proactive_greeting ({greeting_type}): {e}")
