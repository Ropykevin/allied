"""Admin invoice management."""

from decimal import Decimal

from flask import flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import InvoiceEditForm
from app.extensions import db
from app.models import Invoice
from app.services.invoice_service import InvoiceError, InvoiceService


def _parse_invoice_items_from_request() -> list[dict]:
    descriptions = request.form.getlist("item_description")
    quantities = request.form.getlist("item_quantity")
    unit_prices = request.form.getlist("item_unit_price")
    removes = set(request.form.getlist("item_remove"))
    items: list[dict] = []
    for idx, description in enumerate(descriptions):
        if str(idx) in removes:
            continue
        items.append(
            {
                "description": description,
                "quantity": quantities[idx] if idx < len(quantities) else 1,
                "unit_price": unit_prices[idx] if idx < len(unit_prices) else 0,
            }
        )
    return items


@bp.route("/invoices")
@login_required
@permission_required("invoices.view")
def invoices_list():
    status = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    query = Invoice.query
    if status == "pending":
        query = query.filter(Invoice.status.in_(["DRAFT", "SENT"]))
    elif status == "paid":
        query = query.filter_by(status="PAID")
    elif status == "outstanding":
        query = query.filter(Invoice.status.in_(["SENT", "PARTIALLY_PAID", "OVERDUE"]))
    elif status != "all":
        query = query.filter_by(status=status.upper())
    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        "admin/invoices/list.html",
        pagination=pagination,
        invoices=pagination.items,
        status=status,
    )


@bp.route("/invoices/<int:invoice_id>", methods=["GET", "POST"])
@login_required
@permission_required("invoices.view")
def invoices_detail(invoice_id: int):
    invoice = Invoice.query.get_or_404(invoice_id)
    can_edit = (
        current_user.has_permission("invoices.update")
        and invoice.status in ("DRAFT", "SENT", "OVERDUE")
        and (invoice.amount_paid or Decimal("0")) <= 0
    )
    form = InvoiceEditForm(obj=invoice)
    if request.method == "GET":
        form.discount.data = invoice.discount or Decimal("0")
        form.due_date.data = invoice.due_date
        form.payment_instructions.data = invoice.payment_instructions
        form.terms.data = invoice.terms
        form.notes.data = invoice.notes

    if can_edit and form.validate_on_submit():
        try:
            items = _parse_invoice_items_from_request()
            InvoiceService.update_invoice(
                invoice,
                items=items,
                discount=form.discount.data if form.discount.data is not None else Decimal("0"),
                due_date=form.due_date.data,
                clear_due_date=form.due_date.data is None,
                payment_instructions=form.payment_instructions.data or "",
                terms=form.terms.data or "",
                notes=form.notes.data or "",
            )
            flash("Invoice details saved.", "success")
            return redirect(url_for("admin.invoices_detail", invoice_id=invoice.id))
        except InvoiceError as exc:
            flash(str(exc), "danger")

    booking = invoice.booking
    return render_template(
        "admin/invoices/detail.html",
        invoice=invoice,
        form=form,
        can_edit=can_edit,
        booking=booking,
    )


@bp.route("/invoices/<int:invoice_id>/send", methods=["POST"])
@login_required
@permission_required("invoices.send")
def invoices_send(invoice_id: int):
    invoice = Invoice.query.get_or_404(invoice_id)
    try:
        InvoiceService.send_invoice(invoice)
        flash("Invoice sent to customer.", "success")
    except InvoiceError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.invoices_detail", invoice_id=invoice.id))


@bp.route("/invoices/<int:invoice_id>/pdf")
@login_required
@permission_required("invoices.view")
def invoices_pdf(invoice_id: int):
    invoice = Invoice.query.get_or_404(invoice_id)
    # Always rebuild so branding/logo updates appear on download.
    pdf_rel = InvoiceService.generate_pdf(invoice)
    invoice.pdf_path = pdf_rel
    db.session.commit()
    pdf_file = InvoiceService.resolve_pdf_path(invoice)
    if not pdf_file:
        flash("Invoice PDF could not be generated.", "danger")
        return redirect(url_for("admin.invoices_detail", invoice_id=invoice.id))
    return send_from_directory(
        pdf_file.parent,
        pdf_file.name,
        as_attachment=True,
        download_name=f"{invoice.invoice_number}.pdf",
    )
