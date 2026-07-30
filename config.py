import os
import shutil
import sqlalchemy
from urllib.parse import quote_plus

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_uri():
    """
    Menyediakan URI database secara aman & stabil (Fail-safe System):
    1. Menggunakan DATABASE_URL jika diset di Vercel Environment Variables.
    2. Menggunakan MySQL hanya jika diset USE_MYSQL=1 di Environment Variables.
    3. Default: SQLite (database.db dengan dukungan /tmp Vercel) -> 100% Bebas dari Limit 5 Koneksi
       Filess.io (Error 1226) yang Menyebabkan Crash 404/500 di Vercel.
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")

    if os.environ.get("USE_MYSQL", "").lower() in ["1", "true", "yes"]:
        db_user = os.environ.get("DB_USER", "angkringan_pressurein")
        db_pass = os.environ.get("DB_PASSWORD", "3b5a72170d914772a091f36ea8ba0d0c72376e99")
        db_host = os.environ.get("DB_HOST", "cpij9v.h.filess.io")
        db_port = os.environ.get("DB_PORT", "3307")
        db_name = os.environ.get("DB_NAME", "angkringan_pressurein")
        return (
            f"mysql+pymysql://{db_user}:{quote_plus(db_pass)}"
            f"@{db_host}:{db_port}/{db_name}"
        )

    sqlite_src = os.path.join(BASE_DIR, "database.db")
    tmp_dir = "/tmp"
    if os.path.exists(tmp_dir) and os.access(tmp_dir, os.W_OK):
        sqlite_dst = os.path.join(tmp_dir, "database.db")
        if not os.path.exists(sqlite_dst) and os.path.exists(sqlite_src):
            try:
                shutil.copy2(sqlite_src, sqlite_dst)
            except Exception:
                pass
        if os.path.exists(sqlite_dst):
            return f"sqlite:///{sqlite_dst}"
    return f"sqlite:///{sqlite_src}"


class Config:
    """
    Konfigurasi utama aplikasi Angkringan Raminten.
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "angkringan-raminten-secret-key-uas-pbo")
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 2,
        "max_overflow": 0,
        "pool_recycle": 60,
        "pool_timeout": 10,
        "pool_pre_ping": True,
    }
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