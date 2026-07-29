from flask_sqlalchemy import SQLAlchemy

# Instance SQLAlchemy tunggal yang dipakai oleh seluruh model (Staff, MenuItem,
# Order, OrderItem, Transaction, Table) sehingga data pelanggan dan pegawai
# tersimpan pada satu database yang sama (SQLite) dan selalu tersinkronisasi.
db = SQLAlchemy()
