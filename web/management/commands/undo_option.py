# apps/web/management/commands/remove_booking_option.py
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from web.models import Trip, TripBookingOption, Booking  # adjust app label if needed


class Command(BaseCommand):
    help = (
        "Remove TripBookingOption records by name (default: 'Launch Trip'). "
        "Useful to undo a previous seed. Idempotent and supports dry-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="Launch Trip",
            help="Option name to remove (case-insensitive). Default: 'Launch Trip'.",
        )
        parser.add_argument(
            "--price",
            default=None,
            help="If provided, only remove options with this exact price_per_person (e.g., 15.00).",
        )
        parser.add_argument(
            "--exclude-services",
            action="store_true",
            help="Skip options on trips where Trip.is_service=True.",
        )
        parser.add_argument(
            "--normalize-positions",
            action="store_true",
            help="After deletion, re-sequence remaining options per trip to positions 1..N.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )

    def handle(self, *args, **options):
        name: str = options["name"]
        price_str: Optional[str] = options["price"]
        exclude_services: bool = options["exclude_services"]
        normalize_positions: bool = options["normalize_positions"]
        dry_run: bool = options["dry_run"]

        price: Optional[Decimal] = None
        if price_str is not None:
            try:
                price = Decimal(price_str)
            except (InvalidOperation, TypeError) as e:
                raise CommandError(f"Invalid --price value: {price_str!r}") from e

        # Build base queryset
        qs = TripBookingOption.objects.select_related("trip").filter(name__iexact=name)
        if price is not None:
            qs = qs.filter(price_per_person=price)
        if exclude_services:
            qs = qs.filter(trip__is_service=False)

        total_options = qs.count()
        if total_options == 0:
            self.stdout.write(self.style.WARNING("No matching options found. Nothing to remove."))
            return

        self.stdout.write(
            f"Matched {total_options} option(s) named {name!r}"
            + (f" with price {price}" if price is not None else "")
            + (" (excluding service trips)" if exclude_services else "")
            + (", DRY RUN" if dry_run else "")
        )

        options_by_trip: dict[int, list[TripBookingOption]] = {}
        for opt in qs.order_by("trip_id", "id"):
            options_by_trip.setdefault(opt.trip_id, []).append(opt)

        deleted_count = 0
        affected_bookings = 0

        ctx = transaction.atomic() if not dry_run else _NullContext()
        with ctx:
            # Report bookings that currently reference these options (SET_NULL will be applied on delete)
            for trip_id, opts in options_by_trip.items():
                trip_title = opts[0].trip.title if opts else f"Trip#{trip_id}"
                for opt in opts:
                    bk_count = Booking.objects.filter(trip_option=opt).count()
                    if bk_count:
                        self.stdout.write(
                            f"[INFO]  {trip_title!r}: option {opt.name!r} (id={opt.id}) "
                            f"is referenced by {bk_count} booking(s) — will be SET_NULL on delete."
                        )
                    affected_bookings += bk_count

            # Delete the options
            for trip_id, opts in options_by_trip.items():
                trip_title = opts[0].trip.title if opts else f"Trip#{trip_id}"
                for opt in opts:
                    self.stdout.write(f"[DELETE] {trip_title!r}: removing option {opt.name!r} (id={opt.id})")
                    if not dry_run:
                        opt.delete()
                    deleted_count += 1

            # Normalize positions if requested
            if normalize_positions and not dry_run:
                for trip_id in options_by_trip.keys():
                    self._normalize_trip_positions(trip_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. deleted_options={deleted_count}, "
                f"bookings_set_null={affected_bookings}, dry_run={dry_run}"
            )
        )

    def _normalize_trip_positions(self, trip_id: int) -> None:
        remaining = (
            TripBookingOption.objects.filter(trip_id=trip_id)
            .order_by("position", "id")
            .only("id", "position")
        )
        new_pos = 1
        for opt in remaining:
            if opt.position != new_pos:
                TripBookingOption.objects.filter(pk=opt.id).update(position=new_pos)
            new_pos += 1


class _NullContext:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
