from database import db


class MenuItem(db.Model):
    """
    Class MenuItem merepresentasikan satu menu Angkringan Raminten
    (makanan, minuman, atau cemilan).

    Encapsulation: harga (_price) disimpan sebagai atribut privat dan hanya
    bisa dibaca/diubah lewat property 'price' agar nilai harga selalu tervalidasi
    (tidak boleh negatif) dan tidak bisa diubah sembarangan dari luar class.
    """

    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    _price = db.Column("price", db.Float, nullable=False)
    category = db.Column(db.String(20), nullable=False)  # Makanan / Minuman / Cemilan
    description = db.Column(db.String(255), default="")
    image = db.Column(db.String(255), default="default-menu.jpg")
    is_available = db.Column(db.Boolean, default=True)

    order_items = db.relationship("OrderItem", backref="menu_item", lazy=True)

    # ---------- Encapsulation: getter & setter untuk harga ----------
    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value is None or value < 0:
            raise ValueError("Harga menu tidak boleh negatif.")
        self._price = value

    # ---------- Polymorphism: display_info() punya bentuk sendiri di sini ----------
    def display_info(self):
        return f"{self.name} ({self.category}) - Rp{self._price:,.0f}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self._price,
            "category": self.category,
            "description": self.description,
            "image": self.image,
            "is_available": self.is_available,
        }

    def __repr__(self):
        return f"<MenuItem {self.name}>"
