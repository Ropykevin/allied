"""Admin departure schedule management."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import DepartureForm
from app.extensions import db
from app.models import Departure, Tour
from app.utils.audit import log_action


def _tour_choices(form: DepartureForm) -> None:
    form.tour_id.choices = [
        (t.id, t.name)
        for t in Tour.query.filter(Tour.archived_at.is_(None)).order_by(Tour.name).all()
    ]


@bp.route("/departures")
@login_required
@permission_required("departures.view")
def departures_list():
    tour_id = request.args.get("tour", type=int)
    query = Departure.query
    if tour_id:
        query = query.filter_by(tour_id=tour_id)
    items = query.order_by(Departure.departure_date.desc()).limit(200).all()
    tours = Tour.query.filter(Tour.archived_at.is_(None)).order_by(Tour.name).all()
    return render_template(
        "admin/departures/list.html", departures=items, tours=tours, selected_tour=tour_id
    )


@bp.route("/departures/new", methods=["GET", "POST"])
@login_required
@permission_required("departures.create")
def departures_create():
    form = DepartureForm()
    _tour_choices(form)
    if form.validate_on_submit():
        dep = Departure(
            tour_id=form.tour_id.data,
            departure_date=form.departure_date.data,
            return_date=form.return_date.data,
            capacity=form.capacity.data,
            price_adult=form.price_adult.data,
            price_child=form.price_child.data,
            status=form.status.data,
            notes=form.notes.data,
            is_active=form.is_active.data,
        )
        db.session.add(dep)
        try:
            db.session.commit()
        except Exception:  # noqa: BLE001
            db.session.rollback()
            flash("Could not create departure. Date may already exist for this tour.", "danger")
            return render_template("admin/departures/form.html", form=form, departure=None)
        log_action("departure.created", "departure", dep.id)
        flash("Departure created.", "success")
        return redirect(url_for("admin.departures_list"))
    return render_template("admin/departures/form.html", form=form, departure=None)


@bp.route("/departures/<int:departure_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("departures.update")
def departures_edit(departure_id: int):
    departure = Departure.query.get_or_404(departure_id)
    form = DepartureForm(obj=departure)
    _tour_choices(form)
    if form.validate_on_submit():
        form.populate_obj(departure)
        db.session.commit()
        log_action("departure.updated", "departure", departure.id)
        flash("Departure updated.", "success")
        return redirect(url_for("admin.departures_list"))
    return render_template("admin/departures/form.html", form=form, departure=departure)
