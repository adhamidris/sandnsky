"""
Test settings: uses SQLite locally to avoid MySQL grants for test DB creation.
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }
}

# Keep emails quiet during tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
