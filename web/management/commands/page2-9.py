# web/management/commands/seed_trip_cairo_museums_day.py
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
TITLE = "Cairo to Giza: Museums Double — Grand Egyptian Museum & Egyptian Museum Day Tour"
TEASER = (
    "One epic museum day: the cutting-edge Grand Egyptian Museum near the pyramids, "
    "then the historic Egyptian Museum in Tahrir. Private A/C transport, Egyptologist guide, "
    "entries and lunch included."
)

# Default primary where the day is anchored (GEM near Giza); also show on Cairo
PRIMARY_DEST_DEFAULT = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1              # ~8 hours
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("130.00") # “$130,00” → 130.00
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Trip",
    "Museums",
    "GEM",
    "Egyptian Museum",
    "Cairo",
    "Giza",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Visit two world-class museums in one day: modern GEM and classic Egyptian Museum.",
    "See Tutankhamun’s treasures presented together at the Grand Egyptian Museum.",
    "Expert commentary from a licensed Egyptologist guide.",
    "Comfortable round-trip transport with hotel pickup in Cairo/Giza.",
    "Lunch included at a local restaurant; bottled water provided.",
    "Ideal for first-timers and Egyptology enthusiasts alike.",
]

ABOUT = """\
Dive deep into Egypt’s past in a single curated day. Begin at the Grand Egyptian Museum—immersive, modern galleries showcasing
colossal statues and the complete Tutankhamun collection—then continue to the time-honored Egyptian Museum in Tahrir, where
decades of Egyptology history line classic halls. Your Egyptologist guide handles context, tickets, and pacing; private A/C transport,
entries, lunch, and bottled water keep things seamless.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "GEM & Egyptian Museum Day",
        "steps": [
            ("", "Hotel pickup in Cairo or Giza; drive to Giza plateau area."),
            ("", "Arrive at the Grand Egyptian Museum (GEM). Guided visit: Tutankhamun collection, statues hall, interactive galleries."),
            ("", "Lunch at a local restaurant."),
            ("", "Drive to downtown Cairo; arrive at the Egyptian Museum in Tahrir."),
            ("", "Guided tour: Royal mummies area (if open), Old Kingdom to Greco-Roman highlights, iconic artifacts."),
            ("", "Return transfer to your hotel in Cairo/Giza."),
        ],
    },
]

INCLUSIONS = [
    "Hotel pickup and drop-off (Cairo & Giza)",
    "Private air-conditioned vehicle",
    "Entry tickets to the Grand Egyptian Museum and the Egyptian Museum",
    "Professional Egyptologist tour guide",
    "Lunch at a local restaurant",
    "Bottled water during the tour",
    "All service charges and taxes",
]

EXCLUSIONS = [
    "Tipping / gratuities for guide and driver",
    "Optional activities or personal expenses",
    "Entry to special exhibition halls (e.g., Royal Mummies Room) if separately ticketed",
    "Travel insurance",
]

FAQS = [
    ("Is the Grand Egyptian Museum fully open?",
     "GEM is in phased opening with major galleries accessible; the experience is substantial and impressive."),
    ("How long is the tour?",
     "Typically 8–9 hours including transportation and guided visits."),
    ("Can I customize start time or add extras?",
     "Yes—private tours can adjust pickup time and add experiences (e.g., Nile cruise)."),
    ("Do I need to buy tickets in advance?",
     "No—standard entries are included and handled by your guide."),
    ("Is photography allowed?",
     "Generally yes; some areas (like Royal Mummies) may have restrictions or require a photo pass."),
    ("What should I wear?",
     "Comfortable clothing and shoes; most time is indoors but expect some walking."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the GEM + Egyptian Museum day tour with price, content, languages, categories, and multi-destination listing."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["giza", "cairo"], default="giza",
                            help="Choose the primary destination (default: giza).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        primary_map = {
            "giza": DestinationName.GIZA,
            "cairo": DestinationName.CAIRO,
        }
        primary_name = primary_map[opts["primary"]]
        addl_names = [d for d in ALSO_APPEARS_IN + [PRIMARY_DEST_DEFAULT] if d != primary_name]

        # Resolve destinations
        try:
            dest_primary = Destination.objects.get(name=primary_name)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Primary destination '{primary_name}' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in addl_names:
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

            # Update core fields if needed
            changed = []
            def setf(field, value):
                old = getattr(trip, field)
                if old != value:
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

            # Related content (reseed if asked)
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


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
