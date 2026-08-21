import logging
from flask import Flask
from threading import Thread
from config import PORT

logger = logging.getLogger(__name__)
app = Flask(__name__)

@app.route('/')
def home():
    return (
        "<h1>🌸 Nara Virtual AI - Telegram Bot Online 24/7</h1>"
        "<p>Bot pacar virtual berjalan aktif & lancar.</p>"
    )

@app.route('/health')
def health():
    return {"status": "ok", "bot": "Nara Virtual AI", "health": "healthy"}

def run():
    # Run Flask server silently
    cli = logging.getLogger('werkzeug')
    cli.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=PORT)

def keep_alive():
    """Menjalankan HTTP Web Server kecil di thread terpisah untuk pemicu UptimeRobot."""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logger.info(f"Keep-Alive Web Server berjalan di port {PORT}")
