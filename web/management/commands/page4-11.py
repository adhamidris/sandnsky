# web/management/commands/seed_trip_giza_atv.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# ------------------------------------------------------------
# Trip core (enhanced name format)
# ------------------------------------------------------------
TITLE = "Giza Pyramids Desert: Quad Bike (ATV) Sunrise/Sunset Ride"
TEASER = (
    "Kick up desert sand on a guided ATV ride with wide-open Giza pyramid panoramas—"
    "beginner-friendly, epic photos, sunrise or sunset options."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1                   # ~2 hours experience
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("35.00")
TOUR_TYPE_LABEL = "Daily Tour — Desert ATV"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Adventure",
    "ATV",
    "Desert",
    "Giza Pyramids",
    "Photography",
    "Sunrise",
    "Sunset",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Ride your own quad bike through the open Giza desert with pyramid panoramas.",
    "Beginner-friendly route with safety briefing and protective gear included.",
    "Choose sunrise, daytime, or sunset slots for the best light and cooler temps.",
    "Expert local leader guides safe tracks away from traffic and crowds.",
    "Stop for epic photos at exclusive desert viewpoints.",
    "Optional hotel pickup/drop-off for a smooth, hassle-free experience.",
]

ABOUT = """\
Swap the city for golden dunes on a high-energy ATV ride with panoramic views of the Giza pyramids.
After a quick safety briefing, follow your guide over rolling desert tracks to wide-open vantage points for
unforgettable photos. Machines are automatic and suitable for first-timers. Pick sunrise or sunset for cooler
temps and dramatic light—then throttle up for pure, sandy fun.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "ATV Ride at the Giza Desert (≈2 hours)",
        "steps": [
            ("", "Meet at the desert ATV base (or hotel pickup if selected)."),
            ("", "Safety briefing, helmet/goggles fitting, and ATV controls overview."),
            ("", "Guided ride across desert tracks with pyramid panoramas."),
            ("", "Photo stop at a high-viewpoint; short rests as needed."),
            ("", "Ride back to base; return gear and debrief."),
            ("", "Hotel drop-off if transfers option selected."),
        ],
    },
]

INCLUSIONS = [
    "Quad bike rental for the duration of the ride",
    "Safety equipment (helmet, goggles)",
    "Experienced local tour leader/guide",
    "Instructions and safety briefing before the ride",
    "Bottled water",
    "Photo stop with panoramic pyramid view",
    "Round-trip hotel transfers (if option selected)",
]

EXCLUSIONS = [
    "Entry tickets to the Giza Pyramids site (this is a desert ride outside the complex)",
    "Meals or snacks",
    "Personal expenses",
    "Tips for guide (optional)",
    "Camel or horse rides",
]

FAQS = [
    ("Do I need prior ATV experience?", "No—automatic bikes and a full briefing make it beginner-friendly."),
    ("Is it safe to ride in the desert?", "Yes—gear is provided and routes are chosen for safety away from traffic."),
    ("Can children join?", "Generally 16+ to ride solo; younger passengers may ride with an adult (subject to local policy)."),
    ("How long is the actual ride?", "About 1 hour of riding time with short stops for photos and rest."),
    ("What should I wear?", "Closed-toe shoes, sunglasses; a scarf/bandana is recommended for dust."),
    ("Can we visit inside the pyramid complex?", "This experience stays in the desert zone with distant views; complex entry isn’t included."),
    ("What start times are available?", "Sunrise, mid-day, and sunset. Sunrise/sunset have cooler temps and great light."),
]

# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Giza Pyramids Desert ATV tour with destinations, price, languages, categories, and full content."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Primary destination 'Giza' not found. Seed destinations first."))
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

            # Update core fields on re-run
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
