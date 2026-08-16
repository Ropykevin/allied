"""Configuration loader."""

import os


def get_config(name: str | None = None):
    """Return a config class for the given environment name.

    Unknown environments fail closed instead of falling back to DEBUG development.
    """
    from app.config.development import DevelopmentConfig
    from app.config.production import ProductionConfig
    from app.config.testing import TestingConfig

    env = (name or os.getenv("FLASK_ENV", "development")).lower().strip()
    mapping = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    if env not in mapping:
        raise RuntimeError(
            f"Unknown FLASK_ENV={env!r}. Use one of: development, production, testing."
        )
    return mapping[env]
