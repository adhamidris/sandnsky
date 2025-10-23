from __future__ import annotations

from .booking_cart import cart_entry_count, get_contact


def booking_cart(request):
    session = getattr(request, "session", None)
    if session is None:
        return {"booking_cart_count": 0, "booking_cart_contact": {}}

    return {
        "booking_cart_count": cart_entry_count(session),
        "booking_cart_contact": get_contact(session),
    }
