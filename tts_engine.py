import os
import re
import logging
import asyncio
import tempfile
import subprocess
import edge_tts

logger = logging.getLogger(__name__)

# Microsoft Edge Indonesian Female Voice
VOICE_NAME = "id-ID-GadisNeural"

def get_ffmpeg_exe() -> str:
    """Mencari path executable ffmpeg dari imageio_ffmpeg atau system PATH."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return "ffmpeg"

def clean_text_for_tts(text: str) -> str:
    """
    Membersihkan teks dari tag PAP, URL, markdown, dan quotes agar dibaca alami oleh TTS.
    """
    if not text:
        return ""
    # Hapus tag PAP jika ada
    text = re.sub(r"\[PAP:\s*.*?\]", "", text, flags=re.IGNORECASE | re.DOTALL)
    # Hapus URL
    text = re.sub(r"https?://\S+", "", text)
    # Hapus simbol format markdown (*, _, ~, `, #)
    text = re.sub(r"[\*\_~`#]", "", text)
    # Hapus berbagai jenis tanda petik
    text = text.replace('“', '').replace('”', '').replace('"', '').replace("'", "")
    return text.strip()

async def text_to_speech(text: str, output_path: str) -> bool:
    """
    Mengubah teks menjadi file audio Telegram Voice Note (.ogg Opus) menggunakan edge-tts + ffmpeg conversion.
    """
    try:
        cleaned_text = clean_text_for_tts(text)
        if not cleaned_text:
            cleaned_text = text or "Halo!"

        # Step 1: Save temporary MP3 output from edge_tts
        tmp_fd, tmp_mp3 = tempfile.mkstemp(suffix=".mp3")
        os.close(tmp_fd)

        try:
            communicate = edge_tts.Communicate(cleaned_text, VOICE_NAME)
            await communicate.save(tmp_mp3)

            if not os.path.exists(tmp_mp3) or os.path.getsize(tmp_mp3) == 0:
                logger.error("File MP3 sementara dari edge-tts kosong atau tidak terbuat.")
                return False

            # Step 2: Convert MP3 to OGG OPUS via ffmpeg (Telegram Voice Note standard)
            ffmpeg_bin = get_ffmpeg_exe()
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i", tmp_mp3,
                "-c:a", "libopus",
                "-b:a", "32k",
                "-vbr", "on",
                "-f", "ogg",
                output_path
            ]
            
            # Execute conversion synchronously in thread pool to avoid Windows event loop subprocess issues
            res = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True
            )

            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Berhasil membuat Voice Note OGG Opus di: {output_path}")
                return True
            else:
                stderr_msg = res.stderr.decode('utf-8', errors='ignore') if res.stderr else "Unknown error"
                logger.error(f"Gagal mengonversi MP3 ke OGG Opus. Code: {res.returncode}, Error: {stderr_msg}")
                return False
        finally:
            if os.path.exists(tmp_mp3):
                try:
                    os.remove(tmp_mp3)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Gagal membuat Voice Note dengan edge-tts: {e}", exc_info=True)
        return False


def generate_voice_note_sync(text: str, output_path: str) -> bool:
    """Wrapper sinkron untuk dipanggil dari context luar async."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = loop.create_task(text_to_speech(text, output_path))
            return True
        else:
            return asyncio.run(text_to_speech(text, output_path))
    except Exception as e:
        logger.error(f"Error in generate_voice_note_sync: {e}")
        return False


