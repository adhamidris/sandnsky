# web/management/commands/seed_trip_cairo_luxor_flight.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# --- Trip core (enhanced title) ---------------------------------------------

TITLE = "Cairo to Luxor: Day Trip by Flight (Karnak, Valley of the Kings & Hatshepsut)"
TEASER = (
    "Round-trip flights from Cairo, Egyptologist guide, Karnak Temple, Valley of the Kings (3 tombs), "
    "Hatshepsut Temple, Colossi of Memnon, lunch and transport—done in one seamless day."
)

PRIMARY_DEST = DestinationName.LUXOR
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1                 # ~12 hours same-day
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("390.00")    # “from $390,00” → 390.00
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Flight Day Trip",
    "Karnak",
    "Valley of the Kings",
    "Hatshepsut Temple",
]

# --- Content blocks ----------------------------------------------------------

HIGHLIGHTS = [
    "Fly Cairo ↔ Luxor in one day—skip long overland drives.",
    "Guided visit to Karnak Temple, Egypt’s largest temple complex.",
    "Explore the Valley of the Kings (entry to 3 tombs).",
    "Discover the Mortuary Temple of Hatshepsut at Deir el-Bahari.",
    "Photo stop at the Colossi of Memnon.",
    "Included lunch at a local restaurant; bottled water provided.",
    "Led by a professional Egyptologist guide with air-conditioned transport.",
]

ABOUT = """\
Make the most of limited time with a seamless day trip to Luxor by air. Start with an early transfer for your Cairo→Luxor flight, then
meet your Egyptologist guide to explore Karnak Temple, the Valley of the Kings (entry to 3 tombs), the cliff-carved Temple of Queen
Hatshepsut, and the Colossi of Memnon. Lunch is included before your return flight back to Cairo and hotel drop-off. A compact,
comfortable way to experience Ancient Thebes in a single, unforgettable day.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Hotel Pickup (Cairo) • Fly to Luxor • East & West Bank Highlights • Fly Back",
        "steps": [
            ("", "Pick-up from your Cairo hotel and transfer to airport."),
            ("", "Flight from Cairo to Luxor."),
            ("", "Meet your Egyptologist guide on arrival; begin the tour."),
            ("", "Visit Karnak Temple Complex (East Bank)."),
            ("", "Cross the Nile to the West Bank."),
            ("", "Explore the Valley of the Kings (entry to 3 tombs)."),
            ("", "Visit the Temple of Hatshepsut (Deir el-Bahari)."),
            ("", "Photo stop at the Colossi of Memnon."),
            ("", "Enjoy lunch at a local restaurant."),
            ("", "Free time or optional add-ons (e.g., felucca ride)."),
            ("", "Transfer to Luxor Airport • flight back to Cairo."),
            ("", "Arrival in Cairo and hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Round-trip domestic flights Cairo ↔ Luxor",
    "Hotel pick-up and drop-off in Cairo",
    "Air-conditioned transportation in Luxor",
    "Professional English-speaking Egyptologist guide",
    "Entrance fees to all mentioned sites",
    "Lunch at a local restaurant",
    "Bottled water",
]

EXCLUSIONS = [
    "Personal expenses",
    "Tips and gratuities",
    "Optional activities (e.g., felucca ride on the Nile)",
    "Drinks during lunch (unless specified)",
    "Any services not mentioned",
]

FAQS = [
    ("Is the tour suitable for children?",
     "Yes—note the early start and flights can make the day long for younger kids."),
    ("What should I bring?",
     "Passport for check-in, comfortable shoes, hat, sunglasses, sunscreen, and some cash for extras."),
    ("Are flights included?",
     "Yes—round-trip domestic flights between Cairo and Luxor are included."),
    ("Do I need to book in advance?",
     "Yes—due to flight coordination, advance booking is strongly recommended."),
    ("Can I choose which tombs to enter in the Valley of the Kings?",
     "Yes—choose three from those open to the public on the day."),
    ("Are vegetarian or special meals available?",
     "Yes—please advise dietary needs in advance."),
]


# --- Command -----------------------------------------------------------------

class Command(BaseCommand):
    help = "Seeds the Cairo → Luxor flight day trip with destinations, price, content, and relations."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["luxor", "cairo"], default="luxor",
                            help="Choose which destination is primary (default: luxor).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Allow switching primary via flag
        primary_name = DestinationName.LUXOR if opts["primary"] == "luxor" else DestinationName.CAIRO
        secondary = DestinationName.CAIRO if primary_name == DestinationName.LUXOR else DestinationName.LUXOR

        # Resolve destinations (must exist)
        try:
            dest_primary = Destination.objects.get(name=primary_name)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Primary destination '{primary_name}' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in [secondary]:
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

            # Update core fields if changed
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

            # M2M sets
            if not dry:
                trip.additional_destinations.set(addl_dests)
                trip.languages.set(lang_objs)
                trip.category_tags.set(cat_objs)

            # Related content handling
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
