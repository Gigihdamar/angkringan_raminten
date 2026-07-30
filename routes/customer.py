from flask import (Blueprint, render_template, request, redirect, url_for,
                    session, flash, jsonify, send_file)

from database import db
from models import MenuItem, Order, OrderItem, Transaction, Table, QRPayment, Receipt

customer_bp = Blueprint("customer", __name__)


def _get_cart():
    return session.setdefault("cart", [])


def _add_history(order_id):
    history = session.get("order_history", [])
    if order_id not in history:
        history.append(order_id)
    session["order_history"] = history
    session.modified = True


# ---------------------------------------------------------------- HOME / MENU
@customer_bp.route("/")
def home():
    return render_template("customer/home.html")


@customer_bp.route("/menu")
def menu():
    # Menu ditampilkan terkelompok per kategori dalam satu halaman
    category_order = ["Makanan", "Minuman", "Cemilan"]
    sections = []
    try:
        for cat in category_order:
            items = (MenuItem.query
                     .filter_by(is_available=True, category=cat)
                     .order_by(MenuItem.name)
                     .all())
            if items:
                sections.append({"category": cat, "menu_items": items})

        # Ambil kategori tambahan jika ada yang dibuat via admin
        other_items = (MenuItem.query
                       .filter(MenuItem.is_available.is_(True), MenuItem.category.notin_(category_order))
                       .order_by(MenuItem.name)
                       .all())
        if other_items:
            other_cats = list(dict.fromkeys(i.category for i in other_items))
            for ocat in other_cats:
                cat_items = [i for i in other_items if i.category == ocat]
                sections.append({"category": ocat, "menu_items": cat_items})
    except Exception as e:
        db.session.rollback()

    return render_template("customer/menu.html", sections=sections)


# ---------------------------------------------------------------- PENCARIAN
@customer_bp.route("/api/search")
def api_search():
    """Pencarian global untuk kotak cari di navbar.

    Berbeda dari pencarian menu biasa, endpoint ini juga mencocokkan
    query terhadap halaman/informasi situs (lokasi, jam buka, kontak,
    riwayat pesanan, dst) supaya kotak cari bisa dipakai lebih dari
    sekadar mencari nama menu.
    """
    from config import Config

    q = (request.args.get("q") or "").strip()
    result = {"menu": [], "pages": []}
    if not q:
        return jsonify(result)

    menu_matches = (MenuItem.query
                     .filter(MenuItem.is_available.is_(True), MenuItem.name.ilike(f"%{q}%"))
                     .order_by(MenuItem.name)
                     .limit(6).all())
    for item in menu_matches:
        harga = f"Rp{int(item.price):,}".replace(",", ".")
        result["menu"].append({
            "title": item.name,
            "desc": f"{item.category} \u00b7 {harga}",
            "image": item.image,
            "url": url_for("customer.menu") + f"#cat-{item.category.lower()}",
        })

    site_pages = [
        {"title": "Beranda", "desc": "Halaman utama & sekilas kategori menu",
         "icon": "bi-house", "url": url_for("customer.home"),
         "keywords": "home beranda utama depan"},
        {"title": "Menu", "desc": "Semua makanan, minuman & cemilan",
         "icon": "bi-egg-fried", "url": url_for("customer.menu"),
         "keywords": "menu makanan minuman cemilan harga daftar nasi kucing sate wedang"},
        {"title": "Pesanan Saya", "desc": "Riwayat & lacak status pesanan Anda",
         "icon": "bi-receipt", "url": url_for("customer.riwayat"),
         "keywords": "pesanan saya riwayat status order lacak tracking transaksi"},
        {"title": "Tentang Kami", "desc": "Cerita, lokasi, jam buka & kontak kami",
         "icon": "bi-info-circle", "url": url_for("customer.about"),
         "keywords": ("tentang kami cerita lokasi alamat jam buka operasional kontak "
                      "whatsapp telepon maps peta about " + Config.ADDRESS_TEXT)},
    ]
    q_lower = q.lower()
    for p in site_pages:
        haystack = f"{p['title']} {p['desc']} {p['keywords']}".lower()
        if q_lower in haystack:
            result["pages"].append({
                "title": p["title"], "desc": p["desc"],
                "icon": p["icon"], "url": p["url"],
            })

    return jsonify(result)


# ---------------------------------------------------------------- KERANJANG
@customer_bp.route("/cart/add", methods=["POST"])
def cart_add():
    menu_id = int(request.form.get("menu_id"))
    quantity = max(1, int(request.form.get("quantity", 1)))

    item = MenuItem.query.get_or_404(menu_id)
    cart = _get_cart()

    for row in cart:
        if row["menu_id"] == menu_id:
            row["quantity"] += quantity
            break
    else:
        cart.append({
            "menu_id": menu_id,
            "name": item.name,
            "price": item.price,
            "quantity": quantity,
        })

    session["cart"] = cart
    session.modified = True

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        cart_count = sum(row["quantity"] for row in cart)
        return jsonify({
            "success": True,
            "message": f"{item.name} ditambahkan ke keranjang.",
            "cart_count": cart_count,
        })

    flash(f"{item.name} ditambahkan ke keranjang.", "success")
    return redirect(url_for("customer.menu"))


@customer_bp.route("/cart/fragment")
def cart_fragment():
    """Mengembalikan potongan HTML isi cart drawer terbaru, dipakai JS agar
    keranjang bisa disegarkan tanpa reload halaman penuh."""
    return render_template("customer/_cart_drawer_content.html")


@customer_bp.route("/cart")
def cart():
    cart = _get_cart()
    total = sum(row["price"] * row["quantity"] for row in cart)
    tables = Table.query.order_by(Table.number).all()
    return render_template("customer/cart.html", cart=cart, total=total, tables=tables)


@customer_bp.route("/cart/update", methods=["POST"])
def cart_update():
    menu_id = int(request.form.get("menu_id"))
    quantity = int(request.form.get("quantity", 1))
    cart = _get_cart()

    if quantity <= 0:
        cart = [row for row in cart if row["menu_id"] != menu_id]
    else:
        for row in cart:
            if row["menu_id"] == menu_id:
                row["quantity"] = quantity

    session["cart"] = cart
    session.modified = True
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/remove/<int:menu_id>")
def cart_remove(menu_id):
    cart = [row for row in _get_cart() if row["menu_id"] != menu_id]
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("customer.cart"))


# ---------------------------------------------------------------- CHECKOUT
@customer_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = _get_cart()
    if not cart:
        flash("Keranjang masih kosong, silakan pilih menu terlebih dahulu.", "warning")
        return redirect(url_for("customer.menu"))

    if request.method == "GET":
        last_order_id = session.get("last_order_id")
        if last_order_id:
            return redirect(url_for("customer.order_summary", order_id=last_order_id))
        return redirect(url_for("customer.cart"))

    table_number_raw = request.form.get("table_number", "1").strip()
    try:
        table_number = int(table_number_raw) if table_number_raw else 1
    except ValueError:
        table_number = 1

    customer_name = request.form.get("customer_name", "").strip() or "Pelanggan"
    customer_phone = request.form.get("customer_phone", "").strip()
    note = request.form.get("note", "").strip()

    table = Table.query.filter_by(number=table_number).first()
    if not table:
        table = Table(number=table_number, is_occupied=True)
        db.session.add(table)
        db.session.flush()
    else:
        table.is_occupied = True

    order = Order(
        table_id=table.id,
        table_number=table_number,
        customer_name=customer_name,
        customer_phone=customer_phone,
        note=note,
    )
    db.session.add(order)
    db.session.flush()
    order.generate_order_number()

    for row in cart:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=row["menu_id"],
            quantity=row["quantity"],
            price_at_order=row["price"],
        )
        db.session.add(order_item)

    db.session.flush()

    transaction = Transaction(order_id=order.id, payment_method="QRIS")
    transaction.generate_transaction_id()
    transaction.calculate_total(order)
    db.session.add(transaction)

    db.session.commit()

    session["cart"] = []
    session["last_order_id"] = order.id
    _add_history(order.id)

    return redirect(url_for("customer.order_summary", order_id=order.id))


@customer_bp.route("/checkout/summary/<int:order_id>")
def order_summary(order_id):
    order = Order.query.get_or_404(order_id)
    if order.is_paid:
        return redirect(url_for("customer.receipt", order_id=order.id))
    return render_template("customer/order_summary.html", order=order)


@customer_bp.route("/checkout/payment/<int:order_id>")
def payment_method(order_id):
    order = Order.query.get_or_404(order_id)
    if order.is_paid:
        return redirect(url_for("customer.receipt", order_id=order.id))
    return render_template("customer/payment_method.html", order=order)


@customer_bp.route("/checkout/payment/<int:order_id>/qris", methods=["GET", "POST"])
def payment_select_qris(order_id):
    order = Order.query.get_or_404(order_id)
    if order.is_paid:
        return redirect(url_for("customer.receipt", order_id=order.id))

    transaction = order.transaction
    if not transaction:
        transaction = Transaction(order_id=order.id, payment_method="QRIS")
        transaction.generate_transaction_id()
        transaction.calculate_total(order)
        db.session.add(transaction)
        db.session.flush()

    payment = transaction.payment
    if not payment or not isinstance(payment, QRPayment):
        payment = QRPayment(transaction_id=transaction.id)
        db.session.add(payment)

    payment.generate_qr(order)
    db.session.commit()

    return redirect(url_for("customer.qris_page", order_id=order.id))


@customer_bp.route("/checkout/qris/<int:order_id>")
def qris_page(order_id):
    order = Order.query.get_or_404(order_id)
    if order.is_paid:
        return redirect(url_for("customer.receipt", order_id=order.id))

    transaction = order.transaction
    if not transaction:
        transaction = Transaction(order_id=order.id, payment_method="QRIS")
        transaction.generate_transaction_id()
        transaction.calculate_total(order)
        db.session.add(transaction)
        db.session.flush()

    payment = transaction.payment
    if not payment or not isinstance(payment, QRPayment):
        payment = QRPayment(transaction_id=transaction.id)
        db.session.add(payment)

    if not payment.qr_data or payment.is_expired:
        payment.generate_qr(order)
        db.session.commit()

    return render_template("customer/qris.html", order=order, transaction=transaction, payment=payment)


@customer_bp.route("/checkout/qris/<int:order_id>/confirm", methods=["GET", "POST"])
def payment_confirm(order_id):
    order = Order.query.get_or_404(order_id)
    if order.is_paid:
        return redirect(url_for("customer.receipt", order_id=order.id))

    transaction = order.transaction
    if not transaction:
        transaction = Transaction(order_id=order.id, payment_method="QRIS")
        transaction.generate_transaction_id()
        transaction.calculate_total(order)
        db.session.add(transaction)
        db.session.flush()

    payment = transaction.payment
    if not payment or not isinstance(payment, QRPayment):
        payment = QRPayment(transaction_id=transaction.id)
        db.session.add(payment)
        payment.generate_qr(order)

    payment.confirm()
    transaction.mark_paid()
    order.mark_paid(method="QRIS")
    db.session.commit()

    flash("Pembayaran berhasil! Pesanan Anda telah diteruskan ke dapur.", "success")
    return redirect(url_for("customer.receipt", order_id=order.id))


# ---------------------------------------------------------------- STRUK / RECEIPT
@customer_bp.route("/receipt/<int:order_id>")
def receipt(order_id):
    order = Order.query.get_or_404(order_id)
    if not order.is_paid:
        flash("Pesanan ini belum dibayar.", "warning")
        return redirect(url_for("customer.order_summary", order_id=order.id))
    return render_template("customer/receipt.html", order=order, transaction=order.transaction)


@customer_bp.route("/receipt/<int:order_id>/pdf")
def receipt_pdf(order_id):
    order = Order.query.get_or_404(order_id)
    if not order.is_paid:
        flash("Pesanan ini belum dibayar.", "warning")
        return redirect(url_for("customer.order_summary", order_id=order.id))

    pdf_buffer = Receipt(order).generate_pdf()
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"struk-{order.order_number}.pdf",
    )


# ---------------------------------------------------------------- RIWAYAT PESANAN
@customer_bp.route("/riwayat")
def riwayat():
    history_ids = session.get("order_history", [])
    orders = (
        Order.query.filter(Order.id.in_(history_ids)).order_by(Order.created_at.desc()).all()
        if history_ids else []
    )
    return render_template("customer/riwayat.html", orders=orders)


# ---------------------------------------------------------------- STATUS PESANAN
@customer_bp.route("/status")
@customer_bp.route("/status/<int:order_id>")
def status(order_id=None):
    if order_id is None:
        order_id = session.get("last_order_id")
        if not order_id:
            flash("Belum ada pesanan yang bisa dilacak.", "info")
            return redirect(url_for("customer.menu"))
    order = Order.query.get_or_404(order_id)
    return render_template("customer/status.html", order=order)


@customer_bp.route("/api/order/<int:order_id>/status")
def api_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())


@customer_bp.route("/about")
def about():
    return render_template("customer/about.html")
