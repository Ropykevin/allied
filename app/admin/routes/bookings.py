"""Admin booking management."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import BookingStatusForm, InvoiceCreateForm
from app.extensions import db
from app.models import Booking
from app.services.booking_service import BookingError, BookingService
from app.services.email_service import EmailService
from app.services.invoice_service import InvoiceError, InvoiceService
from app.utils.audit import log_action
from flask_login import current_user


@bp.route("/bookings")
@login_required
@permission_required("bookings.view")
def bookings_list():
    status = request.args.get("status", "all")
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Booking.query
    if status != "all":
        query = query.filter_by(booking_status=status.upper())
    if q:
        query = query.filter(Booking.reference.ilike(f"%{q}%"))
    pagination = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        "admin/bookings/list.html",
        pagination=pagination,
        bookings=pagination.items,
        status=status,
        q=q,
    )


@bp.route("/bookings/<int:booking_id>", methods=["GET", "POST"])
@login_required
@permission_required("bookings.view")
def bookings_detail(booking_id: int):
    booking = Booking.query.get_or_404(booking_id)
    status_form = BookingStatusForm(obj=booking)
    invoice_form = InvoiceCreateForm()
    if status_form.validate_on_submit() and status_form.submit.data is not False:
        if request.form.get("form_name") == "status" and current_user.has_permission("bookings.update"):
            try:
                BookingService.update_status(booking, status_form.booking_status.data)
                booking.admin_notes = status_form.admin_notes.data
                db.session.commit()
                if booking.booking_status == "CANCELLED":
                    EmailService.booking_cancelled(booking)
                log_action("booking.status_updated", "booking", booking.id, booking.booking_status)
                flash("Booking updated.", "success")
            except BookingError as exc:
                flash(str(exc), "danger")
            return redirect(url_for("admin.bookings_detail", booking_id=booking.id))

    if invoice_form.validate_on_submit() and request.form.get("form_name") == "invoice":
        if not current_user.has_permission("invoices.create"):
            flash("You cannot create invoices.", "danger")
        else:
            try:
                invoice = InvoiceService.create_from_booking(
                    booking,
                    discount=invoice_form.discount.data or 0,
                    due_days=invoice_form.due_days.data,
                    payment_instructions=invoice_form.payment_instructions.data,
                    terms=invoice_form.terms.data,
                    admin_id=current_user.id,
                )
                flash(f"Invoice {invoice.invoice_number} generated.", "success")
                return redirect(url_for("admin.invoices_detail", invoice_id=invoice.id))
            except InvoiceError as exc:
                flash(str(exc), "danger")
        return redirect(url_for("admin.bookings_detail", booking_id=booking.id))

    return render_template(
        "admin/bookings/detail.html",
        booking=booking,
        status_form=status_form,
        invoice_form=invoice_form,
    )


@bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
@permission_required("bookings.cancel")
def bookings_cancel(booking_id: int):
    booking = Booking.query.get_or_404(booking_id)
    BookingService.update_status(booking, "CANCELLED")
    EmailService.booking_cancelled(booking)
    log_action("booking.cancelled", "booking", booking.id, booking.reference)
    flash("Booking cancelled.", "success")
    return redirect(url_for("admin.bookings_detail", booking_id=booking.id))
