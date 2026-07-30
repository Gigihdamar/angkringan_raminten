"""
Script inisialisasi database Angkringan Raminten.

CARA PAKAI:
    Jalankan file ini SEKALI SAJA setelah database MySQL (Filess.io)
    sudah dikonfigurasi di config.py, baik dari komputer lokal maupun
    dari terminal manapun yang bisa mengakses internet ke host MySQL-nya.

        python init_db.py

Script ini AMAN dijalankan berulang kali (idempotent) -- db.create_all()
tidak akan menghapus tabel yang sudah ada, dan seed_data() hanya mengisi
data kalau tabel terkait masih kosong.

Setelah dijalankan sekali dan berhasil, TIDAK PERLU dijalankan lagi saat
deploy ke Vercel. app.py tidak lagi memanggil fungsi ini secara otomatis,
supaya tidak dieksekusi berulang-ulang di setiap "cold start" serverless
function (yang berisiko menyebabkan race condition / crash saat beberapa
instance jalan bersamaan).
"""

from app import app
from database import db
from models import MenuItem, CashierStaff, KitchenStaff, Table


def seed_data():
    """Mengisi data awal (akun pegawai & menu contoh) jika database masih kosong."""

    if CashierStaff.query.count() == 0:
        cashier = CashierStaff(username="admin", name="Admin Kasir", role="cashier")
        cashier.set_password("admin123")
        db.session.add(cashier)
        print("  + Akun kasir 'admin' dibuat.")

        kitchen = KitchenStaff(username="dapur", name="Pegawai Dapur", role="kitchen")
        kitchen.set_password("dapur123")
        db.session.add(kitchen)
        print("  + Akun dapur 'dapur' dibuat.")
    else:
        print("  = Akun staff sudah ada, dilewati.")

    if Table.query.count() == 0:
        for number in range(1, 11):
            db.session.add(Table(number=number))
        print("  + 10 meja dibuat.")
    else:
        print("  = Data meja sudah ada, dilewati.")

    if MenuItem.query.count() == 0:
        # (nama, kategori, harga, deskripsi, nama file foto di static/images/menu/)
        sample_menu = [
            ("Nasi Kucing Teri", "Makanan", 4000, "Nasi porsi kecil khas angkringan dengan sambal teri.", "nasi-kucing-teri.jpg"),
            ("Nasi Kucing Oseng Tempe", "Makanan", 4000, "Nasi porsi kecil dengan oseng tempe pedas.", "nasi-kucing-oseng-tempe.jpg"),
            ("Nasi Kucing Spesial", "Makanan", 5000, "Nasi kucing dengan lauk lebih lengkap dan sambal spesial.", "nasi-kucing-spesial.jpg"),
            ("Sate Usus", "Makanan", 3000, "Sate usus ayam bumbu kecap, dibakar hangat.", "sate-usus.jpg"),
            ("Sate Telur Puyuh", "Makanan", 3000, "Sate telur puyuh bumbu bacem.", "sate-telur-puyuh.jpg"),
            ("Tempe Bacem", "Makanan", 2000, "Tempe bacem manis gurih khas Jogja.", "tempe-bacem.jpg"),
            ("Wedang Ronde", "Minuman", 8000, "Wedang jahe hangat dengan isian ronde.", "wedang-ronde.jpg"),
            ("Es Teh Manis", "Minuman", 5000, "Teh manis dingin segar.", "es-teh-manis.jpg"),
            ("Kopi Hitam", "Minuman", 6000, "Kopi hitam tubruk khas angkringan.", "kopi-hitam.jpg"),
            ("Wedang Uwuh", "Minuman", 8000, "Minuman rempah hangat khas Jogja.", "wedang-uwuh.jpg"),
            ("Wedang Jahe", "Minuman", 6000, "Wedang jahe hangat pedas menyegarkan.", "wedang-jahe.jpg"),
            ("Wedang Tamyet", "Minuman", 7000, "Wedang rempah khas angkringan, hangat di badan.", "wedang-tamyet.jpg"),
            ("Tahu Susu Goreng", "Cemilan", 3000, "Tahu isi goreng renyah.", "tahu-susu-goreng.jpg"),
            ("Tempe Mendoan", "Cemilan", 3000, "Tempe mendoan tepung crispy.", "tempe-mendoan.jpg"),
            ("Kacang Rebus", "Cemilan", 3000, "Kacang tanah rebus gurih.", "kacang-rebus.jpg"),
            ("Perkedel Halilintar", "Cemilan", 3000, "Perkedel goreng pedas menggelegar.", "perding-halilitar.jpg"),
        ]
        for name, category, price, desc, image in sample_menu:
            item = MenuItem(name=name, category=category, description=desc, image=f"menu/{image}")
            item.price = price
            db.session.add(item)
        print(f"  + {len(sample_menu)} menu contoh dibuat.")
    else:
        print("  = Data menu sudah ada, dilewati.")

    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        print("Menghubungkan ke database & membuat tabel (kalau belum ada)...")
        db.create_all()
        print("Tabel siap. Mengisi data awal...")
        seed_data()
        print("Selesai! Database sudah siap dipakai.")