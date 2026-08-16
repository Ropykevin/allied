"""Financial and operations reports."""

from decimal import Decimal

from flask import render_template
from flask_login import login_required
from sqlalchemy import func

from app.admin import bp
from app.admin.decorators import permission_required
from app.extensions import db
from app.models import Booking, Invoice, Payment, Tour


@bp.route("/reports")
@login_required
@permission_required("reports.view")
def reports():
    by_status = (
        db.session.query(Booking.booking_status, func.count(Booking.id))
        .group_by(Booking.booking_status)
        .all()
    )
    payment_by_method = (
        db.session.query(Payment.method, func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status.in_(["RECORDED", "VERIFIED"]))
        .group_by(Payment.method)
        .all()
    )
    top_tours = (
        db.session.query(Tour.name, func.count(Booking.id))
        .join(Booking, Booking.tour_id == Tour.id)
        .group_by(Tour.id)
        .order_by(func.count(Booking.id).desc())
        .limit(10)
        .all()
    )
    outstanding = (
        db.session.query(func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0))
        .filter(Invoice.status.in_(["SENT", "PARTIALLY_PAID", "OVERDUE"]))
        .scalar()
        or 0
    )
    return render_template(
        "admin/reports/index.html",
        by_status=by_status,
        payment_by_method=payment_by_method,
        top_tours=top_tours,
        outstanding=Decimal(outstanding),
    )
