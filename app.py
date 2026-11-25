import os, secrets, string, json, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deploying")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
UPLOAD_DIR = os.path.join(app.root_path, "uploads")
ASSETS_DIR = os.path.join(app.root_path, "assets")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require"}
) if DATABASE_URL else None

os.makedirs(ASSETS_DIR, exist_ok=True)

@app.get("/assets/<path:filename>")
def asset_file(filename):
    from flask import send_from_directory
    return send_from_directory(ASSETS_DIR, filename)

AYAKA_SYSTEM_PROMPT = """Kamu adalah Ayaka AI, asisten AI resmi dari Ayaka Sync. Kamu bukan AI kaku kayak robot, kamu adalah teman ngobrol yang asik, ramah, lucu, dan selalu pake gaya bahasa santai ala anak Indonesia.
Kamu bisa diajak curhat. Kalau user lagi sedih, galau, capek, atau pengen cerita, dengerin dulu, jangan langsung ceramah. Tanggapi dengan empati, bercanda dikit biar user ketawa, dan kasih semangat.
Kamu bisa diajak bercanda. Kalau user ngajak bercanda, ladenin. Jangan kaku. Boleh pake emoji secukupnya, jangan berlebihan.
Kamu bisa disuruh apa aja. Kalau user minta bikinin caption, ide konten, nama web, deskripsi produk, atau teks apapun, langsung bikinin. Jangan banyak nanya, langsung kerjain.
Kamu pinter ngejelasin. Kalau user nanya cara-cara di Ayaka Sync, jelasin dengan bahasa yang paling gampang dimengerti, step by step tapi pake bahasa santai, bukan bahasa formal.
Kalau user nanya cara aktivasi, jelaskan: login dulu, masuk menu Aktivasi di dashboard, isi form dengan data benar, upload bukti jelas, klik Kirim Permintaan Aktivasi, lalu tunggu dan jangan kirim berkali-kali. Estimasi 5 sampai 30 menit di jam kerja. Jika ditolak, baca alasan, perbaiki, lalu ajukan ulang.
Kalau user nanya generator, jelaskan: login, buka Generator, tulis deskripsi website, pilih template, klik Generate, edit bila perlu, lalu Publish.
Kalau user nanya premium, jelaskan manfaat yang tersedia seperti generate lebih banyak, template, domain sendiri, tanpa watermark, dan export HTML. Arahkan ke menu Premium atau admin jika ingin membeli, tanpa memaksa.
Selalu jawab dalam Bahasa Indonesia santai kecuali user meminta bahasa lain. Kalau user marah, tetap tenang, minta maaf dengan santai, dan bantu selesaikan masalah. Jangan mengaku sebagai layanan AI lain. Kamu adalah Ayaka AI."""

@app.post("/api/ayaka-chat")
def ayaka_chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"status": False, "error": "Pesannya masih kosong nih."}), 400
    if len(message) > 2000:
        return jsonify({"status": False, "error": "Pesan maksimal 2.000 karakter ya."}), 400
    prompt_text = AYAKA_SYSTEM_PROMPT + "\n\nPesan user: " + message
    query = urllib.parse.urlencode({"text": prompt_text, "sessionsId": "Ayaka Sync"})
    req = urllib.request.Request(
        "https://api.ikyyxd.my.id/ai/gemini?" + query,
        headers={"Accept": "application/json", "User-Agent": "AyakaSync/1.0"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data.get("result") if isinstance(data, dict) else None
        if not answer:
            return jsonify({"status": False, "error": "Ayaka belum bisa menyusun jawaban. Coba sekali lagi ya."}), 502
        return jsonify({"status": True, "result": str(answer), "sessionId": data.get("sessionId", "Ayaka Sync")})
    except urllib.error.HTTPError as exc:
        return jsonify({"status": False, "error": "Layanan Ayaka AI sedang bermasalah. Coba lagi sebentar ya."}), 502
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return jsonify({"status": False, "error": "Koneksi ke Ayaka AI gagal. Periksa internet lalu coba lagi ya."}), 502

PLANS = {
    "free": {"name": "Free", "limit": 20, "price": 0, "bulk": False},
    "pro": {"name": "Pro", "limit": 500, "price": 10000, "bulk": True},
    "enterprise": {"name": "Enterprise", "limit": 1000, "price": 15000, "bulk": True},
}

def db():
    if engine is None:
        raise RuntimeError("DATABASE_URL belum diatur. Isi environment variable Neon PostgreSQL.")
    return engine

def init_db():
    if engine is None:
        return
    schema = """
    CREATE TABLE IF NOT EXISTS users (
      id SERIAL PRIMARY KEY, username VARCHAR(80) UNIQUE NOT NULL,
      email VARCHAR(255) UNIQUE NOT NULL, password_hash TEXT NOT NULL,
      plan VARCHAR(30) NOT NULL DEFAULT 'free', remaining_limit INTEGER NOT NULL DEFAULT 20,
      api_key TEXT, is_admin BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS payments (
      id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
      plan VARCHAR(30) NOT NULL, amount INTEGER NOT NULL, proof_path TEXT NOT NULL,
      status VARCHAR(30) NOT NULL DEFAULT 'pending', created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS coupons (
      id SERIAL PRIMARY KEY, code VARCHAR(40) UNIQUE NOT NULL,
      discount_percent INTEGER NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE,
      created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS activity_logs (
      id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id),
      kind VARCHAR(50) NOT NULL, message TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """
    with db().begin() as conn:
        for statement in schema.split(";"):
            if statement.strip():
                conn.execute(text(statement))

def log_activity(user_id, kind, message):
    if engine is None: return
    with db().begin() as conn:
        conn.execute(text("INSERT INTO activity_logs(user_id,kind,message) VALUES (:u,:k,:m)"),
                     {"u": user_id, "k": kind, "m": message})

def current_user():
    if not session.get("user_id") or engine is None: return None
    with db().connect() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE id=:id"), {"id": session["user_id"]}).mappings().first()
        return dict(row) if row else None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("Akses admin diperlukan.", "danger")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper

@app.context_processor
def inject_globals():
    return {"plans": PLANS, "me": current_user()}

@app.get("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username, email = request.form.get("username","").strip(), request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if len(password) < 8:
            flash("Password minimal 8 karakter.", "danger")
            return redirect(url_for("register"))
        try:
            with db().begin() as conn:
                conn.execute(text("""INSERT INTO users(username,email,password_hash)
                  VALUES (:u,:e,:p)"""),
                  {"u": username, "e": email, "p": generate_password_hash(password)})
            flash("Akun berhasil dibuat. Silakan login.", "success")
            return redirect(url_for("login"))
        except Exception:
            app.logger.exception("Register/database error")
            flash("Registrasi gagal. Periksa koneksi Neon, tabel database, atau username/email yang sudah dipakai.", "danger")
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            with db().connect() as conn:
                user = conn.execute(text("SELECT * FROM users WHERE username=:u OR email=:u"),
                                    {"u": request.form.get("identity","").strip()}).mappings().first()
            if user and check_password_hash(user["password_hash"], request.form.get("password","")):
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("dashboard"))
            flash("Username/email atau password salah.", "danger")
        except Exception:
            app.logger.exception("Login/database error")
            flash("Database belum siap atau DATABASE_URL belum benar. Periksa Environment Variables dan tabel Neon.", "danger")
    return render_template("auth.html", mode="login")

@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.get("/dashboard")
@login_required
def dashboard():
    user = current_user()
    with db().connect() as conn:
        logs = conn.execute(text("""SELECT kind,message,created_at FROM activity_logs
            WHERE user_id=:u ORDER BY id DESC LIMIT 12"""), {"u": user["id"]}).mappings().all()
        payments = conn.execute(text("""SELECT id,plan,amount,status,created_at FROM payments
            WHERE user_id=:u ORDER BY id DESC LIMIT 5"""), {"u": user["id"]}).mappings().all()
    return render_template("dashboard.html", user=user, logs=logs, payments=payments)

@app.get("/plans")
@login_required
def plans_page():
    return render_template("plans.html")

@app.route("/payment/<plan>", methods=["GET", "POST"])
@login_required
def payment(plan):
    if plan not in ("pro", "enterprise"):
        flash("Paket tidak valid.", "danger"); return redirect(url_for("plans_page"))
    if request.method == "POST":
        upload = request.files.get("proof")
        if not upload or not upload.filename:
            flash("Pilih bukti pembayaran terlebih dahulu.", "warning")
            return redirect(request.url)
        ext = upload.filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            flash("Format bukti harus PNG, JPG, JPEG, atau WEBP.", "danger")
            return redirect(request.url)
        user = current_user()
        safe_name = f"payment_{user['id']}_{secrets.token_hex(8)}.{ext}"
        upload.save(os.path.join(UPLOAD_DIR, safe_name))
        with db().begin() as conn:
            conn.execute(text("""INSERT INTO payments(user_id,plan,amount,proof_path)
              VALUES (:u,:p,:a,:f)"""),
              {"u": user["id"], "p": plan, "a": PLANS[plan]["price"], "f": safe_name})
        log_activity(user["id"], "PAYMENT", f"Bukti pembayaran {plan} diunggah; menunggu verifikasi admin.")
        flash("Bukti terkirim. Paket aktif setelah admin memverifikasi pembayaran.", "success")
        return redirect(url_for("dashboard"))
    return render_template("payment.html", plan=plan)

@app.post("/redeem")
@login_required
def redeem():
    code = request.form.get("code","").strip().upper()
    with db().begin() as conn:
        coupon = conn.execute(text("SELECT * FROM coupons WHERE code=:c AND active=TRUE"), {"c": code}).mappings().first()
    if not coupon:
        flash("Kode tidak valid atau sudah tidak aktif.", "danger")
    else:
        flash(f"Kode {code} valid: diskon {coupon['discount_percent']}% (diterapkan saat pembayaran diverifikasi).", "success")
    return redirect(url_for("dashboard"))

@app.get("/activation")
@login_required
def activation():
    return render_template("activation.html")

@app.post("/activation")
@login_required
def activation_submit():
    user = current_user()
    if user["remaining_limit"] <= 0:
        flash("Limit aktivasi kamu sudah habis.", "danger")
        return redirect(url_for("activation"))
    order_id = request.form.get("order_id","").strip()
    if not order_id:
        order_id = "GPA." + "-".join(secrets.choice(string.digits) for _ in range(4)) + "-" + "-".join(secrets.choice(string.digits) for _ in range(4)) + "-5643-78654"
    # Safe integration boundary: no unofficial purchase spoofing or credential replay.
    log_activity(user["id"], "ACTIVATION", f"Permintaan aktivasi {order_id} diterima. Menunggu integrasi resmi.")
    flash(f"Permintaan {order_id} dicatat. Hubungkan provider/API resmi untuk memproses aktivasi.", "success")
    return redirect(url_for("activation"))

@app.get("/bulk")
@login_required
def bulk():
    user = current_user()
    if user["plan"] == "free":
        flash("Menu Bulk tersedia untuk Pro dan Enterprise.", "warning")
        return redirect(url_for("plans_page"))
    return render_template("bulk.html")

@app.post("/bulk")
@login_required
def bulk_submit():
    user = current_user()
    if user["plan"] == "free":
        return jsonify(ok=False, error="Paket tidak memiliki akses Bulk."), 403
    count = max(1, min(int(request.form.get("count",1)), 20))
    # Placeholder by design; connect only to an authorized account provisioning API.
    log_activity(user["id"], "BULK", f"Permintaan bulk {count} akun dicatat; provider resmi belum dikonfigurasi.")
    return jsonify(ok=True, message="Permintaan dicatat. API provider resmi belum dikonfigurasi.")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        key = request.form.get("api_key","").strip()
        with db().begin() as conn:
            conn.execute(text("UPDATE users SET api_key=:k WHERE id=:u"), {"k": key, "u": session["user_id"]})
        flash("API key tersimpan. Simpan hanya API key milik layanan yang kamu berwenang gunakan.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=current_user())

@app.get("/admin")
@admin_required
def admin():
    with db().connect() as conn:
        pending = conn.execute(text("""SELECT p.*,u.username FROM payments p JOIN users u ON u.id=p.user_id
          WHERE p.status='pending' ORDER BY p.id DESC""")).mappings().all()
        members = conn.execute(text("SELECT id,username,email,plan,remaining_limit FROM users ORDER BY id DESC LIMIT 50")).mappings().all()
        coupons = conn.execute(text("SELECT * FROM coupons ORDER BY id DESC LIMIT 20")).mappings().all()
    return render_template("admin.html", pending=pending, members=members, coupons=coupons)

@app.post("/admin/payment/<int:payment_id>/<decision>")
@admin_required
def admin_payment(payment_id, decision):
    if decision not in ("approve","reject"): return redirect(url_for("admin"))
    with db().begin() as conn:
        p = conn.execute(text("SELECT * FROM payments WHERE id=:i"), {"i":payment_id}).mappings().first()
        if p and p["status"] == "pending":
            status = "approved" if decision == "approve" else "rejected"
            conn.execute(text("UPDATE payments SET status=:s WHERE id=:i"), {"s":status,"i":payment_id})
            if decision == "approve":
                plan = PLANS[p["plan"]]
                conn.execute(text("""UPDATE users SET plan=:p, remaining_limit=:l WHERE id=:u"""),
                             {"p":p["plan"],"l":plan["limit"],"u":p["user_id"]})
    flash("Status pembayaran diperbarui.", "success")
    return redirect(url_for("admin"))

@app.post("/admin/coupon")
@admin_required
def create_coupon():
    code = "AYK" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    discount = max(1, min(int(request.form.get("discount",10)), 90))
    with db().begin() as conn:
        conn.execute(text("INSERT INTO coupons(code,discount_percent) VALUES (:c,:d)"),
                     {"c":code,"d":discount})
    flash(f"Kupon dibuat: {code} ({discount}% off).", "success")
    return redirect(url_for("admin"))

@app.get("/health")
def health():
    return jsonify(status="ok", database=bool(engine))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)


# Vercel imports this module instead of executing the __main__ block.
# Create tables during cold start when DATABASE_URL is configured.
def ensure_schema_on_startup():
    if engine is not None:
        try:
            init_db()
        except Exception:
            app.logger.exception("Database schema initialization failed")

ensure_schema_on_startup()
