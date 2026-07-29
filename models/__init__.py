"""
Package models berisi seluruh class OOP aplikasi Angkringan Raminten:
Staff (+ CashierStaff, KitchenStaff), MenuItem, Order, OrderItem,
Transaction, Table, Payment (+ QRPayment), dan Receipt. Setiap class
dipisah ke file-nya masing-masing agar struktur project rapi dan mudah
dipelajari.
"""

from .staff import Staff, CashierStaff, KitchenStaff
from .menu import MenuItem
from .order import Order, OrderItem, STATUS_FLOW, PAYMENT_STATUS_FLOW, PAYMENT_BELUM_DIBAYAR, PAYMENT_LUNAS
from .transaction import Transaction
from .table import Table
from .payment import Payment, QRPayment
from .receipt import Receipt

__all__ = [
    "Staff",
    "CashierStaff",
    "KitchenStaff",
    "MenuItem",
    "Order",
    "OrderItem",
    "STATUS_FLOW",
    "PAYMENT_STATUS_FLOW",
    "PAYMENT_BELUM_DIBAYAR",
    "PAYMENT_LUNAS",
    "Transaction",
    "Table",
    "Payment",
    "QRPayment",
    "Receipt",
]
