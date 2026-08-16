"""Database URL helpers for Docker / production."""

from __future__ import annotations

import os
from urllib.parse import quote_plus


def build_database_url_from_postgres_env() -> str | None:
    """Build SQLAlchemy URL from POSTGRES_* when DATABASE_URL is unset/blank."""
    password = os.environ.get("POSTGRES_PASSWORD") or ""
    if not password:
        return None
    user = os.environ.get("POSTGRES_USER") or "allied"
    host = os.environ.get("POSTGRES_HOST") or "db"
    port = os.environ.get("POSTGRES_PORT") or "5432"
    name = os.environ.get("POSTGRES_DB") or "allied_tours"
    return (
        f"postgresql+psycopg2://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


def ensure_database_url() -> str | None:
    """Ensure DATABASE_URL is set in the process environment; return it."""
    current = (os.environ.get("DATABASE_URL") or "").strip()
    # Reject broken compose interpolations that still contain raw @ in the userinfo
    # without encoding (host wrongly includes password fragments).
    if current and "@db:" in current.split("@")[-1]:
        # Looks like host is db — likely fine
        os.environ["DATABASE_URL"] = current
        return current
    if current and "://" in current:
        # If hostname part looks corrupted (password @ leaked into host), rebuild.
        try:
            after_scheme = current.split("://", 1)[1]
            # user:pass@host — more than one @ means password had @
            if after_scheme.count("@") > 1:
                rebuilt = build_database_url_from_postgres_env()
                if rebuilt:
                    os.environ["DATABASE_URL"] = rebuilt
                    return rebuilt
        except Exception:  # noqa: BLE001
            pass
        os.environ["DATABASE_URL"] = current
        return current

    rebuilt = build_database_url_from_postgres_env()
    if rebuilt:
        os.environ["DATABASE_URL"] = rebuilt
    return rebuilt
