"""Admin customer records (no authentication)."""

from decimal import Decimal

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import CustomerForm
from sqlalchemy import or_

from app.extensions import db
from app.models import Booking, Customer, Invoice
from app.utils.audit import log_action


@bp.route("/customers")
@login_required
@permission_required("customers.view")
def customers_list():
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    query = Customer.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
            )
        )
    pagination = query.order_by(Customer.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        "admin/customers/list.html",
        pagination=pagination,
        customers=pagination.items,
        q=q,
    )


@bp.route("/customers/<int:customer_id>", methods=["GET", "POST"])
@login_required
@permission_required("customers.view")
def customers_detail(customer_id: int):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm(obj=customer)
    bookings = (
        Booking.query.filter_by(customer_id=customer.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    invoices = Invoice.query.filter_by(customer_id=customer.id).all()
    total_paid = sum((inv.amount_paid for inv in invoices), Decimal("0"))
    outstanding = sum((inv.balance for inv in invoices), Decimal("0"))
    return render_template(
        "admin/customers/detail.html",
        customer=customer,
        form=form,
        bookings=bookings,
        total_paid=total_paid,
        outstanding=outstanding,
    )


@bp.route("/customers/<int:customer_id>/edit", methods=["POST"])
@login_required
@permission_required("customers.update")
def customers_edit(customer_id: int):
    customer = Customer.query.get_or_404(customer_id)
    form = CustomerForm()
    if form.validate_on_submit():
        customer.full_name = form.full_name.data
        customer.email = form.email.data.lower().strip()
        customer.phone = form.phone.data
        customer.country = form.country.data
        db.session.commit()
        log_action("customer.updated", "customer", customer.id)
        flash("Customer updated.", "success")
    else:
        flash("Could not update customer.", "danger")
    return redirect(url_for("admin.customers_detail", customer_id=customer.id))
