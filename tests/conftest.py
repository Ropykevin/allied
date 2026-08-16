"""Pytest fixtures for Allied Tours & Travel."""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from app.models import Admin, Departure, Destination, Role, Tour
from app.utils.permissions import PERMISSIONS, ROLE_PERMISSION_MAP
from app.models import Permission
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        _seed_rbac()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _seed_rbac():
    perms = {}
    for code, name, category in PERMISSIONS:
        p = Permission(code=code, name=name, category=category)
        db.session.add(p)
        perms[code] = p
    db.session.flush()

    roles = {}
    for slug, codes in ROLE_PERMISSION_MAP.items():
        role = Role(name=slug.replace("-", " ").title(), slug=slug, is_system=True)
        role.permissions = [perms[c] for c in codes]
        db.session.add(role)
        roles[slug] = role
    db.session.flush()

    for email, slug, name in [
        ("admin@test.example", "super-admin", "Super Admin"),
        ("ops@test.example", "operations-manager", "Ops"),
        ("booking@test.example", "booking-manager", "Booking"),
        ("finance@test.example", "finance", "Finance"),
        ("content@test.example", "content-manager", "Content"),
    ]:
        admin = Admin(email=email, full_name=name, role_id=roles[slug].id, is_active=True)
        admin.set_password("TestPass!12345")
        db.session.add(admin)

    dest = Destination(
        name="Test Mara",
        slug="test-mara",
        is_published=True,
        short_description="Test destination",
    )
    db.session.add(dest)
    db.session.flush()
    tour = Tour(
        name="Test Safari",
        slug="test-safari",
        destination_id=dest.id,
        duration_days=3,
        starting_price=Decimal("10000"),
        currency="KES",
        default_capacity=10,
        is_published=True,
        short_description="Demo tour for tests",
        overview="Test overview",
    )
    db.session.add(tour)
    db.session.flush()
    db.session.add(
        Departure(
            tour_id=tour.id,
            departure_date=date.today() + timedelta(days=20),
            capacity=10,
            price_adult=Decimal("10000"),
            price_child=Decimal("7000"),
            status="OPEN",
            is_active=True,
        )
    )
    db.session.commit()


@pytest.fixture()
def admin_client(client):
    client.post(
        "/admin/login",
        data={"email": "admin@test.example", "password": "TestPass!12345"},
        follow_redirects=True,
    )
    return client


@pytest.fixture()
def login_as():
    def _login(client, email: str):
        return client.post(
            "/admin/login",
            data={"email": email, "password": "TestPass!12345"},
            follow_redirects=True,
        )

    return _login
