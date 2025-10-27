# web/management/commands/seed_trip_felucca_cairo.py
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
TITLE = "Cairo: Felucca Nile Cruise — Traditional Sailboat Experience"
TEASER = (
    "Unwind on a classic wind-powered felucca as you glide along the Nile and take in Cairo’s skyline. "
    "Flexible morning, afternoon, sunset, or evening departures. Gentle, photogenic, and family-friendly."
)

PRIMARY_DEST = DestinationName.CAIRO
DURATION_DAYS = 1            # day product; duration (45–60 mins) reflected in copy
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("35.00")
TOUR_TYPE_LABEL = "Daily Tour — Single"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
]

CATEGORY_TAGS = [
    "Day Trip",
    "Boat",
    "Nile",
    "Felucca",
    "Cairo",
    "Sunset",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Sail the Nile on a traditional wooden felucca (wind-powered).",
    "Peaceful skyline views of Cairo from the water.",
    "Choose morning, afternoon, sunset, or evening rides.",
    "Ideal for couples, families, solo travelers, and small groups.",
    "Relaxed pace with optional tea or soft drinks on board.",
    "Optional hotel pickup and drop-off for seamless logistics.",
]

ABOUT = """\
Experience Cairo’s gentlest, most authentic river activity aboard a traditional wooden felucca. With no engine, the boat
glides quietly on the Nile, offering fresh breezes and photogenic views of bridges, river birds, and the city skyline.
Pick a daytime slot or aim for the golden hues of sunset—either way, it’s an easy, short escape that fits any itinerary.
Great for couples, families, and small groups; life jackets are provided.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Felucca Sail on the Nile (45–60 minutes)",
        "steps": [
            ("", "Meet at the riverside dock (optional hotel pickup available)."),
            ("", "Board your classic wooden felucca; safety briefing and push-off."),
            ("", "Leisurely sail with skyline views; optional tea/soft drinks as available."),
            ("", "Return to dock; optional transfer back to hotel."),
        ],
    },
]

INCLUSIONS = [
    "Traditional felucca boat ride on the Nile (approx. 45–60 minutes)",
    "English-speaking captain/guide",
    "Life jackets for safety",
    "Bottled water",
]

EXCLUSIONS = [
    "Hotel pickup and drop-off (available as an add-on)",
    "Meals or snacks (unless pre-arranged)",
    "Gratuities (optional)",
    "Personal expenses",
]

FAQS = [
    ("How long is the felucca ride?",
     "Most rides last between 45 and 60 minutes."),
    ("Is it a private boat?",
     "Both private and shared options are available—choose during booking."),
    ("Can I book a sunset ride?",
     "Yes—sunset departures are very popular; booking ahead is recommended."),
    ("Is it safe for kids or seniors?",
     "Yes—feluccas sail gently and life jackets are provided."),
    ("What should I bring?",
     "Sunglasses, hat, camera, and a light jacket for evening rides."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Cairo Felucca Nile Cruise with price, content, languages, and categories."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Destination
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Primary destination 'Cairo' not found. Seed destinations first."))
            return

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

            # Update core fields if re-run
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
                trip.additional_destinations.clear()  # Cairo-only listing
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
        self.stdout.write("Languages: " + ", ".join(f"{l.name} ({l.code})" for l in lang_objs))
        self.stdout.write("Categories: " + ", ".join(c.name for c in cat_objs))
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
