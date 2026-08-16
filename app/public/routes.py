"""Public client website routes — no customer accounts."""

from __future__ import annotations

from datetime import date

from flask import (
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import or_

from app.extensions import db, limiter
from app.models import (
    FAQ,
    BlogPost,
    Booking,
    Departure,
    Destination,
    GalleryImage,
    Partner,
    Review,
    Service,
    Tour,
)
from app.public import bp
from app.public.forms import BookingForm, CheckBookingForm, ContactForm, ServiceBookingForm
from app.services.booking_service import BookingError, BookingService
from app.services.email_service import EmailService
from app.utils.helpers import generate_token


def _published_tours_query():
    return Tour.query.filter(
        Tour.is_published.is_(True),
        Tour.archived_at.is_(None),
    )


def _published_services_query():
    return Service.query.filter(Service.is_published.is_(True))


@bp.route("/")
def home():
    featured_tours = (
        _published_tours_query()
        .filter(Tour.is_featured.is_(True))
        .order_by(Tour.updated_at.desc())
        .limit(6)
        .all()
    )
    if len(featured_tours) < 3:
        featured_tours = _published_tours_query().order_by(Tour.updated_at.desc()).limit(6).all()

    destinations = (
        Destination.query.filter(
            Destination.is_published.is_(True),
            Destination.archived_at.is_(None),
        )
        .order_by(Destination.is_featured.desc(), Destination.sort_order, Destination.name)
        .limit(6)
        .all()
    )
    reviews = (
        Review.query.filter(Review.is_published.is_(True), Review.is_demo.is_(False))
        .order_by(Review.is_featured.desc(), Review.created_at.desc())
        .limit(24)
        .all()
    )
    # In development, allow demo testimonials only when explicitly published
    if not reviews:
        reviews = (
            Review.query.filter(Review.is_published.is_(True))
            .order_by(Review.is_featured.desc(), Review.created_at.desc())
            .limit(24)
            .all()
        )
    gallery = (
        GalleryImage.query.filter(
            GalleryImage.is_published.is_(True),
            GalleryImage.is_featured.is_(True),
        )
        .order_by(GalleryImage.sort_order)
        .limit(8)
        .all()
    )
    # Hero slideshow: prefer featured gallery images, else any published gallery photos
    hero_images = (
        GalleryImage.query.filter(
            GalleryImage.is_published.is_(True),
            GalleryImage.is_featured.is_(True),
        )
        .order_by(GalleryImage.sort_order, GalleryImage.id.desc())
        .limit(12)
        .all()
    )
    if not hero_images:
        hero_images = (
            GalleryImage.query.filter(GalleryImage.is_published.is_(True))
            .order_by(GalleryImage.sort_order, GalleryImage.id.desc())
            .limit(12)
            .all()
        )
    services = (
        Service.query.filter(Service.is_published.is_(True), Service.is_featured.is_(True))
        .order_by(Service.sort_order, Service.id)
        .limit(6)
        .all()
    )
    if not services:
        services = (
            Service.query.filter(Service.is_published.is_(True))
            .order_by(Service.sort_order, Service.id)
            .limit(6)
            .all()
        )
    partners = (
        Partner.query.filter(Partner.is_published.is_(True), Partner.is_featured.is_(True))
        .order_by(Partner.sort_order, Partner.id)
        .limit(12)
        .all()
    )
    if not partners:
        partners = (
            Partner.query.filter(Partner.is_published.is_(True))
            .order_by(Partner.sort_order, Partner.id)
            .limit(12)
            .all()
        )
    return render_template(
        "public/home.html",
        featured_tours=featured_tours,
        destinations=destinations,
        reviews=reviews,
        gallery=gallery,
        hero_images=hero_images,
        services=services,
        partners=partners,
        seo={
            "title": "Allied Tours & Travel | Your one-stop travel shop.",
            "description": (
                "Discover unforgettable African travel experiences with Allied Tours & Travel. "
                "Browse tours, request a booking, and receive your invoice."
            ),
        },
    )


@bp.route("/tours")
def tours():
    q = request.args.get("q", "").strip()
    destination_id = request.args.get("destination", type=int)
    category = request.args.get("category", "").strip()
    duration = request.args.get("duration", type=int)
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    sort = request.args.get("sort", "featured")
    page = request.args.get("page", 1, type=int)

    query = _published_tours_query()
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Tour.name.ilike(like), Tour.short_description.ilike(like), Tour.overview.ilike(like))
        )
    if destination_id:
        query = query.filter(Tour.destination_id == destination_id)
    if category:
        query = query.filter(Tour.category == category)
    if duration:
        query = query.filter(Tour.duration_days == duration)
    if min_price is not None:
        query = query.filter(Tour.starting_price >= min_price)
    if max_price is not None:
        query = query.filter(Tour.starting_price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Tour.starting_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Tour.starting_price.desc())
    elif sort == "duration":
        query = query.order_by(Tour.duration_days.asc())
    elif sort == "name":
        query = query.order_by(Tour.name.asc())
    else:
        query = query.order_by(Tour.is_featured.desc(), Tour.updated_at.desc())

    pagination = query.paginate(page=page, per_page=9, error_out=False)
    destinations = (
        Destination.query.filter(
            Destination.is_published.is_(True),
            Destination.archived_at.is_(None),
        )
        .order_by(Destination.name)
        .all()
    )
    categories = (
        db.session.query(Tour.category)
        .filter(Tour.category.isnot(None), Tour.is_published.is_(True))
        .distinct()
        .all()
    )
    return render_template(
        "public/tours.html",
        pagination=pagination,
        tours=pagination.items,
        destinations=destinations,
        categories=[c[0] for c in categories if c[0]],
        filters={
            "q": q,
            "destination": destination_id,
            "category": category,
            "duration": duration,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
        },
        seo={
            "title": "Tours | Allied Tours & Travel",
            "description": "Explore curated African tours and adventures from Allied Tours & Travel.",
        },
    )


@bp.route("/tours/<slug>")
def tour_detail(slug: str):
    tour = _published_tours_query().filter_by(slug=slug).first_or_404()
    departures = (
        Departure.query.filter(
            Departure.tour_id == tour.id,
            Departure.is_active.is_(True),
            Departure.status == "OPEN",
            Departure.departure_date >= date.today(),
        )
        .order_by(Departure.departure_date.asc())
        .all()
    )
    reviews = (
        Review.query.filter(
            Review.tour_id == tour.id,
            Review.is_published.is_(True),
        )
        .order_by(Review.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "public/tour_detail.html",
        tour=tour,
        departures=departures,
        reviews=reviews,
        seo={
            "title": tour.seo_title or f"{tour.name} | Allied Tours & Travel",
            "description": tour.seo_description or tour.short_description,
            "og_image": tour.og_image or tour.hero_image,
            "canonical": url_for("public.tour_detail", slug=tour.slug, _external=True),
        },
    )


@bp.route("/destinations")
def destinations():
    items = (
        Destination.query.filter(
            Destination.is_published.is_(True),
            Destination.archived_at.is_(None),
        )
        .order_by(Destination.sort_order, Destination.name)
        .all()
    )
    return render_template(
        "public/destinations.html",
        destinations=items,
        seo={
            "title": "Destinations | Allied Tours & Travel",
            "description": "Discover destinations offered by Allied Tours & Travel.",
        },
    )


@bp.route("/destinations/<slug>")
def destination_detail(slug: str):
    destination = Destination.query.filter(
        Destination.slug == slug,
        Destination.is_published.is_(True),
        Destination.archived_at.is_(None),
    ).first_or_404()
    tours = (
        _published_tours_query()
        .filter(Tour.destination_id == destination.id)
        .order_by(Tour.is_featured.desc(), Tour.name)
        .all()
    )
    return render_template(
        "public/destination_detail.html",
        destination=destination,
        tours=tours,
        seo={
            "title": destination.seo_title or f"{destination.name} | Allied Tours & Travel",
            "description": destination.seo_description or destination.short_description,
            "og_image": destination.og_image or destination.hero_image,
        },
    )


@bp.route("/book/<slug>", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def book_tour(slug: str):
    tour = _published_tours_query().filter_by(slug=slug).first_or_404()
    departures = (
        Departure.query.filter(
            Departure.tour_id == tour.id,
            Departure.is_active.is_(True),
            Departure.status == "OPEN",
            Departure.departure_date >= date.today(),
        )
        .order_by(Departure.departure_date.asc())
        .all()
    )
    bookable = [d for d in departures if d.available_seats > 0]
    form = BookingForm()
    form.departure_id.choices = [
        (
            d.id,
            f"{d.departure_date.strftime('%d %B %Y')} — {d.available_seats} seats — "
            f"{tour.currency} {d.price_adult:,.0f}",
        )
        for d in bookable
    ]

    if request.method == "GET":
        form.submission_token.data = generate_token()
        preselect = request.args.get("departure", type=int)
        if preselect and any(d.id == preselect for d in bookable):
            form.departure_id.data = preselect

    if form.validate_on_submit():
        try:
            booking = BookingService.create_booking(
                departure_id=form.departure_id.data,
                full_name=form.full_name.data,
                email=form.email.data,
                phone=form.phone.data,
                country=form.country.data,
                adults=form.adults.data,
                children=form.children.data or 0,
                pickup_location=form.pickup_location.data,
                special_requests=form.special_requests.data,
                submission_token=form.submission_token.data,
            )
            return redirect(
                url_for(
                    "public.booking_confirmation",
                    reference=booking.reference,
                    token=BookingService.confirmation_token(booking.reference),
                )
            )
        except BookingError as exc:
            flash(str(exc), "danger")

    return render_template(
        "public/book.html",
        tour=tour,
        form=form,
        departures=bookable,
        seo={
            "title": f"Book {tour.name} | Allied Tours & Travel",
            "description": "Submit a booking request. No payment is required at this step.",
        },
    )


@bp.route("/booking-confirmation/<reference>")
@limiter.limit("30 per hour")
def booking_confirmation(reference: str):
    token = request.args.get("token")
    if not BookingService.verify_confirmation_token(reference, token):
        flash("Use Check Booking with your reference and email/phone to view booking details.", "warning")
        return redirect(url_for("public.check_booking"))
    booking = Booking.query.filter_by(reference=reference).first_or_404()
    return render_template(
        "public/booking_confirmation.html",
        booking=booking,
        seo={"title": f"Booking Received — {booking.reference}", "noindex": True},
    )


@bp.route("/check-booking", methods=["GET", "POST"])
@limiter.limit("30 per hour")
def check_booking():
    form = CheckBookingForm()
    booking = None
    if form.validate_on_submit():
        from app.utils.sanitize import normalize_phone

        reference = form.reference.data.strip().upper()
        contact = form.contact.data.strip().lower()
        candidate = Booking.query.filter_by(reference=reference).first()
        if candidate and candidate.customer:
            email = (candidate.customer.email or "").lower().strip()
            phone_digits = normalize_phone(candidate.customer.phone)
            contact_digits = normalize_phone(contact)
            if contact == email or (contact_digits and contact_digits == phone_digits):
                booking = candidate
        if not booking:
            flash("No booking found for that reference and contact details.", "warning")
    return render_template(
        "public/check_booking.html",
        form=form,
        booking=booking,
        seo={
            "title": "Check Booking | Allied Tours & Travel",
            "description": "Look up your Allied Tours & Travel booking status using your booking reference.",
        },
    )


@bp.route("/about")
def about():
    return render_template(
        "public/about.html",
        seo={
            "title": "About Us | Allied Tours & Travel",
            "description": "Learn about Allied Tours & Travel — your one-stop travel shop.",
        },
    )


@bp.route("/services")
def services():
    items = (
        _published_services_query()
        .order_by(Service.sort_order, Service.id)
        .all()
    )
    return render_template(
        "public/services.html",
        services=items,
        seo={
            "title": "Our Services | Allied Tours & Travel",
            "description": "Air Ticketing (AT), Visa Services (VS), and Travel Insurance from Allied Tours & Travel.",
        },
    )


@bp.route("/services/<slug>")
def service_detail(slug: str):
    service = _published_services_query().filter_by(slug=slug).first_or_404()
    return render_template(
        "public/service_detail.html",
        service=service,
        seo={
            "title": service.seo_title or f"{service.name} | Allied Tours & Travel",
            "description": service.seo_description
            or service.short_description
            or service.description,
            "og_image": service.hero_image or service.icon_image,
        },
    )


@bp.route("/services/<slug>/book", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def book_service(slug: str):
    service = (
        _published_services_query()
        .filter_by(slug=slug, is_bookable=True)
        .first_or_404()
    )
    form = ServiceBookingForm()
    if request.method == "GET":
        form.submission_token.data = generate_token()

    if form.validate_on_submit():
        try:
            booking = BookingService.create_service_booking(
                service_id=service.id,
                full_name=form.full_name.data,
                email=form.email.data,
                phone=form.phone.data,
                country=form.country.data,
                travelers=form.travelers.data,
                preferred_travel_date=form.preferred_travel_date.data,
                destination_country=form.destination_country.data,
                special_requests=form.special_requests.data,
                submission_token=form.submission_token.data,
            )
            return redirect(
                url_for(
                    "public.booking_confirmation",
                    reference=booking.reference,
                    token=BookingService.confirmation_token(booking.reference),
                )
            )
        except BookingError as exc:
            flash(str(exc), "danger")

    return render_template(
        "public/book_service.html",
        service=service,
        form=form,
        seo={
            "title": f"Book {service.name} | Allied Tours & Travel",
            "description": "Submit a service request. No payment is required at this step.",
        },
    )


@bp.route("/partners")
def partners():
    items = (
        Partner.query.filter(Partner.is_published.is_(True))
        .order_by(Partner.sort_order, Partner.id)
        .all()
    )
    return render_template(
        "public/partners.html",
        partners=items,
        seo={
            "title": "Our Partners | Allied Tours & Travel",
            "description": "Trusted partners of Allied Tours & Travel.",
        },
    )


@bp.route("/gallery")
def gallery():
    images = (
        GalleryImage.query.filter(GalleryImage.is_published.is_(True))
        .order_by(GalleryImage.sort_order, GalleryImage.created_at.desc())
        .all()
    )
    return render_template(
        "public/gallery.html",
        images=images,
        seo={
            "title": "Gallery | Allied Tours & Travel",
            "description": "Travel moments and destinations from Allied Tours & Travel.",
        },
    )


@bp.route("/blog")
def blog():
    page = request.args.get("page", 1, type=int)
    pagination = (
        BlogPost.query.filter(BlogPost.is_published.is_(True))
        .order_by(BlogPost.published_at.desc(), BlogPost.created_at.desc())
        .paginate(page=page, per_page=9, error_out=False)
    )
    return render_template(
        "public/blog.html",
        pagination=pagination,
        posts=pagination.items,
        seo={
            "title": "Blog | Allied Tours & Travel",
            "description": "Travel tips and destination stories from Allied Tours & Travel.",
        },
    )


@bp.route("/blog/<slug>")
def blog_detail(slug: str):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template(
        "public/blog_detail.html",
        post=post,
        seo={
            "title": post.seo_title or f"{post.title} | Allied Tours & Travel",
            "description": post.seo_description or post.excerpt,
            "og_image": post.og_image or post.featured_image,
        },
    )


@bp.route("/faqs")
def faqs():
    items = (
        FAQ.query.filter(FAQ.is_published.is_(True))
        .order_by(FAQ.sort_order, FAQ.id)
        .all()
    )
    return render_template(
        "public/faqs.html",
        faqs=items,
        seo={
            "title": "FAQs | Allied Tours & Travel",
            "description": "Frequently asked questions about booking with Allied Tours & Travel.",
        },
    )


@bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Email company inbox if configured; never create client accounts
        subject_raw = (form.subject.data or "").replace("\r", " ").replace("\n", " ").strip()
        try:
            EmailService.send(
                subject=f"Contact: {subject_raw[:180]}",
                recipients=[current_app.config.get("COMPANY_EMAIL")],
                template="emails/contact_message.html",
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                subject_line=subject_raw,
                message=form.message.data,
            )
        except Exception:  # noqa: BLE001
            current_app.logger.exception("Contact form email failed")
        flash("Thank you. Your message has been sent. We will get back to you shortly.", "success")
        return redirect(url_for("public.contact"))
    return render_template(
        "public/contact.html",
        form=form,
        seo={
            "title": "Contact Us | Allied Tours & Travel",
            "description": "Contact Allied Tours & Travel for tour enquiries and booking support.",
        },
    )


@bp.route("/terms")
def terms():
    return render_template(
        "public/terms.html",
        seo={"title": "Terms & Conditions | Allied Tours & Travel"},
    )


@bp.route("/privacy")
def privacy():
    return render_template(
        "public/privacy.html",
        seo={"title": "Privacy Policy | Allied Tours & Travel"},
    )


@bp.route("/robots.txt")
def robots():
    body = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /check-booking
Sitemap: {url_for('public.sitemap', _external=True)}
"""
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    urls = [
        url_for("public.home", _external=True),
        url_for("public.tours", _external=True),
        url_for("public.destinations", _external=True),
        url_for("public.about", _external=True),
        url_for("public.services", _external=True),
        url_for("public.partners", _external=True),
        url_for("public.gallery", _external=True),
        url_for("public.blog", _external=True),
        url_for("public.faqs", _external=True),
        url_for("public.contact", _external=True),
        url_for("public.terms", _external=True),
        url_for("public.privacy", _external=True),
    ]
    for tour in _published_tours_query().all():
        urls.append(url_for("public.tour_detail", slug=tour.slug, _external=True))
    for dest in Destination.query.filter_by(is_published=True).all():
        urls.append(url_for("public.destination_detail", slug=dest.slug, _external=True))
    for service in _published_services_query().all():
        urls.append(url_for("public.service_detail", slug=service.slug, _external=True))
    for post in BlogPost.query.filter_by(is_published=True).all():
        urls.append(url_for("public.blog_detail", slug=post.slug, _external=True))

    xml_items = "\n".join(
        f"<url><loc>{u}</loc><changefreq>weekly</changefreq></url>" for u in urls
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{xml_items}</urlset>'
    return Response(xml, mimetype="application/xml")
