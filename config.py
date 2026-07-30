import os
from urllib.parse import quote_plus

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Konfigurasi utama aplikasi Angkringan Raminten.
    Semua pengaturan environment aplikasi diletakkan di sini
    agar app.py tetap bersih dan mudah dibaca.
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "angkringan-raminten-secret-key-uas-pbo")

    # ------------------------------------------------------------------
    # Koneksi Database MySQL (Filess.io).
    # Nilai default di bawah diambil dari halaman "Connection Information"
    # Filess.io. Sebaiknya di production nilai ini di-set lewat environment
    # variable (mis. file .env / Vercel Environment Variables), bukan
    # ditulis langsung di kode, agar kredensial tidak ikut ter-commit ke Git.
    # ------------------------------------------------------------------
    DB_USER = os.environ.get("DB_USER", "angkringan_pressurein")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "3b5a72170d914772a091f36ea8ba0d0c72376e99")
    DB_HOST = os.environ.get("DB_HOST", "cpij9v.h.filess.io")
    DB_PORT = os.environ.get("DB_PORT", "3307")
    DB_NAME = os.environ.get("DB_NAME", "angkringan_pressurein")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images", "menu")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # ------------------------------------------------------------------
    # Info kontak & sosial media Angkringan Raminten.
    # GANTI nilai di bawah ini dengan data asli warung Anda -- dipakai
    # oleh tombol Instagram/WhatsApp/Lokasi di footer dan peta di halaman
    # "Tentang Kami" (templates/customer/about.html).
    # ------------------------------------------------------------------
    ADDRESS_TEXT = "Jl. Malioboro, Yogyakarta"
    INSTAGRAM_USERNAME = "angkringanraminten"   # tanpa "@"
    WHATSAPP_NUMBER = "6281234567890"           # format 62xxxxxxxxxx, tanpa +/spasi
    WHATSAPP_DISPLAY = "+62 812-3456-7890"
    WHATSAPP_MESSAGE = "Halo Angkringan Raminten, saya ingin bertanya mengenai menu."

    INSTAGRAM_URL = f"https://instagram.com/{INSTAGRAM_USERNAME}"
    WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}?text={WHATSAPP_MESSAGE.replace(' ', '%20')}"
    MAPS_SEARCH_URL = f"https://www.google.com/maps/search/?api=1&query={ADDRESS_TEXT.replace(' ', '+')}"
    MAPS_EMBED_URL = f"https://maps.google.com/maps?q={ADDRESS_TEXT.replace(' ', '+')}&t=&z=16&ie=UTF8&iwloc=&output=embed"