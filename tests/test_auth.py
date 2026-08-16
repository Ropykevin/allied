"""Authentication and authorization tests."""


def test_admin_login_success(client):
    resp = client.post(
        "/admin/login",
        data={"email": "admin@test.example", "password": "TestPass!12345"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Dashboard" in resp.data or b"New Bookings" in resp.data


def test_admin_login_invalid(client):
    resp = client.post(
        "/admin/login",
        data={"email": "admin@test.example", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert resp.status_code in (200, 401)
    assert b"Invalid email or password" in resp.data


def test_admin_logout(admin_client):
    resp = admin_client.post("/admin/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Sign in" in resp.data or b"password" in resp.data.lower()


def test_booking_confirmation_requires_token(client, app):
    from app.extensions import db
    from app.models import Booking
    from app.services.booking_service import BookingService
    from app.utils.helpers import generate_token
    from datetime import date

    with app.app_context():
        from app.models import Departure

        departure = Departure.query.first()
        booking = BookingService.create_booking(
            departure_id=departure.id,
            full_name="Token User",
            email="token-user@example.com",
            phone="+254711000999",
            country="Kenya",
            adults=1,
            children=0,
            pickup_location=None,
            special_requests=None,
            submission_token=generate_token(),
        )
        ref = booking.reference
        token = BookingService.confirmation_token(ref)

    denied = client.get(f"/booking-confirmation/{ref}", follow_redirects=False)
    assert denied.status_code in (302, 404)

    ok = client.get(f"/booking-confirmation/{ref}?token={token}")
    assert ok.status_code == 200
    assert ref.encode() in ok.data


def test_admin_requires_auth(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code in (302, 401)


def test_finance_cannot_manage_tours(client, login_as):
    login_as(client, "finance@test.example")
    resp = client.get("/admin/tours/new", follow_redirects=False)
    assert resp.status_code == 403


def test_content_cannot_view_payments(client, login_as):
    login_as(client, "content@test.example")
    resp = client.get("/admin/payments", follow_redirects=False)
    assert resp.status_code == 403


def test_booking_manager_can_view_bookings(client, login_as):
    login_as(client, "booking@test.example")
    resp = client.get("/admin/bookings", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Bookings" in resp.data or b"booking" in resp.data.lower()
