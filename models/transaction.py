from datetime import datetime
from database import db
from models.order import PAYMENT_STATUS_FLOW, PAYMENT_BELUM_DIBAYAR, PAYMENT_LUNAS


class Transaction(db.Model):
    """
    Class Transaction merepresentasikan transaksi pembayaran atas sebuah Order.

    Encapsulation:
    - total transaksi (_total) hanya bisa diisi lewat method
      calculate_total() agar nilainya selalu berasal dari perhitungan order,
      bukan dimasukkan sembarangan dari luar class.
    - payment_status (_payment_status) hanya bisa diubah lewat method
      mark_paid(), sehingga status pembayaran transaksi selalu konsisten
      dengan alur simulasi QRIS (Belum Dibayar -> Lunas).

    Relasi: satu Transaction memiliki satu Payment (lihat models/payment.py).
    Payment/QRPayment dipisah dari Transaction agar metode pembayaran baru
    (selain QRIS) dapat ditambahkan di masa depan tanpa mengubah struktur
    Transaction (polymorphism).
    """

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(40), unique=True, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    _total = db.Column("amount", db.Float, default=0)
    payment_method = db.Column(db.String(20), default="QRIS")
    _payment_status = db.Column("payment_status", db.String(20), default=PAYMENT_BELUM_DIBAYAR)
    payment_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payment = db.relationship("Payment", backref="transaction", uselist=False, cascade="all, delete-orphan")

    # ---------- Encapsulation: total hanya lewat calculate_total() ----------
    @property
    def total(self):
        return self._total

    def calculate_total(self, order):
        """Menghitung ulang total transaksi berdasarkan item-item pada order."""
        self._total = order.total_price
        return self._total

    # ---------- Encapsulation: payment_status hanya lewat mark_paid() ----------
    @property
    def payment_status(self):
        return self._payment_status

    def mark_paid(self):
        if self._payment_status not in PAYMENT_STATUS_FLOW:
            self._payment_status = PAYMENT_BELUM_DIBAYAR
        self._payment_status = PAYMENT_LUNAS
        self.payment_time = datetime.utcnow()

    def generate_transaction_id(self):
        self.transaction_id = f"TRX-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{self.order_id:04d}"
        return self.transaction_id

    # ---------- Polymorphism: display_info() versi Transaction ----------
    def display_info(self):
        return (f"Transaksi #{self.id} untuk Order #{self.order_id} - "
                f"Total: Rp{self._total:,.0f} ({self.payment_method}) - {self._payment_status}")

    def __repr__(self):
        return f"<Transaction #{self.id} Rp{self._total:,.0f}>"
