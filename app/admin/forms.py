"""Admin portal forms."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, MultipleFileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    EmailField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError


def strong_password(form, field):
    """Require length + mixed character classes for admin passwords."""
    value = field.data or ""
    if not value:
        return
    if len(value) < 12:
        raise ValidationError("Password must be at least 12 characters.")
    classes = sum(
        [
            any(c.islower() for c in value),
            any(c.isupper() for c in value),
            any(c.isdigit() for c in value),
            any(not c.isalnum() for c in value),
        ]
    )
    if classes < 3:
        raise ValidationError(
            "Password must include at least 3 of: lowercase, uppercase, digit, symbol."
        )


class TourForm(FlaskForm):
    name = StringField("Tour Name", validators=[DataRequired(), Length(max=200)])
    slug = StringField("Slug", validators=[Optional(), Length(max=220)])
    destination_id = SelectField("Destination", coerce=int, validators=[DataRequired()])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    short_description = StringField("Short Description", validators=[Optional(), Length(max=400)])
    overview = TextAreaField("Overview", validators=[Optional()])
    duration_days = IntegerField("Duration (days)", validators=[DataRequired(), NumberRange(min=1)])
    duration_nights = IntegerField("Duration (nights)", validators=[Optional(), NumberRange(min=0)], default=0)
    starting_price = DecimalField("Starting Price", validators=[DataRequired()])
    currency = StringField("Currency", validators=[DataRequired(), Length(max=8)], default="KES")
    default_capacity = IntegerField("Default Capacity", validators=[DataRequired(), NumberRange(min=1)])
    pickup_info = TextAreaField("Pickup Information", validators=[Optional()])
    hero_image_file = FileField(
        "Hero Image",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only")],
    )
    map_embed_url = StringField("Map Embed URL", validators=[Optional(), Length(max=500)])
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published")
    seo_title = StringField("SEO Title", validators=[Optional(), Length(max=180)])
    seo_description = StringField("SEO Description", validators=[Optional(), Length(max=320)])
    inclusions_text = TextAreaField("Inclusions (one per line)", validators=[Optional()])
    exclusions_text = TextAreaField("Exclusions (one per line)", validators=[Optional()])
    submit = SubmitField("Save Tour")


class DestinationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=160)])
    slug = StringField("Slug", validators=[Optional(), Length(max=180)])
    short_description = StringField("Short Description", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Description", validators=[Optional()])
    attractions = TextAreaField("Attractions", validators=[Optional()])
    travel_info = TextAreaField("Travel Information", validators=[Optional()])
    country = StringField("Country", validators=[Optional(), Length(max=120)])
    region = StringField("Region", validators=[Optional(), Length(max=120)])
    map_embed_url = StringField("Map Embed URL", validators=[Optional(), Length(max=500)])
    hero_image_file = FileField(
        "Hero Image",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only")],
    )
    is_featured = BooleanField("Featured")
    is_published = BooleanField("Published")
    sort_order = IntegerField("Sort Order", validators=[Optional()], default=0)
    seo_title = StringField("SEO Title", validators=[Optional(), Length(max=180)])
    seo_description = StringField("SEO Description", validators=[Optional(), Length(max=320)])
    submit = SubmitField("Save Destination")


class DepartureForm(FlaskForm):
    tour_id = SelectField("Tour", coerce=int, validators=[DataRequired()])
    departure_date = DateField("Departure Date", validators=[DataRequired()])
    return_date = DateField("Return Date", validators=[Optional()])
    capacity = IntegerField("Capacity", validators=[DataRequired(), NumberRange(min=1)])
    price_adult = DecimalField("Adult Price", validators=[DataRequired()])
    price_child = DecimalField("Child Price", validators=[Optional()])
    status = SelectField(
        "Status",
        choices=[
            ("OPEN", "Open"),
            ("CLOSED", "Closed"),
            ("CANCELLED", "Cancelled"),
            ("COMPLETED", "Completed"),
        ],
        validators=[DataRequired()],
    )
    notes = StringField("Notes", validators=[Optional(), Length(max=500)])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Departure")


class BookingStatusForm(FlaskForm):
    booking_status = SelectField(
        "Booking Status",
        choices=[
            ("NEW", "New"),
            ("UNDER_REVIEW", "Under Review"),
            ("INVOICED", "Invoiced"),
            ("CONFIRMED", "Confirmed"),
            ("CANCELLED", "Cancelled"),
            ("COMPLETED", "Completed"),
        ],
        validators=[DataRequired()],
    )
    admin_notes = TextAreaField("Admin Notes", validators=[Optional()])
    submit = SubmitField("Update Booking")


class InvoiceCreateForm(FlaskForm):
    discount = DecimalField("Discount", validators=[Optional()], default=0)
    due_days = IntegerField("Due in (days)", validators=[DataRequired(), NumberRange(min=1)], default=7)
    payment_instructions = TextAreaField("Payment Instructions", validators=[Optional()])
    terms = TextAreaField("Terms", validators=[Optional()])
    submit = SubmitField("Generate Invoice")


class InvoiceEditForm(FlaskForm):
    """Meta fields for draft/sent invoice edits. Line items are posted as lists."""

    discount = DecimalField("Discount", validators=[Optional()], default=0)
    due_date = DateField("Due Date", validators=[Optional()])
    payment_instructions = TextAreaField("Payment Instructions", validators=[Optional()])
    terms = TextAreaField("Terms", validators=[Optional()])
    notes = TextAreaField("Internal Notes", validators=[Optional()])
    submit = SubmitField("Save Invoice Details")


class RolePermissionsForm(FlaskForm):
    submit = SubmitField("Save Permissions")


class PaymentForm(FlaskForm):
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)])
    method = SelectField(
        "Payment Method",
        choices=[
            ("M-Pesa", "M-Pesa"),
            ("Bank Transfer", "Bank Transfer"),
            ("Cash", "Cash"),
            ("Card", "Card"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()],
    )
    payment_date = DateField("Payment Date", validators=[DataRequired()])
    transaction_reference = StringField("Transaction Reference", validators=[Optional(), Length(max=120)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Record Payment")


class CustomerForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=40)])
    country = StringField("Country", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Save Customer")


class BlogPostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=220)])
    slug = StringField("Slug", validators=[Optional(), Length(max=240)])
    excerpt = StringField("Excerpt", validators=[Optional(), Length(max=400)])
    body = TextAreaField("Body", validators=[DataRequired()])
    featured_image_file = FileField(
        "Featured Image",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only")],
    )
    is_published = BooleanField("Published")
    seo_title = StringField("SEO Title", validators=[Optional(), Length(max=180)])
    seo_description = StringField("SEO Description", validators=[Optional(), Length(max=320)])
    submit = SubmitField("Save Post")


class ReviewForm(FlaskForm):
    customer_name = StringField("Customer Name", validators=[DataRequired(), Length(max=160)])
    rating = IntegerField("Rating (1-5)", validators=[DataRequired(), NumberRange(min=1, max=5)])
    body = TextAreaField("Review", validators=[DataRequired()])
    tour_id = SelectField("Tour", coerce=int, validators=[Optional()])
    is_published = BooleanField("Published")
    is_featured = BooleanField("Featured")
    submit = SubmitField("Save Testimonial")


class GalleryForm(FlaskForm):
    title = StringField("Title / Prefix", validators=[Optional(), Length(max=200)])
    alt_text = StringField("Alt Text", validators=[Optional(), Length(max=200)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    sort_order = IntegerField("Sort Order", default=0)
    is_published = BooleanField("Published", default=True)
    is_featured = BooleanField("Featured on homepage gallery")
    is_hero = BooleanField("Show on homepage hero")
    image_files = MultipleFileField(
        "Photos & Videos",
        render_kw={
            "multiple": True,
            "accept": (
                ".jpg,.jpeg,.png,.webp,.mp4,.webm,.mov,"
                "image/jpeg,image/png,image/webp,video/mp4,video/webm,video/quicktime"
            ),
        },
        validators=[
            FileAllowed(
                ["jpg", "jpeg", "png", "webp", "mp4", "webm", "mov"],
                "Images (JPG/PNG/WEBP) or videos (MP4/WebM/MOV) only",
            ),
        ],
    )
    submit = SubmitField("Upload Media")


class GalleryEditForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    alt_text = StringField("Alt Text", validators=[Optional(), Length(max=200)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    sort_order = IntegerField("Sort Order", default=0)
    is_published = BooleanField("Published", default=True)
    is_featured = BooleanField("Featured on homepage gallery")
    is_hero = BooleanField("Show on homepage hero")
    image_file = FileField(
        "Replace Media",
        validators=[
            Optional(),
            FileAllowed(
                ["jpg", "jpeg", "png", "webp", "mp4", "webm", "mov"],
                "Images (JPG/PNG/WEBP) or videos (MP4/WebM/MOV) only",
            ),
        ],
    )
    submit = SubmitField("Save Changes")


class FAQForm(FlaskForm):
    question = StringField("Question", validators=[DataRequired(), Length(max=300)])
    answer = TextAreaField("Answer", validators=[DataRequired()])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    sort_order = IntegerField("Sort Order", default=0)
    is_published = BooleanField("Published", default=True)
    submit = SubmitField("Save FAQ")


class ServiceForm(FlaskForm):
    name = StringField("Service Name", validators=[DataRequired(), Length(max=160)])
    short_description = StringField("Short Description", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Summary", validators=[Optional()])
    overview = TextAreaField("Overview", validators=[Optional()])
    highlights = TextAreaField("Highlights (one per line)", validators=[Optional()])
    what_is_included = TextAreaField("What Is Included (one per line)", validators=[Optional()])
    how_it_works = TextAreaField("How It Works (one per line)", validators=[Optional()])
    who_its_for = TextAreaField("Who It's For", validators=[Optional()])
    important_notes = TextAreaField("Important Notes", validators=[Optional()])
    icon_image = FileField(
        "Icon / Image",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only"),
        ],
    )
    hero_image = FileField(
        "Hero Image",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only"),
        ],
    )
    seo_title = StringField("SEO Title", validators=[Optional(), Length(max=200)])
    seo_description = StringField("SEO Description", validators=[Optional(), Length(max=320)])
    sort_order = IntegerField("Sort Order", default=0)
    is_published = BooleanField("Published", default=True)
    is_featured = BooleanField("Show on homepage", default=False)
    is_bookable = BooleanField("Allow online booking requests", default=True)
    submit = SubmitField("Save Service")


class PartnerForm(FlaskForm):
    name = StringField("Partner Name", validators=[DataRequired(), Length(max=160)])
    website_url = StringField("Website URL", validators=[Optional(), Length(max=500)])
    description = StringField("Short Note", validators=[Optional(), Length(max=300)])
    logo = FileField(
        "Logo",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only"),
        ],
    )
    sort_order = IntegerField("Sort Order", default=0)
    is_published = BooleanField("Published", default=True)
    is_featured = BooleanField("Show on homepage", default=False)
    submit = SubmitField("Save Partner")


class AdminUserForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    role_id = SelectField("Role", coerce=int, validators=[DataRequired()])
    password = PasswordField(
        "Password",
        validators=[Optional(), Length(min=12, max=128), strong_password],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[Optional(), EqualTo("password", message="Passwords must match")],
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Admin")


class SettingsForm(FlaskForm):
    company_email = StringField("Company Email", validators=[Optional(), Length(max=255)])
    company_phone = StringField("Company Phone", validators=[Optional(), Length(max=80)])
    company_address = StringField("Company Address", validators=[Optional(), Length(max=255)])
    payment_instructions = TextAreaField("Default Payment Instructions", validators=[Optional()])
    submit = SubmitField("Save Settings")
