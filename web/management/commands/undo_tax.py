from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Literal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from web.models import Trip  # adjust app label if different

Target = Literal["adult", "child", "both"]
Method = Literal["search", "divide"]


def _bump_no_decimals(value: Decimal, factor: Decimal) -> Decimal:
    """Same forward bump used previously: multiply then round to whole unit (no decimals)."""
    return (value * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _is_integer_amount(x: Decimal) -> bool:
    """True if x has .00 cents (i.e., integer)."""
    return x == x.quantize(Decimal("1"))


def _undo_one(current: Decimal, factor: Decimal, method: Method, window_cents: int) -> Decimal:
    """
    Try to find a 0.01-precision 'previous' value whose forward bump equals 'current'.
    - 'divide'  : naive division then round to 0.01
    - 'search'  : start from division result and scan by ±1 cent up to window to find an exact preimage.
    """
    if current is None:
        return None

    # Base candidate by division
    candidate = (current / factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if method == "divide":
        return candidate

    # 'search' method: if candidate re-bumps to current, keep it; else search nearby cents
    if _bump_no_decimals(candidate, factor) == current:
        return candidate

    step = Decimal("0.01")
    for k in range(1, window_cents + 1):
        up = (candidate + step * k).quantize(Decimal("0.01"))
        if _bump_no_decimals(up, factor) == current:
            return up
        down = (candidate - step * k).quantize(Decimal("0.01"))
        if down > Decimal("0") and _bump_no_decimals(down, factor) == current:
            return down

    # Fallback: best-effort candidate
    return candidate


class Command(BaseCommand):
    help = (
        "Revert the previous +X% no-decimals price bump. "
        "Attempts to reconstruct pre-bump prices at 0.01 precision."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--percent",
            default="14",
            help="Percent used in the bump you want to undo (e.g., 14). Default: 14",
        )
        parser.add_argument(
            "--target",
            choices=["adult", "child", "both"],
            default="both",
            help="Which prices to revert. Default: both.",
        )
        parser.add_argument(
            "--method",
            choices=["search", "divide"],
            default="search",
            help=(
                "Reversion method. 'search' tries to find a 2-decimal value that re-bumps exactly "
                "to the current integer price. 'divide' simply divides by factor and rounds to 0.01."
            ),
        )
        parser.add_argument(
            "--search-window-cents",
            type=int,
            default=200,
            help="Max ±cents to scan around the division candidate when --method=search (default: 200 = $2).",
        )
        parser.add_argument(
            "--only-integers",
            action="store_true",
            help="Only revert rows that currently have .00 (helps avoid touching already-accurate prices).",
        )
        parser.add_argument(
            "--exclude-services",
            action="store_true",
            help="Skip trips where Trip.is_service=True.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview without saving.",
        )
        parser.add_argument(
            "--child-null-if-equals-adult",
            action="store_true",
            help=(
                "After revert, if child price equals adult price, set child to NULL (to re-inherit). "
                "Use only if that matches your original policy."
            ),
        )

    def handle(self, *args, **opts):
        # Parse inputs
        try:
            pct = Decimal(opts["percent"])
        except InvalidOperation as e:
            raise CommandError(f"Invalid --percent: {opts['percent']!r}") from e
        if pct <= Decimal("-100"):
            raise CommandError("Percent must be greater than -100.")
        factor = (Decimal(100) + pct) / Decimal(100)

        target: Target = opts["target"]
        method: Method = opts["method"]
        window_cents: int = int(opts["search_window_cents"])
        only_integers: bool = opts["only_integers"]
        exclude_services: bool = opts["exclude_services"]
        dry_run: bool = opts["dry_run"]
        child_null_if_equals_adult: bool = opts["child_null_if_equals_adult"]

        qs = Trip.objects.all()
        if exclude_services:
            qs = qs.filter(is_service=False)

        scanned = 0
        reverted_adult = 0
        reverted_child = 0
        skipped_int_check_adult = 0
        skipped_int_check_child = 0

        ctx = transaction.atomic() if not dry_run else _NullCtx()
        with ctx:
            for trip in qs.iterator():
                scanned += 1
                updates = []

                # Adult
                if target in ("adult", "both"):
                    cur_a = trip.base_price_per_person
                    if cur_a is not None:
                        if only_integers and not _is_integer_amount(cur_a):
                            skipped_int_check_adult += 1
                        else:
                            prev_a = _undo_one(cur_a, factor, method, window_cents)
                            if prev_a != cur_a and prev_a > 0:
                                self.stdout.write(
                                    f"[ADULT-REV] {trip.title!r}: {cur_a} -> {prev_a}"
                                    + (" [preview]" if dry_run else "")
                                )
                                trip.base_price_per_person = prev_a
                                updates.append("base_price_per_person")
                                reverted_adult += 1

                # Child
                if target in ("child", "both"):
                    cur_c = trip.child_price_per_person
                    if cur_c is None:
                        # Nothing to revert (was NULL before or materialized earlier but later cleared)
                        pass
                    else:
                        if only_integers and not _is_integer_amount(cur_c):
                            skipped_int_check_child += 1
                        else:
                            prev_c = _undo_one(cur_c, factor, method, window_cents)
                            if prev_c != cur_c and prev_c > 0:
                                self.stdout.write(
                                    f"[CHILD-REV] {trip.title!r}: {cur_c} -> {prev_c}"
                                    + (" [preview]" if dry_run else "")
                                )
                                trip.child_price_per_person = prev_c
                                updates.append("child_price_per_person")
                                reverted_child += 1

                # Optional: after revert, restore child to NULL if it equals adult (re-inherit)
                if (
                    target in ("child", "both")
                    and child_null_if_equals_adult
                    and trip.child_price_per_person is not None
                    and trip.base_price_per_person == trip.child_price_per_person
                ):
                    self.stdout.write(
                        f"[CHILD->NULL] {trip.title!r}: child equals adult; setting child to NULL"
                        + (" [preview]" if dry_run else "")
                    )
                    trip.child_price_per_person = None
                    if "child_price_per_person" not in updates:
                        updates.append("child_price_per_person")

                if updates and not dry_run:
                    trip.save(update_fields=updates)

        self.stdout.write(self.style.SUCCESS(
            "Done. "
            f"trips_scanned={scanned}, adult_reverted={reverted_adult}, child_reverted={reverted_child}, "
            f"adult_skipped_non_integer={skipped_int_check_adult}, child_skipped_non_integer={skipped_int_check_child}, "
            f"dry_run={dry_run}"
        ))


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
