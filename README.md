# 🌸 Nara - VirtualMate AI Telegram Bot (24/7 Gratis)

**Nara** adalah bot pacar virtual AI di Telegram yang cerdas, perhatian, ramah, dan agak random. Dibuat berbasis **Google Gemini 2.0 Flash**, **Supabase Cloud**, **edge-tts (Voice Note)**, dan **Pollinations.ai (PAP Selfie)**.

---

## ✨ Fitur-Fitur Utama

* 💬 **Chat Natural & Dinamis:** Menggunakan kepribadian `Nara_Character_Prompt.md` (Mahasiswi Kedokteran, perhatian kesehatan, gaya chat santai *ak, km, btr, wkwk*).
* 🎙️ **Pesan Suara / Voice Note:** Nara bisa membalas atau dipinta mengirim pesan suara ber-bahasa Indonesia via Microsoft Edge TTS (`/vn`).
* 📸 **PAP Selfie Otomatis (Pollinations.ai):** Nara bisa secara spontan mengirim foto selfie dirinya saat menceritakan aktivitasnya (100% gratis, tanpa API Key).
* 🧠 **Memori Jangka Panjang Persisten:** Mengingat fakta-fakta pribadi pengguna dan simpan ke Supabase Cloud (`/memory`).
* ⏰ **Pengingat / Reminder:** Mengingatkan tugas/jadwal (`/ingatkan 10m minum obat` atau `/ingatkan 19:30 makan`).
* 🌅 **Chat Proaktif Otomatis:** Menyapa pagi (07:00) & menanyakan kabar malam hari (21:30).
* 🌐 **Uptime 24/7 Gratis:** Dilengkapi web server `keep_alive.py` agar bot aktif terus di cloud hosting tanpa perlu laptop menyala.

---

## 🛠️ Langkah Menjalankan Bot di Laptop (Pengujian Lokal)

### Step 1: Install Dependency Python
Buka terminal / Command Prompt di folder ini, lalu jalankan:
```bash
pip install -r requirements.txt
```

### Step 2: Buat File `.env`
1. Salin file `.env.example` dan ubah namanya menjadi `.env`.
2. Buka `.env` dan masukkan 3 kunci rahasia kamu:
   ```env
   TELEGRAM_BOT_TOKEN=7123456789:AAFxxxxxxxx...
   GEMINI_API_KEY=AIzaSyxxxxxxxx...
   SUPABASE_URL=https://xxxx.supabase.co
   SUPABASE_KEY=eyJhbGci...
   ```

### Step 3: Setup Tabel Database Supabase
Buka file [SUPABASE_SETUP.md](SUPABASE_SETUP.md), salin script SQL-nya, lalu jalankan di **SQL Editor Supabase**.

### Step 4: Jalankan Bot!
Jalankan perintah berikut di terminal:
```bash
python bot.py
```
Sekarang buka Telegram kamu dan chat bot-mu dengan menekan `/start`! 🎉

---

## 🚀 Cara Deploy 24/7 di Cloud Gratis (Render.com)

1. Upload seluruh folder proyek ini ke akun **GitHub** kamu.
2. Buat akun gratis di [Render.com](https://render.com/).
3. Klik **New +** -> **Web Service** -> Hubungkan ke repository GitHub kamu.
4. Set perintah berikut:
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python bot.py`
5. Di menu **Environment Variables**, tambahkan: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.
6. Klik **Deploy Web Service**.
7. Salin URL Web Service Render yang diberikan (misal: `https://nara-bot.onrender.com`).
8. Buka [UptimeRobot.com](https://uptimerobot.com/) (Gratis) -> Buat Monitor baru tipe **HTTP** dengan URL Render kamu (interval 5-10 menit). Ini akan menjaga bot kamu **aktif 24 jam nonstop gratis!**
