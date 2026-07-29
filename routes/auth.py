from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from database import db
from models import Staff

auth_bp = Blueprint("auth", __name__)


def login_required(view_func):
    """Decorator sederhana untuk melindungi halaman/route khusus pegawai."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("staff_id"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapped


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        staff = Staff.query.filter_by(username=username).first()

        if staff and staff.check_password(password):
            session["staff_id"] = staff.id
            session["staff_name"] = staff.name
            session["staff_type"] = staff.type
            flash(f"Selamat datang kembali, {staff.name}!", "success")
            return redirect(url_for("admin.dashboard"))

        flash("Username atau password salah.", "danger")

    return render_template("admin/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("customer.home"))
