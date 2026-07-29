import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Konfigurasi utama aplikasi Angkringan Raminten.
    Semua pengaturan environment aplikasi diletakkan di sini
    agar app.py tetap bersih dan mudah dibaca.
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "angkringan-raminten-secret-key-uas-pbo")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
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
