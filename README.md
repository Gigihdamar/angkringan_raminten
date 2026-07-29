# 🏮 Angkringan Raminten — Sistem Pemesanan Digital

Project UAS Pemrograman Berorientasi Object (Python) — dibangun dengan **Flask**,
**SQLite**, dan **SQLAlchemy ORM**, menerapkan konsep OOP secara nyata: Class,
Object, Encapsulation, Inheritance, dan Polymorphism.

Satu project ini menggabungkan dua role dalam satu website:

- **Pelanggan** — memesan langsung tanpa login: pilih menu → keranjang →
  checkout → ringkasan pesanan → pilih metode pembayaran → simulasi QRIS →
  struk pembayaran → status pesanan real-time → riwayat pesanan.
- **Pegawai (Kasir & Dapur)** — login untuk mengelola pesanan (yang sudah
  **Lunas** saja), menu, dan laporan.

Kedua role terhubung lewat satu database SQLite yang sama, dan halaman status
pelanggan maupun dashboard pegawai **auto-refresh setiap 5 detik**.

---

## 🚀 Cara Menjalankan

```bash
pip install -r requirements.txt
python app.py
```

Lalu buka `http://127.0.0.1:5000` di browser.

- Halaman pelanggan: `http://127.0.0.1:5000/`
- Login pegawai: `http://127.0.0.1:5000/login`

Akun demo yang otomatis dibuat saat pertama kali dijalankan:

| Role   | Username | Password  |
|--------|----------|-----------|
| Kasir  | admin    | admin123  |
| Dapur  | dapur    | dapur123  |

Database (`database.db`) beserta beberapa menu contoh & 10 meja akan dibuat
otomatis saat pertama kali `app.py` dijalankan.

---

## 📁 Struktur Project

```text
angkringan_raminten/
├── app.py                 # Entry point, factory app, seed data awal
├── config.py               # Konfigurasi (SECRET_KEY, path database, dll)
├── database.py              # Instance SQLAlchemy tunggal (db)
├── requirements.txt
│
├── models/                 # Seluruh class OOP
│   ├── staff.py             # Staff, CashierStaff, KitchenStaff
│   ├── menu.py               # MenuItem
│   ├── order.py               # Order, OrderItem (status pesanan & pembayaran terpisah)
│   ├── transaction.py          # Transaction
│   ├── payment.py               # Payment, QRPayment (simulasi QRIS)
│   ├── receipt.py                # Receipt (bentuk & cetak struk PDF)
│   └── table.py                   # Table
│
├── routes/                 # Blueprint (Controller/Route layer - pola MVC)
│   ├── auth.py               # Login/logout pegawai
│   ├── customer.py            # Semua route pelanggan (home, menu, cart,
│   │                            checkout, pembayaran QRIS, struk, riwayat, status)
│   └── admin.py                # Semua route pegawai (dashboard, pesanan, menu, laporan)
│
├── templates/
│   ├── customer/              # home, menu, cart, order_summary, payment_method,
│   │                            qris, receipt, riwayat, status, about
│   └── admin/                  # login, dashboard, orders, order_detail, menu, report
│
├── static/
│   ├── css/style.css           # Tema angkringan (cream, coklat, orange)
│   └── js/main.js
│
└── database.db              # Dibuat otomatis saat pertama kali dijalankan
```

---

## 🧩 Penerapan Konsep OOP

### 1. Class & Object
Setiap entitas dunia nyata (pegawai, menu, pesanan, transaksi, pembayaran,
meja) direpresentasikan sebagai class tersendiri di folder `models/`, dan
setiap baris data di database adalah **object** dari class tersebut.

### 2. Encapsulation
- `Staff._password_hash` — password tidak pernah disimpan/dibaca sebagai teks
  polos; hanya bisa diubah lewat `set_password()` dan diverifikasi lewat
  `check_password()`.
- `MenuItem._price` — hanya bisa diakses lewat `property price`, dengan
  validasi agar harga tidak boleh negatif.
- `Order._status` (status pesanan) dan `Order._payment_status` (status
  pembayaran) adalah **dua field terpisah**, masing-masing hanya bisa diubah
  lewat property/method miliknya sendiri (`status`, `payment_status`,
  `mark_paid()`) agar tidak pernah tercampur menjadi satu field.
- `Transaction._total` — hanya diisi lewat method `calculate_total()`.
- `Payment._status` — hanya bisa diubah lewat method `confirm()` / `expire()`.

### 3. Inheritance
- `CashierStaff` dan `KitchenStaff` (di `models/staff.py`) merupakan
  sub-class dari `Staff`.
- `QRPayment` (di `models/payment.py`) merupakan sub-class dari `Payment`,
  mewarisi atribut & method dasar (id, method, status) sekaligus menambahkan
  perilaku khusus untuk simulasi QRIS (QR data & countdown kadaluarsa).

### 4. Polymorphism
- `Staff.process_order()` di-override berbeda oleh `CashierStaff` &
  `KitchenStaff` — dipanggil dari route yang sama
  (`/admin/orders/<id>/process`) tanpa perlu tahu jenis staff-nya.
- `Payment.process_payment()` di-override oleh `QRPayment`, sehingga sistem
  pembayaran bisa dikembangkan untuk metode lain (mis. transfer bank, tunai)
  di masa depan tanpa mengubah kode yang memanggilnya.
- `display_info()` pada `MenuItem`, `Order`, `Transaction`, `Payment`, dsb.
  masing-masing menghasilkan format output berbeda meski nama method sama.

---

## 🔄 Alur Pemesanan & Pembayaran (Simulasi QRIS)

1. **Checkout** — pelanggan mengisi nomor meja → sistem membuat `Order`,
   `OrderItem`, dan `Transaction` dengan `payment_status = "Belum Dibayar"`.
   Order ini **belum tampil** di dashboard pegawai.
2. **Ringkasan Pesanan** — menampilkan daftar item & total sebelum lanjut.
3. **Pilih Metode Pembayaran** — saat ini hanya QRIS yang aktif (opsi lain
   ditampilkan non-aktif sebagai contoh ekstensibilitas polymorphism).
4. **Simulasi QRIS** — sistem membuat object `QRPayment`, menampilkan QR Code
   simulasi (BUKAN payment gateway asli) beserta countdown 5 menit.
5. Pelanggan menekan **"Saya Sudah Membayar"** → muncul popup konfirmasi
   nominal → jika disetujui, `payment_status` diubah menjadi **Lunas**,
   `Order.status` diset ke `"Menunggu Diproses"`, dan **baru pada titik ini**
   pesanan otomatis muncul di dashboard/halaman Kelola Pesanan pegawai.
6. **Struk Pembayaran** — halaman "Pembayaran Berhasil" menampilkan detail
   struk lengkap dengan tombol **Download PDF** (dibuat oleh class `Receipt`)
   dan **Kembali ke Home**.
7. **Riwayat Pesanan** — pelanggan dapat melihat semua pesanan yang pernah
   dibuat di perangkatnya, lengkap dengan status pembayaran, status pesanan,
   dan tombol download struk.

Dashboard & halaman **Kelola Pesanan** pegawai membaca tabel yang sama dan
auto-refresh setiap 5 detik, begitu pula halaman **Status Pesanan**
pelanggan (lewat endpoint `/api/order/<id>/status`) sehingga perubahan
status pesanan langsung terlihat di device lain tanpa reload manual.

---

## 🎨 Desain UI

Tema visual mengikuti nuansa angkringan tradisional: warna **cream**,
**coklat**, dan **orange**, tipografi serif hangat (Fraunces) untuk judul dan
Plus Jakarta Sans untuk teks, dibangun di atas Bootstrap 5 + Bootstrap Icons,
responsif dari mobile hingga desktop.
