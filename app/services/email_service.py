"""Reusable email service with branded templates."""

from __future__ import annotations

import logging

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send(subject: str, recipients: list[str], template: str, **context) -> bool:
        if not recipients:
            return False
        try:
            html = render_template(template, **context)
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=html,
                sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            )
            mail.send(msg)
            return True
        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to send email '%s' to %s recipient(s)",
                subject,
                len([r for r in recipients if r]),
            )
            return False

    @classmethod
    def booking_received(cls, booking) -> bool:
        return cls.send(
            subject=f"Booking Received — {booking.reference}",
            recipients=[booking.customer.email],
            template="emails/booking_received.html",
            booking=booking,
        )

    @classmethod
    def invoice_sent(cls, invoice) -> bool:
        return cls.send(
            subject=f"Invoice {invoice.invoice_number} — Allied Tours & Travel",
            recipients=[invoice.customer.email],
            template="emails/invoice_sent.html",
            invoice=invoice,
            booking=invoice.booking,
        )

    @classmethod
    def payment_recorded(cls, payment) -> bool:
        return cls.send(
            subject=f"Payment Recorded — {payment.booking.reference}",
            recipients=[payment.booking.customer.email],
            template="emails/payment_recorded.html",
            payment=payment,
            booking=payment.booking,
            invoice=payment.invoice,
        )

    @classmethod
    def booking_confirmed(cls, booking) -> bool:
        return cls.send(
            subject=f"Booking Confirmed — {booking.reference}",
            recipients=[booking.customer.email],
            template="emails/booking_confirmed.html",
            booking=booking,
        )

    @classmethod
    def booking_cancelled(cls, booking) -> bool:
        return cls.send(
            subject=f"Booking Cancelled — {booking.reference}",
            recipients=[booking.customer.email],
            template="emails/booking_cancelled.html",
            booking=booking,
        )

    @classmethod
    def upcoming_reminder(cls, booking) -> bool:
        return cls.send(
            subject=f"Upcoming Tour Reminder — {booking.reference}",
            recipients=[booking.customer.email],
            template="emails/upcoming_reminder.html",
            booking=booking,
        )
