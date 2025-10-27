# web/management/commands/seed_trip_bahariya_overnight.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# ------------------------------------------------------------
# Trip core (enhanced name)
# ------------------------------------------------------------
TITLE = "Cairo to Bahariya Oasis: Overnight Desert Safari (Black Desert, Crystal Mountain & White Desert)"
TEASER = (
    "Escape Cairo for an overnight 4×4 desert adventure—Black Desert peaks, Crystal Mountain, "
    "Agabat valleys, and camping under the stars in the surreal White Desert."
)

PRIMARY_DEST = DestinationName.BAHAREYA  # “Bahareya Oasis”
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.WHITE_BLACK]

DURATION_DAYS = 2
GROUP_SIZE_MAX = 49
BASE_PRICE = Decimal("330.00")
TOUR_TYPE_LABEL = "Daily Tour — Safari / Camping"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Desert",
    "Overnight",
    "Camping",
    "Safari",
    "White Desert",
    "Bahariya Oasis",
    "4x4",
    "Stargazing",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Discover the palm groves and springs of Bahariya Oasis.",
    "See volcanic peaks in the otherworldly Black Desert.",
    "Walk the glittering ridge of Crystal Mountain, formed of natural quartz.",
    "Traverse the Valley of Agabat’s dramatic dunes and limestone formations.",
    "Camp in the White Desert amid surreal chalk sculptures.",
    "Enjoy a Bedouin dinner by the campfire and stargaze under pristine skies.",
    "Wake to a breathtaking desert sunrise before the return to Cairo.",
]

ABOUT = """\
Trade city noise for desert silence on an overnight 4×4 safari from Cairo. After a scenic drive to Bahariya Oasis,
head by Jeep across the Black Desert’s volcanic hills, stop at crystal-studded ridges, then sweep through the
golden dunes of Agabat. As daylight fades, camp among the White Desert’s wind-sculpted chalk formations,
share a Bedouin dinner by the fire, and marvel at a riot of stars. Sunrise, breakfast, and a relaxed ride back round
out Egypt’s most rewarding short desert escape.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo → Bahariya Oasis → Black Desert • Crystal Mountain • Agabat • White Desert Camp",
        "steps": [
            ("", "Morning pickup in Cairo; drive ~4 hours to Bahariya Oasis."),
            ("", "Switch to 4×4 Jeeps and begin the desert safari."),
            ("", "Stop at the Black Desert’s basalt-capped hills for views and photos."),
            ("", "Visit Crystal Mountain; continue to the Valley of Agabat."),
            ("", "Arrive in the White Desert; set up camp and enjoy Bedouin dinner."),
            ("", "Stargazing around the campfire; overnight in the desert."),
        ],
    },
    {
        "day": 2,
        "title": "White Desert Sunrise • Return via Bahariya Oasis → Cairo",
        "steps": [
            ("", "Sunrise over the White Desert; camp breakfast."),
            ("", "Break camp; 4×4 drive back to Bahariya Oasis."),
            ("", "Short oasis stop and lunch; begin return drive to Cairo."),
            ("", "Evening drop-off at your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Pick-up & drop-off from Cairo hotel in private air-conditioned vehicle",
    "4×4 Jeep for the desert safari",
    "Accommodation: 1 night camping in the White Desert",
    "Professional English-speaking desert guide",
    "Meals: 1 Breakfast, 2 Lunches, 1 Dinner",
    "Bottled water and soft drinks",
    "Entrance fees to all mentioned sites",
]

EXCLUSIONS = [
    "Personal expenses",
    "Tips (gratuities)",
    "Travel insurance",
    "Optional activities not listed in the program",
]

FAQS = [
    ("How long is the drive from Cairo to Bahariya Oasis?", "Around 4 hours each way, with rest stops en route."),
    ("Is camping in the White Desert safe?", "Yes—guided by professional desert teams with all equipment provided."),
    ("Are bathrooms available at the campsite?", "Facilities are basic in the desert; essential amenities are provided."),
    ("What should I pack?", "Comfortable clothing, sturdy shoes, sunscreen, hat, light jacket for cool nights, and a camera."),
    ("Can vegetarian or special meals be arranged?", "Yes—please share dietary requirements in advance."),
]

# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Seed the Bahariya Oasis Overnight Desert Safari trip, with destinations, price, languages, categories, and full content."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Destinations
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Primary destination 'Bahareya Oasis' not found. Seed destinations first."))
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

        class _NullCtx:
            def __enter__(self): return self
            def __exit__(self, *a): return False

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
                ),
            )

            # Update core fields for re-runs
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
