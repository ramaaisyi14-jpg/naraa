import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

supabase_client: Client = None

def init_supabase():
    global supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("SUPABASE_URL atau SUPABASE_KEY belum diisi.")
        return None
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Berhasil terhubung ke Supabase Cloud!")
        return supabase_client
    except Exception as e:
        logger.error(f"Gagal menghubungkan ke Supabase: {e}")
        return None

def get_or_create_user(user_id: int, name: str = "", username: str = ""):
    if not supabase_client:
        return None
    try:
        res = supabase_client.table("user_profiles").select("*").eq("user_id", user_id).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        
        # Create user profile if not existing
        new_user = {
            "user_id": user_id,
            "name": name,
            "username": username,
            "persona": "default"
        }
        res = supabase_client.table("user_profiles").insert(new_user).execute()
        return res.data[0] if res.data else new_user
    except Exception as e:
        logger.error(f"Error get_or_create_user: {e}")
        return None

def get_chat_history(user_id: int, limit: int = 15):
    if not supabase_client:
        return []
    try:
        res = (
            supabase_client.table("chat_history")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        if res.data:
            # Return in chronological order
            return list(reversed(res.data))
        return []
    except Exception as e:
        logger.error(f"Error get_chat_history: {e}")
        return []

def add_chat_message(user_id: int, role: str, content: str):
    if not supabase_client:
        return
    try:
        supabase_client.table("chat_history").insert({
            "user_id": user_id,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        logger.error(f"Error add_chat_message: {e}")

def get_user_memories(user_id: int):
    if not supabase_client:
        return []
    try:
        res = supabase_client.table("memories").select("*").eq("user_id", user_id).execute()
        if res.data:
            return [m["fact"] for m in res.data if "fact" in m]
        return []
    except Exception as e:
        logger.error(f"Error get_user_memories: {e}")
        return []

def add_user_memory(user_id: int, fact: str):
    if not supabase_client:
        return
    try:
        # Check if fact already exists to prevent duplicate
        existing = supabase_client.table("memories").select("*").eq("user_id", user_id).eq("fact", fact).execute()
        if not existing.data:
            supabase_client.table("memories").insert({
                "user_id": user_id,
                "fact": fact
            }).execute()
            logger.info(f"Memori baru disimpan untuk user {user_id}: {fact}")
    except Exception as e:
        logger.error(f"Error add_user_memory: {e}")

def add_reminder(user_id: int, reminder_text: str, rem_time: str):
    if not supabase_client:
        return None
    try:
        res = supabase_client.table("reminders").insert({
            "user_id": user_id,
            "reminder_text": reminder_text,
            "rem_time": rem_time,
            "is_sent": False
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Error add_reminder: {e}")
        return None

def get_due_reminders(current_time_iso: str):
    if not supabase_client:
        return []
    try:
        res = (
            supabase_client.table("reminders")
            .select("*")
            .lte("rem_time", current_time_iso)
            .eq("is_sent", False)
            .execute()
        )
        return res.data if res.data else []
    except Exception as e:
        logger.error(f"Error get_due_reminders: {e}")
        return []

def mark_reminder_sent(reminder_id: int):
    if not supabase_client:
        return
    try:
        supabase_client.table("reminders").update({"is_sent": True}).eq("id", reminder_id).execute()
    except Exception as e:
        logger.error(f"Error mark_reminder_sent: {e}")

def get_all_active_users():
    if not supabase_client:
        return []
    try:
        res = supabase_client.table("user_profiles").select("user_id, name").execute()
        return res.data if res.data else []
    except Exception as e:
        logger.error(f"Error get_all_active_users: {e}")
        return []
