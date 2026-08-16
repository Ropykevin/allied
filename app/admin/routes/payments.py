"""Admin payment recording."""

from datetime import date

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import PaymentForm
from app.models import Invoice, Payment
from app.services.payment_service import PaymentError, PaymentService


@bp.route("/payments")
@login_required
@permission_required("payments.view")
def payments_list():
    page = request.args.get("page", 1, type=int)
    pagination = Payment.query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        "admin/payments/list.html", pagination=pagination, payments=pagination.items
    )


@bp.route("/payments/record/<int:invoice_id>", methods=["GET", "POST"])
@login_required
@permission_required("payments.record")
def payments_record(invoice_id: int):
    invoice = Invoice.query.get_or_404(invoice_id)
    form = PaymentForm()
    if request.method == "GET":
        form.payment_date.data = date.today()
        form.amount.data = invoice.balance
    if form.validate_on_submit():
        try:
            payment = PaymentService.record_payment(
                invoice,
                amount=form.amount.data,
                method=form.method.data,
                payment_date=form.payment_date.data,
                transaction_reference=form.transaction_reference.data,
                notes=form.notes.data,
                admin_id=current_user.id,
            )
            flash("Payment recorded.", "success")
            return redirect(url_for("admin.invoices_detail", invoice_id=invoice.id))
        except PaymentError as exc:
            flash(str(exc), "danger")
    return render_template("admin/payments/form.html", form=form, invoice=invoice)


@bp.route("/payments/<int:payment_id>/verify", methods=["POST"])
@login_required
@permission_required("payments.verify")
def payments_verify(payment_id: int):
    payment = Payment.query.get_or_404(payment_id)
    try:
        PaymentService.verify_payment(payment, admin_id=current_user.id)
        flash("Payment verified.", "success")
    except PaymentError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.invoices_detail", invoice_id=payment.invoice_id))


@bp.route("/payments/<int:payment_id>/refund", methods=["POST"])
@login_required
@permission_required("payments.refund")
def payments_refund(payment_id: int):
    payment = Payment.query.get_or_404(payment_id)
    try:
        PaymentService.refund_payment(payment, admin_id=current_user.id)
        flash("Payment refunded.", "success")
    except PaymentError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.invoices_detail", invoice_id=payment.invoice_id))
