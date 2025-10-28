from __future__ import annotations

import copy
import datetime as dt
import uuid
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple
from urllib.parse import quote_plus

from django.utils import timezone

from .models import Trip, TripExtra
from .rewards import (
    CartEntrySnapshot,
    RewardCalculation,
    RewardComputationError,
    RewardPhaseData,
    RewardSelection,
    RewardUnlockProgress,
    apply_reward_calculation_to_entry,
    build_entry_snapshot,
    calculate_entry_reward,
    calculate_unlock_progress,
    get_reward_phases,
    map_phases_by_id,
    normalize_reward_selections,
)

DEFAULT_CURRENCY = "USD"

SESSION_KEY = "booking_cart"
REWARDS_SESSION_KEY = "rewards"
WHATSAPP_BOOKING_HELP_NUMBER = "201108741159"


def _default_cart() -> Dict[str, Any]:
    return {"contact": {}, "entries": [], REWARDS_SESSION_KEY: {}}


def _normalize_cart(cart: Any) -> Dict[str, Any]:
    if not isinstance(cart, dict):
        return _default_cart()
    contact = cart.get("contact")
    entries = cart.get("entries")
    rewards_raw = cart.get(REWARDS_SESSION_KEY)
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
    normalized_rewards = _normalize_rewards_payload(rewards_raw)
    return {
        "contact": normalized_contact,
        "entries": normalized_entries,
        REWARDS_SESSION_KEY: normalized_rewards,
    }


def _normalize_rewards_payload(raw: Any) -> Dict[str, Dict[str, int]]:
    normalized: Dict[str, Dict[str, int]] = {}
    selections = normalize_reward_selections(raw)
    for entry_id, selection in selections.items():
        key = str(entry_id)
        if not key:
            continue
        normalized[key] = {
            "phase_id": int(selection.phase_id),
            "trip_id": int(selection.trip_id),
        }
    return normalized


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


def _ensure_rewards_mapping(cart: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    rewards = cart.get(REWARDS_SESSION_KEY)
    if not isinstance(rewards, dict):
        rewards = {}
        cart[REWARDS_SESSION_KEY] = rewards
    return rewards


def get_reward_selections(session) -> Dict[str, RewardSelection]:
    cart = get_cart(session)
    raw = cart.get(REWARDS_SESSION_KEY, {})
    return normalize_reward_selections(raw)


def apply_reward_selection(
    session,
    *,
    entry_id: str,
    phase_id: int,
    trip_id: int,
) -> Dict[str, Any]:
    cart = get_cart(session)
    rewards = _ensure_rewards_mapping(cart)
    rewards[str(entry_id)] = {
        "phase_id": int(phase_id),
        "trip_id": int(trip_id),
    }
    save_cart(session, cart)
    return cart


def remove_reward_selection(session, entry_id: str | Iterable[str]) -> Dict[str, Any]:
    cart = get_cart(session)
    if _remove_reward_selection_from_cart(cart, entry_id):
        save_cart(session, cart)
    return cart


def _remove_reward_selection_from_cart(
    cart: Dict[str, Any],
    entry_ids: str | Iterable[str],
) -> bool:
    rewards = cart.get(REWARDS_SESSION_KEY)
    if not isinstance(rewards, dict) or not rewards:
        return False
    if isinstance(entry_ids, (str, bytes)):
        entry_iterable: Iterable[str] = [entry_ids]
    else:
        entry_iterable = [str(entry_id) for entry_id in entry_ids]
    removed = False
    for entry_id in entry_iterable:
        key = str(entry_id)
        if key and key in rewards:
            rewards.pop(key, None)
            removed = True
    return removed


@dataclass(frozen=True)
class CartRewardsComputation:
    phases: Tuple[RewardPhaseData, ...]
    phase_map: Dict[int, RewardPhaseData]
    selections: Dict[str, RewardSelection]
    snapshots: Dict[str, CartEntrySnapshot]
    calculations: Dict[str, RewardCalculation]
    invalid_entry_ids: Tuple[str, ...]
    progress: RewardUnlockProgress
    unlocked_phase_ids: Tuple[int, ...]
    pre_discount_total_cents: int


def compute_cart_rewards(cart: Mapping[str, Any]) -> CartRewardsComputation:
    entries = cart.get("entries", [])
    if not isinstance(entries, list):
        entries = []

    selections = normalize_reward_selections(cart.get(REWARDS_SESSION_KEY, {}))
    phases = get_reward_phases(active_only=True)
    phase_map = map_phases_by_id(phases)

    snapshots: Dict[str, CartEntrySnapshot] = {}
    pre_discount_total_cents = 0

    for raw_entry in entries:
        if not isinstance(raw_entry, Mapping):
            continue
        entry_id = str(raw_entry.get("id", ""))
        if not entry_id:
            continue
        try:
            snapshot = build_entry_snapshot(raw_entry)
        except RewardComputationError:
            continue
        snapshots[entry_id] = snapshot
        pre_discount_total_cents += snapshot.grand_total_cents

    progress = calculate_unlock_progress(
        total_cents=pre_discount_total_cents,
        phases=phases,
    )
    unlocked_phase_ids = tuple(progress.unlocked_phase_ids)
    unlocked_set = set(unlocked_phase_ids)

    calculations: Dict[str, RewardCalculation] = {}
    invalid_entry_ids: List[str] = []

    for entry_id, selection in selections.items():
        snapshot = snapshots.get(entry_id)
        if snapshot is None:
            invalid_entry_ids.append(entry_id)
            continue

        phase = phase_map.get(selection.phase_id)
        if phase is None:
            invalid_entry_ids.append(entry_id)
            continue

        if phase.id not in unlocked_set:
            invalid_entry_ids.append(entry_id)
            continue

        if selection.trip_id != snapshot.trip_id:
            invalid_entry_ids.append(entry_id)
            continue

        try:
            calculation = calculate_entry_reward(snapshot=snapshot, phase=phase)
        except RewardComputationError:
            invalid_entry_ids.append(entry_id)
            continue

        calculations[entry_id] = calculation

    return CartRewardsComputation(
        phases=phases,
        phase_map=phase_map,
        selections=selections,
        snapshots=snapshots,
        calculations=calculations,
        invalid_entry_ids=tuple(invalid_entry_ids),
        progress=progress,
        unlocked_phase_ids=unlocked_phase_ids,
        pre_discount_total_cents=pre_discount_total_cents,
    )


def _decimal_to_cents(amount: Decimal | int | float | str) -> int:
    if isinstance(amount, int):
        return amount * 100
    decimal_amount = Decimal(str(amount))
    quantized = decimal_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    cents = (quantized * 100).to_integral_value(rounding=ROUND_HALF_UP)
    return int(cents)


def _safe_int(value: Any) -> int:
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, Decimal):
            return int(value)
        if value is None:
            return 0
        return int(str(value))
    except (TypeError, ValueError):
        return 0


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


def _format_traveler_label(count: int) -> str:
    count = max(int(count or 0), 1)
    return "1 traveler" if count == 1 else f"{count} travelers"


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

    traveler_label = _format_traveler_label(traveler_count)
    if infants:
        infant_label = "infant" if infants == 1 else "infants"
        traveler_label = f"{traveler_label} + {infants} {infant_label}"

    discount_cents = _safe_int(pricing.get("discount_total_cents"))
    original_grand_total_cents = _safe_int(
        pricing.get("original_grand_total_cents") or pricing.get("grand_total_original_cents")
    )
    if not original_grand_total_cents:
        original_grand_total_cents = grand_total_cents

    summary = {
        "id": entry.get("id"),
        "trip_id": entry.get("trip_id"),
        "trip_title": entry.get("trip_title", ""),
        "travel_date_display": travel_date_display,
        "traveler_label": traveler_label,
        "currency": currency,
        "grand_total_cents": grand_total_cents,
        "grand_total_display": _format_money_cents(grand_total_cents),
        "trip_slug": entry.get("trip_slug"),
        "original_grand_total_cents": original_grand_total_cents,
        "original_grand_total_display": _format_money_cents(original_grand_total_cents),
        "discount_total_cents": discount_cents,
        "discount_total_display": _format_money_cents(discount_cents) if discount_cents else "0.00",
    }

    applied_reward = entry.get("applied_reward")
    if applied_reward:
        summary["applied_reward"] = applied_reward
    reward_selection = entry.get("reward_selection")
    if reward_selection:
        summary["reward_selection"] = reward_selection

    return summary


def summarize_cart(session) -> Dict[str, Any]:
    cart = get_cart(session)
    rewards_state = compute_cart_rewards(cart)

    if rewards_state.invalid_entry_ids:
        if _remove_reward_selection_from_cart(cart, rewards_state.invalid_entry_ids):
            save_cart(session, cart)
            rewards_state = compute_cart_rewards(cart)

    entries_summary: List[Dict[str, Any]] = []
    total_cents = 0
    currency = DEFAULT_CURRENCY
    total_discount_cents = 0
    selections_payload: Dict[str, Dict[str, int]] = {}

    raw_entries = cart.get("entries", [])
    if not isinstance(raw_entries, list):
        raw_entries = []

    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            continue

        entry_id = str(raw_entry.get("id", ""))
        entry_copy = copy.deepcopy(raw_entry)

        snapshot = rewards_state.snapshots.get(entry_id)
        calculation = rewards_state.calculations.get(entry_id)

        pricing = entry_copy.setdefault("pricing", {})
        if not isinstance(pricing, MutableMapping):
            pricing = {}
            entry_copy["pricing"] = pricing

        if snapshot:
            pricing.setdefault("currency", snapshot.currency)
            pricing.setdefault("base_total_cents", snapshot.base_total_cents)
            pricing.setdefault("extras_total_cents", snapshot.extras_total_cents)
            pricing.setdefault("grand_total_cents", snapshot.grand_total_cents)
            pricing.setdefault("original_base_total_cents", snapshot.base_total_cents)
            pricing.setdefault("original_grand_total_cents", snapshot.grand_total_cents)

        if calculation:
            apply_reward_calculation_to_entry(entry_copy, calculation)
            pricing = entry_copy["pricing"]
            if isinstance(pricing, MutableMapping):
                pricing.setdefault("original_base_total_cents", rewards_state.snapshots[entry_id].base_total_cents)
                pricing.setdefault("original_grand_total_cents", rewards_state.snapshots[entry_id].grand_total_cents)
            applied_reward_payload = {
                "phase_id": calculation.phase_id,
                "phase_name": rewards_state.phase_map[calculation.phase_id].name,
                "discount_percent": str(calculation.discount_percent),
                "discount_cents": calculation.discount_cents,
                "discount_display": _format_money_cents(calculation.discount_cents),
            }
            entry_copy["applied_reward"] = applied_reward_payload
            total_discount_cents += calculation.discount_cents

        selection = rewards_state.selections.get(entry_id)
        if selection:
            selection_payload = {
                "phase_id": selection.phase_id,
                "trip_id": selection.trip_id,
            }
            selections_payload[entry_id] = selection_payload
            entry_copy["reward_selection"] = selection_payload

        serialized = _serialize_summary_entry(entry_copy)
        entries_summary.append(serialized)
        total_cents += serialized["grand_total_cents"]
        if serialized.get("currency"):
            currency = serialized["currency"]

    total_display = _format_money_cents(total_cents) if total_cents else "0.00"
    pre_discount_total_cents = rewards_state.pre_discount_total_cents
    pre_discount_total_display = (
        _format_money_cents(pre_discount_total_cents) if pre_discount_total_cents else "0.00"
    )

    rewards_metadata = _build_rewards_metadata(
        rewards_state=rewards_state,
        selections_payload=selections_payload,
        total_discount_cents=total_discount_cents,
    )

    return {
        "contact": cart.get("contact", {}),
        "entries": entries_summary,
        "count": len(entries_summary),
        "currency": currency,
        "total_cents": total_cents,
        "total_display": total_display,
        "pre_discount_total_cents": pre_discount_total_cents,
        "pre_discount_total_display": pre_discount_total_display,
        "discount_total_cents": total_discount_cents,
        "discount_total_display": _format_money_cents(total_discount_cents)
        if total_discount_cents
        else "0.00",
        "rewards": rewards_metadata,
    }


def _build_rewards_metadata(
    *,
    rewards_state: CartRewardsComputation,
    selections_payload: Dict[str, Dict[str, int]],
    total_discount_cents: int,
) -> Dict[str, Any]:
    unlocked_set = set(rewards_state.unlocked_phase_ids)

    snapshots_by_trip_id: Dict[int, CartEntrySnapshot] = {}
    default_traveler_count = 1
    for snapshot in rewards_state.snapshots.values():
        trip_key = snapshot.trip_id
        if trip_key not in snapshots_by_trip_id:
            snapshots_by_trip_id[trip_key] = snapshot
        if snapshot.traveler_count > default_traveler_count:
            default_traveler_count = max(snapshot.traveler_count, 1)

    has_snapshot_context = bool(snapshots_by_trip_id)

    phases_payload: List[Dict[str, Any]] = []
    for phase in rewards_state.phases:
        phase_threshold_cents = _decimal_to_cents(phase.threshold_amount)
        discount_percent_value = phase.discount_percent or Decimal("0")
        discount_fraction = discount_percent_value / Decimal("100")

        trip_payloads: List[Dict[str, Any]] = []
        for trip in phase.trips:
            base_price_cents = int(trip.base_price_cents or 0)
            base_price_display = _format_money_cents(base_price_cents) if base_price_cents else "0.00"

            snapshot = snapshots_by_trip_id.get(trip.trip_id)
            traveler_count = snapshot.traveler_count if snapshot else default_traveler_count if has_snapshot_context else 0
            traveler_count = max(int(traveler_count or 0), 0)

            comparison_payload: Optional[Dict[str, Any]] = None
            if traveler_count > 0 and base_price_cents > 0:
                base_total_cents = base_price_cents * traveler_count
                base_total_amount = Decimal(base_total_cents) / Decimal("100")
                discount_amount = base_total_amount * discount_fraction
                discount_cents = min(
                    base_total_cents,
                    _decimal_to_cents(discount_amount),
                )
                reward_total_cents = max(base_total_cents - discount_cents, 0)

                reward_total_amount = Decimal(reward_total_cents) / Decimal("100")
                reward_per_person_amount = (
                    reward_total_amount / Decimal(traveler_count)
                    if traveler_count > 0
                    else Decimal("0")
                )

                comparison_payload = {
                    "traveler_count": traveler_count,
                    "traveler_label": _format_traveler_label(traveler_count),
                    "full_price_cents": base_total_cents,
                    "full_price_display": _format_money_cents(base_total_cents),
                    "reward_price_cents": reward_total_cents,
                    "reward_price_display": _format_money_cents(reward_total_cents),
                    "discount_cents": discount_cents,
                    "discount_display": _format_money_cents(discount_cents),
                    "full_price_per_person_display": base_price_display,
                    "reward_price_per_person_display": _format_money_cents(
                        _decimal_to_cents(reward_per_person_amount)
                    )
                    if traveler_count > 0
                    else base_price_display,
                    "source": "entry" if snapshot else "cart",
                }

            trip_payloads.append(
                {
                    "phase_trip_id": trip.id,
                    "trip_id": trip.trip_id,
                    "slug": trip.slug,
                    "title": trip.title,
                    "position": trip.position,
                    "card_image_url": trip.card_image_url,
                    "base_price_per_person_cents": base_price_cents,
                    "base_price_per_person_display": base_price_display,
                    "comparison": comparison_payload,
                }
            )

        phase_payload = {
            "id": phase.id,
            "name": phase.name,
            "slug": phase.slug,
            "position": phase.position,
            "threshold_amount_cents": phase_threshold_cents,
            "threshold_amount_display": _format_money_cents(phase_threshold_cents),
            "discount_percent": str(phase.discount_percent),
            "currency": phase.currency,
            "is_active": phase.is_active,
            "unlocked": phase.id in unlocked_set,
            "headline": phase.headline,
            "description": phase.description,
            "trip_options": trip_payloads,
            "applied_entry_ids": [
                entry_id
                for entry_id, calculation in rewards_state.calculations.items()
                if calculation.phase_id == phase.id
            ],
        }
        phases_payload.append(phase_payload)

    progress = rewards_state.progress
    remaining_to_next_cents = progress.remaining_to_next_cents
    rewards_summary = {
        "phases": phases_payload,
        "progress": {
            "total_cents": progress.total_cents,
            "total_display": _format_money_cents(progress.total_cents)
            if progress.total_cents
            else "0.00",
            "currency": progress.currency,
            "unlocked_phase_ids": list(rewards_state.unlocked_phase_ids),
            "next_phase_id": progress.next_phase_id,
            "remaining_to_next_cents": remaining_to_next_cents,
            "remaining_to_next_display": (
                _format_money_cents(remaining_to_next_cents)
                if remaining_to_next_cents is not None
                else None
            ),
        },
        "selections": selections_payload,
        "discount_total_cents": total_discount_cents,
        "discount_total_display": _format_money_cents(total_discount_cents)
        if total_discount_cents
        else "0.00",
    }
    return rewards_summary


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
        _remove_reward_selection_from_cart(cart, entry_id)
        save_cart(session, cart)
    return cart


def remove_trip_entries(session, trip_id: int) -> Dict[str, Any]:
    cart = get_cart(session)
    entries = cart.get("entries", [])
    removed_entry_ids: List[str] = []
    updated_entries = []
    for entry in entries:
        if entry.get("trip_id") == trip_id:
            removed_entry_ids.append(str(entry.get("id", "")))
            continue
        updated_entries.append(entry)
    if len(updated_entries) != len(entries):
        cart["entries"] = updated_entries
        if removed_entry_ids:
            _remove_reward_selection_from_cart(cart, removed_entry_ids)
        save_cart(session, cart)
    return cart
