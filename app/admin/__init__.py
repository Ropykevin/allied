"""Admin management portal blueprint."""

from flask import Blueprint

bp = Blueprint("admin", __name__)

from app.admin.routes import (  # noqa: E402, F401
    bookings,
    content,
    customers,
    dashboard,
    destinations,
    departures,
    invoices,
    payments,
    reports,
    settings,
    tours,
    users,
)
