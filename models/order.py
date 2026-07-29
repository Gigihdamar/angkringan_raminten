from datetime import datetime
from database import db

# Urutan status PESANAN (dapur/kasir) yang valid, dipakai untuk validasi
# pada setter status_order. Ini terpisah dari status pembayaran agar tidak
# tercampur menjadi satu field (sesuai requirement laporan UAS).
STATUS_FLOW = [
    "Menunggu Diproses",
    "Sedang Dibuat",
    "Siap Disajikan",
    "Selesai",
]

# Status PEMBAYARAN terpisah dari status pesanan.
PAYMENT_BELUM_DIBAYAR = "Belum Dibayar"
PAYMENT_LUNAS = "Lunas"
PAYMENT_STATUS_FLOW = [PAYMENT_BELUM_DIBAYAR, PAYMENT_LUNAS]


class Order(db.Model):
    """
    Class Order merepresentasikan satu pesanan pelanggan.

    Encapsulation:
    - status pesanan (_status) hanya boleh diubah lewat property 'status'
      yang memvalidasi bahwa nilai baru merupakan salah satu status yang
      sah (STATUS_FLOW).
    - status pembayaran (_payment_status) dipisah dari status pesanan dan
      hanya boleh diubah lewat property 'payment_status' yang tervalidasi
      terhadap PAYMENT_STATUS_FLOW. Sebuah Order baru dianggap 'Belum
      Dibayar' dan TIDAK akan tampil di dashboard pegawai sampai statusnya
      berubah menjadi 'Lunas' (lihat routes/admin.py).
    """

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=True)
    table_number = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), default="Pelanggan")
    customer_phone = db.Column(db.String(30), default="")
    note = db.Column(db.String(255), default="")

    # Status pesanan (dapur/kasir): Menunggu Diproses -> ... -> Selesai
    _status = db.Column("status", db.String(30), default=STATUS_FLOW[0])

    # Status pembayaran: Belum Dibayar -> Lunas (field terpisah, tidak digabung)
    _payment_status = db.Column("payment_status", db.String(20), default=PAYMENT_BELUM_DIBAYAR)
    payment_method = db.Column(db.String(20), default="QRIS")
    paid_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")
    transaction = db.relationship("Transaction", backref="order", uselist=False, cascade="all, delete-orphan")

    # ---------- Encapsulation: getter & setter status pesanan ----------
    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in STATUS_FLOW:
            raise ValueError(f"Status pesanan '{value}' tidak valid.")
        self._status = value
        self.updated_at = datetime.utcnow()

    # ---------- Encapsulation: getter & setter status pembayaran ----------
    @property
    def payment_status(self):
        return self._payment_status

    @payment_status.setter
    def payment_status(self, value):
        if value not in PAYMENT_STATUS_FLOW:
            raise ValueError(f"Status pembayaran '{value}' tidak valid.")
        self._payment_status = value

    @property
    def is_paid(self):
        return self._payment_status == PAYMENT_LUNAS

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items)

    @property
    def status_index(self):
        """Index status pada STATUS_FLOW, dipakai untuk progress bar di UI."""
        return STATUS_FLOW.index(self._status)

    def mark_paid(self, method="QRIS"):
        """Menandai pesanan sebagai lunas & meneruskannya ke antrian dapur."""
        self.payment_status = PAYMENT_LUNAS
        self.payment_method = method
        self.paid_at = datetime.utcnow()
        self.status = STATUS_FLOW[0]

    def generate_order_number(self):
        """Membuat nomor order unik, dipanggil setelah Order memiliki id (flush)."""
        self.order_number = f"ORD-{self.created_at.strftime('%Y%m%d')}-{self.id:04d}"
        return self.order_number

    # ---------- Polymorphism: display_info() versi Order ----------
    def display_info(self):
        return (f"Order #{self.id} - Meja {self.table_number} - "
                f"{len(self.items)} item - Status: {self._status} - Bayar: {self._payment_status}")

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "table_number": self.table_number,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "note": self.note,
            "status": self._status,
            "status_index": self.status_index,
            "payment_status": self._payment_status,
            "payment_method": self.payment_method,
            "total_price": self.total_price,
            "created_at": self.created_at.strftime("%H:%M:%S"),
            "items": [item.to_dict() for item in self.items],
        }

    def __repr__(self):
        return f"<Order #{self.id} - {self._status} - {self._payment_status}>"


class OrderItem(db.Model):
    """
    Class OrderItem merepresentasikan satu baris item menu di dalam sebuah
    Order (relasi many-to-many antara Order dan MenuItem, direalisasikan
    sebagai class tersendiri agar bisa menyimpan jumlah & subtotal).
    """

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price_at_order = db.Column(db.Float, nullable=False)

    @property
    def subtotal(self):
        return self.quantity * self.price_at_order

    def display_info(self):
        return f"{self.menu_item.name} x{self.quantity} = Rp{self.subtotal:,.0f}"

    def to_dict(self):
        return {
            "menu_item_id": self.menu_item_id,
            "name": self.menu_item.name,
            "quantity": self.quantity,
            "price": self.price_at_order,
            "subtotal": self.subtotal,
        }

    def __repr__(self):
        return f"<OrderItem {self.menu_item_id} x{self.quantity}>"
