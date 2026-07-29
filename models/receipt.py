import io


class Receipt:
    """
    Class Receipt merepresentasikan struk pembayaran Angkringan Raminten.

    Berbeda dengan Staff/MenuItem/Order/OrderItem/Transaction/Table/Payment,
    Receipt sengaja TIDAK disimpan sebagai tabel database tersendiri karena
    isinya murni turunan (derived) dari data Order & Transaction yang sudah
    ada -- namun tetap merupakan class OOP mandiri dengan atribut dan method
    sendiri (to_dict, generate_pdf) sesuai kebutuhan cetak struk pada
    laporan UAS.
    """

    def __init__(self, order):
        self.order = order
        self.transaction = order.transaction

    @property
    def receipt_number(self):
        return f"STRUK-{self.order.order_number}"

    def to_dict(self):
        order = self.order
        transaction = self.transaction
        return {
            "receipt_number": self.receipt_number,
            "order_number": order.order_number,
            "table_number": order.table_number,
            "customer_name": order.customer_name,
            "date": order.paid_at.strftime("%d-%m-%Y %H:%M:%S") if order.paid_at else "-",
            "items": [item.to_dict() for item in order.items],
            "subtotal": order.total_price,
            "ppn": 0,
            "total": order.total_price,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "transaction_id": transaction.transaction_id if transaction else "-",
        }

    def generate_pdf(self):
        """Menghasilkan struk dalam bentuk file PDF (BytesIO) menggunakan
        reportlab, agar pelanggan bisa menekan tombol 'Download PDF'."""
        from reportlab.lib.pagesizes import A6
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas

        data = self.to_dict()
        buffer = io.BytesIO()
        width, height = A6
        c = canvas.Canvas(buffer, pagesize=A6)

        y = height - 15 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, y, "ANGKRINGAN RAMINTEN")
        y -= 6 * mm
        c.setFont("Helvetica", 8)
        c.drawCentredString(width / 2, y, "PEMBAYARAN BERHASIL")
        y -= 8 * mm

        c.setFont("Helvetica", 8)
        for label, value in [
            ("No. Order", data["order_number"]),
            ("No. Meja", data["table_number"]),
            ("Tanggal", data["date"]),
            ("Metode", data["payment_method"]),
            ("Status", data["payment_status"]),
        ]:
            c.drawString(8 * mm, y, f"{label}")
            c.drawRightString(width - 8 * mm, y, str(value))
            y -= 5 * mm

        y -= 2 * mm
        c.line(8 * mm, y, width - 8 * mm, y)
        y -= 6 * mm

        c.setFont("Helvetica-Bold", 8)
        c.drawString(8 * mm, y, "Menu")
        c.drawRightString(width - 8 * mm, y, "Subtotal")
        y -= 5 * mm
        c.setFont("Helvetica", 8)
        for item in data["items"]:
            line = f"{item['name']} x{item['quantity']}"
            c.drawString(8 * mm, y, line[:34])
            c.drawRightString(width - 8 * mm, y, f"Rp{item['subtotal']:,.0f}")
            y -= 5 * mm

        y -= 2 * mm
        c.line(8 * mm, y, width - 8 * mm, y)
        y -= 6 * mm

        c.setFont("Helvetica", 8)
        c.drawString(8 * mm, y, "Subtotal")
        c.drawRightString(width - 8 * mm, y, f"Rp{data['subtotal']:,.0f}")
        y -= 5 * mm
        c.drawString(8 * mm, y, "PPN")
        c.drawRightString(width - 8 * mm, y, f"Rp{data['ppn']:,.0f}")
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(8 * mm, y, "TOTAL")
        c.drawRightString(width - 8 * mm, y, f"Rp{data['total']:,.0f}")
        y -= 8 * mm

        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(width / 2, y, f"No. Transaksi: {data['transaction_id']}")
        y -= 5 * mm
        c.drawCentredString(width / 2, y, "Terima kasih telah memesan di Angkringan Raminten")

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    def __repr__(self):
        return f"<Receipt {self.receipt_number}>"
