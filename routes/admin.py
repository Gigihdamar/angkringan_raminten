import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, jsonify, current_app, session)

from database import db
from models import (MenuItem, Order, OrderItem, Transaction, Staff, CashierStaff, KitchenStaff,
                     STATUS_FLOW, PAYMENT_BELUM_DIBAYAR, PAYMENT_LUNAS)
from routes.auth import login_required

admin_bp = Blueprint("admin", __name__)


def _current_staff():
    staff_id = session.get("staff_id")
    return Staff.query.get(staff_id) if staff_id else None


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


# ---------------------------------------------------------------- DASHBOARD
@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("admin/dashboard.html", staff=_current_staff())


@admin_bp.route("/api/search")
@login_required
def api_search():
    """Pencarian global untuk kotak cari di topbar admin: mencocokkan
    pesanan (nomor/nama pelanggan/meja), menu, dan halaman panel."""
    q = (request.args.get("q") or "").strip()
    result = {"orders": [], "menu": [], "pages": []}
    if not q:
        return jsonify(result)

    order_matches = (Order.query
                      .filter(db.or_(
                          Order.order_number.ilike(f"%{q}%"),
                          Order.customer_name.ilike(f"%{q}%"),
                      ))
                      .order_by(Order.created_at.desc())
                      .limit(6).all())
    if not order_matches and q.isdigit():
        order_matches = (Order.query
                          .filter(Order.table_number == int(q))
                          .order_by(Order.created_at.desc())
                          .limit(6).all())
    for o in order_matches:
        result["orders"].append({
            "title": o.order_number or f"Order #{o.id}",
            "desc": f"Meja {o.table_number} \u00b7 {o.customer_name} \u00b7 {o.status}",
            "icon": "bi-receipt",
            "url": url_for("admin.order_detail", order_id=o.id),
        })

    menu_matches = (MenuItem.query
                     .filter(MenuItem.name.ilike(f"%{q}%"))
                     .order_by(MenuItem.name)
                     .limit(6).all())
    for m in menu_matches:
        result["menu"].append({
            "title": m.name,
            "desc": f"{m.category} \u00b7 Rp{int(m.price):,}".replace(",", "."),
            "image": m.image,
            "url": url_for("admin.menu_list") + f"#menu-{m.id}",
        })

    panel_pages = [
        {"title": "Dashboard", "desc": "Ringkasan pesanan & pendapatan hari ini",
         "icon": "bi-grid-1x2", "url": url_for("admin.dashboard"),
         "keywords": "dashboard beranda ringkasan overview"},
        {"title": "Kelola Pesanan", "desc": "Lihat & proses semua pesanan masuk",
         "icon": "bi-receipt", "url": url_for("admin.orders"),
         "keywords": "kelola pesanan orders pending menunggu selesai"},
        {"title": "Kelola Menu", "desc": "Tambah, ubah, atau nonaktifkan menu",
         "icon": "bi-egg-fried", "url": url_for("admin.menu_list"),
         "keywords": "kelola menu makanan minuman cemilan stok harga tambah"},
        {"title": "Laporan", "desc": "Laporan penjualan & pendapatan",
         "icon": "bi-bar-chart", "url": url_for("admin.report"),
         "keywords": "laporan report penjualan pendapatan grafik"},
    ]
    q_lower = q.lower()
    for p in panel_pages:
        haystack = f"{p['title']} {p['desc']} {p['keywords']}".lower()
        if q_lower in haystack:
            result["pages"].append({
                "title": p["title"], "desc": p["desc"],
                "icon": p["icon"], "url": p["url"],
            })

    return jsonify(result)


@admin_bp.route("/api/stats")
@login_required
def api_stats():
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(db.func.date(Order.created_at) == today).all()
    paid_today_orders = [o for o in today_orders if o.payment_status == PAYMENT_LUNAS]

    counts = {status: 0 for status in STATUS_FLOW}
    for order in paid_today_orders:
        counts[order.status] = counts.get(order.status, 0) + 1

    belum_dibayar = len([o for o in today_orders if o.payment_status == PAYMENT_BELUM_DIBAYAR])
    lunas = len(paid_today_orders)
    pesanan_baru = counts.get(STATUS_FLOW[0], 0)

    revenue_today = sum(
        t.total for t in Transaction.query.join(Order)
        .filter(db.func.date(Order.created_at) == today, Order._payment_status == PAYMENT_LUNAS)
        .all()
    )

    best_seller_row = (
        db.session.query(
            OrderItem.menu_item_id,
            db.func.sum(OrderItem.quantity).label("total_qty"),
        )
        .join(Order)
        .filter(db.func.date(Order.created_at) == today, Order._payment_status == PAYMENT_LUNAS)
        .group_by(OrderItem.menu_item_id)
        .order_by(db.func.sum(OrderItem.quantity).desc())
        .first()
    )
    menu_terlaris = None
    if best_seller_row:
        item = MenuItem.query.get(best_seller_row[0])
        if item:
            menu_terlaris = {"name": item.name, "qty": int(best_seller_row[1])}

    return jsonify({
        "total_orders_today": len(today_orders),
        "total_menu": MenuItem.query.count(),
        "pesanan_baru": pesanan_baru,
        "belum_dibayar": belum_dibayar,
        "lunas": lunas,
        "counts": counts,
        "revenue_today": revenue_today,
        "menu_terlaris": menu_terlaris,
    })


# ---------------------------------------------------------------- ORDERS
@admin_bp.route("/orders")
@login_required
def orders():
    """
    Menampilkan semua pesanan yang dibuat pengunjung (bebas berapapun jumlahnya,
    baik yang sudah lunas maupun belum dibayar), agar admin dapat mengelola semuanya.
    """
    status_filter = request.args.get("status", "Semua")
    query = Order.query.order_by(Order.created_at.desc())
    if status_filter != "Semua":
        query = query.filter_by(_status=status_filter)
    order_list = query.all()
    return render_template("admin/orders.html", orders=order_list, status_filter=status_filter,
                            status_flow=STATUS_FLOW)


@admin_bp.route("/api/orders")
@login_required
def api_orders():
    order_list = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in order_list])


@admin_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order, status_flow=STATUS_FLOW)


@admin_bp.route("/orders/<int:order_id>/process", methods=["POST"])
@login_required
def order_process(order_id):
    """
    Staff yang sedang login dapat memproses pesanan apapun secara bebas (Cashier/Kitchen polymorphism).
    """
    order = Order.query.get_or_404(order_id)
    staff = _current_staff()
    if staff:
        message = staff.process_order(order)
        db.session.commit()
        flash(message, "success")
    return redirect(url_for("admin.order_detail", order_id=order.id))


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def order_update_status(order_id):
    """
    Admin/staff bebas mengubah status pesanan ke tahap manapun tanpa dibatasi.
    """
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")

    if new_status in STATUS_FLOW or new_status:
        try:
            order.status = new_status
            db.session.commit()
            flash(f"Status pesanan #{order.id} diubah menjadi '{new_status}'.", "success")
        except Exception:
            db.session.rollback()
            flash("Gagal mengubah status.", "danger")
    return redirect(request.referrer or url_for("admin.orders"))


@admin_bp.route("/orders/<int:order_id>/payment_status", methods=["POST"])
@login_required
def order_toggle_payment(order_id):
    """
    Admin bebas mengubah status pembayaran pesanan (Lunas / Belum Dibayar).
    """
    order = Order.query.get_or_404(order_id)
    target_status = request.form.get("payment_status")
    if target_status in [PAYMENT_LUNAS, PAYMENT_BELUM_DIBAYAR]:
        if target_status == PAYMENT_LUNAS:
            order.mark_paid(method=order.payment_method or "Tunai/Kasir")
            if order.transaction:
                order.transaction.mark_paid()
        else:
            order._payment_status = PAYMENT_BELUM_DIBAYAR
        db.session.commit()
        flash(f"Status pembayaran pesanan #{order.id} diubah menjadi '{target_status}'.", "success")
    return redirect(request.referrer or url_for("admin.order_detail", order_id=order.id))


@admin_bp.route("/orders/<int:order_id>/delete", methods=["POST"])
@login_required
def order_delete(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash("Pesanan dihapus.", "info")
    return redirect(url_for("admin.orders"))


# ---------------------------------------------------------------- MENU CRUD
@admin_bp.route("/menu")
@login_required
def menu_list():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    return render_template("admin/menu.html", items=items)


@admin_bp.route("/menu/add", methods=["POST"])
@login_required
def menu_add():
    name = request.form.get("name", "").strip()
    price = float(request.form.get("price", 0))
    category = request.form.get("category")
    description = request.form.get("description", "").strip()

    item = MenuItem(name=name, category=category, description=description)
    item.price = price  # lewat setter (validasi encapsulation)

    file = request.files.get("image")
    if file and file.filename and _allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
        item.image = f"menu/{filename}"

    db.session.add(item)
    db.session.commit()
    flash(f"Menu '{item.name}' berhasil ditambahkan.", "success")
    return redirect(url_for("admin.menu_list"))


@admin_bp.route("/menu/<int:item_id>/edit", methods=["POST"])
@login_required
def menu_edit(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.name = request.form.get("name", item.name).strip()
    item.price = float(request.form.get("price", item.price))
    item.category = request.form.get("category", item.category)
    item.description = request.form.get("description", item.description).strip()
    item.is_available = bool(request.form.get("is_available"))

    file = request.files.get("image")
    if file and file.filename and _allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
        item.image = f"menu/{filename}"

    db.session.commit()
    flash(f"Menu '{item.name}' berhasil diperbarui.", "success")
    return redirect(url_for("admin.menu_list"))


@admin_bp.route("/menu/<int:item_id>/delete", methods=["POST"])
@login_required
def menu_delete(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(f"Menu '{item.name}' dihapus.", "info")
    return redirect(url_for("admin.menu_list"))


# ---------------------------------------------------------------- REPORT
@admin_bp.route("/report")
@login_required
def report():
    period = request.args.get("period", "harian")
    now = datetime.utcnow()

    if period == "mingguan":
        start = now - timedelta(days=7)
    elif period == "bulanan":
        start = now - timedelta(days=30)
    else:
        start = datetime(now.year, now.month, now.day)

    transactions = (
        Transaction.query.join(Order)
        .filter(Order.created_at >= start, Order._payment_status == PAYMENT_LUNAS)
        .all()
    )
    total_transaksi = len(transactions)
    total_pendapatan = sum(t.total for t in transactions)

    best_seller_rows = (
        db.session.query(
            OrderItem.menu_item_id,
            db.func.sum(OrderItem.quantity).label("total_qty"),
        )
        .join(Order)
        .filter(Order.created_at >= start, Order._payment_status == PAYMENT_LUNAS)
        .group_by(OrderItem.menu_item_id)
        .order_by(db.func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    best_sellers = [
        (MenuItem.query.get(menu_id), qty) for menu_id, qty in best_seller_rows
    ]

    return render_template(
        "admin/report.html",
        period=period,
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
        best_sellers=best_sellers,
    )
