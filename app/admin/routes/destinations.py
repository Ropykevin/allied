"""Admin destination management."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import DestinationForm
from app.extensions import db
from app.models import Destination
from app.utils.audit import log_action
from app.utils.helpers import slugify
from app.utils.sanitize import safe_map_embed_url
from app.utils.uploads import UploadError, save_image


@bp.route("/destinations")
@login_required
@permission_required("destinations.view")
def destinations_list():
    items = (
        Destination.query.filter(Destination.archived_at.is_(None))
        .order_by(Destination.sort_order, Destination.name)
        .all()
    )
    return render_template("admin/destinations/list.html", destinations=items)


@bp.route("/destinations/new", methods=["GET", "POST"])
@login_required
@permission_required("destinations.create")
def destinations_create():
    form = DestinationForm()
    if form.validate_on_submit():
        slug = slugify(form.slug.data or form.name.data)
        if Destination.query.filter_by(slug=slug).first():
            flash("Slug already exists.", "danger")
        else:
            dest = Destination(
                name=form.name.data.strip(),
                slug=slug,
                short_description=form.short_description.data,
                description=form.description.data,
                attractions=form.attractions.data,
                travel_info=form.travel_info.data,
                country=form.country.data,
                region=form.region.data,
                map_embed_url=safe_map_embed_url(form.map_embed_url.data),
                is_featured=form.is_featured.data,
                is_published=form.is_published.data,
                sort_order=form.sort_order.data or 0,
                seo_title=form.seo_title.data,
                seo_description=form.seo_description.data,
            )
            if form.hero_image_file.data:
                try:
                    dest.hero_image = save_image(form.hero_image_file.data, "destinations")
                except UploadError as exc:
                    flash(str(exc), "danger")
                    return render_template("admin/destinations/form.html", form=form, destination=None)
            db.session.add(dest)
            db.session.commit()
            log_action("destination.created", "destination", dest.id, dest.name)
            flash("Destination created.", "success")
            return redirect(url_for("admin.destinations_list"))
    return render_template("admin/destinations/form.html", form=form, destination=None)


@bp.route("/destinations/<int:destination_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("destinations.update")
def destinations_edit(destination_id: int):
    destination = Destination.query.get_or_404(destination_id)
    form = DestinationForm(obj=destination)
    if form.validate_on_submit():
        slug = slugify(form.slug.data or form.name.data)
        clash = Destination.query.filter(Destination.slug == slug, Destination.id != destination.id).first()
        if clash:
            flash("Slug already exists.", "danger")
        else:
            form.populate_obj(destination)
            destination.slug = slug
            destination.map_embed_url = safe_map_embed_url(form.map_embed_url.data)
            if form.hero_image_file.data:
                try:
                    destination.hero_image = save_image(form.hero_image_file.data, "destinations")
                except UploadError as exc:
                    flash(str(exc), "danger")
                    return render_template(
                        "admin/destinations/form.html", form=form, destination=destination
                    )
            db.session.commit()
            log_action("destination.updated", "destination", destination.id, destination.name)
            flash("Destination updated.", "success")
            return redirect(url_for("admin.destinations_list"))
    return render_template("admin/destinations/form.html", form=form, destination=destination)
