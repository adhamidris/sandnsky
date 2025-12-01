from django import template
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
