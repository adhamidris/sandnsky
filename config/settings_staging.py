"""
Staging settings for PythonAnywhere with Django Debug Toolbar enabled safely.

Usage:
  DJANGO_SETTINGS_MODULE=config.settings_staging
"""

from .settings import *  # noqa

# --- Core toggles -----------------------------------------------------------
DEBUG = True  # staging only; do NOT use on production

# Make sure your PA domain is present (your base already includes it, but this
# keeps things explicit and future-proof).
if "adhamidris.pythonanywhere.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("adhamidris.pythonanywhere.com")

# CSRF trusted origins (explicit for clarity)
if "https://adhamidris.pythonanywhere.com" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append("https://adhamidris.pythonanywhere.com")

# --- Debug Toolbar ----------------------------------------------------------
# Install the app
if "debug_toolbar" not in INSTALLED_APPS:
    INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar"]

# Insert the middleware right after SecurityMiddleware if present; else append.
_MW = list(MIDDLEWARE)
try:
    sec_idx = _MW.index("django.middleware.security.SecurityMiddleware")
    _MW.insert(sec_idx + 1, "debug_toolbar.middleware.DebugToolbarMiddleware")
except ValueError:
    _MW.append("debug_toolbar.middleware.DebugToolbarMiddleware")
MIDDLEWARE = _MW

# INTERNAL_IPS is unreliable on PA (behind proxies). We’ll use a callback toggle.
INTERNAL_IPS = []

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "web.debug.always",  # TEMP test
}

