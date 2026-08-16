"""Invoice and payment tests."""

from datetime import date
from decimal import Decimal

from app.extensions import db
from app.models import Booking, Departure, Invoice
from app.services.booking_service import BookingService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService
from app.utils.helpers import generate_token


def _make_booking(app):
    with app.app_context():
        departure = Departure.query.first()
        booking = BookingService.create_booking(
            departure_id=departure.id,
            full_name="Pay User",
            email="pay@example.com",
            phone="+254711000111",
            country="Kenya",
            adults=2,
            children=0,
            pickup_location=None,
            special_requests=None,
            submission_token=generate_token(),
        )
        return booking.id


def test_create_invoice_and_totals(app):
    booking_id = _make_booking(app)
    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        invoice = InvoiceService.create_from_booking(booking, admin_id=1)
        assert invoice.invoice_number.startswith("INV-")
        assert invoice.total == Decimal("20000.00")
        assert invoice.balance == invoice.total
        assert booking.booking_status == "INVOICED"
        assert booking.payment_status == "UNPAID"


def test_partial_and_full_payment(app):
    booking_id = _make_booking(app)
    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        invoice = InvoiceService.create_from_booking(booking, admin_id=1)
        PaymentService.record_payment(
            invoice,
            amount=Decimal("8000"),
            method="M-Pesa",
            payment_date=date.today(),
            transaction_reference="MPX1",
            admin_id=1,
            auto_verify=True,
        )
        invoice = db.session.get(Invoice, invoice.id)
        booking = db.session.get(Booking, booking_id)
        assert invoice.status == "PARTIALLY_PAID"
        assert booking.payment_status == "PARTIALLY_PAID"
        assert invoice.balance == Decimal("12000.00")

        PaymentService.record_payment(
            invoice,
            amount=Decimal("12000"),
            method="Bank Transfer",
            payment_date=date.today(),
            transaction_reference="BT1",
            admin_id=1,
            auto_verify=True,
        )
        invoice = db.session.get(Invoice, invoice.id)
        booking = db.session.get(Booking, booking_id)
        assert invoice.status == "PAID"
        assert invoice.balance == Decimal("0")
        assert booking.payment_status == "PAID"
        assert booking.booking_status == "CONFIRMED"


def test_generate_pdf(app, tmp_path):
    booking_id = _make_booking(app)
    with app.app_context():
        booking = db.session.get(Booking, booking_id)
        invoice = InvoiceService.create_from_booking(booking, admin_id=1)
        path = InvoiceService.generate_pdf(invoice)
        assert path.endswith(".pdf")


def test_update_service_invoice_prices(app):
    from app.models import Service
    from app.services.booking_service import BookingService as BS
    from app.services.invoice_service import InvoiceError

    with app.app_context():
        service = Service.query.filter_by(slug="air-ticketing").first()
        if service is None:
            service = Service(
                name="Air Ticketing (AT)",
                slug="air-ticketing",
                is_published=True,
                is_bookable=True,
                sort_order=1,
            )
            db.session.add(service)
            db.session.commit()

        booking = BS.create_service_booking(
            service_id=service.id,
            full_name="Service Client",
            email="service-client@example.com",
            phone="+254700000001",
            country="Kenya",
            travelers=2,
            preferred_travel_date=date.today(),
            destination_country="UAE",
            special_requests="Need return flights",
            submission_token=generate_token(),
        )
        invoice = InvoiceService.create_from_booking(booking, admin_id=1)
        assert invoice.total == Decimal("0.00")
        assert invoice.status == "DRAFT"

        InvoiceService.update_invoice(
            invoice,
            items=[
                {
                    "description": "Air Ticketing — Nairobi to Dubai return",
                    "quantity": 2,
                    "unit_price": Decimal("45000"),
                },
                {
                    "description": "Service fee",
                    "quantity": 1,
                    "unit_price": Decimal("2500"),
                },
            ],
            discount=Decimal("500"),
        )
        invoice = db.session.get(Invoice, invoice.id)
        assert invoice.subtotal == Decimal("92500.00")
        assert invoice.total == Decimal("92000.00")

        try:
            InvoiceService.send_invoice(
                InvoiceService.create_from_booking(
                    BS.create_service_booking(
                        service_id=service.id,
                        full_name="Zero Quote",
                        email="zero-quote@example.com",
                        phone="+254700000002",
                        country="Kenya",
                        travelers=1,
                        preferred_travel_date=None,
                        destination_country=None,
                        special_requests=None,
                        submission_token=generate_token(),
                    ),
                    admin_id=1,
                )
            )
            assert False, "Expected InvoiceError for zero total"
        except InvoiceError:
            pass
