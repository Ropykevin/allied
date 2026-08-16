"""Tour management tests."""

from app.extensions import db
from app.models import Destination, Tour


def test_create_tour(admin_client, app):
    with app.app_context():
        dest_id = Destination.query.first().id
    resp = admin_client.post(
        "/admin/tours/new",
        data={
            "name": "New Adventure Tour",
            "slug": "new-adventure-tour",
            "destination_id": dest_id,
            "category": "Adventure",
            "short_description": "A short description",
            "overview": "Overview text",
            "duration_days": 2,
            "duration_nights": 1,
            "starting_price": "15000",
            "currency": "KES",
            "default_capacity": 12,
            "is_published": "y",
            "inclusions_text": "Guide\nTransport",
            "exclusions_text": "Flights",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        tour = Tour.query.filter_by(slug="new-adventure-tour").first()
        assert tour is not None
        assert tour.is_published is True


def test_update_and_unpublish_tour(admin_client, app):
    with app.app_context():
        tour = Tour.query.filter_by(slug="test-safari").first()
        tour_id = tour.id
        dest_id = Destination.query.first().id
    resp = admin_client.post(
        f"/admin/tours/{tour_id}/edit",
        data={
            "name": "Updated Safari",
            "slug": "test-safari",
            "destination_id": dest_id,
            "category": "Safari",
            "short_description": "Updated",
            "overview": "Updated overview",
            "duration_days": 3,
            "duration_nights": 2,
            "starting_price": "12000",
            "currency": "KES",
            "default_capacity": 10,
            "inclusions_text": "",
            "exclusions_text": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        tour = db.session.get(Tour, tour_id)
        assert tour.name == "Updated Safari"
        assert tour.is_published is False


def test_archive_tour(admin_client, app):
    with app.app_context():
        tour = Tour.query.filter_by(slug="test-safari").first()
        tour_id = tour.id
    resp = admin_client.post(f"/admin/tours/{tour_id}/archive", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        tour = db.session.get(Tour, tour_id)
        assert tour.is_archived is True


def test_public_tour_list(client):
    resp = client.get("/tours")
    assert resp.status_code == 200
    assert b"Test Safari" in resp.data
