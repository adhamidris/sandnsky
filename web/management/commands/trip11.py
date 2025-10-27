# web/management/commands/seed_trip_cairo_white_desert_7day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# -------------------------------------------------------------------
# Trip core (enhanced name per your rules)
# -------------------------------------------------------------------
TITLE = "Cairo to White Desert: 7-Day Adventure (Bahariya Oasis, El-Fayoum & Pyramids)"
TEASER = (
    "A week of monuments and deserts: Egyptian Museum, Citadel & Khan El Khalili; "
    "Giza, Saqqara, Memphis & Dahshur; El-Fayoum (Wadi El Rayan/Qarun); "
    "Bahariya Oasis with Black Desert, Crystal Mountain, and the otherworldly White Desert—"
    "plus a Nile Maxim dinner cruise."
)

# Default primary and additional destinations
PRIMARY_DEST_DEFAULT = DestinationName.CAIRO
ALSO_APPEARS_IN = [
    DestinationName.FAYOUM,
    DestinationName.BAHAREYA,
    DestinationName.WHITE_BLACK,
]

DURATION_DAYS = 7
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("1230.00")  # “$1.230,00” → 1230.00
TOUR_TYPE_LABEL = "Multi-Day — Desert Safari"

# Languages listed in the brief (no Russian on this one)
LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "Desert Safari",
    "Nile Dinner Cruise",
    "Pyramids",
    "White Desert",
    "Bahariya Oasis",
    "Fayoum",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Luxury Nile Maxim dinner cruise with live music and folklore shows.",
    "Explore the Great Pyramids, Sphinx, Saqqara, Memphis, and Dahshur.",
    "Dive into history at the Egyptian Museum and Saladin Citadel; wander Khan El Khalili.",
    "Day trip to El-Fayoum: Wadi El Rayan waterfalls, Lake Qarun, Mudawara Mountain (optional sandboarding).",
    "Bahariya Oasis off-road adventure: Black Desert and Crystal Mountain.",
    "Camp under the stars in the surreal White Desert with 4x4 support.",
    "Experienced Egyptologist guides; private A/C transport; daily lunches included.",
]

ABOUT = """\
Embark on seven unforgettable days across Cairo and the Western Desert. Begin with the Nile Maxim dinner cruise, then tour the
Egyptian Museum, Saladin Citadel, and Khan El Khalili. Visit the Giza Plateau and nearby necropolises (Saqqara, Memphis, Dahshur),
venture to El-Fayoum’s lakes and waterfalls, and head west to Bahariya Oasis for Black Desert and Crystal Mountain. Spend a full day
in the White Desert’s alien landscapes before returning to Cairo. Daily lunches, expert guides, 4×4 desert support, and all site
entries are included; Cairo accommodation is intentionally left flexible so you can choose where to stay.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Arrival in Cairo • Evening Nile Maxim Dinner Cruise",
        "steps": [
            ("", "Meet & assist at Cairo International Airport."),
            ("", "Evening luxury dinner cruise on the Nile with live entertainment."),
        ],
    },
    {
        "day": 2,
        "title": "Egyptian Museum • Saladin Citadel • Khan El Khalili",
        "steps": [
            ("", "Guided visit to the Egyptian Museum (including Tutankhamun highlights)."),
            ("", "Explore the Saladin Citadel and Mohamed Ali Mosque."),
            ("", "Stroll the historic Khan El Khalili bazaar."),
        ],
    },
    {
        "day": 3,
        "title": "El-Fayoum Day Tour • Giza, Saqqara, Memphis & Dahshur",
        "steps": [
            ("", "Morning: El-Fayoum (Wadi El Rayan waterfalls, Lake Qarun, Mudawara Mountain; optional sandboarding)."),
            ("", "Afternoon: Giza Pyramids & Sphinx, Saqqara Step Pyramid, ancient Memphis, Dahshur (Bent & Red Pyramids)."),
        ],
    },
    {
        "day": 4,
        "title": "Cairo → Bahariya Oasis • Black Desert • Crystal Mountain",
        "steps": [
            ("", "Drive to Bahariya Oasis (approx. 4–5 hours)."),
            ("", "Visit the Black Desert and Crystal Mountain."),
            ("", "Campfire dinner and overnight in desert or local lodge."),
        ],
    },
    {
        "day": 5,
        "title": "White Desert Exploration • Return to Bahariya",
        "steps": [
            ("", "Full-day exploration of the White Desert formations (Mushroom Rock, Chicken Rock, and more)."),
            ("", "Return to Bahariya Oasis for overnight."),
        ],
    },
    {
        "day": 6,
        "title": "Return to Cairo • Free Evening",
        "steps": [
            ("", "Drive back to Cairo after breakfast."),
            ("", "Free evening for optional activities or rest."),
        ],
    },
    {
        "day": 7,
        "title": "Cairo Airport Transfer • Departure",
        "steps": [
            ("", "Transfer to Cairo International Airport for departure."),
        ],
    },
]

INCLUSIONS = [
    "Daily lunch during all touring days",
    "All airport transfers (arrival and departure)",
    "Private air-conditioned transportation throughout",
    "Entry fees to all mentioned attractions",
    "Experienced English-speaking Egyptologist guide",
    "All 4×4 transportation for desert excursions",
    "1 night camping in the White Desert (tents/sleeping gear provided)",
    "1 night in Bahariya Oasis lodge/hotel",
    "Bottled water during desert trips",
    "Government taxes and service charges",
]

EXCLUSIONS = [
    "Hotel accommodation in Cairo",
    "Egypt entry visa",
    "Personal expenses (souvenirs, tips, etc.)",
    "Drinks during meals unless specified",
    "Any extra optional activities not mentioned",
    "Tipping for guides and drivers",
]

FAQS = [
    ("Is accommodation in Cairo included?",
     "No—choose any hotel you like. The package intentionally excludes Cairo stays."),
    ("Do I need a visa to join?",
     "Most travelers need an entry visa (online or on arrival depending on nationality)."),
    ("What vehicles are used in the desert?",
     "4×4 air-conditioned vehicles for all desert segments."),
    ("Is the tour suitable for children or seniors?",
     "Generally yes, but off-road portions may not suit guests with mobility issues."),
    ("Are meals included?",
     "Lunch is included daily; dinner is included on the cruise and camping night; breakfasts depend on your Cairo hotel."),
    ("What should I pack for the desert?",
     "Light layers for day, warm clothes for night, sunscreen, sunglasses, hat, and a camera. Camping gear is provided."),
]


class Command(BaseCommand):
    help = "Seeds the 7-Day Cairo → White Desert adventure (Bahariya, El-Fayoum & Pyramids) with destinations, price, and content."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["cairo", "fayoum", "bahareya", "white-black"], default="cairo",
                            help="Choose which destination is primary (default: cairo).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve primary
        primary_map = {
            "cairo": DestinationName.CAIRO,
            "fayoum": DestinationName.FAYOUM,
            "bahareya": DestinationName.BAHAREYA,
            "white-black": DestinationName.WHITE_BLACK,
        }
        primary_name = primary_map[opts["primary"]]

        # Additional destinations (exclude chosen primary)
        addl_names = [d for d in ALSO_APPEARS_IN + [PRIMARY_DEST_DEFAULT] if d != primary_name]

        # Look up destinations
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


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
