"""Import admin route modules to register views."""

from app.admin.routes import (  # noqa: F401
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
