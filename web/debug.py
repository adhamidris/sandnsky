# Create: core/debug.py
from django.conf import settings

def show_toolbar(request):
    return bool(
        settings.DEBUG
        and (
            request.GET.get("djdt") == "1"  # explicit toggle: add ?djdt=1 to the URL
            or (getattr(request, "user", None) and request.user.is_staff)
        )
    )