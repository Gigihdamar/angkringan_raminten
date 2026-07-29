from flask import Flask, render_template

from config import Config
from database import db
from models import MenuItem, CashierStaff, KitchenStaff, Table


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

    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    """Mengisi data awal (akun pegawai & menu contoh) jika database masih kosong."""

    if CashierStaff.query.count() == 0:
        cashier = CashierStaff(username="admin", name="Admin Kasir", role="cashier")
        cashier.set_password("admin123")
        db.session.add(cashier)

        kitchen = KitchenStaff(username="dapur", name="Pegawai Dapur", role="kitchen")
        kitchen.set_password("dapur123")
        db.session.add(kitchen)

    if Table.query.count() == 0:
        for number in range(1, 11):
            db.session.add(Table(number=number))

    if MenuItem.query.count() == 0:
        # (nama, kategori, harga, deskripsi, nama file foto di static/images/menu/)
        sample_menu = [
            ("Nasi Kucing Teri", "Makanan", 4000, "Nasi porsi kecil khas angkringan dengan sambal teri.", "nasi kucing teri.jpg"),
            ("Nasi Kucing Oseng Tempe", "Makanan", 4000, "Nasi porsi kecil dengan oseng tempe pedas.", "nasi kucing oseng tempe.jpg"),
            ("Nasi Kucing Spesial", "Makanan", 5000, "Nasi kucing dengan lauk lebih lengkap dan sambal spesial.", "nasi kucing spesial.jpg"),
            ("Sate Usus", "Makanan", 3000, "Sate usus ayam bumbu kecap, dibakar hangat.", "sate usus.jpg"),
            ("Sate Telur Puyuh", "Makanan", 3000, "Sate telur puyuh bumbu bacem.", "sate telur puyuh.jpg"),
            ("Tempe Bacem", "Makanan", 2000, "Tempe bacem manis gurih khas Jogja.", "tempe bacem.jpg"),
            ("Wedang Ronde", "Minuman", 8000, "Wedang jahe hangat dengan isian ronde.", "wedang ronde.jpg"),
            ("Es Teh Manis", "Minuman", 5000, "Teh manis dingin segar.", "es teh manis.jpg"),
            ("Kopi Hitam", "Minuman", 6000, "Kopi hitam tubruk khas angkringan.", "kopi hitam.jpg"),
            ("Wedang Uwuh", "Minuman", 8000, "Minuman rempah hangat khas Jogja.", "wedang uwuh.jpg"),
            ("Wedang Jahe", "Minuman", 6000, "Wedang jahe hangat pedas menyegarkan.", "wedang jahe.jpg"),
            ("Wedang Tamyet", "Minuman", 7000, "Wedang rempah khas angkringan, hangat di badan.", "wedang tamyet.jpg"),
            ("Tahu Susu Goreng", "Cemilan", 3000, "Tahu isi goreng renyah.", "tahu susu goreng.jpg"),
            ("Tempe Mendoan", "Cemilan", 3000, "Tempe mendoan tepung crispy.", "tempe mendoan.jpg"),
            ("Kacang Rebus", "Cemilan", 3000, "Kacang tanah rebus gurih.", "kacang rebus.jpg"),
            ("Perkedel Halilintar", "Cemilan", 3000, "Perkedel goreng pedas menggelegar.", "perding halilitar.jpg"),
        ]
        for name, category, price, desc, image in sample_menu:
            item = MenuItem(name=name, category=category, description=desc, image=f"menu/{image}")
            item.price = price
            db.session.add(item)

    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
