"""Invoice generation, PDF export, and status sync."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import secrets

from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.extensions import db
from app.models import Booking, Invoice, InvoiceItem
from app.services.email_service import EmailService
from app.utils.audit import log_action


class InvoiceError(Exception):
    pass


class InvoiceService:
    @staticmethod
    def generate_number() -> str:
        from datetime import datetime, timezone

        year = datetime.now(timezone.utc).year
        prefix = f"INV-{year}-"
        last = (
            Invoice.query.filter(Invoice.invoice_number.like(f"{prefix}%"))
            .order_by(Invoice.id.desc())
            .first()
        )
        if last:
            try:
                seq = int(last.invoice_number.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"

    @classmethod
    def create_from_booking(
        cls,
        booking: Booking,
        *,
        discount: Decimal = Decimal("0"),
        due_days: int = 7,
        payment_instructions: str | None = None,
        terms: str | None = None,
        admin_id: int | None = None,
    ) -> Invoice:
        if booking.booking_status == "CANCELLED":
            raise InvoiceError("Cannot invoice a cancelled booking.")

        items = []
        if booking.is_service_booking:
            service_name = booking.display_title
            travelers = booking.total_travelers or 1
            items.append(
                {
                    "description": (
                        f"{service_name} — service request"
                        f"{f' × {travelers} traveler(s)' if travelers else ''}"
                    ),
                    "quantity": travelers,
                    "unit_price": Decimal("0"),
                    "sort_order": 1,
                }
            )
            terms_default = (
                "This invoice is for a service request. Final fees will be confirmed by Allied Tours & Travel. "
                "Payment confirms your service arrangement."
            )
        else:
            departure = booking.departure
            if not departure:
                raise InvoiceError("Tour booking is missing departure details.")
            adult_price = departure.price_adult
            child_price = (
                departure.price_child if departure.price_child is not None else adult_price
            )
            if booking.adults:
                items.append(
                    {
                        "description": f"{booking.display_title} — Adult × {booking.adults}",
                        "quantity": booking.adults,
                        "unit_price": adult_price,
                        "sort_order": 1,
                    }
                )
            if booking.children:
                items.append(
                    {
                        "description": f"{booking.display_title} — Child × {booking.children}",
                        "quantity": booking.children,
                        "unit_price": child_price,
                        "sort_order": 2,
                    }
                )
            terms_default = (
                "Payment confirms your place on the tour. Cancellations are subject to company policy."
            )

        invoice = Invoice(
            invoice_number=cls.generate_number(),
            booking_id=booking.id,
            customer_id=booking.customer_id,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=due_days),
            status="DRAFT",
            discount=discount or Decimal("0"),
            currency=booking.currency,
            payment_instructions=payment_instructions
            or current_app.config.get(
                "DEFAULT_PAYMENT_INSTRUCTIONS",
                "Please pay via M-Pesa or bank transfer using the booking reference as narration. "
                "Share your payment confirmation with Allied Tours & Travel.",
            ),
            terms=terms or terms_default,
            created_by_id=admin_id,
        )
        db.session.add(invoice)
        db.session.flush()

        invoice_items = []
        for row in items:
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=row["description"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                sort_order=row["sort_order"],
            )
            item.compute_line_total()
            db.session.add(item)
            invoice_items.append(item)

        db.session.flush()
        invoice.items = invoice_items
        invoice.recalculate_totals()
        booking.booking_status = "INVOICED" if booking.booking_status in ("NEW", "UNDER_REVIEW") else booking.booking_status
        db.session.commit()
        log_action("invoice.generated", "invoice", invoice.id, invoice.invoice_number)
        return invoice

    @classmethod
    def update_invoice(
        cls,
        invoice: Invoice,
        *,
        items: list[dict],
        discount: Decimal | None = None,
        due_date: date | None = None,
        payment_instructions: str | None = None,
        terms: str | None = None,
        notes: str | None = None,
        clear_due_date: bool = False,
    ) -> Invoice:
        """Replace line items and meta fields before payments are recorded.

        Intended for service quotes (and tour adjustments) while status is DRAFT
        or SENT with no amount paid.
        """
        if invoice.status in ("PAID", "VOID", "PARTIALLY_PAID"):
            raise InvoiceError("Paid or void invoices cannot be edited.")
        if (invoice.amount_paid or Decimal("0")) > 0:
            raise InvoiceError("Cannot edit invoice after payments have been recorded.")
        if invoice.status not in ("DRAFT", "SENT", "OVERDUE"):
            raise InvoiceError("This invoice status cannot be edited.")

        cleaned: list[dict] = []
        for raw in items:
            description = (raw.get("description") or "").strip()
            if not description:
                continue
            try:
                quantity = int(raw.get("quantity") or 1)
            except (TypeError, ValueError) as exc:
                raise InvoiceError("Quantity must be a whole number.") from exc
            if quantity < 1:
                raise InvoiceError("Quantity must be at least 1.")
            try:
                unit_price = Decimal(str(raw.get("unit_price") or "0"))
            except Exception as exc:  # noqa: BLE001
                raise InvoiceError("Unit price must be a valid amount.") from exc
            if unit_price < 0:
                raise InvoiceError("Unit price cannot be negative.")
            cleaned.append(
                {
                    "description": description[:300],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "sort_order": len(cleaned) + 1,
                }
            )

        if not cleaned:
            raise InvoiceError("Add at least one invoice line item.")

        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
        db.session.expire(invoice, ["items"])
        for row in cleaned:
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=row["description"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                sort_order=row["sort_order"],
            )
            item.compute_line_total()
            db.session.add(item)

        if discount is not None:
            if discount < 0:
                raise InvoiceError("Discount cannot be negative.")
            invoice.discount = discount
        if clear_due_date:
            invoice.due_date = None
        elif due_date is not None:
            invoice.due_date = due_date
        if payment_instructions is not None:
            invoice.payment_instructions = payment_instructions.strip() or None
        if terms is not None:
            invoice.terms = terms.strip() or None
        if notes is not None:
            invoice.notes = notes.strip() or None

        db.session.flush()
        db.session.refresh(invoice)
        invoice.recalculate_totals()
        # Invalidate cached PDF so next download/send uses updated figures.
        invoice.pdf_path = None
        db.session.commit()
        log_action("invoice.updated", "invoice", invoice.id, invoice.invoice_number)
        return invoice

    @classmethod
    def send_invoice(cls, invoice: Invoice) -> Invoice:
        if invoice.status == "DRAFT" and (invoice.total or Decimal("0")) <= 0:
            raise InvoiceError(
                "Set line-item prices before sending. Service invoices start at zero until you add the quote."
            )
        pdf_path = cls.generate_pdf(invoice)
        invoice.pdf_path = pdf_path
        from app.models.mixins import utcnow

        invoice.sent_at = utcnow()
        if invoice.status == "DRAFT":
            invoice.status = "SENT"
        if invoice.booking.booking_status in ("NEW", "UNDER_REVIEW"):
            invoice.booking.booking_status = "INVOICED"
        db.session.commit()
        EmailService.invoice_sent(invoice)
        log_action("invoice.sent", "invoice", invoice.id, invoice.invoice_number)
        return invoice

    @staticmethod
    def _invoice_storage_dir() -> Path:
        """Private invoice directory (not web-accessible via /static)."""
        root = Path(current_app.instance_path) / "invoices"
        root.mkdir(parents=True, exist_ok=True)
        return root

    @classmethod
    def resolve_pdf_path(cls, invoice: Invoice) -> Path | None:
        """Resolve invoice PDF on disk (private instance path, with legacy static fallback)."""
        if not invoice.pdf_path:
            return None
        rel = invoice.pdf_path.replace("\\", "/").lstrip("/")
        # New layout: invoices/<file>.pdf under instance/
        if rel.startswith("invoices/"):
            candidate = (Path(current_app.instance_path) / rel).resolve()
            try:
                candidate.relative_to(Path(current_app.instance_path).resolve())
            except ValueError:
                return None
            return candidate if candidate.is_file() else None
        # Legacy public static path — still readable by admin, but should be migrated.
        if rel.startswith("uploads/invoices/"):
            candidate = (Path(current_app.root_path) / "static" / rel).resolve()
            upload_root = (Path(current_app.root_path) / "static" / "uploads" / "invoices").resolve()
            try:
                candidate.relative_to(upload_root)
            except ValueError:
                return None
            return candidate if candidate.is_file() else None
        return None

    @staticmethod
    def generate_pdf(invoice: Invoice) -> str:
        from app.utils.sanitize import escape_pdf_text

        storage = InvoiceService._invoice_storage_dir()
        token = secrets.token_hex(8)
        filename = f"{invoice.invoice_number}_{token}.pdf"
        filepath = storage / filename

        company = current_app.config.get("COMPANY_NAME", "Allied Tours & Travel")
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleBrand",
            parent=styles["Heading1"],
            textColor=colors.HexColor("#412919"),
            fontSize=18,
            spaceAfter=6,
        )
        body = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            textColor=colors.HexColor("#29231F"),
            fontSize=10,
            leading=14,
        )
        muted = ParagraphStyle(
            "Muted",
            parent=styles["Normal"],
            textColor=colors.HexColor("#746B63"),
            fontSize=9,
            leading=12,
        )

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
        )
        story = []

        brand_dir = Path(current_app.root_path) / "static" / "assets" / "brand"
        logo_path = next(
            (
                candidate
                for candidate in (
                    brand_dir / "logo-invoice.png",
                    brand_dir / "logo-primary.png",
                    brand_dir / "logo-dark.png",
                )
                if candidate.exists()
            ),
            None,
        )
        if logo_path is not None:
            logo = Image(str(logo_path))
            logo._restrictSize(90 * mm, 28 * mm)
            story.append(logo)
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(escape_pdf_text(company), title_style))

        story.append(
            Paragraph(
                f"{escape_pdf_text(current_app.config.get('COMPANY_OFFICE', ''))}<br/>"
                f"{escape_pdf_text(current_app.config.get('COMPANY_ADDRESS', ''))}<br/>"
                f"{escape_pdf_text(current_app.config.get('COMPANY_EMAIL', ''))} · "
                f"{escape_pdf_text(current_app.config.get('COMPANY_PHONE', ''))}",
                muted,
            )
        )
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Invoice {escape_pdf_text(invoice.invoice_number)}", title_style))
        story.append(
            Paragraph(
                f"Booking Reference: <b>{escape_pdf_text(invoice.booking.reference)}</b><br/>"
                f"Issue Date: {invoice.issue_date.strftime('%d %B %Y')}<br/>"
                f"Due Date: {invoice.due_date.strftime('%d %B %Y') if invoice.due_date else '—'}",
                body,
            )
        )
        story.append(Spacer(1, 10))
        customer = invoice.customer
        story.append(
            Paragraph(
                f"<b>Bill To</b><br/>{escape_pdf_text(customer.full_name if customer else '')}<br/>"
                f"{escape_pdf_text(customer.email if customer else '')}<br/>"
                f"{escape_pdf_text(customer.phone if customer else '')}",
                body,
            )
        )
        story.append(Spacer(1, 12))

        data = [["Description", "Qty", "Unit Price", "Total"]]
        for item in invoice.items:
            data.append(
                [
                    escape_pdf_text(item.description),
                    str(item.quantity),
                    f"{invoice.currency} {item.unit_price:,.2f}",
                    f"{invoice.currency} {item.line_total:,.2f}",
                ]
            )
        data.append(["", "", "Subtotal", f"{invoice.currency} {invoice.subtotal:,.2f}"])
        if invoice.discount:
            data.append(["", "", "Discount", f"- {invoice.currency} {invoice.discount:,.2f}"])
        data.append(["", "", "Total", f"{invoice.currency} {invoice.total:,.2f}"])
        data.append(["", "", "Amount Paid", f"{invoice.currency} {invoice.amount_paid:,.2f}"])
        data.append(["", "", "Balance", f"{invoice.currency} {invoice.balance:,.2f}"])

        table = Table(data, colWidths=[90 * mm, 20 * mm, 35 * mm, 35 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#412919")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -5), 0.25, colors.HexColor("#D6CFC6")),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("BACKGROUND", (2, -3), (-1, -1), colors.HexColor("#FAF8F4")),
                    ("FONTNAME", (2, -3), (-1, -1), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#29231F")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 14))
        if invoice.payment_instructions:
            story.append(Paragraph("<b>Payment Instructions</b>", body))
            story.append(
                Paragraph(
                    escape_pdf_text(invoice.payment_instructions).replace("\n", "<br/>"),
                    body,
                )
            )
        if invoice.terms:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Terms</b>", body))
            story.append(
                Paragraph(escape_pdf_text(invoice.terms).replace("\n", "<br/>"), muted)
            )

        doc.build(story)
        return f"invoices/{filename}"
