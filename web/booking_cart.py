from __future__ import annotations

import copy
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any

from django.utils import timezone

from .models import Trip, TripExtra

DEFAULT_CURRENCY = "USD"

SESSION_KEY = "booking_cart"


def _default_cart() -> Dict[str, Any]:
    return {"contact": {}, "entries": []}


def _normalize_cart(cart: Any) -> Dict[str, Any]:
    if not isinstance(cart, dict):
        return _default_cart()
    contact = cart.get("contact")
    entries = cart.get("entries")
    if not isinstance(contact, dict):
        contact = {}
    if not isinstance(entries, list):
        entries = []
    normalized_entries: List[Dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, dict):
            normalized_entries.append(copy.deepcopy(entry))
    return {"contact": copy.deepcopy(contact), "entries": normalized_entries}


def get_cart(session) -> Dict[str, Any]:
    cart = session.get(SESSION_KEY)
    return _normalize_cart(cart)


def save_cart(session, cart: Dict[str, Any]) -> None:
    session[SESSION_KEY] = cart
    session.modified = True


def clear_cart(session) -> None:
    if SESSION_KEY in session:
        del session[SESSION_KEY]
        session.modified = True


def cart_entry_count(session) -> int:
    cart = get_cart(session)
    return len(cart["entries"])


def get_contact(session) -> Dict[str, str]:
    cart = get_cart(session)
    contact = cart.get("contact", {})
    return {key: value for key, value in contact.items() if isinstance(value, str)}


def update_contact(session, *, name: str | None = None, email: str | None = None, phone: str | None = None) -> Dict[str, Any]:
    cart = get_cart(session)
    contact = cart.setdefault("contact", {})
    if name is not None:
        contact["name"] = name.strip()
    if email is not None:
        contact["email"] = email.strip()
    if phone is not None:
        contact["phone"] = phone.strip()
    save_cart(session, cart)
    return cart


def _decimal_to_cents(amount: Decimal | int | float | str) -> int:
    if isinstance(amount, int):
        return amount * 100
    decimal_amount = Decimal(str(amount))
    quantized = decimal_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cents = (quantized * 100).to_integral_value(rounding=ROUND_HALF_UP)
    return int(cents)


def _selected_extras(trip: Trip, extras_ids: List[int]) -> List[TripExtra]:
    if not extras_ids:
        return []
    return list(
        trip.extras.filter(pk__in=extras_ids).order_by("position", "id")
    )


def build_cart_entry(trip: Trip, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
    date = cleaned_data["date"]
    adults = int(cleaned_data.get("adults") or 0)
    children = int(cleaned_data.get("children") or 0)
    infants = int(cleaned_data.get("infants") or 0)
    traveler_count = max(adults + children, 1)

    extras_raw = cleaned_data.get("extras") or []
    extras_ids: List[int] = []
    for extra_id in extras_raw:
        try:
            extras_ids.append(int(extra_id))
        except (TypeError, ValueError):
            continue

    selected_extras = _selected_extras(trip, extras_ids)

    base_price = getattr(trip, "base_price_per_person", Decimal("0"))
    currency = getattr(trip, "currency", DEFAULT_CURRENCY)

    base_total = Decimal(base_price) * traveler_count
    extras_total = sum((extra.price for extra in selected_extras), Decimal("0"))
    grand_total = base_total + extras_total

    entry = {
        "id": uuid.uuid4().hex,
        "trip_id": trip.pk,
        "trip_slug": trip.slug,
        "trip_title": trip.title,
        "travel_date": date.isoformat(),
        "adults": adults,
        "children": children,
        "infants": infants,
        "message": cleaned_data.get("message", ""),
        "extras": [
            {
                "id": extra.pk,
                "name": extra.name,
                "price_cents": _decimal_to_cents(extra.price),
            }
            for extra in selected_extras
        ],
        "pricing": {
            "currency": currency,
            "base_price_cents": _decimal_to_cents(base_price),
            "base_total_cents": _decimal_to_cents(base_total),
            "extras_total_cents": _decimal_to_cents(extras_total),
            "grand_total_cents": _decimal_to_cents(grand_total),
        },
        "created_at": timezone.now().isoformat(),
    }

    return entry


def add_entry(session, entry: Dict[str, Any], *, contact: Dict[str, str] | None = None) -> Dict[str, Any]:
    cart = get_cart(session)
    if contact:
        update_payload = {
            key: value
            for key, value in contact.items()
            if key in {"name", "email", "phone"} and isinstance(value, str)
        }
        if update_payload:
            contact_values = cart.setdefault("contact", {})
            for key, value in update_payload.items():
                contact_values[key] = value.strip()
    cart.setdefault("entries", []).append(entry)
    save_cart(session, cart)
    return cart
