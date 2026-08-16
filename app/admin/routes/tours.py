"""Admin tour management."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import TourForm
from app.extensions import db
from app.models import Destination, Tour, TourExclusion, TourInclusion
from app.utils.audit import log_action
from app.utils.helpers import slugify
from app.utils.uploads import UploadError, save_image


def _populate_tour_choices(form: TourForm) -> None:
    form.destination_id.choices = [
        (d.id, d.name)
        for d in Destination.query.filter(Destination.archived_at.is_(None))
        .order_by(Destination.name)
        .all()
    ]


def _sync_lines(tour: Tour, text: str | None, model, attr: str) -> None:
    getattr(tour, attr).clear()
    db.session.flush()
    if not text:
        return
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if line:
            db.session.add(model(tour_id=tour.id, item=line, sort_order=i))


@bp.route("/tours")
@login_required
@permission_required("tours.view")
def tours_list():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)
    query = Tour.query.filter(Tour.archived_at.is_(None))
    if q:
        query = query.filter(Tour.name.ilike(f"%{q}%"))
    if status == "published":
        query = query.filter(Tour.is_published.is_(True))
    elif status == "draft":
        query = query.filter(Tour.is_published.is_(False))
    pagination = query.order_by(Tour.updated_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/tours/list.html", pagination=pagination, tours=pagination.items, q=q, status=status)


@bp.route("/tours/new", methods=["GET", "POST"])
@login_required
@permission_required("tours.create")
def tours_create():
    form = TourForm()
    _populate_tour_choices(form)
    if form.validate_on_submit():
        slug = slugify(form.slug.data or form.name.data)
        if Tour.query.filter_by(slug=slug).first():
            flash("A tour with this slug already exists.", "danger")
        else:
            tour = Tour(
                name=form.name.data.strip(),
                slug=slug,
                destination_id=form.destination_id.data,
                category=form.category.data,
                short_description=form.short_description.data,
                overview=form.overview.data,
                duration_days=form.duration_days.data,
                duration_nights=form.duration_nights.data or 0,
                starting_price=form.starting_price.data,
                currency=form.currency.data or "KES",
                default_capacity=form.default_capacity.data,
                pickup_info=form.pickup_info.data,
                map_embed_url=form.map_embed_url.data,
                is_featured=form.is_featured.data,
                is_published=form.is_published.data,
                seo_title=form.seo_title.data,
                seo_description=form.seo_description.data,
            )
            if form.hero_image_file.data:
                try:
                    tour.hero_image = save_image(form.hero_image_file.data, "tours")
                except UploadError as exc:
                    flash(str(exc), "danger")
                    return render_template("admin/tours/form.html", form=form, tour=None)
            db.session.add(tour)
            db.session.flush()
            _sync_lines(tour, form.inclusions_text.data, TourInclusion, "inclusions")
            _sync_lines(tour, form.exclusions_text.data, TourExclusion, "exclusions")
            db.session.commit()
            log_action("tour.created", "tour", tour.id, tour.name)
            flash("Tour created.", "success")
            return redirect(url_for("admin.tours_list"))
    return render_template("admin/tours/form.html", form=form, tour=None)


@bp.route("/tours/<int:tour_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("tours.update")
def tours_edit(tour_id: int):
    tour = Tour.query.get_or_404(tour_id)
    form = TourForm(obj=tour)
    _populate_tour_choices(form)
    if request.method == "GET":
        form.inclusions_text.data = "\n".join(i.item for i in tour.inclusions)
        form.exclusions_text.data = "\n".join(e.item for e in tour.exclusions)
    if form.validate_on_submit():
        slug = slugify(form.slug.data or form.name.data)
        clash = Tour.query.filter(Tour.slug == slug, Tour.id != tour.id).first()
        if clash:
            flash("A tour with this slug already exists.", "danger")
        else:
            tour.name = form.name.data.strip()
            tour.slug = slug
            tour.destination_id = form.destination_id.data
            tour.category = form.category.data
            tour.short_description = form.short_description.data
            tour.overview = form.overview.data
            tour.duration_days = form.duration_days.data
            tour.duration_nights = form.duration_nights.data or 0
            tour.starting_price = form.starting_price.data
            tour.currency = form.currency.data or "KES"
            tour.default_capacity = form.default_capacity.data
            tour.pickup_info = form.pickup_info.data
            tour.map_embed_url = form.map_embed_url.data
            tour.is_featured = form.is_featured.data
            tour.is_published = form.is_published.data
            tour.seo_title = form.seo_title.data
            tour.seo_description = form.seo_description.data
            if form.hero_image_file.data:
                try:
                    tour.hero_image = save_image(form.hero_image_file.data, "tours")
                except UploadError as exc:
                    flash(str(exc), "danger")
                    return render_template("admin/tours/form.html", form=form, tour=tour)
            TourInclusion.query.filter_by(tour_id=tour.id).delete()
            TourExclusion.query.filter_by(tour_id=tour.id).delete()
            db.session.flush()
            for i, line in enumerate((form.inclusions_text.data or "").splitlines()):
                if line.strip():
                    db.session.add(TourInclusion(tour_id=tour.id, item=line.strip(), sort_order=i))
            for i, line in enumerate((form.exclusions_text.data or "").splitlines()):
                if line.strip():
                    db.session.add(TourExclusion(tour_id=tour.id, item=line.strip(), sort_order=i))
            db.session.commit()
            log_action("tour.updated", "tour", tour.id, tour.name)
            flash("Tour updated.", "success")
            return redirect(url_for("admin.tours_list"))
    return render_template("admin/tours/form.html", form=form, tour=tour)


@bp.route("/tours/<int:tour_id>/archive", methods=["POST"])
@login_required
@permission_required("tours.delete")
def tours_archive(tour_id: int):
    tour = Tour.query.get_or_404(tour_id)
    tour.archive()
    tour.is_published = False
    db.session.commit()
    log_action("tour.archived", "tour", tour.id, tour.name)
    flash("Tour archived.", "success")
    return redirect(url_for("admin.tours_list"))
