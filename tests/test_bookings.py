"""Booking workflow tests."""

from app.extensions import db
from app.models import Booking, Departure
from app.services.booking_service import BookingError, BookingService
from app.utils.helpers import generate_token


def test_create_booking_public(client, app):
    with app.app_context():
        departure = Departure.query.first()
        dep_id = departure.id
        slug = departure.tour.slug
    token = generate_token()
    resp = client.post(
        f"/book/{slug}",
        data={
            "departure_id": dep_id,
            "adults": 2,
            "children": 1,
            "full_name": "Jane Traveler",
            "email": "jane@example.com",
            "phone": "+254700111222",
            "country": "Kenya",
            "pickup_location": "Nairobi Hotel",
            "special_requests": "Window seat if possible",
            "submission_token": token,
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Booking Request Received" in resp.data or b"Awaiting Invoice" in resp.data
    with app.app_context():
        booking = Booking.query.filter_by(submission_token=token).first()
        assert booking is not None
        assert booking.booking_status == "NEW"
        assert booking.payment_status == "UNPAID"
        assert booking.reference.startswith("ATT-")


def test_duplicate_submission_token(app):
    with app.app_context():
        departure = Departure.query.first()
        token = generate_token()
        first = BookingService.create_booking(
            departure_id=departure.id,
            full_name="Dup User",
            email="dup@example.com",
            phone="+254700000001",
            country="Kenya",
            adults=1,
            children=0,
            pickup_location=None,
            special_requests=None,
            submission_token=token,
        )
        second = BookingService.create_booking(
            departure_id=departure.id,
            full_name="Dup User",
            email="dup@example.com",
            phone="+254700000001",
            country="Kenya",
            adults=1,
            children=0,
            pickup_location=None,
            special_requests=None,
            submission_token=token,
        )
        assert first.id == second.id


def test_capacity_validation(app):
    with app.app_context():
        departure = Departure.query.first()
        departure.capacity = 2
        db.session.commit()
        BookingService.create_booking(
            departure_id=departure.id,
            full_name="Full One",
            email="full1@example.com",
            phone="+254700000010",
            country="Kenya",
            adults=2,
            children=0,
            pickup_location=None,
            special_requests=None,
            submission_token=generate_token(),
        )
        try:
            BookingService.create_booking(
                departure_id=departure.id,
                full_name="Full Two",
                email="full2@example.com",
                phone="+254700000011",
                country="Kenya",
                adults=1,
                children=0,
                pickup_location=None,
                special_requests=None,
                submission_token=generate_token(),
            )
            assert False, "Expected BookingError"
        except BookingError:
            pass


def test_check_booking(client, app):
    with app.app_context():
        departure = Departure.query.first()
        booking = BookingService.create_booking(
            departure_id=departure.id,
            full_name="Check User",
            email="check@example.com",
            phone="+254700999888",
            country="Kenya",
            adults=1,
            children=0,
            pickup_location=None,
            special_requests=None,
            submission_token=generate_token(),
        )
        reference = booking.reference
    resp = client.post(
        "/check-booking",
        data={"reference": reference, "contact": "check@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert reference.encode() in resp.data
