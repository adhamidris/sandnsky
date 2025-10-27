# web/management/commands/seed_trip_siwa_3day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# -------------------------------------------------------------------
# Trip core (enhanced title per your convention)
# -------------------------------------------------------------------
TITLE = "Cairo to Siwa Oasis: 3-Day Desert Escape — Oracle Temple, Salt Lakes & Great Sand Sea"
TEASER = (
    "Leave Cairo for Egypt’s hidden paradise: Siwa. Explore the Oracle Temple and Shali Fortress, float in salt lakes, "
    "soak in Cleopatra’s Bath, and ride 4×4 into the Great Sand Sea for dune bashing, sandboarding, and a Bedouin "
    "dinner under the stars."
)

PRIMARY_DEST = DestinationName.SIWA
ALSO_APPEARS_IN = [DestinationName.CAIRO]  # dual listing (starts/ends in Cairo)

DURATION_DAYS = 3
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("590.00")
TOUR_TYPE_LABEL = "Daily Tour — Safari"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "Siwa",
    "Desert Safari",
    "Oasis",
    "Nature",
    "Culture",
    "Adventure",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Discover one of Egypt’s most remote oases: Siwa’s palm groves, salt lakes, and hot springs.",
    "Visit the Oracle Temple of Amun and the ancient mud-brick Shali Fortress.",
    "Float in the surreal Siwa salt lakes and relax at Cleopatra’s Bath.",
    "4×4 adventure into the Great Sand Sea with dune bashing and sandboarding.",
    "Bedouin dinner under a star-studded desert sky.",
    "Two nights in Siwa (half-board) at an eco-lodge or hotel.",
]

ABOUT = """\
Tucked near the Libyan border, Siwa Oasis blends Berber heritage, dreamlike landscapes, and deep calm. This 3-day escape
starts in Cairo and carries you across the Western Desert to Siwa’s palm groves, salt lakes, hot springs, and mud-brick history.
Explore the Oracle Temple of Amun and the Shali Fortress, float effortlessly in mineral-rich lakes, then plunge into the Great
Sand Sea by 4×4 for dune bashing, sandboarding, sunset views, and a Bedouin dinner by the fire.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo → Siwa Oasis (Drive ~8–9 hrs)",
        "steps": [
            ("", "Early pickup in Cairo; scenic Western Desert drive with comfort stops."),
            ("", "Arrive in Siwa; check in at eco-lodge/hotel (half-board)."),
            ("", "Leisure evening to explore the oasis town; overnight in Siwa."),
        ],
    },
    {
        "day": 2,
        "title": "Siwa Culture & Great Sand Sea Safari",
        "steps": [
            ("", "Breakfast at the lodge."),
            ("", "Visit the Oracle Temple of Amun and the Shali Fortress."),
            ("", "Stop at Cleopatra’s Bath; float in Siwa’s famed salt lakes."),
            ("", "Afternoon 4×4 into the Great Sand Sea: dune bashing and sandboarding; sunset viewpoint."),
            ("", "Bedouin dinner in the desert; return and overnight in Siwa."),
        ],
    },
    {
        "day": 3,
        "title": "Siwa → Cairo",
        "steps": [
            ("", "Morning free time for springs or last stroll."),
            ("", "Depart Siwa for Cairo; evening drop-off at hotel."),
        ],
    },
]

INCLUSIONS = [
    "Private air-conditioned transfers Cairo ↔ Siwa and during touring",
    "Accommodation in Siwa (2 nights, half-board)",
    "Lunch at a local restaurant or picnic lunch (excluding drinks)",
    "4×4 desert safari in the Great Sand Sea",
    "English-speaking guide",
    "Entrance fees to mentioned sites",
    "Bedouin dinner in the desert",
    "Bottled water during the trip",
    "Hotel pickup and drop-off (Cairo)",
]

EXCLUSIONS = [
    "Personal expenses",
    "Tips for guides and drivers",
    "Travel insurance",
    "Optional activities not mentioned in the itinerary",
    "Drinks with meals unless specified",
]

FAQS = [
    ("How long is the drive from Cairo to Siwa?", "Approximately 8–9 hours with scenic stops."),
    ("What type of accommodation is provided?", "Traditional eco-lodge or comfortable hotel, half-board basis."),
    ("Is the desert safari safe?", "Yes, operated by professional 4×4 drivers experienced in desert terrain."),
    ("What should I pack?", "Light clothes, hat, sunscreen, sturdy shoes, swimwear, and a warm layer for evenings."),
    ("Can dietary needs be accommodated?", "Yes—please share requirements in advance."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the 3-Day Siwa Oasis trip with price, content, languages, categories, and dual destination listing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace-related", action="store_true",
            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip."
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show changes without writing to DB."
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Primary destination 'Siwa' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in ALSO_APPEARS_IN:
            try:
                addl_dests.append(Destination.objects.get(name=d))
            except Destination.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Additional destination '{d}' not found (skipping)."))

        # Languages
        lang_objs = []
        for lname, code in LANGS:
            obj, _ = Language.objects.get_or_create(name=lname, code=code)
            lang_objs.append(obj)

        # Categories
        cat_objs = []
        for tag in CATEGORY_TAGS:
            slug = (
                tag.lower()
                .replace("&", "and")
                .replace("—", "-").replace("–", "-")
                .replace(" ", "-")
            )
            obj, _ = TripCategory.objects.get_or_create(name=tag, defaults={"slug": slug})
            if not obj.slug:
                obj.slug = slug
                obj.save()
            cat_objs.append(obj)

        created = False

        class _NullCtx:
            def __enter__(self): return self
            def __exit__(self, *a): return False

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

            # Update core fields on reruns
            changed = []
            def setf(field, value):
                if getattr(trip, field) != value:
                    setattr(trip, field, value)
                    changed.append(field)

            setf("destination", dest_primary)
            setf("teaser", TEASER)
            setf("duration_days", DURATION_DAYS)
            setf("group_size_max", GROUP_SIZE_MAX)
            setf("base_price_per_person", BASE_PRICE)
            setf("tour_type_label", TOUR_TYPE_LABEL)

            if not dry and changed:
                trip.save()

            # M2M
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
        self.stdout.write("Languages: " + ", ".join(f"{l.name} ({l.code})" for l in lang_objs))
        self.stdout.write("Categories: " + ", ".join(c.name for c in cat_objs))
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))
