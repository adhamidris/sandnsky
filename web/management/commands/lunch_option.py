# apps/web/management/commands/seed_lunch_booking_options.py
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from web.models import Trip, TripBookingOption  # adjust app label if needed

INCLUDE_NAME_DEFAULT = "Including Lunch"
EXCLUDE_NAME_DEFAULT = "Excluding Lunch"


class Command(BaseCommand):
    help = (
        "Seed per-trip booking options for lunch:\n"
        f"- '{INCLUDE_NAME_DEFAULT}': base price + surcharge (default $15)\n"
        f"- '{EXCLUDE_NAME_DEFAULT}': base price only\n"
        "Idempotent; can update existing option prices."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-name",
            default=INCLUDE_NAME_DEFAULT,
            help=f"Name for the 'including lunch' option (default: '{INCLUDE_NAME_DEFAULT}').",
        )
        parser.add_argument(
            "--exclude-name",
            default=EXCLUDE_NAME_DEFAULT,
            help=f"Name for the 'excluding lunch' option (default: '{EXCLUDE_NAME_DEFAULT}').",
        )
        parser.add_argument(
            "--surcharge",
            default="15.00",
            help="Lunch surcharge added per person to the 'including lunch' option (default: 15.00).",
        )
        parser.add_argument(
            "--update-price",
            action="store_true",
            help="If an option already exists, update its price to match current trip prices + surcharge.",
        )
        parser.add_argument(
            "--normalize-positions",
            action="store_true",
            help="Ensure 'Excluding Lunch' appears before 'Including Lunch' by position.",
        )
        parser.add_argument(
            "--exclude-services",
            action="store_true",
            help="Skip trips where Trip.is_service=True.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without writing to the database.",
        )

    def handle(self, *args, **options):
        include_name: str = options["include_name"]
        exclude_name: str = options["exclude_name"]
        surcharge = Decimal(options["surcharge"])
        update_price: bool = options["update_price"]
        normalize_positions: bool = options["normalize_positions"]
        exclude_services: bool = options["exclude_services"]
        dry_run: bool = options["dry_run"]

        trips_qs = Trip.objects.all()
        if exclude_services:
            trips_qs = trips_qs.filter(is_service=False)

        created_inc = created_exc = updated_inc = updated_exc = skipped = 0

        ctx = transaction.atomic() if not dry_run else _nullcontext()
        with ctx:
            for trip in trips_qs.iterator():
                base_adult = trip.base_price_per_person
                base_child = trip.get_child_price_per_person()

                inc_adult = base_adult + surcharge
                inc_child = base_child + surcharge
                exc_adult = base_adult
                # IMPORTANT: inherit child price for EXCLUDING lunch so it tracks trip changes
                exc_child = None  # None => inherit from trip as per model help_text

                # Fetch existing options (case-insensitive by name)
                inc_qs = TripBookingOption.objects.filter(trip=trip, name__iexact=include_name)
                exc_qs = TripBookingOption.objects.filter(trip=trip, name__iexact=exclude_name)

                # Determine next position
                next_pos = (TripBookingOption.objects.filter(trip=trip).aggregate(
                    maxp=Max("position")
                )["maxp"] or 0) + 1

                # Create or update EXCLUDING lunch
                if exc_qs.exists():
                    option = exc_qs.earliest("id")
                    if update_price and (option.price_per_person != exc_adult or option.child_price_per_person is not None):
                        self.stdout.write(
                            f"[UPDATE] {trip.title!r}: {exclude_name} "
                            f"adult {option.price_per_person} -> {exc_adult}; child -> inherit"
                        )
                        if not dry_run:
                            option.price_per_person = exc_adult
                            option.child_price_per_person = exc_child  # enforce inherit
                            option.save(update_fields=["price_per_person", "child_price_per_person"])
                        updated_exc += 1
                    else:
                        self.stdout.write(f"[SKIP]   {trip.title!r}: {exclude_name} already exists")
                        skipped += 1
                    exc_option = option
                else:
                    self.stdout.write(
                        f"[CREATE] {trip.title!r}: {exclude_name} at {exc_adult} (pos {next_pos})"
                    )
                    exc_option = None
                    if not dry_run:
                        exc_option = TripBookingOption.objects.create(
                            trip=trip,
                            name=exclude_name,
                            price_per_person=exc_adult,
                            child_price_per_person=exc_child,  # inherit
                            position=next_pos,
                        )
                    created_exc += 1
                    next_pos += 1

                # Create or update INCLUDING lunch
                if inc_qs.exists():
                    option = inc_qs.earliest("id")
                    if update_price and (
                        option.price_per_person != inc_adult
                        or (option.child_price_per_person or Decimal("0")) != inc_child
                    ):
                        self.stdout.write(
                            f"[UPDATE] {trip.title!r}: {include_name} "
                            f"adult {option.price_per_person} -> {inc_adult}; child -> {inc_child}"
                        )
                        if not dry_run:
                            option.price_per_person = inc_adult
                            option.child_price_per_person = inc_child
                            option.save(update_fields=["price_per_person", "child_price_per_person"])
                        updated_inc += 1
                    else:
                        self.stdout.write(f"[SKIP]   {trip.title!r}: {include_name} already exists")
                        skipped += 1
                    inc_option = option
                else:
                    self.stdout.write(
                        f"[CREATE] {trip.title!r}: {include_name} at {inc_adult} (pos {next_pos})"
                    )
                    inc_option = None
                    if not dry_run:
                        inc_option = TripBookingOption.objects.create(
                            trip=trip,
                            name=include_name,
                            price_per_person=inc_adult,
                            child_price_per_person=inc_child,
                            position=next_pos,
                        )
                    created_inc += 1
                    next_pos += 1

                # Optional: normalize positions to ensure EXCLUDING comes before INCLUDING
                if normalize_positions and not dry_run and exc_option and inc_option:
                    if (inc_option.position or 0) < (exc_option.position or 0):
                        # swap to make excluding first
                        exc_pos, inc_pos = exc_option.position, inc_option.position
                        exc_option.position, inc_option.position = inc_pos, exc_pos
                        exc_option.save(update_fields=["position"])
                        inc_option.save(update_fields=["position"])
                        self.stdout.write(
                            f"[ORDER]  {trip.title!r}: ensured '{exclude_name}' before '{include_name}'"
                        )

        self.stdout.write(
            self.style.SUCCESS(
                "Done. "
                f"created_excluding={created_exc}, created_including={created_inc}, "
                f"updated_excluding={updated_exc}, updated_including={updated_inc}, "
                f"skipped={skipped}, dry_run={dry_run}"
            )
        )


class _nullcontext:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
