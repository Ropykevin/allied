"""Booking creation and capacity management."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import secrets

from flask import current_app
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Booking, Customer, Departure, Service
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.utils.helpers import generate_token


class BookingError(Exception):
    pass


class BookingService:
    @staticmethod
    def generate_reference() -> str:
        """Opaque booking reference — not sequential / enumerable."""
        from datetime import datetime, timezone

        year = datetime.now(timezone.utc).year
        # ATT-2026-A1B2C3D4 style (unguessable)
        return f"ATT-{year}-{secrets.token_hex(4).upper()}"

    @staticmethod
    def confirmation_token(reference: str) -> str:
        from itsdangerous import URLSafeTimedSerializer
        from flask import current_app

        serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"], salt="booking-confirmation"
        )
        return serializer.dumps(reference)

    @staticmethod
    def verify_confirmation_token(reference: str, token: str | None, max_age: int = 60 * 60 * 24 * 14) -> bool:
        if not token:
            return False
        from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
        from flask import current_app

        serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"], salt="booking-confirmation"
        )
        try:
            payload = serializer.loads(token, max_age=max_age)
        except (BadSignature, SignatureExpired):
            return False
        return payload == reference

    @staticmethod
    def _upsert_customer(
        *,
        full_name: str,
        email: str,
        phone: str,
        country: str | None,
    ) -> Customer:
        email_norm = email.lower().strip()
        phone_norm = phone.strip()
        # Prefer exact email match; do not match-or-overwrite via phone alone.
        customer = Customer.query.filter_by(email=email_norm).first()
        if customer:
            # Update display name/country only; keep verified contact identifiers stable.
            customer.full_name = full_name.strip()
            if country:
                customer.country = country
            # Update phone only when blank or already the same number.
            if not customer.phone or customer.phone.strip() == phone_norm:
                customer.phone = phone_norm
        else:
            # If phone exists on another account, still create by email (unique email).
            customer = Customer(
                full_name=full_name.strip(),
                email=email_norm,
                phone=phone_norm,
                country=country,
            )
            db.session.add(customer)
            db.session.flush()
        return customer

    @classmethod
    def create_booking(
        cls,
        *,
        departure_id: int,
        full_name: str,
        email: str,
        phone: str,
        country: str | None,
        adults: int,
        children: int,
        pickup_location: str | None,
        special_requests: str | None,
        submission_token: str | None = None,
    ) -> Booking:
        if adults < 1:
            raise BookingError("At least one adult traveler is required.")
        if children < 0:
            raise BookingError("Invalid number of children.")
        travelers = adults + children
        if travelers < 1:
            raise BookingError("At least one traveler is required.")

        if submission_token:
            existing = Booking.query.filter_by(submission_token=submission_token).first()
            if existing:
                return existing

        try:
            with db.session.begin_nested():
                departure = (
                    db.session.execute(
                        select(Departure)
                        .where(Departure.id == departure_id)
                        .with_for_update()
                    )
                    .scalar_one_or_none()
                )
                if not departure or not departure.is_bookable:
                    raise BookingError("Selected departure is not available.")
                if travelers > departure.available_seats:
                    raise BookingError(
                        f"Only {departure.available_seats} seats remain for this departure."
                    )

                customer = cls._upsert_customer(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    country=country,
                )

                adult_price = departure.price_adult or Decimal("0")
                child_price = (
                    departure.price_child if departure.price_child is not None else adult_price
                )
                estimated = (adult_price * adults) + (child_price * children)

                booking = Booking(
                    reference=cls.generate_reference(),
                    booking_type="TOUR",
                    tour_id=departure.tour_id,
                    departure_id=departure.id,
                    customer_id=customer.id,
                    adults=adults,
                    children=children,
                    pickup_location=pickup_location,
                    special_requests=special_requests,
                    booking_status="NEW",
                    payment_status="UNPAID",
                    estimated_total=estimated,
                    currency=departure.tour.currency if departure.tour else "KES",
                    submission_token=submission_token or generate_token(),
                )
                db.session.add(booking)
                db.session.flush()
        except IntegrityError as exc:
            db.session.rollback()
            raise BookingError("Unable to create booking. Please try again.") from exc

        db.session.commit()
        EmailService.booking_received(booking)
        NotificationService.notify_admins(
            title="New booking request",
            message=f"{booking.reference} — {booking.display_title}",
            link=f"/admin/bookings/{booking.id}",
            category="booking",
        )
        return booking

    @classmethod
    def create_service_booking(
        cls,
        *,
        service_id: int,
        full_name: str,
        email: str,
        phone: str,
        country: str | None,
        travelers: int,
        preferred_travel_date: date | None,
        destination_country: str | None,
        special_requests: str | None,
        submission_token: str | None = None,
    ) -> Booking:
        if travelers < 1:
            raise BookingError("At least one traveler is required.")

        if submission_token:
            existing = Booking.query.filter_by(submission_token=submission_token).first()
            if existing:
                return existing

        service = Service.query.filter_by(
            id=service_id, is_published=True, is_bookable=True
        ).first()
        if not service:
            raise BookingError("This service is not available for booking.")

        try:
            with db.session.begin_nested():
                customer = cls._upsert_customer(
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    country=country,
                )
                booking = Booking(
                    reference=cls.generate_reference(),
                    booking_type="SERVICE",
                    service_id=service.id,
                    tour_id=None,
                    departure_id=None,
                    customer_id=customer.id,
                    adults=travelers,
                    children=0,
                    preferred_travel_date=preferred_travel_date,
                    destination_country=(destination_country or "").strip() or None,
                    special_requests=special_requests,
                    booking_status="NEW",
                    payment_status="UNPAID",
                    estimated_total=Decimal("0"),
                    currency=current_app.config.get("COMPANY_CURRENCY", "KES"),
                    submission_token=submission_token or generate_token(),
                )
                db.session.add(booking)
                db.session.flush()
        except IntegrityError as exc:
            db.session.rollback()
            raise BookingError("Unable to create service booking. Please try again.") from exc

        db.session.commit()
        EmailService.booking_received(booking)
        NotificationService.notify_admins(
            title="New service booking request",
            message=f"{booking.reference} — {booking.display_title}",
            link=f"/admin/bookings/{booking.id}",
            category="booking",
        )
        return booking

    @staticmethod
    def update_status(booking: Booking, status: str) -> Booking:
        allowed = {"NEW", "UNDER_REVIEW", "INVOICED", "CONFIRMED", "CANCELLED", "COMPLETED"}
        if status not in allowed:
            raise BookingError("Invalid booking status.")
        booking.booking_status = status
        if status == "CANCELLED":
            from app.models.mixins import utcnow

            booking.cancelled_at = utcnow()
        if status == "CONFIRMED":
            from app.models.mixins import utcnow

            booking.confirmed_at = utcnow()
        db.session.commit()
        return booking
