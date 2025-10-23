from __future__ import annotations

from .booking_cart import summarize_cart


def booking_cart(request):
    session = getattr(request, "session", None)
    if session is None:
        return {
            "booking_cart_count": 0,
            "booking_cart_contact": {},
            "booking_cart_entries": [],
            "booking_cart_total_display": "0.00",
            "booking_cart_currency": "USD",
        }

    summary = summarize_cart(session)

    return {
        "booking_cart_count": summary["count"],
        "booking_cart_contact": summary["contact"],
        "booking_cart_entries": summary["entries"],
        "booking_cart_total_display": summary["total_display"],
        "booking_cart_currency": summary["currency"],
    }
