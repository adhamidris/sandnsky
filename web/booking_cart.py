from __future__ import annotations

import copy
import datetime as dt
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List
from urllib.parse import quote_plus

from django.utils import timezone

from .models import Trip, TripExtra

DEFAULT_CURRENCY = "USD"

SESSION_KEY = "booking_cart"
WHATSAPP_BOOKING_HELP_NUMBER = "201108741159"


def _default_cart() -> Dict[str, Any]:
    return {"contact": {}, "entries": []}


def _normalize_cart(cart: Any) -> Dict[str, Any]:
    if not isinstance(cart, dict):
        return _default_cart()
    contact = cart.get("contact")
    entries = cart.get("entries")
    if not isinstance(contact, dict):
        contact = {}
    normalized_contact = {}
    for key, value in contact.items():
        if isinstance(value, str):
            normalized_contact[key] = value
    if not isinstance(entries, list):
        entries = []
    normalized_entries: List[Dict[str, Any]] = []
    for entry in entries:
        if isinstance(entry, dict):
            normalized_entries.append(copy.deepcopy(entry))
    return {"contact": normalized_contact, "entries": normalized_entries}


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


def update_contact(
    session,
    *,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    notes: str | None = None,
) -> Dict[str, Any]:
    cart = get_cart(session)
    contact = cart.setdefault("contact", {})
    if name is not None:
        contact["name"] = name.strip()
    if email is not None:
        contact["email"] = email.strip()
    if phone is not None:
        contact["phone"] = phone.strip()
    if notes is not None:
        contact["notes"] = notes.strip()
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


def _format_money_cents(cents: int) -> str:
    amount = Decimal(cents) / Decimal("100")
    quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return format(quantized, ",.2f")


def _serialize_summary_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    pricing = entry.get("pricing") or {}
    try:
        grand_total_cents = int(pricing.get("grand_total_cents", 0))
    except (TypeError, ValueError):
        grand_total_cents = 0

    currency = pricing.get("currency") or DEFAULT_CURRENCY

    date_raw = entry.get("travel_date")
    travel_date: dt.date | None = None
    travel_date_display = ""
    if isinstance(date_raw, dt.date):
        travel_date = date_raw
    elif isinstance(date_raw, str):
        try:
            travel_date = dt.date.fromisoformat(date_raw)
        except ValueError:
            travel_date = None
    if travel_date is not None:
        travel_date_display = travel_date.strftime("%b %d, %Y")

    adults = int(entry.get("adults") or 0)
    children = int(entry.get("children") or 0)
    infants = int(entry.get("infants") or 0)
    traveler_count = max(adults + children, 1)

    traveler_label = "1 traveler" if traveler_count == 1 else f"{traveler_count} travelers"
    if infants:
        infant_label = "infant" if infants == 1 else "infants"
        traveler_label = f"{traveler_label} + {infants} {infant_label}"

    return {
        "id": entry.get("id"),
        "trip_title": entry.get("trip_title", ""),
        "travel_date_display": travel_date_display,
        "traveler_label": traveler_label,
        "currency": currency,
        "grand_total_cents": grand_total_cents,
        "grand_total_display": _format_money_cents(grand_total_cents),
        "trip_slug": entry.get("trip_slug"),
    }


def summarize_cart(session) -> Dict[str, Any]:
    cart = get_cart(session)
    entries = []
    total_cents = 0
    currency = DEFAULT_CURRENCY

    for raw_entry in cart.get("entries", []):
        serialized = _serialize_summary_entry(raw_entry)
        entries.append(serialized)
        total_cents += serialized["grand_total_cents"]
        if serialized.get("currency"):
            currency = serialized["currency"]

    total_display = _format_money_cents(total_cents) if total_cents else "0.00"

    return {
        "contact": cart.get("contact", {}),
        "entries": entries,
        "count": len(entries),
        "currency": currency,
        "total_cents": total_cents,
        "total_display": total_display,
    }


def build_booking_help_link(entries: List[Dict[str, Any]]) -> str:
    lines = ["Hi Sand & Sky, I need help with my booking list."]

    for entry in entries:
        parts: List[str] = []
        title = entry.get("trip_title")
        if title:
            parts.append(str(title))

        travel_date = entry.get("travel_date_display")
        if travel_date:
            parts.append(str(travel_date))

        traveler_label = entry.get("traveler_label")
        if traveler_label:
            parts.append(str(traveler_label))

        currency = entry.get("currency")
        total_display = entry.get("grand_total_display")
        if currency and total_display:
            parts.append(f"{currency} {total_display}")

        if parts:
            lines.append(f"- {' • '.join(parts)}")

    message = "\n".join(lines)
    encoded = quote_plus(message)
    return f"https://wa.me/{WHATSAPP_BOOKING_HELP_NUMBER}?text={encoded}"


def add_entry(session, entry: Dict[str, Any], *, contact: Dict[str, str] | None = None) -> Dict[str, Any]:
    cart = get_cart(session)
    if contact:
        update_payload = {
            key: value
            for key, value in contact.items()
            if key in {"name", "email", "phone"}
            and isinstance(value, str)
            and value.strip()
        }
        if update_payload:
            contact_values = cart.setdefault("contact", {})
            for key, value in update_payload.items():
                contact_values[key] = value.strip()
    cart.setdefault("entries", []).append(entry)
    save_cart(session, cart)
    return cart


def remove_entry(session, entry_id: str) -> Dict[str, Any]:
    cart = get_cart(session)
    entries = cart.get("entries", [])
    updated_entries = [entry for entry in entries if entry.get("id") != entry_id]
    if len(updated_entries) != len(entries):
        cart["entries"] = updated_entries
        save_cart(session, cart)
    return cart


def remove_trip_entries(session, trip_id: int) -> Dict[str, Any]:
    cart = get_cart(session)
    entries = cart.get("entries", [])
    updated_entries = [entry for entry in entries if entry.get("trip_id") != trip_id]
    if len(updated_entries) != len(entries):
        cart["entries"] = updated_entries
        save_cart(session, cart)
    return cart
