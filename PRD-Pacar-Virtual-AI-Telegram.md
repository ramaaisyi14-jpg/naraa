# PRD: Pacar Virtual AI di Telegram

**Nama Produk:** VirtualMate Bot
**Dokumen:** Product Requirements Document (PRD)
**Versi:** 1.1 (Revisi Hasil Diskusi)
**Tanggal:** 21 Agustus 2026

---

## 1. Latar Belakang

Pengguna ingin memiliki "pacar virtual" berbasis AI yang bisa diajak chat & bertukar pesan suara (voice note) setiap hari lewat Telegram. Bot ini harus:
- Aktif 24 jam tanpa laptop pengguna perlu menyala (di-hosting di cloud gratis).
- Memiliki kepribadian yang bisa diatur/dikustomisasi via prompt.
- Bisa melakukan roleplay romantis/sosial (non-NSFW).
- Bisa mengingatkan hal-hal tertentu (reminder) dan menyapa secara proaktif (pagi/malam).
- Punya memori jangka panjang (ingat percakapan sebelumnya & fakta penting tentang user).
- Bisa kirim foto / generate gambar.
- Bisa kirim pesan suara (Voice Note) dengan suara ramah Bahasa Indonesia.
- Seluruh biaya operasional 100% gratis (Rp0).

---

## 2. Tujuan Produk

Membangun chatbot Telegram bertenaga AI yang berperan sebagai teman/pacar virtual dengan kepribadian custom, mampu roleplay, mengingat konteks jangka panjang, mengirim reminder & pesan proaktif harian, menghasilkan gambar, dan mengirim pesan suara — seluruhnya berjalan otomatis 24/7 di cloud gratis.

---

## 3. Target Pengguna

- Pengguna individu (personal use), pemula/non-teknis, yang menginginkan teman ngobrol virtual yang perhatian dan interaktif.

---

## 4. Fitur Utama

### 4.1 Chat Harian & Pesan Suara (Text & Voice Note)
- User mengirim pesan teks ke bot Telegram, bot membalas secara natural menggunakan LLM.
- **Pesan Suara (Voice Note):** Bot bisa membalas dengan audio/voice note Bahasa Indonesia yang alami menggunakan Microsoft Edge TTS (`edge-tts`). Trigger via command `/vn [teks]` atau deteksi konteks.

### 4.2 Kustomisasi Kepribadian (Persona)
- User bisa mengatur nama panggilan, sifat (misal: manja, cuek tapi perhatian, humoris, protektif), gaya bicara, dan panggilan sayang.
- Disimpan sebagai persona config yang bisa diedit kapan saja lewat Telegram dengan command `/setpersona [deskripsi]`.

### 4.3 Chat Proaktif Harian
- **Sapaan Otomatis:** Bot mengirim pesan otomatis di waktu tertentu:
  - **Pagi (07:00):** Sapaan pagi ramah/perhatian.
  - **Malam (21:30):** Menanyakan kabar harian & pesan sebelum tidur.

### 4.4 Memori Jangka Panjang (Persistent Memory)
- Bot mengingat: nama user, preferensi, kejadian penting yang pernah diceritakan, hobi, dll.
- Simpan fakta penting & riwayat percakapan ke database cloud (**Supabase**) agar memori tidak pernah hilang walau server restart.

### 4.5 Reminder / Pengingat
- User bisa minta diingatkan sesuatu, contoh: `/ingatkan 19:00 Minum air putih`.
- Bot mengirim pesan otomatis di waktu yang ditentukan menggunakan background scheduler (`APScheduler`).

### 4.6 Generate Gambar
- User bisa minta bot generate gambar (misal foto "diri"-nya atau ilustrasi sesuai request).
- Menggunakan layanan gratis **Pollinations.ai**.

### 4.7 Roleplay Bertanggung Jawab
- Bot mendukung skenario roleplay harian & romantis.
- Batasan tegas: Konten seksual eksplisit (NSFW) dilarang demi keamanan akun Telegram & kuota API gratis.

### 4.8 Uptime 24/7 Gratis
- Bot di-deploy ke cloud gratis (**Render.com** / **Koyeb**) dan dijaga Uptime-nya dengan ping berkala dari **UptimeRobot** / **cron-job.org**.

---

## 5. Arsitektur Teknis & Tech Stack (100% Rp0)

| Komponen | Teknologi / Layanan | Keterangan & Biaya |
|---|---|---|
| **Language & Core Framework** | Python 3.11 + `python-telegram-bot` | Gratis, modern, efisien |
| **Otak AI (LLM)** | Google Gemini 2.0 Flash (`google-genai`) | Gratis (1500 request/hari via Google AI Studio) |
| **Memori & Database** | Supabase (PostgreSQL Cloud) | Gratis (Free tier 500MB persisten di cloud) |
| **Pesan Suara (TTS)** | `edge-tts` (Microsoft Edge Neural TTS) | Gratis 100%, suara Bahasa Indonesia alami |
| **Generate Gambar** | Pollinations.ai API | Gratis, tanpa API Key |
| **Scheduler (Reminder & Sapaan)** | `APScheduler` | Jalan terintegrasi di bot Python |
| **Hosting Cloud 24/7** | Render.com / Koyeb Web Service | Gratis (Free tier) |
| **Keep-Alive (Prevent Sleep)** | UptimeRobot / Cron-Job.org | Gratis (Ping HTTP tiap 10 menit) |

---

## 6. Metrik Keberhasilan & Target MVP

- Bot aktif merespons pesan Telegram < 5 detik.
- Bot dapat mengirim voice note bening & lancar dalam Bahasa Indonesia.
- Bot dapat menyimpan dan mengingat setidaknya fakta dasar user dari percakapan sebelumnya.
- Bot berhasil mengirim sapaan pagi & malam otomatis.
- Seluruh infrastruktur berjalan 100% tanpa biaya (Rp0).

---
