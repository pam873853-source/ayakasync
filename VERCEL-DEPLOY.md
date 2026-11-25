# Deploy Ayaka Sync ke Vercel

## 1. Import project
Upload/push seluruh isi folder ini ke GitHub, lalu import repository dari Vercel.

## 2. Environment Variables
Di Vercel > Project > Settings > Environment Variables, tambahkan:
- `SECRET_KEY`: string acak panjang dan rahasia.
- `DATABASE_URL`: Neon connection string. Gunakan format `postgresql://...` atau `postgresql+psycopg://...` dengan SSL.

Redeploy setelah mengubah environment variables.

## 3. Neon
Pastikan database Neon aktif dan kredensial benar. Aplikasi akan mencoba membuat tabel ketika serverless function melakukan cold start. Jika login masih gagal, buka Vercel > Deployments > Functions > Logs untuk pesan error yang sebenarnya.

## 4. Admin
Daftarkan akun admin dari halaman Register, lalu jalankan di Neon SQL Editor:
```sql
UPDATE users SET is_admin = TRUE WHERE username = 'OLPI STORE';
```
Gunakan password baru yang kuat. Jangan gunakan password contoh yang pernah dikirim di chat.

## 5. QRIS
Taruh gambar QRIS milik toko sendiri di folder `assets/`, misalnya `assets/qris.png`, lalu ubah `filename='qris-placeholder.svg'` pada `templates/payment.html` menjadi `filename='qris.png'`.

## Catatan penting
Vercel Function memiliki filesystem sementara. Bukti pembayaran yang diunggah ke folder `uploads/` tidak cocok untuk penyimpanan permanen. Untuk produksi, pindahkan bukti pembayaran ke object storage privat (misalnya Vercel Blob atau S3-compatible storage). Jangan menyimpan secret API provider di frontend.
