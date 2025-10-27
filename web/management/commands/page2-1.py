# web/management/commands/seed_trip_cairo_elminya_day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# --- Trip core (enhanced title) ---------------------------------------------
TITLE = "Cairo to El-Minya: Full-Day Tour (Beni Hassan & Tell El-Amarna)"
TEASER = (
    "Private full-day drive from Cairo to Middle Egypt: Beni Hassan’s painted tombs and Akhenaten’s Tell El-Amarna, "
    "with Egyptologist guide, lunch, entries, and A/C transport."
)

PRIMARY_DEST = DestinationName.CAIRO      # El-Minya isn’t a DestinationName in your enum
ALSO_APPEARS_IN = []                      # no secondary destinations available in enum

DURATION_DAYS = 1                         # ~12 hours same day
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("220.00")            # “$220,00” → 220.00
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Trip",
    "Middle Egypt",
    "El-Minya",
    "Beni Hassan",
    "Tell El-Amarna",
    "Archaeology",
]

# --- Content blocks ----------------------------------------------------------
HIGHLIGHTS = [
    "Explore Beni Hassan tombs with vivid Middle Kingdom wall paintings.",
    "Visit Tell El-Amarna, Akhenaten’s short-lived capital devoted to Aten.",
    "Scenic Nile-valley drive through Middle Egypt with comfort stops.",
    "Private A/C vehicle and licensed Egyptologist guide.",
    "Authentic Egyptian lunch at a local restaurant (drinks extra).",
    "Entrance fees to listed sites included.",
]

ABOUT = """\
Escape Cairo for a deep dive into Middle Egypt’s lesser-visited treasures. Travel by private A/C vehicle with your Egyptologist guide
to El-Minya, where Beni Hassan’s painted tombs bring daily life scenes to color, then continue to Tell El-Amarna—the revolutionary
capital of Akhenaten and Nefertiti. Lunch along the Nile, bottled water, and all listed entries are included for a seamless, insightful day.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo → El-Minya • Beni Hassan • Tell El-Amarna • Return",
        "steps": [
            ("", "Early hotel pickup in Cairo; depart by private A/C vehicle."),
            ("", "Scenic drive along the Nile valley with comfort/rest stops."),
            ("", "Guided visit: Beni Hassan tombs and Middle Kingdom scenes."),
            ("", "Continue to Tell El-Amarna; explore temples, palatial ruins, and royal tomb area (as accessible)."),
            ("", "Lunch at a local El-Minya restaurant (drinks extra)."),
            ("", "Return drive to Cairo; hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Private air-conditioned vehicle transfers Cairo ↔ El-Minya",
    "Licensed Egyptologist tour guide",
    "Entrance fees to Beni Hassan and Tell El-Amarna",
    "Lunch at a local restaurant in El-Minya",
    "Bottled water during the tour",
    "All taxes and service charges",
]

EXCLUSIONS = [
    "Personal expenses",
    "Gratuities (optional but recommended)",
    "Any additional entrance fees not mentioned",
    "Drinks during lunch",
    "Optional activities not included in the itinerary",
]

FAQS = [
    ("Is this a private or group tour?", "Private—your own guide, vehicle, and schedule pacing."),
    ("How long is the tour?", "About 12–13 hours including driving time."),
    ("Is it suitable for children?", "Yes, though the long drive may be tiring for very young kids."),
    ("Are there restroom stops on the way?", "Yes—comfort stops are planned both ways."),
    ("Can I customize this tour?", "Absolutely—tell us your interests or requests in advance."),
    ("What should I bring?", "Comfortable shoes, hat, sunscreen, and a camera; bring cash for tips and extras."),
]

# --- Command -----------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Cairo → El-Minya day trip (Beni Hassan & Tell El-Amarna) with price, content, and categories."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        # Keep primary switch for consistency (only 'cairo' makes sense with current enum)
        parser.add_argument("--primary", choices=["cairo"], default="cairo",
                            help="Choose which destination is primary (default: cairo).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations (must exist)
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Destination 'Cairo' not found. Seed destinations first."))
            return

        addl_dests = []  # none in enum for El-Minya

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

            # Update core fields if changed
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

            if not dry:
                trip.additional_destinations.set(addl_dests)  # none
                trip.languages.set(lang_objs)
                trip.category_tags.set(cat_objs)

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


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
