from __future__ import annotations

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Run all November trip seeding commands (novtrip1 → novtrip23)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the commands that would run without executing them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        commands = [f"novtrip{i}" for i in range(1, 24)]

        self.stdout.write(self.style.MIGRATE_HEADING("Starting November trip seeding…"))
        for name in commands:
            if dry_run:
                self.stdout.write(self.style.WARNING(f"[DRY RUN] Would run: {name}"))
                continue

            self.stdout.write(self.style.HTTP_INFO(f"→ Running: {name}"))
            try:
                call_command(name)
                self.stdout.write(self.style.SUCCESS(f"✓ Finished: {name}"))
            except Exception as exc:
                # Decide whether to stop or continue on error
                self.stderr.write(self.style.ERROR(f"✗ Error in {name}: {exc}"))
                # If you prefer to stop on the first error, uncomment this:
                # raise

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete. No commands were executed."))
        else:
            self.stdout.write(self.style.SUCCESS("All novtrip commands completed (or attempted)."))
