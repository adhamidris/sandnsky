# web/management/commands/seed_trip_cairo_by_night.py
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
TITLE = "Cairo by Night: Free Walking Tour — Horse Carriage, Ice Cream & Cairo Tower Views"
TEASER = (
    "Feel Cairo after dark with a guided night walk + horse-drawn carriage, Nile Corniche vibes, local ice cream, "
    "and Cairo Tower views. A relaxed, social, pay-what-you-want style experience with easy hotel pickup/drop-off."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.GIZA]  # shows under both Cairo & Giza

# Your Trip model stores integer days (min 1). For 3-hour tours, set to 1.
DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("40.00")
TOUR_TYPE_LABEL = "Daily Tour — Night Walk"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
]

CATEGORY_TAGS = [
    "Night Tour",
    "Cairo",
    "Walking Tour",
    "City Lights",
    "Foodie Stop",
    "Culture",
    "City Tour",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Explore downtown Cairo and Khedival avenues with a local night guide.",
    "Horse-drawn carriage ride through atmospheric streets and the Nile Corniche.",
    "Savor a local ice cream stop and casual social time.",
    "External view/photo stop of Cairo Tower with skyline panoramas.",
    "Insider stories on Tahrir Square and modern Cairo life.",
    "Flexible, relaxed pacing—great for solo travelers and small groups.",
]

ABOUT = """\
“Cairo Nights” blends the city’s glow, stories, and flavors into a three-hour evening walk. Start with a horse-drawn carriage
through Khedival streets and along the Nile Corniche, wander lively downtown alleys, cool off with local ice cream, and
cap it with Cairo Tower views from outside. Your guide threads history, daily life, and hidden corners into an easy,
sociable night out—with simple logistics and hotel pickup/drop-off.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo by Night Highlights (3 hours)",
        "steps": [
            ("18:00", "Hotel pickup in Cairo/Giza and transfer downtown."),
            ("", "Horse-drawn carriage ride through Khedival Cairo and the Nile Corniche."),
            ("", "Guided night walk: downtown streets, Tahrir Square context, local life & stories."),
            ("", "Local ice cream stop (classic Egyptian flavors)."),
            ("", "Cairo Tower (external stop) for skyline photos."),
            ("21:00", "Return transfer and hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Guided night experience with local tour leader",
    "Horse carriage ride",
    "Complimentary local ice cream",
    "Hotel pickup & drop-off (Cairo/Giza)",
    "Photo stops along the way",
    "Private air-conditioned vehicle for transfers",
    "Bottled water",
]

EXCLUSIONS = [
    "Personal expenses",
    "Gratuities (tipping)",
    "Optional tours or add-ons",
    "Entry to Cairo Tower interior (external photo stop only)",
]

FAQS = [
    ("Is the walking tour really free?", "Yes—pay-what-you-want style. Tips for your guide are appreciated."),
    ("How long is the tour?", "About 3 hours including transfers and stops."),
    ("Is it suitable for children?", "Yes. Families are welcome; pace can be adjusted."),
    ("Do I need to book in advance?", "Recommended—spots are limited, especially for sunset/evening slots."),
    ("What should I bring?", "Comfortable shoes, a light jacket for evenings, camera/phone, and some cash for extras."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the 'Cairo by Night' free walking tour with price, content, languages, and categories."

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
            self.stderr.write(self.style.ERROR("Primary destination 'Cairo' not found. Seed destinations first."))
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
                )
            )

            # Update core fields if rerun
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
