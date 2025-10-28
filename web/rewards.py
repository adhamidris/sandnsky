from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from .models import Booking, BookingReward, RewardPhase

CENT = Decimal("0.01")


class RewardComputationError(Exception):
    """Raised when reward calculations cannot be completed."""


@dataclass(frozen=True)
class PhaseTripData:
    id: int
    trip_id: int
    slug: str
    title: str
    position: int
    card_image_url: str


@dataclass(frozen=True)
class RewardPhaseData:
    id: int
    name: str
    slug: str
    position: int
    threshold_amount: Decimal
    discount_percent: Decimal
    currency: str
    is_active: bool
    headline: str
    description: str
    trips: Tuple[PhaseTripData, ...]


@dataclass(frozen=True)
class RewardUnlockProgress:
    total_cents: int
    currency: str
    unlocked_phase_ids: Tuple[int, ...]
    next_phase_id: Optional[int]
    remaining_to_next_cents: Optional[int]


@dataclass(frozen=True)
class CartEntrySnapshot:
    entry_id: str
    trip_id: int
    traveler_count: int
    base_price_cents: int
    base_total_cents: int
    extras_total_cents: int
    grand_total_cents: int
    currency: str


@dataclass(frozen=True)
class RewardSelection:
    entry_id: str
    phase_id: int
    trip_id: int


@dataclass(frozen=True)
class RewardCalculation:
    entry_id: str
    phase_id: int
    trip_id: int
    traveler_count: int
    discount_cents: int
    updated_base_total_cents: int
    updated_grand_total_cents: int
    currency: str
    discount_percent: Decimal

    @property
    def discount_amount(self) -> Decimal:
        return _cents_to_decimal(self.discount_cents)


def _quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _cents_to_decimal(value: int | str | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return _quantize_money(value)
    if isinstance(value, str):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return Decimal("0.00")
    return _quantize_money((Decimal(value) or Decimal("0")) / Decimal("100"))


def _decimal_to_cents(amount: Decimal | int | str) -> int:
    if isinstance(amount, int):
        return amount
    if isinstance(amount, str):
        amount = Decimal(amount)
    quantized = _quantize_money(Decimal(amount))
    cents = (quantized * 100).to_integral_value(rounding=ROUND_HALF_UP)
    return int(cents)


def _phase_queryset():
    return RewardPhase.objects.prefetch_related(
        "phase_trips__trip",
        "phase_trips",
    ).order_by("position", "id")


@lru_cache(maxsize=2)
def _load_reward_phases_cached(active_only: bool) -> Tuple[RewardPhaseData, ...]:
    return tuple(_load_reward_phases(active_only=active_only))


def invalidate_reward_phase_cache() -> None:
    _load_reward_phases_cached.cache_clear()  # type: ignore[attr-defined]


def get_reward_phases(*, active_only: bool = True, use_cache: bool = True) -> Tuple[RewardPhaseData, ...]:
    if use_cache:
        return _load_reward_phases_cached(active_only)
    return tuple(_load_reward_phases(active_only=active_only))


def _load_reward_phases(*, active_only: bool) -> List[RewardPhaseData]:
    queryset = _phase_queryset()
    if active_only:
        queryset = queryset.filter(status=RewardPhase.Status.ACTIVE)

    phases: List[RewardPhaseData] = []
    for phase in queryset:
        trips: List[PhaseTripData] = []
        for linking in phase.phase_trips.all():
            trip = linking.trip
            card_image_url = ""
            if trip.card_image:
                try:
                    card_image_url = trip.card_image.url
                except Exception:
                    card_image_url = ""
            trips.append(
                PhaseTripData(
                    id=linking.id,
                    trip_id=trip.pk,
                    slug=trip.slug,
                    title=trip.title,
                    position=linking.position,
                    card_image_url=card_image_url,
                )
            )
        trips.sort(key=lambda item: (item.position, item.id))
        phases.append(
            RewardPhaseData(
                id=phase.pk,
                name=phase.name,
                slug=phase.slug,
                position=phase.position,
                threshold_amount=_quantize_money(phase.threshold_amount),
                discount_percent=_quantize_money(phase.discount_percent),
                currency=phase.currency,
                is_active=phase.status == RewardPhase.Status.ACTIVE,
                headline=phase.headline,
                description=phase.description,
                trips=tuple(trips),
            )
        )
    return phases


def calculate_unlock_progress(
    *,
    total_cents: int,
    phases: Sequence[RewardPhaseData],
) -> RewardUnlockProgress:
    currency = phases[0].currency if phases else "USD"
    total_amount = _cents_to_decimal(total_cents)

    unlocked: List[int] = []
    next_phase_id: Optional[int] = None
    remaining_to_next: Optional[int] = None

    for phase in phases:
        if phase.currency != currency:
            # Mixed currencies; treat as unavailable until harmonised.
            continue
        if total_amount >= phase.threshold_amount:
            unlocked.append(phase.id)
            continue
        if next_phase_id is None:
            next_phase_id = phase.id
            remaining = phase.threshold_amount - total_amount
            remaining_to_next = max(_decimal_to_cents(remaining), 0)

    return RewardUnlockProgress(
        total_cents=total_cents,
        currency=currency,
        unlocked_phase_ids=tuple(unlocked),
        next_phase_id=next_phase_id,
        remaining_to_next_cents=remaining_to_next,
    )


def build_entry_snapshot(entry: Mapping[str, object]) -> CartEntrySnapshot:
    entry_id = str(entry.get("id", ""))
    trip_id = entry.get("trip_id")
    if not entry_id:
        raise RewardComputationError("Cart entry is missing an identifier.")
    if not isinstance(trip_id, int):
        raise RewardComputationError("Cart entry must include trip_id.")

    pricing = entry.get("pricing")
    if not isinstance(pricing, Mapping):
        raise RewardComputationError("Cart entry pricing payload is invalid.")

    currency = str(pricing.get("currency") or "USD")
    base_price_cents = _safe_int(pricing.get("base_price_cents"))
    base_total_cents = _safe_int(pricing.get("base_total_cents"))
    extras_total_cents = _safe_int(pricing.get("extras_total_cents"))
    grand_total_cents = _safe_int(pricing.get("grand_total_cents"))

    adults = _safe_int(entry.get("adults"))
    children = _safe_int(entry.get("children"))
    traveler_count = max(adults + children, 1)

    return CartEntrySnapshot(
        entry_id=entry_id,
        trip_id=trip_id,
        traveler_count=traveler_count,
        base_price_cents=base_price_cents,
        base_total_cents=base_total_cents or (base_price_cents * traveler_count),
        extras_total_cents=extras_total_cents,
        grand_total_cents=grand_total_cents
        or (base_price_cents * traveler_count) + extras_total_cents,
        currency=currency,
    )


def _safe_int(value: object) -> int:
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, Decimal):
            return int(value)
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def map_phases_by_id(phases: Iterable[RewardPhaseData]) -> Dict[int, RewardPhaseData]:
    return {phase.id: phase for phase in phases}


def extract_phase_trip_ids(phase: RewardPhaseData) -> Tuple[int, ...]:
    return tuple(item.trip_id for item in phase.trips)


def calculate_entry_reward(
    *,
    snapshot: CartEntrySnapshot,
    phase: RewardPhaseData,
) -> RewardCalculation:
    if not phase.is_active:
        raise RewardComputationError("Reward phase is inactive.")
    if snapshot.currency != phase.currency:
        raise RewardComputationError("Currency mismatch between cart entry and reward phase.")

    eligible_trip_ids = extract_phase_trip_ids(phase)
    if snapshot.trip_id not in eligible_trip_ids:
        raise RewardComputationError("Trip is not eligible for the selected reward phase.")

    base_total = _cents_to_decimal(snapshot.base_total_cents)
    discount_percent = phase.discount_percent / Decimal("100")
    discount = _quantize_money(base_total * discount_percent)
    discount_cents = min(
        snapshot.base_total_cents,
        _decimal_to_cents(discount),
    )

    updated_base_total_cents = snapshot.base_total_cents - discount_cents
    updated_grand_total_cents = updated_base_total_cents + snapshot.extras_total_cents

    return RewardCalculation(
        entry_id=snapshot.entry_id,
        phase_id=phase.id,
        trip_id=snapshot.trip_id,
        traveler_count=snapshot.traveler_count,
        discount_cents=discount_cents,
        updated_base_total_cents=updated_base_total_cents,
        updated_grand_total_cents=updated_grand_total_cents,
        currency=snapshot.currency,
        discount_percent=phase.discount_percent,
    )


def normalize_reward_selections(raw: object) -> Dict[str, RewardSelection]:
    selections: Dict[str, RewardSelection] = {}

    if isinstance(raw, Mapping):
        items = raw.items()
    elif isinstance(raw, Iterable):
        items = []
        for value in raw:
            if isinstance(value, Mapping):
                entry_id = value.get("entry_id")
                items.append((entry_id, value))
            else:
                continue
    else:
        return selections

    for entry_key, value in items:
        entry_id = str(entry_key or "")
        if not entry_id:
            continue
        phase_id = _safe_int(_pluck(value, "phase_id"))
        trip_id = _safe_int(_pluck(value, "trip_id"))
        if phase_id <= 0 or trip_id <= 0:
            continue
        selections[entry_id] = RewardSelection(
            entry_id=entry_id,
            phase_id=phase_id,
            trip_id=trip_id,
        )
    return selections


def _pluck(mapping: object, key: str) -> object:
    if isinstance(mapping, Mapping):
        return mapping.get(key)
    return None


def apply_reward_calculation_to_entry(
    entry: MutableMapping[str, object],
    calculation: RewardCalculation,
) -> None:
    pricing = entry.get("pricing")
    if not isinstance(pricing, MutableMapping):
        raise RewardComputationError("Cannot mutate cart entry pricing payload.")

    pricing["discount_total_cents"] = calculation.discount_cents
    pricing["base_total_cents"] = calculation.updated_base_total_cents
    pricing["grand_total_cents"] = calculation.updated_grand_total_cents


def persist_booking_reward(
    *,
    booking: Booking,
    phase: RewardPhaseData,
    calculation: RewardCalculation,
) -> BookingReward:
    reward = BookingReward.objects.create(
        booking=booking,
        reward_phase_id=phase.id,
        trip_id=calculation.trip_id,
        traveler_count=calculation.traveler_count,
        discount_percent=calculation.discount_percent,
        discount_amount=calculation.discount_amount,
        currency=calculation.currency,
    )
    return reward
