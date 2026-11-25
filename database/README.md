# Database Ayaka Sync

- `schema.sql`: skema PostgreSQL lengkap untuk akun, sesi login, limit, statistik harian, uptime, pembayaran, kupon, aktivitas, audit, dan token.
- Jalankan dengan `psql "$DATABASE_URL" -f database/schema.sql`, atau aplikasi akan menginisialisasikannya saat startup jika `DATABASE_URL` tersedia.
- `login_sessions` menyimpan hash token sesi (bukan token mentah), alamat IP, user-agent, masa berlaku, dan status pencabutan.
- `statistics_daily` adalah agregat harian; `uptime_checks` menyimpan riwayat pemeriksaan; `server_instances` menyimpan heartbeat instance.
- `usage_limits` adalah ringkasan kuota; `limit_usage_events` adalah histori perubahan/pemakaian kuota.

Catatan: endpoint aktivasi pada starter project masih berupa pencatatan permintaan. Kuota tidak dikurangi sampai integrasi provider resmi berhasil dan aturan konsumsi limit diterapkan.
