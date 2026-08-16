"""Payment recording abstraction — manual now, gateway-ready later."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Booking, Invoice, Payment
from app.services.email_service import EmailService
from app.utils.audit import log_action


class PaymentError(Exception):
    pass


class PaymentService:
    """
    Abstraction for payment operations.

    Current provider: manual admin recording.
    Future providers (M-Pesa, Paystack, Stripe) can plug into
    `provider` / `provider_payment_id` without schema redesign.
    """

    METHODS = ("M-Pesa", "Bank Transfer", "Cash", "Card", "Other")

    @classmethod
    def record_payment(
        cls,
        invoice: Invoice,
        *,
        amount: Decimal,
        method: str,
        payment_date: date,
        transaction_reference: str | None = None,
        notes: str | None = None,
        admin_id: int | None = None,
        provider: str = "manual",
        provider_payment_id: str | None = None,
        auto_verify: bool = False,
    ) -> Payment:
        if amount <= 0:
            raise PaymentError("Payment amount must be greater than zero.")
        if method not in cls.METHODS:
            raise PaymentError("Invalid payment method.")
        if invoice.status == "VOID":
            raise PaymentError("Cannot record payment against a void invoice.")

        payment = Payment(
            invoice_id=invoice.id,
            booking_id=invoice.booking_id,
            amount=amount,
            currency=invoice.currency,
            method=method,
            transaction_reference=transaction_reference,
            payment_date=payment_date,
            status="VERIFIED" if auto_verify else "RECORDED",
            provider=provider,
            provider_payment_id=provider_payment_id,
            notes=notes,
            recorded_by_id=admin_id,
        )
        if auto_verify:
            from app.models.mixins import utcnow

            payment.verified_by_id = admin_id
            payment.verified_at = utcnow()

        db.session.add(payment)
        db.session.flush()
        cls._sync_invoice_and_booking(invoice)
        db.session.commit()
        EmailService.payment_recorded(payment)
        log_action("payment.recorded", "payment", payment.id, f"{amount} via {method}")
        return payment

    @classmethod
    def verify_payment(cls, payment: Payment, admin_id: int | None = None) -> Payment:
        if payment.status == "REFUNDED":
            raise PaymentError("Cannot verify a refunded payment.")
        from app.models.mixins import utcnow

        payment.status = "VERIFIED"
        payment.verified_by_id = admin_id
        payment.verified_at = utcnow()
        cls._sync_invoice_and_booking(payment.invoice)
        db.session.commit()
        log_action("payment.verified", "payment", payment.id)
        return payment

    @classmethod
    def refund_payment(cls, payment: Payment, admin_id: int | None = None) -> Payment:
        if payment.status == "REFUNDED":
            raise PaymentError("Payment already refunded.")
        from app.models.mixins import utcnow

        payment.status = "REFUNDED"
        payment.refunded_at = utcnow()
        cls._sync_invoice_and_booking(payment.invoice)
        booking = payment.booking
        if booking.payment_status != "UNPAID":
            # leave booking status unless fully unpaid after refund sync
            pass
        db.session.commit()
        log_action("payment.refunded", "payment", payment.id, admin_id and str(admin_id))
        return payment

    @staticmethod
    def _sync_invoice_and_booking(invoice: Invoice) -> None:
        invoice.sync_payment_totals()
        booking: Booking = invoice.booking
        if invoice.amount_paid <= 0:
            booking.payment_status = "UNPAID"
        elif invoice.amount_paid < invoice.total:
            booking.payment_status = "PARTIALLY_PAID"
        else:
            booking.payment_status = "PAID"
            if booking.booking_status in ("NEW", "UNDER_REVIEW", "INVOICED"):
                from app.models.mixins import utcnow

                booking.booking_status = "CONFIRMED"
                booking.confirmed_at = utcnow()
                EmailService.booking_confirmed(booking)
