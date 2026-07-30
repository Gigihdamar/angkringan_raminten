from flask import Flask, render_template

from config import Config
from database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Registrasi Blueprint (routes) - dipisah per role sesuai struktur MVC
    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.admin import admin_bp

    app.register_blueprint(customer_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        # Pastikan session yang gagal di-rollback, supaya request
        # berikutnya di instance yang sama tidak ikut error karena
        # transaksi lama masih "menggantung".
        db.session.rollback()
        return render_template("404.html"), 500

    @app.context_processor
    def inject_contact():
        """Membuat info kontak/sosial media (config.py) tersedia di semua
        template lewat variabel 'contact', dipakai footer & halaman About."""
        return {
            "contact": {
                "address": Config.ADDRESS_TEXT,
                "instagram_url": Config.INSTAGRAM_URL,
                "whatsapp_url": Config.WHATSAPP_URL,
                "whatsapp_display": Config.WHATSAPP_DISPLAY,
                "maps_search_url": Config.MAPS_SEARCH_URL,
                "maps_embed_url": Config.MAPS_EMBED_URL,
            }
        }

    # ------------------------------------------------------------------
    # PENTING (Vercel / serverless):
    # db.create_all() dan seed_data() SENGAJA TIDAK dijalankan otomatis
    # di sini lagi. Di lingkungan serverless, blok ini akan dieksekusi
    # ulang setiap kali terjadi "cold start", dan beberapa instance bisa
    # berjalan bersamaan (paralel) sehingga proses seeding bisa saling
    # tabrakan (duplicate insert -> IntegrityError -> function crash).
    #
    # Jalankan pembuatan tabel & seed data SEKALI SAJA secara manual
    # lewat file init_db.py (lihat instruksi di file tersebut), baik di
    # komputer lokal maupun lewat "Run Command" di dashboard Vercel.
    # ------------------------------------------------------------------

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)