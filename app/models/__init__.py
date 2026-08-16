"""SQLAlchemy models package."""

from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.models.blog import BlogCategory, BlogPost, BlogTag, blog_post_tags
from app.models.booking import Booking, BookingPassenger
from app.models.customer import Customer
from app.models.departure import Departure
from app.models.destination import Destination
from app.models.gallery import GalleryImage
from app.models.invoice import Invoice, InvoiceItem
from app.models.notification import Notification
from app.models.partner import Partner
from app.models.payment import Payment
from app.models.permission import Permission
from app.models.review import Review
from app.models.role import Role, role_permissions
from app.models.service import Service
from app.models.setting import Setting
from app.models.tour import (
    FAQ,
    Tour,
    TourExclusion,
    TourFAQ,
    TourImage,
    TourInclusion,
    TourItinerary,
)

__all__ = [
    "Admin",
    "Role",
    "Permission",
    "role_permissions",
    "Tour",
    "TourImage",
    "TourItinerary",
    "TourInclusion",
    "TourExclusion",
    "TourFAQ",
    "FAQ",
    "Destination",
    "Departure",
    "Customer",
    "Booking",
    "BookingPassenger",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "Review",
    "BlogPost",
    "BlogCategory",
    "BlogTag",
    "blog_post_tags",
    "GalleryImage",
    "Service",
    "Partner",
    "Notification",
    "Setting",
    "AuditLog",
]
