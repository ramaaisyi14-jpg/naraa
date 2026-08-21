# Panduan Setup Database Supabase (1-Click SQL Script)

Untuk membuat tabel-tabel dan menonaktifkan aturan RLS agar bot dapat menyimpan memori secara gratis tanpa hambatan, ikuti langkah berikut:

1. Login ke dashboard [Supabase](https://supabase.com/).
2. Buka proyek kamu -> Klik menu **SQL Editor** (ikon `>_` di menu sebelah kiri).
3. Klik **"New query"**.
4. Copy-paste (salin & tempel) seluruh kode SQL di bawah ini:

```sql
-- 1. Tabel Profil User
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id BIGINT PRIMARY KEY,
    name TEXT,
    username TEXT,
    persona TEXT DEFAULT 'default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabel Riwayat Chat
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabel Memori / Fakta User
CREATE TABLE IF NOT EXISTS memories (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    fact TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabel Pengingat (Reminders)
CREATE TABLE IF NOT EXISTS reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    reminder_text TEXT NOT NULL,
    rem_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Menonaktifkan Row Level Security (RLS) agar bot bebas menyimpan data
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE memories DISABLE ROW LEVEL SECURITY;
ALTER TABLE reminders DISABLE ROW LEVEL SECURITY;
```

5. Klik tombol **"Run"** (atau `Ctrl + Enter`).
6. Selesai! Seluruh tabel dan izin simpan memori Nara sudah siap 100%!
