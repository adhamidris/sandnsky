from __future__ import annotations

import sys
import subprocess

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run all November trip seeding commands (novtrip1 → novtrip23)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--stop-on-error",
            action="store_true",
            help="Stop immediately if any novtrip command fails.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which novtrip commands would run, without executing them.",
        )

    def handle(self, *args, **options):
        stop_on_error = options["stop_on_error"]
        dry_run = options["dry_run"]

        commands = [f"novtrip{i}" for i in range(1, 24)]  # novtrip1..novtrip23

        if dry_run:
            self.stdout.write(self.style.MIGRATE_HEADING("DRY RUN: November trip seeding plan"))
            for name in commands:
                self.stdout.write(self.style.WARNING(f"[DRY RUN] Would run: {name}"))
            self.stdout.write(self.style.WARNING("Dry run complete. No commands were executed."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("Starting November trip seeding…"))

        for name in commands:
            self.stdout.write(self.style.HTTP_INFO(f"→ Running: {name}"))

            # Run exactly as if you typed: python manage.py novtripX
            result = subprocess.run(
                [sys.executable, "manage.py", name],
            )

            if result.returncode != 0:
                self.stderr.write(
                    self.style.ERROR(f"✗ Error in {name}: exited with code {result.returncode}")
                )
                if stop_on_error:
                    break
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ Finished: {name}"))

        self.stdout.write(self.style.SUCCESS("All novtrip commands completed (or attempted)."))
