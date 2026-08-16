"""Seed roles, permissions, demo admins, and sample content.

Demo content is clearly labeled. Do not treat demo testimonials as production social proof.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import (
    FAQ,
    Admin,
    BlogPost,
    Departure,
    Destination,
    GalleryImage,
    Partner,
    Permission,
    Review,
    Role,
    Service,
    Setting,
    Tour,
    TourExclusion,
    TourInclusion,
    TourItinerary,
)
from app.utils.permissions import PERMISSIONS, ROLE_PERMISSION_MAP


def _ensure_permissions() -> dict[str, Permission]:
    mapping: dict[str, Permission] = {}
    for code, name, category in PERMISSIONS:
        perm = Permission.query.filter_by(code=code).first()
        if not perm:
            perm = Permission(code=code, name=name, category=category, description=name)
            db.session.add(perm)
        mapping[code] = perm
    db.session.flush()
    return mapping


def _ensure_roles(perms: dict[str, Permission]) -> dict[str, Role]:
    role_meta = {
        "super-admin": ("Super Admin", "Full system access"),
        "operations-manager": ("Operations Manager", "Tours, departures, and bookings operations"),
        "booking-manager": ("Booking Manager", "Booking and invoice operations"),
        "finance": ("Finance", "Invoices, payments, and financial reports"),
        "content-manager": ("Content Manager", "Website content and media"),
    }
    roles: dict[str, Role] = {}
    for slug, (name, desc) in role_meta.items():
        role = Role.query.filter_by(slug=slug).first()
        if not role:
            role = Role(name=name, slug=slug, description=desc, is_system=True)
            db.session.add(role)
            db.session.flush()
        role.permissions = [perms[code] for code in ROLE_PERMISSION_MAP[slug] if code in perms]
        roles[slug] = role
    db.session.flush()
    return roles


def _ensure_admins(roles: dict[str, Role]) -> None:
    """Create admin users.

    Production-safe defaults:
    - Demo role accounts are created only when SEED_DEMO_USERS=true
    - Super Admin is created when missing if SEED_ADMIN_EMAIL + SEED_ADMIN_PASSWORD are set
      (development falls back to example credentials for local bootstrap only)
    """
    seed_demo = os.getenv("SEED_DEMO_USERS", "false").lower() in {"1", "true", "yes"}
    env = os.getenv("FLASK_ENV", "development").lower()

    super_email = os.getenv("SEED_ADMIN_EMAIL", "").strip().lower()
    super_password = os.getenv("SEED_ADMIN_PASSWORD", "").strip()
    if env == "development" and not super_email:
        super_email = "admin@alliedtours.example"
        super_password = super_password or "ChangeMeNow!123"

    defaults: list[tuple[str, str, str, str]] = []
    if super_email and super_password:
        defaults.append((super_email, super_password, "Super Admin", "super-admin"))

    if seed_demo:
        defaults.extend(
            [
                ("ops@alliedtours.example", "OpsDemo!12345", "Operations Manager", "operations-manager"),
                ("bookings@alliedtours.example", "BookDemo!12345", "Booking Manager", "booking-manager"),
                ("finance@alliedtours.example", "FinanceDemo!123", "Finance Officer", "finance"),
                ("content@alliedtours.example", "ContentDemo!123", "Content Manager", "content-manager"),
            ]
        )

    for email, password, full_name, role_slug in defaults:
        admin = Admin.query.filter_by(email=email).first()
        if not admin:
            admin = Admin(
                email=email,
                full_name=full_name,
                role_id=roles[role_slug].id,
                is_active=True,
            )
            admin.set_password(password)
            db.session.add(admin)


def _seed_services_and_partners() -> None:
    """Idempotent seed for services/partners (works on existing databases)."""
def _service_catalog() -> list[dict]:
    return [
        {
            "name": "Air Ticketing (AT)",
            "slug": "air-ticketing",
            "short_description": "Domestic and international flight bookings at competitive fares.",
            "description": "Flight booking support for leisure, family, group, and corporate travel.",
            "overview": (
                "Allied Tours & Travel helps you secure domestic and international air tickets "
                "with clear options on routes, schedules, and fares. Whether you are travelling alone, "
                "with family, or as a corporate group, we handle the ticketing process so you can focus on your trip."
            ),
            "highlights": "Domestic and international routes\nFlexible date options\nGroup and corporate bookings\nItinerary coordination support",
            "what_is_included": "Fare search and options\nBooking and ticketing assistance\nTravel document checklist guidance\nPost-booking support for changes where available",
            "how_it_works": "Submit a service request with travel dates and destination\nWe review routes and fare options\nYou receive a quote/invoice\nOnce payment is confirmed, tickets are processed",
            "who_its_for": "Individuals, families, groups, corporates, and business travellers who need reliable flight arrangements.",
            "important_notes": "Final ticket prices depend on airline availability, season, and fare rules. Changes and cancellations follow airline policy.",
            "sort_order": 1,
        },
        {
            "name": "Visa Services (VS)",
            "slug": "visa-services",
            "short_description": "Guided visa application support for your destination.",
            "description": "Visa guidance and application support for your travel destination.",
            "overview": (
                "Our Visa Services team guides you through destination requirements, documentation, "
                "and application steps. We help reduce uncertainty around paperwork so your travel plans stay on track."
            ),
            "highlights": "Destination requirement guidance\nDocument checklist support\nApplication process assistance\nFollow-up communication",
            "what_is_included": "Visa category guidance based on travel purpose\nDocument preparation support\nApplication submission guidance\nStatus follow-up where applicable",
            "how_it_works": "Tell us your destination and travel purpose\nWe outline requirements and next steps\nYou submit documents and we support the process\nWe update you as the application progresses",
            "who_its_for": "Travellers who need visa support for leisure, study visits, conferences, or business travel.",
            "important_notes": "Visa approval is determined by the relevant embassy/immigration authority. Processing times and requirements can change.",
            "sort_order": 2,
        },
        {
            "name": "Travel Insurance",
            "slug": "travel-insurance",
            "short_description": "Travel cover options for peace of mind on every trip.",
            "description": "Travel insurance options matched to your itinerary and traveler needs.",
            "overview": (
                "Protect your journey with travel insurance options arranged around your itinerary, "
                "destination, and trip duration. We help you understand cover choices before you travel."
            ),
            "highlights": "Cover options for leisure and business trips\nSupport for individuals and groups\nGuidance on policy choices\nAssistance before departure",
            "what_is_included": "Needs assessment based on trip details\nRecommended cover options\nPolicy arrangement support\nPre-travel clarification of key terms",
            "how_it_works": "Share your travel dates and destination\nWe recommend suitable cover options\nYou receive a quote/invoice\nPolicy is arranged after confirmation",
            "who_its_for": "Anyone seeking travel protection for local or international journeys.",
            "important_notes": "Cover terms, exclusions, and claims processes are defined by the insurer. Always review policy documents carefully.",
            "sort_order": 3,
        },
    ]


def _seed_services_and_partners() -> None:
    """Idempotent seed/enrichment for services and partners."""
    catalog = _service_catalog()
    if not Service.query.count():
        for item in catalog:
            db.session.add(
                Service(
                    **item,
                    is_published=True,
                    is_featured=True,
                    is_bookable=True,
                )
            )
    else:
        for item in catalog:
            service = Service.query.filter_by(slug=item["slug"]).first()
            if not service:
                db.session.add(
                    Service(
                        **item,
                        is_published=True,
                        is_featured=True,
                        is_bookable=True,
                    )
                )
                continue
            # Enrich existing rows that still lack detail pages content
            if not service.overview:
                for key, value in item.items():
                    if key in {"name", "slug"}:
                        continue
                    setattr(service, key, value)
                service.is_bookable = True
                service.is_published = True
                service.is_featured = True

    if not Partner.query.count():
        db.session.add_all(
            [
                Partner(
                    name="Demo Lodge Partner",
                    logo_path="assets/brand/logo-dark.png",
                    description="DEMO partner — replace with a real partner logo before production.",
                    sort_order=1,
                    is_published=True,
                    is_featured=True,
                ),
                Partner(
                    name="Demo Airline Partner",
                    logo_path="assets/brand/logo-dark.png",
                    description="DEMO partner — replace with a real partner logo before production.",
                    sort_order=2,
                    is_published=True,
                    is_featured=True,
                ),
            ]
        )


def _seed_content() -> None:
    if Destination.query.count():
        _seed_services_and_partners()
        return

    mara = Destination(
        name="Maasai Mara",
        slug="maasai-mara",
        short_description="Kenya’s iconic savannah home to the Great Migration.",
        description=(
            "The Maasai Mara is one of Africa’s most celebrated wildlife destinations, "
            "known for open plains, big cats, and Maasai culture."
        ),
        attractions="Game drives, balloon safaris, cultural visits",
        travel_info="Best visited during the dry season and migration months (July–October).",
        country="Kenya",
        region="Narok",
        is_featured=True,
        is_published=True,
        sort_order=1,
        seo_title="Maasai Mara Tours | Allied Tours & Travel",
        seo_description="Explore Maasai Mara safari experiences with Allied Tours & Travel.",
    )
    amboseli = Destination(
        name="Amboseli",
        slug="amboseli",
        short_description="Elephants beneath the majestic Mount Kilimanjaro.",
        description="Amboseli National Park offers sweeping views of Kilimanjaro and large elephant herds.",
        attractions="Elephant viewing, photography, mountain vistas",
        travel_info="Year-round destination with excellent visibility in the dry months.",
        country="Kenya",
        region="Kajiado",
        is_featured=True,
        is_published=True,
        sort_order=2,
    )
    coast = Destination(
        name="Kenyan Coast",
        slug="kenyan-coast",
        short_description="White sands, Swahili culture, and Indian Ocean breezes.",
        description="From Diani to Watamu, the Kenyan coast blends beaches, reefs, and coastal heritage.",
        attractions="Beaches, snorkeling, dhow cruises",
        travel_info="Ideal for beach extensions after safari itineraries.",
        country="Kenya",
        region="Coast",
        is_featured=True,
        is_published=True,
        sort_order=3,
    )
    db.session.add_all([mara, amboseli, coast])
    db.session.flush()

    safari = Tour(
        name="Maasai Mara Safari",
        slug="maasai-mara-safari",
        short_description="A classic 3-day safari through the Mara plains.",
        overview=(
            "Experience game drives across the Maasai Mara with professional guides. "
            "This DEMO tour is provided for development and staging only."
        ),
        category="Safari",
        duration_days=3,
        duration_nights=2,
        starting_price=Decimal("45000"),
        currency="KES",
        default_capacity=20,
        pickup_info="Hotel pickup in Nairobi at 07:00.",
        is_featured=True,
        is_published=True,
        destination_id=mara.id,
        seo_title="Maasai Mara Safari | Allied Tours & Travel",
        seo_description="Book a Maasai Mara safari request with Allied Tours & Travel.",
    )
    beach = Tour(
        name="Diani Beach Escape",
        slug="diani-beach-escape",
        short_description="Sun, sand, and coastal relaxation on Diani Beach.",
        overview="A DEMO beach package showcasing Allied coastal itineraries.",
        category="Beach",
        duration_days=4,
        duration_nights=3,
        starting_price=Decimal("38000"),
        currency="KES",
        default_capacity=16,
        pickup_info="Airport or hotel transfer on the south coast.",
        is_featured=True,
        is_published=True,
        destination_id=coast.id,
    )
    amboseli_tour = Tour(
        name="Amboseli Elephant Encounter",
        slug="amboseli-elephant-encounter",
        short_description="Two nights among Amboseli’s elephant herds.",
        overview="DEMO itinerary featuring Amboseli game drives and Kilimanjaro views.",
        category="Safari",
        duration_days=3,
        duration_nights=2,
        starting_price=Decimal("42000"),
        currency="KES",
        default_capacity=18,
        pickup_info="Nairobi pickup available on request.",
        is_featured=False,
        is_published=True,
        destination_id=amboseli.id,
    )
    db.session.add_all([safari, beach, amboseli_tour])
    db.session.flush()

    for day, title, desc in [
        (1, "Nairobi to Maasai Mara", "Scenic drive to the Mara and afternoon game drive."),
        (2, "Full Day Game Drives", "Morning and afternoon wildlife viewing across the reserve."),
        (3, "Final Drive & Return", "Early game drive then return to Nairobi."),
    ]:
        db.session.add(
            TourItinerary(tour_id=safari.id, day_number=day, title=title, description=desc)
        )
    for i, item in enumerate(["Park fees", "Transport", "Accommodation", "Meals as indicated"]):
        db.session.add(TourInclusion(tour_id=safari.id, item=item, sort_order=i))
    for i, item in enumerate(["International flights", "Travel insurance", "Personal expenses"]):
        db.session.add(TourExclusion(tour_id=safari.id, item=item, sort_order=i))

    today = date.today()
    for tour, offset, capacity, price in [
        (safari, 30, 20, Decimal("45000")),
        (safari, 45, 20, Decimal("48000")),
        (beach, 40, 16, Decimal("38000")),
        (amboseli_tour, 35, 18, Decimal("42000")),
    ]:
        db.session.add(
            Departure(
                tour_id=tour.id,
                departure_date=today + timedelta(days=offset),
                return_date=today + timedelta(days=offset + tour.duration_days - 1),
                capacity=capacity,
                price_adult=price,
                price_child=price * Decimal("0.7"),
                status="OPEN",
                is_active=True,
            )
        )

    db.session.add(
        Review(
            customer_name="Demo Traveler",
            rating=5,
            body=(
                "DEMO TESTIMONIAL — Replace with genuine guest feedback before production. "
                "Sample review for UI demonstration only."
            ),
            tour_id=safari.id,
            is_published=True,
            is_featured=True,
            is_demo=True,
        )
    )
    db.session.add_all(
        [
            FAQ(
                question="Do I pay when I submit a booking?",
                answer=(
                    "No. Submitting a booking creates a request only. Allied Tours & Travel "
                    "reviews your request and sends an invoice with payment instructions."
                ),
                category="Booking",
                sort_order=1,
                is_published=True,
            ),
            FAQ(
                question="How do I check my booking status?",
                answer="Use the Check Booking page with your booking reference and email or phone number.",
                category="Booking",
                sort_order=2,
                is_published=True,
            ),
            BlogPost(
                title="Planning Your First Kenya Safari (Demo)",
                slug="planning-your-first-kenya-safari-demo",
                excerpt="DEMO article — practical tips for first-time safari travelers.",
                body=(
                    "<p>This is demo content for Allied Tours & Travel. "
                    "Replace with original editorial before going live.</p>"
                    "<p>Consider seasonality, packing lists, and realistic daily itineraries.</p>"
                ),
                is_published=True,
                is_demo=True,
                seo_title="Planning Your First Kenya Safari | Allied Tours & Travel",
                seo_description="Demo travel tips article for Allied Tours & Travel.",
            ),
            GalleryImage(
                title="Demo — Savannah Morning",
                image_path="assets/brand/logo-dark.png",
                alt_text="Allied Tours & Travel branding placeholder",
                category="Company",
                sort_order=1,
                is_published=True,
                is_featured=True,
            ),
            Setting(
                key="payment_instructions",
                value=(
                    "Pay via M-Pesa or bank transfer using your booking reference as the narration. "
                    "Share confirmation with Allied Tours & Travel for verification."
                ),
                description="Default invoice payment instructions",
            ),
        ]
    )
    _seed_services_and_partners()


def run_seed() -> None:
    perms = _ensure_permissions()
    roles = _ensure_roles(perms)
    _ensure_admins(roles)
    _seed_content()
    db.session.commit()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        run_seed()
        print("Seed complete.")
