from __future__ import annotations

from .booking_cart import build_booking_help_link, summarize_cart


def booking_cart(request):
    session = getattr(request, "session", None)
    if session is None:
        help_link = build_booking_help_link([])
        return {
            "booking_cart_count": 0,
            "booking_cart_contact": {},
            "booking_cart_entries": [],
            "booking_cart_total_display": "0.00",
            "booking_cart_currency": "USD",
            "booking_cart_help_link": help_link,
        }

    summary = summarize_cart(session)

    entries = summary["entries"]
    whatsapp_link = build_booking_help_link(entries)

    return {
        "booking_cart_count": summary["count"],
        "booking_cart_contact": summary["contact"],
        "booking_cart_entries": entries,
        "booking_cart_total_display": summary["total_display"],
        "booking_cart_currency": summary["currency"],
        "booking_cart_help_link": whatsapp_link,
    }
