"""Public website forms."""

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    EmailField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional


class BookingForm(FlaskForm):
    departure_id = SelectField("Departure Date", coerce=int, validators=[DataRequired()])
    adults = IntegerField("Adults", validators=[DataRequired(), NumberRange(min=1, max=50)], default=1)
    children = IntegerField("Children", validators=[Optional(), NumberRange(min=0, max=50)], default=0)
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(max=40)])
    country = StringField("Country", validators=[Optional(), Length(max=120)])
    pickup_location = StringField("Pickup Location", validators=[Optional(), Length(max=255)])
    special_requests = TextAreaField("Special Requests", validators=[Optional(), Length(max=2000)])
    submission_token = HiddenField()
    submit = SubmitField("Submit Booking Request")


class ServiceBookingForm(FlaskForm):
    travelers = IntegerField(
        "Number of Travelers",
        validators=[DataRequired(), NumberRange(min=1, max=50)],
        default=1,
    )
    preferred_travel_date = DateField(
        "Preferred Travel Date",
        validators=[Optional()],
        format="%Y-%m-%d",
    )
    destination_country = StringField("Destination Country", validators=[Optional(), Length(max=120)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(max=40)])
    country = StringField("Country of Residence", validators=[Optional(), Length(max=120)])
    special_requests = TextAreaField(
        "Additional Details",
        validators=[Optional(), Length(max=3000)],
        description="Share travel plans, passport details needed, visa type, coverage needs, etc.",
    )
    submission_token = HiddenField()
    submit = SubmitField("Submit Service Request")


class CheckBookingForm(FlaskForm):
    reference = StringField("Booking Reference", validators=[DataRequired(), Length(max=32)])
    contact = StringField("Email or Phone", validators=[DataRequired(), Length(max=255)])
    submit = SubmitField("Check Booking")


class ContactForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=160)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=3000)])
    submit = SubmitField("Send Message")
