from database import db


class Table(db.Model):
    """
    Class Table merepresentasikan meja pelanggan di Angkringan Raminten.
    Digunakan untuk menyimpan nomor meja yang dipilih pelanggan saat memesan.
    """

    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)

    orders = db.relationship("Order", backref="table", lazy=True)

    def display_info(self):
        status = "Terisi" if self.is_occupied else "Kosong"
        return f"Meja #{self.number} - {status}"

    def __repr__(self):
        return f"<Table {self.number}>"
