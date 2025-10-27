# web/management/commands/seed_destinations.py
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from web.models import Destination, DestinationName, ALLOWED_DESTINATIONS

# 1) Desired visual order (top-left → bottom-right of your grid)
GRID_LABELS = [
    "Giza", "Cairo", "Alexandria", "Ain El Sokhna",
    "Fayoum", "Bahariya Oasis", "Sinai", "Siwa",
]

# 2) Map image labels → canonical enum value
CANONICAL_MAP = {
    "Giza": DestinationName.GIZA,
    "Cairo": DestinationName.CAIRO,
    "Alexandria": DestinationName.ALEXANDRIA,
    "Ain El Sokhna": DestinationName.AIN_EL_SOKHNA,
    "Fayoum": DestinationName.FAYOUM,
    "Bahariya Oasis": DestinationName.BAHAREYA,  # normalized spelling
    "Sinai": DestinationName.SINAI,
    "Siwa": DestinationName.SIWA,
}


class Command(BaseCommand):
    help = (
        "Seed/Update Destination rows in a specific order, mark them as featured, "
        "and assign featured_position based on GRID_LABELS order."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--unfeature-rest",
            action="store_true",
            help="Unfeature any Destination not in the GRID_LABELS allowed set.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        unfeature_rest = opts["unfeature_rest"]

        allowed = set(ALLOWED_DESTINATIONS)
        ordered_allowed_values = []  # canonical enum values in order

        skipped = []
        for label in GRID_LABELS:
            canonical = CANONICAL_MAP.get(label)
            if not canonical:
                skipped.append(f"{label} (not in map)")
                continue
            if canonical not in allowed:
                skipped.append(f"{label} (not in ALLOWED_DESTINATIONS)")
                continue
            ordered_allowed_values.append(canonical)

        created, updated, existed = [], [], []
        errors = []

        # Map of name -> (is_featured, featured_position) we want to enforce
        desired_state = {}
        for pos, name_value in enumerate(ordered_allowed_values, start=1):
            desired_state[name_value] = (True, pos)

        # Apply updates/creates atomically unless dry-run
        ctx = transaction.atomic() if not dry_run else _NullContextManager()
        with ctx:
            # Upsert featured set in the given order
            for name_value, (should_feature, pos) in desired_state.items():
                try:
                    obj, was_created = Destination.objects.get_or_create(name=name_value)
                    before = (obj.is_featured, obj.featured_position)

                    obj.is_featured = should_feature
                    obj.featured_position = pos

                    if dry_run:
                        (created if was_created else (updated if before != (obj.is_featured, obj.featured_position) else existed)).append(obj.name)
                    else:
                        obj.save()
                        (created if was_created else (updated if before != (obj.is_featured, obj.featured_position) else existed)).append(obj.name)

                except IntegrityError as e:
                    errors.append((name_value, str(e)))

            # Optionally unfeature everything else
            if unfeature_rest:
                qs_rest = Destination.objects.exclude(name__in=ordered_allowed_values).filter(is_featured=True)
                if dry_run:
                    updated.extend(list(qs_rest.values_list("name", flat=True)))
                else:
                    for obj in qs_rest:
                        obj.is_featured = False
                        # keep their old featured_position or zero it—choose policy:
                        obj.featured_position = 0
                        obj.save()
                        updated.append(obj.name)

        # Summary
        self.stdout.write(self.style.SUCCESS("\n--- Destination Seeding (Featured Ordering) ---"))
        if created:
            self.stdout.write(f"Created: {', '.join(created)}")
        if updated:
            self.stdout.write(f"Updated: {', '.join(updated)}")
        if existed:
            self.stdout.write(f"No change: {', '.join(existed)}")
        if skipped:
            self.stdout.write(self.style.WARNING(f"Skipped: {', '.join(skipped)}"))
        if errors:
            self.stdout.write(self.style.ERROR("Errors:"))
            for name, err in errors:
                self.stdout.write(self.style.ERROR(f"  - {name}: {err}"))
        self.stdout.write(self.style.SUCCESS(f"Mode: {'DRY-RUN' if dry_run else 'APPLY'}  |  Unfeature rest: {unfeature_rest}"))
        self.stdout.write(self.style.SUCCESS("------------------------------------------------\n"))


class _NullContextManager:
    """Used to reuse the same 'with' structure for dry-run."""
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
