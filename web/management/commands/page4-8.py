# web/management/commands/seed_trip_giza_light_show.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Giza: Pyramids Sound & Light Show Night Experience"
TEASER = (
    "Evening Sound and Light Show at Giza Pyramids: Watch pyramids illuminate with lights, "
    "laser projections, and narration by the Sphinx. Multilingual audio with hotel transfers available."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("50.00")
TOUR_TYPE_LABEL = "Daily Tour — Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Evening Tour",
    "Entertainment",
    "Historical",
    "Cultural",
    "Night Experience",
]

HIGHLIGHTS = [
    "Witness mesmerizing Sound & Light Show with pyramids illuminated under night sky.",
    "Hear ancient Egyptian history narrated by the Great Sphinx in dramatic audio-visual performance.",
    "See stunning night views of Giza Plateau with pyramids and desert landscape in magical colors.",
    "Convenient hotel transfers available from Cairo or Giza in air-conditioned vehicles.",
    "Multilingual narration available including English, Spanish, Italian, Russian and more.",
    "VIP seating options available for front-row views and immersive experience.",
    "Perfect for families, couples and groups - safe evening activity for all ages.",
    "Capture iconic night photos with lit-up pyramids as backdrop - bucket-list moment.",
]

ABOUT = """\
Step into the magical world of Ancient Egypt with the Sound and Light Show at the Giza Pyramids, an unforgettable journey through thousands of years of history told through light, sound, and the shadowy silhouettes of Egypt's most iconic monuments. As the sun sets behind the mighty pyramids, the Giza Plateau transforms into an open-air theatre where history is brought vividly to life.

This world-renowned show, set against the backdrop of the Great Pyramid of Khufu, the Pyramid of Khafre, and the Pyramid of Menkaure, is a dramatic retelling of Egypt's ancient past, narrated by the mystical voice of the Great Sphinx. The narration—available in multiple languages—takes you back in time to explore the lives of the pharaohs, the construction of the pyramids, and the rich mythology of this ancient civilization.

Dazzling laser projections, cinematic sound effects, and dramatic lighting cast stunning visual displays across the pyramids and desert sands, creating an immersive experience that is both educational and awe-inspiring. Whether you're a history enthusiast or simply looking to experience something uniquely Egyptian, this tour offers a memorable way to explore Egypt's rich cultural heritage.

With hotel pickup and drop-off available, the evening is stress-free and perfectly suited for couples, families, solo travelers, or groups. Choose between general admission or a VIP seating area for the best views of the show.

Whether it's your first visit to Cairo or you're returning for more, the Sound and Light Show at the Giza Pyramids is an essential part of any Egyptian adventure.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Giza Pyramids Sound and Light Show Evening",
        "steps": [
            ("Evening", "Hotel pickup in Cairo or Giza (time varies by season)"),
            ("Evening", "Arrive at Giza Plateau and enjoy panoramic views at dusk"),
            ("Night", "Take your seats and prepare for the show"),
            ("Night", "Sound and Light Show begins - Duration approx. 50 minutes"),
            ("Night", "Show ends; optional time for photos near the pyramids"),
            ("Late Night", "Return transfer to your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Admission ticket to the Sound and Light Show at Giza Pyramids",
    "Multilingual audio guide or live commentary (depending on show time)",
    "Local guide/host to assist on-site",
    "Round-trip transportation from your Cairo or Giza hotel (optional upgrade)",
    "Air-conditioned vehicle for transfers",
    "All taxes and service charges",
]

EXCLUSIONS = [
    "Meals and drinks during the tour",
    "Gratuities for driver or guide",
    "Personal expenses and souvenirs",
    "Entrance to the pyramids or museum (nighttime show only)",
    "Photography or videography fees (if applicable)",
    "VIP seating upgrades (available at extra cost)",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("What is the duration of the Sound and Light Show?",
     "The show lasts approximately 50 minutes."),
    ("Is the show suitable for children?",
     "Yes, the show is family-friendly and suitable for children of all ages."),
    ("Is photography allowed during the show?",
     "Non-flash photography is usually allowed, but video recording may be restricted or require a separate fee."),
    ("In what languages is the show available?",
     "The show is offered in multiple languages including English, Arabic, French, Spanish, German, and more. Check the schedule to select your preferred language night."),
    ("What should I wear?",
     "Casual and comfortable clothing is recommended. Bring a light jacket, especially in the winter months."),
    ("Is the show wheelchair accessible?",
     "Yes, the venue is generally accessible for wheelchairs. Please inform us in advance for special arrangements."),
    ("What happens in case of bad weather?",
     "The show usually runs regardless of weather conditions unless there are safety concerns. In case of cancellation, rescheduling or refund will be offered."),
    ("Can I upgrade to VIP seating?",
     "Yes, VIP seating upgrades are available at an additional cost for better views and comfort."),
]


class Command(BaseCommand):
    help = "Seeds the Giza Pyramids Sound and Light Show evening experience."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true", help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations (must already exist from your destination seeder)
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Primary destination '{PRIMARY_DEST}' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in ALSO_APPEARS_IN:
            try:
                addl_dests.append(Destination.objects.get(name=d))
            except Destination.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Additional destination '{d}' not found (skipping)."))

        # Languages (get_or_create)
        lang_objs = []
        for lname, code in LANGS:
            obj, _ = Language.objects.get_or_create(name=lname, code=code)
            lang_objs.append(obj)

        # Category tags (as TripCategory rows)
        cat_objs = []
        for tag in CATEGORY_TAGS:
            slug = tag.lower().replace("&", "and").replace("—", "-").replace(" ", "-")
            obj, _ = TripCategory.objects.get_or_create(name=tag, defaults={"slug": slug})
            if not obj.slug:
                obj.slug = slug
                obj.save()
            cat_objs.append(obj)

        # Upsert trip
        created = False
        with (transaction.atomic() if not dry else _NullCtx()):
            trip, created = Trip.objects.get_or_create(
                title=TITLE,
                defaults=dict(
                    destination=dest_primary,
                    teaser=TEASER,
                    duration_days=DURATION_DAYS,
                    group_size_max=GROUP_SIZE_MAX,
                    base_price_per_person=BASE_PRICE,
                    tour_type_label=TOUR_TYPE_LABEL,
                )
            )

            # If exists, update core fields
            changed = []
            def setf(attr, value):
                old = getattr(trip, attr)
                if old != value:
                    setattr(trip, attr, value)
                    changed.append(attr)

            setf("destination", dest_primary)
            setf("teaser", TEASER)
            setf("duration_days", DURATION_DAYS)
            setf("group_size_max", GROUP_SIZE_MAX)
            setf("base_price_per_person", BASE_PRICE)
            setf("tour_type_label", TOUR_TYPE_LABEL)

            if not dry and changed:
                trip.save()

            # M2M: additional_destinations, languages, categories
            if not dry:
                trip.additional_destinations.set(addl_dests)
                trip.languages.set(lang_objs)
                trip.category_tags.set(cat_objs)

            # Related content
            if replace_related and not dry:
                trip.highlights.all().delete()
                trip.itinerary_days.all().delete()
                trip.inclusions.all().delete()
                trip.exclusions.all().delete()
                trip.faqs.all().delete()
                if hasattr(trip, "about"):
                    trip.about.delete()

            # Create related if empty (idempotent friendly)
            if not dry:
                if not TripAbout.objects.filter(trip=trip).exists():
                    TripAbout.objects.create(trip=trip, body=ABOUT)

                if not TripHighlight.objects.filter(trip=trip).exists():
                    for i, text in enumerate(HIGHLIGHTS, start=1):
                        TripHighlight.objects.create(trip=trip, text=text, position=i)

                if not TripItineraryDay.objects.filter(trip=trip).exists():
                    for day in ITINERARY:
                        d = TripItineraryDay.objects.create(
                            trip=trip, day_number=day["day"], title=day["title"]
                        )
                        for idx, (time_label, title) in enumerate(day["steps"], start=1):
                            TripItineraryStep.objects.create(
                                day=d, time_label=time_label, title=title, position=idx
                            )

                if not TripInclusion.objects.filter(trip=trip).exists():
                    for i, text in enumerate(INCLUSIONS, start=1):
                        TripInclusion.objects.create(trip=trip, text=text, position=i)

                if not TripExclusion.objects.filter(trip=trip).exists():
                    for i, text in enumerate(EXCLUSIONS, start=1):
                        TripExclusion.objects.create(trip=trip, text=text, position=i)

                if not TripFAQ.objects.filter(trip=trip).exists():
                    for i, (q, a) in enumerate(FAQS, start=1):
                        TripFAQ.objects.create(trip=trip, question=q, answer=a, position=i)

        # Summary
        mode = "DRY-RUN" if dry else "APPLY"
        self.stdout.write(self.style.SUCCESS("\n— Trip seeding summary —"))
        self.stdout.write(f"Trip: {TITLE}")
        self.stdout.write(f"Primary destination: {dest_primary.name}")
        if addl_dests:
            self.stdout.write("Also appears in: " + ", ".join(d.name for d in addl_dests))
        self.stdout.write(f"Languages: " + ", ".join(f"{l.name} ({l.code})" for l in lang_objs))
        self.stdout.write(f"Categories: " + ", ".join(c.name for c in cat_objs))
        self.stdout.write(f"Base Price: ${BASE_PRICE}")
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False