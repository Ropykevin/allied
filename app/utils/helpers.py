"""General helpers."""

from __future__ import annotations

import re
import secrets
import unicodedata
from decimal import Decimal


def slugify(value: str, max_length: int = 200) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value[:max_length].strip("-") or secrets.token_hex(4)


def money(amount: Decimal | float | int | None, currency: str = "KES") -> str:
    value = Decimal(amount or 0)
    return f"{currency} {value:,.2f}"


def generate_token(nbytes: int = 16) -> str:
    return secrets.token_hex(nbytes)
