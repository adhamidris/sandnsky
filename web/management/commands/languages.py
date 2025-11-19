from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import Trip, Language


REQUIRED_LANGUAGES = [
    ("English", "EN"),
    ("Spanish", "ES"),
    ("Italian", "IT"),
    ("Russian", "RU"),
]


class Command(BaseCommand):
    help = "Ensure all trips have the default language set: EN / ES / IT / RU."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding trip languages..."))

        with transaction.atomic():
            # 1) Ensure the Language objects exist (case-insensitive on code).
            code_to_lang = {}

            for name, code in REQUIRED_LANGUAGES:
                existing = Language.objects.filter(code__iexact=code).first()
                if existing:
                    # Optionally normalize the name if you want to enforce it
                    if existing.name != name:
                        existing.name = name
                        existing.save(update_fields=["name"])
                    lang = existing
                    created = False
                else:
                    lang = Language.objects.create(name=name, code=code)
                    created = True

                code_to_lang[code.upper()] = lang

                msg = f"Language {lang.code} ({lang.name}) - {'created' if created else 'reused'}"
                self.stdout.write(self.style.SUCCESS(msg))

            languages = list(code_to_lang.values())

            # 2) Attach languages to trips that are missing them.
            trips_qs = Trip.objects.all().prefetch_related("languages")

            total_trips = trips_qs.count()
            updated_trips = 0
            total_links_created = 0

            self.stdout.write(
                self.style.NOTICE(f"Processing {total_trips} trips to ensure languages are set...")
            )

            for trip in trips_qs:
                current_lang_ids = set(trip.languages.values_list("id", flat=True))

                # If you ONLY want to affect trips with NO languages at all,
                # uncomment the next two lines:
                # if current_lang_ids:
                #     continue

                missing_langs = [lang for lang in languages if lang.id not in current_lang_ids]

                if missing_langs:
                    trip.languages.add(*missing_langs)
                    updated_trips += 1
                    total_links_created += len(missing_langs)
                    self.stdout.write(
                        f"- Trip #{trip.id} · {trip.title}: added {len(missing_langs)} language(s)"
                    )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done seeding trip languages."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Trips updated: {updated_trips} | Language links created: {total_links_created}"
            )
        )
