# apps/web/management/commands/bump_trip_prices.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Literal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from web.models import Trip  # adjust app label if needed

Target = Literal["adult", "child", "both"]

def _as_decimal_percent(p: str) -> Decimal:
    try:
        d = Decimal(p)
    except InvalidOperation as e:
        raise CommandError(f"Invalid --percent value: {p!r}") from e
    return d

def _bump_no_decimals(value: Decimal, factor: Decimal) -> Decimal:
    """
    Multiply by factor, then round to an integer (no decimals) using HALF_UP.
    DecimalField with 2 dp will store it as .00 automatically.
    """
    return (value * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

class Command(BaseCommand):
    help = (
        "Increase Trip prices by a percentage with no decimals.\n"
        "Defaults: +14%% on ADULT base price only."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            choices=["adult", "child", "both"],
            default="adult",
            help="Which prices to bump (default: adult).",
        )
        parser.add_argument(
            "--percent",
            default="14",
            help="Percentage to increase (e.g. 14 for +14%%). Default: 14",
        )
        parser.add_argument(
            "--exclude-services",
            action="store_true",
            help="Skip trips where Trip.is_service=True.",
        )
        parser.add_argument(
            "--materialize-child-if-null",
            action="store_true",
            help=(
                "If target includes child and a trip has no explicit child rate (NULL), "
                "create one based on the ADULT price × (1+percent)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving.",
        )

    def handle(self, *args, **opts):
        target: Target = opts["target"]
        percent_str: str = opts["percent"]
        exclude_services: bool = opts["exclude_services"]
        materialize_child: bool = opts["materialize_child_if_null"]
        dry_run: bool = opts["dry_run"]

        pct = _as_decimal_percent(percent_str)
        factor = (Decimal(100) + pct) / Decimal(100)

        if pct <= Decimal("-100"):
            raise CommandError("Percent must be greater than -100 (cannot reduce to zero or below).")

        qs = Trip.objects.all()
        if exclude_services:
            qs = qs.filter(is_service=False)

        updated_adult = 0
        updated_child = 0
        skipped_child_null = 0
        total = 0

        ctx = transaction.atomic() if not dry_run else _NullCtx()
        with ctx:
            for trip in qs.iterator():
                total += 1
                updates = []

                # bump adult if requested
                if target in ("adult", "both"):
                    old_adult = trip.base_price_per_person
                    new_adult = _bump_no_decimals(old_adult, factor)
                    if new_adult != old_adult:
                        self.stdout.write(
                            f"[ADULT] {trip.title!r}: {old_adult} -> {new_adult}"
                            + (" [preview]" if dry_run else "")
                        )
                        trip.base_price_per_person = new_adult
                        updates.append("base_price_per_person")
                        updated_adult += 1

                # bump child if requested
                if target in ("child", "both"):
                    if trip.child_price_per_person is None:
                        if materialize_child:
                            # base on (potentially updated) adult price on the instance
                            basis = trip.base_price_per_person
                            new_child = _bump_no_decimals(basis, factor)
                            self.stdout.write(
                                f"[CHI]()
