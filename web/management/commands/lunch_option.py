# apps/web/management/commands/seed_launch_booking_option.py
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max

from web.models import Trip, TripBookingOption  # adjust if your app label differs


class Command(BaseCommand):
    help = (
        "Seed a 'Launch Trip' booking option (default $15.00) on all trips. "
        "Idempotent; can update existing option price."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            default="Launch Trip",
            help="Label for the booking option (default: 'Launch Trip').",
        )
        parser.add_argument(
            "--price",
            default="15.00",
            help="Price per person as decimal string (default: 15.00).",
        )
        parser.add_argument(
            "--update-price",
            action="store_true",
            help="If the option already exists on a trip, update its price to --price.",
        )
        parser.add_argument(
            "--exclude-services",
            action="store_true",
            help="Skip trips where Trip.is_service=True.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without writing to the database.",
        )

    def handle(self, *args, **options):
        name: str = options["name"]
        price = Decimal(options["price"])
        update_price: bool = options["update_price"]
        exclude_services: bool = options["exclude_services"]
        dry_run: bool = options["dry_run"]

        trips_qs = Trip.objects.all()
        if exclude_services:
            trips_qs = trips_qs.filter(is_service=False)

        created = 0
        updated = 0
        skipped = 0

        # Wrap in a transaction unless it's a dry run
        ctx = transaction.atomic() if not dry_run else _nullcontext()

        with ctx:
            for trip in trips_qs.iterator():
                existing_qs = TripBookingOption.objects.filter(
                    trip=trip, name__iexact=name
                )

                if existing_qs.exists():
                    if update_price:
                        option = existing_qs.earliest("id")
                        if option.price_per_person != price:
                            self.stdout.write(
                                f"[UPDATE] {trip.title!r}: {name} "
                                f"{option.price_per_person} -> {price}"
                            )
                            if not dry_run:
                                option.price_per_person = price
                                option.save(update_fields=["price_per_person"])
                            updated += 1
                        else:
                            self.stdout.write(
                                f"[SKIP]   {trip.title!r}: {name} already at {price}"
                            )
                            skipped += 1
                    else:
                        self.stdout.write(
                            f"[SKIP]   {trip.title!r}: {name} already exists"
                        )
                        skipped += 1
                    continue

                # Append at the end based on current max position
                next_position = (
                    TripBookingOption.objects.filter(trip=trip).aggregate(
                        maxp=Max("position")
                    )["maxp"]
                    or 0
                ) + 1

                self.stdout.write(
                    f"[CREATE] {trip.title!r}: {name} at {price} (position {next_position})"
                )

                if not dry_run:
                    TripBookingOption.objects.create(
                        trip=trip,
                        name=name,
                        price_per_person=price,
                        child_price_per_person=None,  # inherit trip child rate
                        position=next_position,
                    )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. created={created}, updated={updated}, skipped={skipped}, dry_run={dry_run}"
            )
        )


class _nullcontext:
    """Minimal context manager used when --dry-run is set."""
    def __enter__(self):  # noqa: D401
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
