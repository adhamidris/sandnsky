from django import template
from django.contrib.admin.models import LogEntry
from django.core.paginator import Paginator
from django.utils import timezone

from web.models import Booking

register = template.Library()


@register.simple_tag
def booking_counts():
    """
    Return quick booking metrics for the admin dashboard.
    Keys: new, confirmed, past_confirmed.
    """
    today = timezone.localdate()
    return {
        "new": Booking.objects.filter(status=Booking.Status.RECEIVED).count(),
        "confirmed": Booking.objects.filter(status=Booking.Status.CONFIRMED).count(),
        "past_confirmed": Booking.objects.filter(
            status=Booking.Status.CONFIRMED,
            travel_date__lt=today,
        ).count(),
    }


@register.simple_tag(takes_context=True)
def recent_admin_events(context, limit=100, per_page=10):
    """
    Return a paginated object of recent admin log entries.
    """
    limit = int(limit or 100)
    per_page = int(per_page or 10)

    qs = (
        LogEntry.objects.select_related("user", "content_type")
        .order_by("-action_time")[:limit]
    )
    paginator = Paginator(qs, per_page)

    request = context.get("request")
    page_number = None
    if request:
        page_number = request.GET.get("events_page")

    page_obj = paginator.get_page(page_number)
    return {"page_obj": page_obj, "paginator": paginator}
