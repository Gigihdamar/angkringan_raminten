from datetime import datetime, timedelta
from database import db

PAYMENT_MENUNGGU = "Menunggu Pembayaran"
PAYMENT_LUNAS = "Lunas"
PAYMENT_KADALUARSA = "Kadaluarsa"


class Payment(db.Model):
    """
    Class induk (parent/base class) untuk seluruh metode pembayaran di
    Angkringan Raminten.

    - Encapsulation : status pembayaran (_status) hanya bisa diubah lewat
      method confirm()/expire(), tidak langsung dari luar class.
    - Inheritance   : QRPayment mewarisi seluruh atribut & method dasar
      Payment (id, method, status, waktu dibuat).
    - Polymorphism  : method process_payment() akan menghasilkan pesan
      berbeda tergantung sub-class yang memanggilnya, sehingga sistem
      pembayaran dapat dikembangkan untuk metode lain (mis. transfer bank,
      tunai) di masa depan tanpa mengubah kode yang memanggilnya.

    Menggunakan SQLAlchemy Single Table Inheritance (kolom 'type').
    """

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"), unique=True, nullable=False)
    method = db.Column(db.String(20), default="Manual")
    _status = db.Column("status", db.String(30), default=PAYMENT_MENUNGGU)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20))

    __mapper_args__ = {
        "polymorphic_identity": "payment",
        "polymorphic_on": type,
    }

    # ---------- Encapsulation: status hanya lewat confirm()/expire() ----------
    @property
    def status(self):
        return self._status

    def confirm(self):
        """Menandai pembayaran ini LUNAS. Dipanggil setelah customer menekan
        'Saya Sudah Membayar' dan mengonfirmasi nominal pada popup."""
        self._status = PAYMENT_LUNAS
        return self._status

    def expire(self):
        self._status = PAYMENT_KADALUARSA
        return self._status

    # ---------- Polymorphism: di-override oleh sub-class ----------
    def process_payment(self):
        return f"Pembayaran #{self.id} sedang diproses dengan metode {self.method}."

    def display_info(self):
        return f"Payment #{self.id} - {self.method} - {self._status}"

    def __repr__(self):
        return f"<Payment {self.method} ({self._status})>"


class QRPayment(Payment):
    """
    Sub-class Payment yang merepresentasikan simulasi pembayaran QRIS.
    Mewarisi (inheritance) atribut & method dasar dari Payment, lalu
    meng-override process_payment() dan display_info() (polymorphism)
    agar berperilaku khusus: menghasilkan data QR simulasi dan memiliki
    batas waktu (countdown 5 menit) sebelum kadaluarsa.
    """

    __mapper_args__ = {"polymorphic_identity": "qris"}

    qr_data = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def generate_qr(self, order):
        """Membuat data QR simulasi (BUKAN payment gateway asli) berisi
        nomor order & nominal tagihan, lalu mengatur waktu kadaluarsa
        5 menit dari sekarang sesuai flow simulasi QRIS pada laporan."""
        self.method = "QRIS"
        self.qr_data = f"QRIS-RAMINTEN|{order.order_number}|Rp{order.total_price:,.0f}"
        self.expires_at = datetime.utcnow() + timedelta(minutes=5)
        self._status = PAYMENT_MENUNGGU
        return self.qr_data

    @property
    def is_expired(self):
        return bool(self.expires_at) and datetime.utcnow() > self.expires_at and self._status != PAYMENT_LUNAS

    def process_payment(self):
        return f"Menunggu customer melakukan scan QRIS untuk data: {self.qr_data}"

    def display_info(self):
        return f"QRPayment #{self.id} - QRIS - {self._status} (kadaluarsa {self.expires_at})"

    def __repr__(self):
        return f"<QRPayment ({self._status})>"
