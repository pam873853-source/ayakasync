# Ayaka Sync

Starter project Flask untuk dashboard membership dan pencatatan aktivasi.

## Fitur
- Landing page responsif, sidebar member, dark/light mode, GSAP motion.
- Login/register dengan password hashing dan server-side session.
- Plan Free (20), Pro (500), Enterprise (1000).
- Upload bukti QRIS, verifikasi manual oleh admin.
- Admin generate kupon AYK + kode acak.
- Activity log, activation request, dan bulk request placeholder.
- Neon PostgreSQL melalui `DATABASE_URL`.

## Jalankan lokal
1. Install Python 3.10+.
2. Buat database PostgreSQL di Neon.
3. Salin `.env.example` menjadi `.env`, lalu isi `SECRET_KEY` dan `DATABASE_URL`.
4. Buat virtual environment dan install dependensi:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Buat admin pertama melalui SQL setelah register:
   ```sql
   UPDATE users SET is_admin = TRUE WHERE username = 'OLPI STORE';
   ```
   Daftarkan akun admin terlebih dahulu melalui halaman Register. Jangan gunakan password contoh/yang pernah dibagikan; buat password baru yang kuat.
6. Jalankan:
   ```bash
   python app.py
   ```
7. Buka `http://localhost:5000`.

## Konfigurasi QRIS
Di `templates/payment.html`, ganti kotak placeholder QRIS dengan gambar QRIS merchant resmi milikmu. Jangan memakai QR pembayaran milik orang lain.

## Integrasi aktivasi dan bulk
Route `/activation` dan `/bulk` saat ini hanya mencatat permintaan. Hubungkan ke API resmi/berizin yang dokumentasi dan kredensialnya memang kamu kuasai. Jangan menaruh token rahasia di JavaScript frontend. Simpan credential provider di environment variable atau secret manager.

## Catatan produksi
- Ganti `SECRET_KEY` dengan nilai acak kuat.
- Gunakan HTTPS.
- Batasi ukuran file upload di reverse proxy, scan file upload, dan simpan bukti transaksi di object storage privat.
- Tambahkan CSRF protection, rate limiting, email verification, reset password, audit log, dan kebijakan retensi data sebelum dipakai publik.
- Buat verifikasi pembayaran berbasis webhook provider bila tersedia. Jangan mengaktifkan plan hanya karena file diunggah.
- Sistem limit starter ini belum melakukan decrement limit karena tiap jenis aktivasi perlu aturan bisnis dan provider yang sah. Implementasikan decrement secara atomik setelah aktivasi sukses.
- Coupon starter mencatat kode dan diskon; perhitungan diskon checkout perlu disambungkan ke alur pembayaran sebelum digunakan untuk transaksi riil.


## Neo Brutalism Edition
- Landing page dilengkapi panduan penggunaan dan tutorial aktivasi.
- Header menampilkan jam, tanggal, estimasi baterai (jika browser mendukung Battery Status API), dan uptime sesi halaman.
- Uptime yang ditampilkan adalah durasi sejak halaman dibuka, bukan uptime server.
- Navigasi utama: Home, Aktivasi, Plan, Profil.
- GSAP + ScrollTrigger digunakan untuk animasi masuk dan animasi saat scroll.


## Landing page content update
- Landing page sekarang memuat bagian 3 sampai 10 sesuai naskah yang diberikan: definisi aktivasi, persiapan, langkah pengajuan, status, alasan penolakan, FAQ, CTA, dan footer.
- Animasi GSAP hanya menjadi progressive enhancement. Semua kartu dan teks tetap terlihat jika CDN GSAP/ScrollTrigger gagal dimuat.
- Layout mobile memakai grid satu kolom dan mencegah horizontal overflow.
- Estimasi waktu 5–30 menit adalah keterangan panduan yang ditampilkan, bukan jaminan SLA.


## Pemisahan Landing Page dan Home
- `/` adalah landing page publik dengan sambutan "Selamat datang di Ayaka Aktivasi" dan panduan.
- `/dashboard` adalah Home khusus member setelah login.
- Home menampilkan sapaan personal berdasarkan username akun dan jam lokal perangkat (pagi/siang/sore/malam), diperbarui otomatis.
- Home memiliki tombol "Mulai Aktivasi" dan "Jelajahi Website Aktivasi Alight Motion".
- Halaman `/activation` memiliki bagian workspace Alight Motion. Aktivasi otomatis akun sebenarnya tetap memerlukan provider resmi yang berwenang.
