"""Admin dashboard."""

from datetime import date, timedelta
from decimal import Decimal

from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.admin import bp
from app.admin.decorators import admin_required
from app.extensions import db
from app.models import Booking, Departure, Invoice, Payment, Tour


@bp.route("/")
@login_required
@admin_required
def dashboard():
    today = date.today()
    can_bookings = current_user.has_permission("bookings.view")
    can_invoices = current_user.has_permission("invoices.view")
    can_payments = current_user.has_permission("payments.view")
    can_reports = current_user.has_permission("reports.view")
    can_departures = current_user.has_permission("departures.view")

    stats = {
        "new_bookings": Booking.query.filter_by(booking_status="NEW").count() if can_bookings else None,
        "pending_invoices": (
            Invoice.query.filter(Invoice.status.in_(["DRAFT", "SENT"])).count() if can_invoices else None
        ),
        "awaiting_payments": (
            Booking.query.filter(
                Booking.payment_status == "UNPAID",
                Booking.booking_status.in_(["INVOICED", "UNDER_REVIEW"]),
            ).count()
            if can_bookings
            else None
        ),
        "partially_paid": (
            Booking.query.filter_by(payment_status="PARTIALLY_PAID").count() if can_bookings else None
        ),
        "confirmed_bookings": (
            Booking.query.filter_by(booking_status="CONFIRMED").count() if can_bookings else None
        ),
        "upcoming_departures": (
            Departure.query.filter(
                Departure.departure_date >= today,
                Departure.status == "OPEN",
                Departure.is_active.is_(True),
            ).count()
            if can_departures
            else None
        ),
        "total_invoiced": None,
        "total_collected": None,
        "outstanding": None,
    }

    if can_invoices or can_reports:
        total_invoiced = db.session.query(func.coalesce(func.sum(Invoice.total), 0)).scalar() or 0
        stats["total_invoiced"] = Decimal(total_invoiced)
        if can_payments or can_reports:
            total_collected = (
                db.session.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter(Payment.status.in_(["RECORDED", "VERIFIED"]))
                .scalar()
                or 0
            )
            stats["total_collected"] = Decimal(total_collected)
            stats["outstanding"] = max(
                Decimal(total_invoiced) - Decimal(total_collected), Decimal("0")
            )

    trend_labels = []
    trend_values = []
    if can_bookings:
        for i in range(13, -1, -1):
            day = today - timedelta(days=i)
            trend_labels.append(day.strftime("%d %b"))
            count = Booking.query.filter(func.date(Booking.created_at) == day).count()
            trend_values.append(count)

    popular_tours = []
    if can_bookings:
        popular_tours = (
            db.session.query(Tour.name, func.count(Booking.id).label("total"))
            .join(Booking, Booking.tour_id == Tour.id)
            .group_by(Tour.id)
            .order_by(func.count(Booking.id).desc())
            .limit(5)
            .all()
        )

    payment_status = {}
    if can_bookings or can_payments:
        payment_status = {
            "UNPAID": Booking.query.filter_by(payment_status="UNPAID").count(),
            "PARTIALLY_PAID": Booking.query.filter_by(payment_status="PARTIALLY_PAID").count(),
            "PAID": Booking.query.filter_by(payment_status="PAID").count(),
            "REFUNDED": Booking.query.filter_by(payment_status="REFUNDED").count(),
        }

    recent_bookings = []
    if can_bookings:
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        trend_labels=trend_labels,
        trend_values=trend_values,
        popular_tours=popular_tours,
        payment_status=payment_status,
        recent_bookings=recent_bookings,
        can_bookings=can_bookings,
        can_invoices=can_invoices,
        can_payments=can_payments,
        can_reports=can_reports,
    )
