"""Content management: blog, gallery, reviews, FAQs, services, partners."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.admin import bp
from app.admin.decorators import permission_required
from app.admin.forms import (
    BlogPostForm,
    FAQForm,
    GalleryEditForm,
    GalleryForm,
    PartnerForm,
    ReviewForm,
    ServiceForm,
)
from app.extensions import db
from app.models import FAQ, BlogPost, GalleryImage, Partner, Review, Service, Tour
from app.models.mixins import utcnow
from app.utils.audit import log_action
from app.utils.helpers import slugify
from app.utils.sanitize import safe_external_url
from app.utils.uploads import UploadError, delete_upload, has_upload, save_gallery_media, save_image


@bp.route("/content/blog")
@login_required
@permission_required("content.view")
def blog_list():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template("admin/content/blog_list.html", posts=posts)


@bp.route("/content/blog/new", methods=["GET", "POST"])
@login_required
@permission_required("content.create")
def blog_create():
    form = BlogPostForm()
    if form.validate_on_submit():
        slug = slugify(form.slug.data or form.title.data)
        post = BlogPost(
            title=form.title.data,
            slug=slug,
            excerpt=form.excerpt.data,
            body=form.body.data,
            is_published=form.is_published.data,
            seo_title=form.seo_title.data,
            seo_description=form.seo_description.data,
            author_id=current_user.id,
            published_at=utcnow() if form.is_published.data else None,
        )
        if has_upload(form.featured_image_file.data):
            try:
                post.featured_image = save_image(form.featured_image_file.data, "blog")
            except UploadError as exc:
                flash(str(exc), "danger")
                return render_template("admin/content/blog_form.html", form=form, post=None)
        db.session.add(post)
        db.session.commit()
        log_action("blog.created", "blog", post.id, post.title)
        flash("Blog post saved.", "success")
        return redirect(url_for("admin.blog_list"))
    return render_template("admin/content/blog_form.html", form=form, post=None)


@bp.route("/content/blog/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("content.update")
def blog_edit(post_id: int):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = slugify(form.slug.data or form.title.data)
        post.excerpt = form.excerpt.data
        post.body = form.body.data
        post.is_published = form.is_published.data
        post.seo_title = form.seo_title.data
        post.seo_description = form.seo_description.data
        if form.is_published.data and not post.published_at:
            post.published_at = utcnow()
        if has_upload(form.featured_image_file.data):
            try:
                post.featured_image = save_image(form.featured_image_file.data, "blog")
            except UploadError as exc:
                flash(str(exc), "danger")
                return render_template("admin/content/blog_form.html", form=form, post=post)
        db.session.commit()
        log_action("blog.updated", "blog", post.id, post.title)
        flash("Blog post updated.", "success")
        return redirect(url_for("admin.blog_list"))
    return render_template("admin/content/blog_form.html", form=form, post=post)


@bp.route("/content/gallery", methods=["GET", "POST"])
@login_required
@permission_required("content.view")
def gallery_list():
    form = GalleryForm()
    if request.method == "POST" and current_user.has_permission("content.create"):
        # getlist keeps every selected file from a multi-select picker
        files = [
            f
            for f in request.files.getlist("image_files")
            if f and getattr(f, "filename", None)
        ]
        form.validate()  # CSRF + field checks
        if form.csrf_token.errors:
            flash("Security check failed. Please try uploading again.", "danger")
        elif not files:
            flash("Select at least one photo or video to upload.", "danger")
        else:
            saved = 0
            errors = []
            base_title = (form.title.data or "").strip()
            base_sort = form.sort_order.data or 0
            for index, file in enumerate(files):
                try:
                    path, media_type = save_gallery_media(file)
                    original = (file.filename or "media").rsplit(".", 1)[0]
                    title = base_title
                    if len(files) > 1:
                        title = f"{base_title} ({index + 1})" if base_title else original
                    elif not title:
                        title = original
                    image = GalleryImage(
                        title=title[:200],
                        alt_text=form.alt_text.data or title[:200],
                        category=form.category.data,
                        sort_order=base_sort + index,
                        is_published=form.is_published.data,
                        is_featured=form.is_featured.data,
                        is_hero=form.is_hero.data if media_type == "image" else False,
                        image_path=path,
                        media_type=media_type,
                    )
                    db.session.add(image)
                    saved += 1
                except UploadError as exc:
                    errors.append(f"{file.filename}: {exc}")
            if saved:
                db.session.commit()
                log_action("gallery.uploaded", "gallery", None, f"{saved} media item(s)")
                flash(
                    f"{saved} item{'s' if saved != 1 else ''} uploaded to the gallery.",
                    "success",
                )
            if errors:
                flash("Some uploads failed: " + "; ".join(errors[:3]), "danger")
            if saved:
                return redirect(url_for("admin.gallery_list"))
    images = GalleryImage.query.order_by(GalleryImage.sort_order, GalleryImage.id.desc()).all()
    return render_template("admin/content/gallery.html", form=form, images=images)


@bp.route("/content/gallery/<int:image_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("content.update")
def gallery_edit(image_id: int):
    image = GalleryImage.query.get_or_404(image_id)
    form = GalleryEditForm(obj=image)
    if form.validate_on_submit():
        image.title = form.title.data.strip()
        image.alt_text = form.alt_text.data
        image.category = form.category.data
        image.sort_order = form.sort_order.data or 0
        image.is_published = form.is_published.data
        image.is_featured = form.is_featured.data
        if has_upload(form.image_file.data):
            try:
                old_path = image.image_path
                path, media_type = save_gallery_media(form.image_file.data)
                image.image_path = path
                image.media_type = media_type
                if old_path and old_path.startswith("uploads/"):
                    delete_upload(old_path)
            except UploadError as exc:
                flash(str(exc), "danger")
                return render_template("admin/content/gallery_edit.html", form=form, image=image)
        # Hero slideshow is photo-only
        image.is_hero = bool(form.is_hero.data) and image.is_image
        db.session.commit()
        log_action("gallery.updated", "gallery", image.id, image.title)
        flash("Gallery item updated.", "success")
        return redirect(url_for("admin.gallery_list"))
    return render_template("admin/content/gallery_edit.html", form=form, image=image)


@bp.route("/content/gallery/<int:image_id>/delete", methods=["POST"])
@login_required
@permission_required("content.delete")
def gallery_delete(image_id: int):
    image = GalleryImage.query.get_or_404(image_id)
    title = image.title
    path = image.image_path
    db.session.delete(image)
    db.session.commit()
    if path and path.startswith("uploads/"):
        delete_upload(path)
    log_action("gallery.deleted", "gallery", image_id, title)
    flash("Gallery item deleted.", "success")
    return redirect(url_for("admin.gallery_list"))


def _review_tour_choices(form: ReviewForm) -> None:
    form.tour_id.choices = [(0, "— General —")] + [
        (t.id, t.name)
        for t in Tour.query.filter(Tour.archived_at.is_(None)).order_by(Tour.name)
    ]


@bp.route("/content/testimonials", methods=["GET", "POST"])
@login_required
@permission_required("content.view")
def reviews_list():
    form = ReviewForm()
    _review_tour_choices(form)
    if form.validate_on_submit() and current_user.has_permission("content.create"):
        tour_id = form.tour_id.data or None
        if tour_id == 0:
            tour_id = None
        review = Review(
            customer_name=form.customer_name.data.strip(),
            rating=form.rating.data,
            body=form.body.data.strip(),
            tour_id=tour_id,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            is_demo=False,
        )
        db.session.add(review)
        db.session.commit()
        log_action("review.created", "review", review.id)
        flash("Testimonial saved.", "success")
        return redirect(url_for("admin.reviews_list"))
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/content/reviews.html", form=form, reviews=reviews)


@bp.route("/content/testimonials/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("content.update")
def reviews_edit(review_id: int):
    review = Review.query.get_or_404(review_id)
    form = ReviewForm(obj=review)
    _review_tour_choices(form)
    if request.method == "GET":
        form.tour_id.data = review.tour_id or 0
    if form.validate_on_submit():
        tour_id = form.tour_id.data or None
        if tour_id == 0:
            tour_id = None
        review.customer_name = form.customer_name.data.strip()
        review.rating = form.rating.data
        review.body = form.body.data.strip()
        review.tour_id = tour_id
        review.is_published = form.is_published.data
        review.is_featured = form.is_featured.data
        db.session.commit()
        log_action("review.updated", "review", review.id, review.customer_name)
        flash("Testimonial updated.", "success")
        return redirect(url_for("admin.reviews_list"))
    return render_template("admin/content/reviews_edit.html", form=form, review=review)


@bp.route("/content/testimonials/<int:review_id>/delete", methods=["POST"])
@login_required
@permission_required("content.delete")
def reviews_delete(review_id: int):
    review = Review.query.get_or_404(review_id)
    name = review.customer_name
    db.session.delete(review)
    db.session.commit()
    log_action("review.deleted", "review", review_id, name)
    flash("Testimonial deleted.", "success")
    return redirect(url_for("admin.reviews_list"))


@bp.route("/content/faqs", methods=["GET", "POST"])
@login_required
@permission_required("content.view")
def faqs_list():
    form = FAQForm()
    if form.validate_on_submit() and current_user.has_permission("content.create"):
        faq = FAQ(
            question=form.question.data,
            answer=form.answer.data,
            category=form.category.data,
            sort_order=form.sort_order.data or 0,
            is_published=form.is_published.data,
        )
        db.session.add(faq)
        db.session.commit()
        flash("FAQ saved.", "success")
        return redirect(url_for("admin.faqs_list"))
    faqs = FAQ.query.order_by(FAQ.sort_order, FAQ.id).all()
    return render_template("admin/content/faqs.html", form=form, faqs=faqs)


@bp.route("/content/services", methods=["GET", "POST"])
@login_required
@permission_required("content.view")
def services_list():
    form = ServiceForm()
    if form.validate_on_submit() and current_user.has_permission("content.create"):
        slug = slugify(form.name.data)
        existing = Service.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{Service.query.count() + 1}"
        service = Service(
            name=form.name.data.strip(),
            slug=slug,
            short_description=(form.short_description.data or "").strip() or None,
            description=(form.description.data or "").strip() or None,
            overview=(form.overview.data or "").strip() or None,
            highlights=(form.highlights.data or "").strip() or None,
            what_is_included=(form.what_is_included.data or "").strip() or None,
            how_it_works=(form.how_it_works.data or "").strip() or None,
            who_its_for=(form.who_its_for.data or "").strip() or None,
            important_notes=(form.important_notes.data or "").strip() or None,
            seo_title=(form.seo_title.data or "").strip() or None,
            seo_description=(form.seo_description.data or "").strip() or None,
            sort_order=form.sort_order.data or 0,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
            is_bookable=form.is_bookable.data,
        )
        if has_upload(form.icon_image.data):
            try:
                service.icon_image = save_image(form.icon_image.data, "services", max_width=800)
            except UploadError as exc:
                flash(str(exc), "danger")
                services = Service.query.order_by(Service.sort_order, Service.id).all()
                return render_template("admin/content/services.html", form=form, services=services)
        if has_upload(form.hero_image.data):
            try:
                service.hero_image = save_image(form.hero_image.data, "services", max_width=1800)
            except UploadError as exc:
                flash(str(exc), "danger")
                services = Service.query.order_by(Service.sort_order, Service.id).all()
                return render_template("admin/content/services.html", form=form, services=services)
        db.session.add(service)
        db.session.commit()
        log_action("service.created", "service", service.id, service.name)
        flash("Service saved.", "success")
        return redirect(url_for("admin.services_list"))
    services = Service.query.order_by(Service.sort_order, Service.id).all()
    return render_template("admin/content/services.html", form=form, services=services)


@bp.route("/content/services/<int:service_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("content.update")
def services_edit(service_id: int):
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    if form.validate_on_submit():
        service.name = form.name.data.strip()
        service.slug = slugify(form.name.data)
        service.short_description = (form.short_description.data or "").strip() or None
        service.description = (form.description.data or "").strip() or None
        service.overview = (form.overview.data or "").strip() or None
        service.highlights = (form.highlights.data or "").strip() or None
        service.what_is_included = (form.what_is_included.data or "").strip() or None
        service.how_it_works = (form.how_it_works.data or "").strip() or None
        service.who_its_for = (form.who_its_for.data or "").strip() or None
        service.important_notes = (form.important_notes.data or "").strip() or None
        service.seo_title = (form.seo_title.data or "").strip() or None
        service.seo_description = (form.seo_description.data or "").strip() or None
        service.sort_order = form.sort_order.data or 0
        service.is_published = form.is_published.data
        service.is_featured = form.is_featured.data
        service.is_bookable = form.is_bookable.data
        if has_upload(form.icon_image.data):
            try:
                new_path = save_image(form.icon_image.data, "services", max_width=800)
                delete_upload(service.icon_image)
                service.icon_image = new_path
            except UploadError as exc:
                flash(str(exc), "danger")
                return render_template("admin/content/services_edit.html", form=form, service=service)
        if has_upload(form.hero_image.data):
            try:
                new_path = save_image(form.hero_image.data, "services", max_width=1800)
                delete_upload(service.hero_image)
                service.hero_image = new_path
            except UploadError as exc:
                flash(str(exc), "danger")
                return render_template("admin/content/services_edit.html", form=form, service=service)
        db.session.commit()
        log_action("service.updated", "service", service.id, service.name)
        flash("Service updated.", "success")
        return redirect(url_for("admin.services_list"))
    return render_template("admin/content/services_edit.html", form=form, service=service)


@bp.route("/content/services/<int:service_id>/delete", methods=["POST"])
@login_required
@permission_required("content.delete")
def services_delete(service_id: int):
    service = Service.query.get_or_404(service_id)
    name = service.name
    delete_upload(service.icon_image)
    delete_upload(service.hero_image)
    db.session.delete(service)
    db.session.commit()
    log_action("service.deleted", "service", service_id, name)
    flash("Service deleted.", "success")
    return redirect(url_for("admin.services_list"))


@bp.route("/content/partners", methods=["GET", "POST"])
@login_required
@permission_required("content.view")
def partners_list():
    form = PartnerForm()
    if form.validate_on_submit() and current_user.has_permission("content.create"):
        partner = Partner(
            name=form.name.data.strip(),
            website_url=safe_external_url((form.website_url.data or "").strip()),
            description=(form.description.data or "").strip() or None,
            sort_order=form.sort_order.data or 0,
            is_published=form.is_published.data,
            is_featured=form.is_featured.data,
        )
        if has_upload(form.logo.data):
            try:
                partner.logo_path = save_image(form.logo.data, "partners", max_width=600)
            except UploadError as exc:
                flash(str(exc), "danger")
                partners = Partner.query.order_by(Partner.sort_order, Partner.id).all()
                return render_template("admin/content/partners.html", form=form, partners=partners)
        db.session.add(partner)
        db.session.commit()
        log_action("partner.created", "partner", partner.id, partner.name)
        flash("Partner saved.", "success")
        return redirect(url_for("admin.partners_list"))
    partners = Partner.query.order_by(Partner.sort_order, Partner.id).all()
    return render_template("admin/content/partners.html", form=form, partners=partners)


@bp.route("/content/partners/<int:partner_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("content.update")
def partners_edit(partner_id: int):
    partner = Partner.query.get_or_404(partner_id)
    form = PartnerForm(obj=partner)
    if form.validate_on_submit():
        partner.name = form.name.data.strip()
        partner.website_url = safe_external_url((form.website_url.data or "").strip())
        partner.description = (form.description.data or "").strip() or None
        partner.sort_order = form.sort_order.data or 0
        partner.is_published = form.is_published.data
        partner.is_featured = form.is_featured.data
        if has_upload(form.logo.data):
            try:
                new_path = save_image(form.logo.data, "partners", max_width=600)
                delete_upload(partner.logo_path)
                partner.logo_path = new_path
            except UploadError as exc:
                flash(str(exc), "danger")
                return render_template("admin/content/partners_edit.html", form=form, partner=partner)
        db.session.commit()
        log_action("partner.updated", "partner", partner.id, partner.name)
        flash("Partner updated.", "success")
        return redirect(url_for("admin.partners_list"))
    return render_template("admin/content/partners_edit.html", form=form, partner=partner)


@bp.route("/content/partners/<int:partner_id>/delete", methods=["POST"])
@login_required
@permission_required("content.delete")
def partners_delete(partner_id: int):
    partner = Partner.query.get_or_404(partner_id)
    name = partner.name
    delete_upload(partner.logo_path)
    db.session.delete(partner)
    db.session.commit()
    log_action("partner.deleted", "partner", partner_id, name)
    flash("Partner deleted.", "success")
    return redirect(url_for("admin.partners_list"))
