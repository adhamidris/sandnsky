# web/management/commands/seed_trip_cairo_alexandria_2day.py
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
TITLE = "Cairo to Alexandria: 2-Day Highlights (Pyramids, Museum & Coastal City) — Meals Included"
TEASER = (
    "Two-day private tour covering Cairo’s Giza Pyramids, Sphinx and Egyptian Museum, "
    "then Alexandria’s Kom El Shoqafa, Pompey’s Pillar, Roman Amphitheatre and Bibliotheca. "
    "Hotel pickups, entries and lunches both days included; no accommodation (flexible)."
)

PRIMARY_DEST_DEFAULT = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.ALEXANDRIA, DestinationName.GIZA]

DURATION_DAYS = 2
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("280.00")  # “$280,00” → 280.00
TOUR_TYPE_LABEL = "Multi-Day — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "Cairo",
    "Alexandria",
    "Giza",
    "Pyramids",
    "Museums",
    "Coastal",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Stand before the Pyramids of Giza and the Great Sphinx.",
    "Explore the Egyptian Museum’s treasures, including Tutankhamun highlights.",
    "Descend into the Catacombs of Kom El Shoqafa in Alexandria.",
    "See Pompey’s Pillar, the Roman Amphitheatre, and Bibliotheca Alexandrina.",
    "Private A/C transport with Egyptologist guide; hotel pickup & drop-off.",
    "Lunch included both days at handpicked local restaurants.",
]

ABOUT = """\
Experience two iconic Egyptian cities in one seamless 2-day package. Day 1 focuses on Cairo’s ancient wonders at the Giza Plateau
and the Egyptian Museum. Day 2 heads to Alexandria for Greco-Roman highlights and coastal vibes. Private A/C transport, expert
guide, all standard entries, bottled water, and lunches are included. Accommodation is intentionally excluded so you can stay
wherever suits your style and budget in Cairo.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo Highlights — Giza Pyramids, Sphinx & Egyptian Museum",
        "steps": [
            ("", "Pickup from your hotel in Cairo or Giza."),
            ("", "Visit the Giza Pyramids and Great Sphinx (photo stops; optional add-ons not included)."),
            ("", "Explore the Egyptian Museum with your Egyptologist guide."),
            ("", "Lunch at a local restaurant."),
            ("", "Optional brief stop at a bazaar or perfume/oil shop."),
            ("", "Return transfer to your hotel in Cairo/Giza."),
        ],
    },
    {
        "day": 2,
        "title": "Alexandria Discovery — Kom El Shoqafa, Roman Sites & Bibliotheca",
        "steps": [
            ("", "Early pickup; drive to Alexandria (approx. 2.5–3 hours)."),
            ("", "Visit the Catacombs of Kom El Shoqafa."),
            ("", "See Pompey’s Pillar and the Roman Amphitheatre."),
            ("", "Explore the Bibliotheca Alexandrina (interior/exterior per opening hours)."),
            ("", "Lunch at a seaside restaurant."),
            ("", "Drive back to Cairo; hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Professional Egyptologist guide (multilingual on request)",
    "Private air-conditioned vehicle for both days",
    "Hotel pickup and drop-off in Cairo or Giza",
    "Entrance fees to all listed sites",
    "Lunch at local restaurants on both days",
    "Bottled water",
    "All service charges and taxes",
]

EXCLUSIONS = [
    "Hotel accommodation",
    "Breakfast and dinner",
    "Gratuities (optional)",
    "Personal expenses",
    "Entrance to special exhibits (e.g., Mummy Room at the Egyptian Museum)",
    "Any services not mentioned under Inclusions",
]

FAQS = [
    ("Is accommodation included in the tour?",
     "No—this package is designed for travelers who already have lodging in Cairo."),
    ("Are hotel pickups and drop-offs included?",
     "Yes, from Cairo or Giza hotels on both days."),
    ("Are meals provided?",
     "Lunch is included on both days at local restaurants."),
    ("Is the tour private or group-based?",
     "Private by default; we can arrange small groups on request."),
    ("Can I customize the itinerary?",
     "Yes—tell us your preferences during booking."),
    ("How far is Alexandria from Cairo?",
     "About 220 km (roughly 2.5–3 hours each way)."),
    ("What should I bring?",
     "Comfortable shoes, sun protection, camera, passport/ID, and personal items."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the 2-Day Cairo & Alexandria tour with price, content, languages, categories, and multi-destination listing."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["cairo", "alexandria", "giza"], default="cairo",
                            help="Choose primary destination (default: cairo).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        primary_map = {
            "cairo": DestinationName.CAIRO,
            "alexandria": DestinationName.ALEXANDRIA,
            "giza": DestinationName.GIZA,
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
