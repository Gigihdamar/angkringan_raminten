from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db


class Staff(db.Model):
    """
    Class induk (parent/base class) yang merepresentasikan pegawai Angkringan
    Raminten. Class ini menerapkan konsep OOP:

    - Encapsulation : atribut password disimpan sebagai '_password_hash'
      (private/protected) dan hanya bisa diubah lewat method set_password(),
      tidak bisa diakses atau diubah langsung dari luar class.
    - Inheritance   : class CashierStaff dan KitchenStaff mewarisi seluruh
      atribut & method dasar dari class Staff ini (id, username, name, role).
    - Polymorphism  : method display_info() dan process_order() akan
      menghasilkan output yang berbeda tergantung sub-class yang memanggilnya
      (lihat CashierStaff & KitchenStaff di bawah).

    Menggunakan SQLAlchemy Single Table Inheritance: kolom 'type' dipakai
    sebagai penanda class turunan (polymorphic_identity), sehingga secara
    nyata Staff, CashierStaff, dan KitchenStaff tersimpan pada satu tabel
    'staff' namun tetap merupakan class Python yang berbeda dan saling
    mewarisi.
    """

    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column("password_hash", db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="staff")
    type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __mapper_args__ = {
        "polymorphic_identity": "staff",
        "polymorphic_on": type,
    }

    # ---------- Encapsulation: password tidak boleh diakses langsung ----------
    def set_password(self, plain_password):
        """Setter: menyimpan password dalam bentuk hash, bukan teks polos."""
        self._password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        """Memverifikasi password tanpa pernah membuka nilai aslinya."""
        return check_password_hash(self._password_hash, plain_password)

    # ---------- Polymorphism: akan di-override oleh sub-class ----------
    def display_info(self):
        """Representasi default seorang pegawai (akan berbeda di sub-class)."""
        return f"Staff #{self.id} - {self.name} ({self.role})"

    def process_order(self, order):
        """
        Method dasar untuk memproses pesanan. Setiap sub-class (CashierStaff,
        KitchenStaff) meng-override method ini sehingga menghasilkan perilaku
        yang berbeda meskipun nama method-nya sama (polymorphism).
        """
        return f"{self.name} sedang menangani pesanan #{order.id}."

    def __repr__(self):
        return f"<Staff {self.username} ({self.type})>"


class CashierStaff(Staff):
    """
    Sub-class Staff yang merepresentasikan Kasir.
    Mewarisi (inheritance) atribut id, username, name, role dari Staff,
    lalu meng-override display_info() dan process_order() (polymorphism)
    agar perilakunya sesuai tugas seorang kasir: menerima pembayaran &
    memverifikasi pesanan masuk.
    """

    __mapper_args__ = {"polymorphic_identity": "cashier"}

    def display_info(self):
        return f"Kasir #{self.id} - {self.name} bertugas memverifikasi & menerima pembayaran pesanan."

    def process_order(self, order):
        order.status = "Menunggu Diproses"
        return f"Kasir {self.name} telah menerima & memverifikasi pesanan #{order.id}."


class KitchenStaff(Staff):
    """
    Sub-class Staff yang merepresentasikan Pegawai Dapur.
    Sama seperti CashierStaff, class ini mewarisi Staff namun meng-override
    method display_info() dan process_order() dengan perilaku yang berbeda,
    sesuai tanggung jawabnya yaitu memasak & menyiapkan pesanan.
    """

    __mapper_args__ = {"polymorphic_identity": "kitchen"}

    def display_info(self):
        return f"Dapur #{self.id} - {self.name} bertugas menyiapkan & memasak pesanan."

    def process_order(self, order):
        order.status = "Sedang Dibuat"
        return f"Pegawai dapur {self.name} sedang menyiapkan pesanan #{order.id}."
