# web/management/commands/seed_trip_cairo_alex_3day.py
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
TITLE = "Cairo to Alexandria: 3-Day Highlights (Pyramids ATV, GEM & Nile Dinner Cruise)"
TEASER = (
    "3 days of Egypt’s essentials: Pyramids & Sphinx with a 1-hour ATV ride, the Grand Egyptian Museum, "
    "Memphis–Saqqara–Dahshur, Nile Maxim Dinner Cruise, and a full-day Alexandria tour—lunch included daily."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.ALEXANDRIA, DestinationName.GIZA]

DURATION_DAYS = 3
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("500.00")  # “from $500,00” → 500.00
TOUR_TYPE_LABEL = "Multi-Day — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "ATV",
    "Nile Dinner Cruise",
    "GEM",
    "Alexandria Day Trip",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Giza Pyramids & Sphinx with a thrilling 1-hour ATV ride on the desert plateau.",
    "Explore the Grand Egyptian Museum (GEM) including Tutankhamun treasures.",
    "Visit Memphis (ancient capital) and Saqqara’s Step Pyramid.",
    "Enter the Bent/Red Pyramids at Dahshur (as available).",
    "Unwind on the Nile Maxim Dinner Cruise with live shows and buffet dinner.",
    "Full-day Alexandria: Catacombs, Qaitbay Citadel, Roman Theater, Bibliotheca Alexandrina.",
    "Daily lunches included; private, air-conditioned transport and bottled water.",
    "Expert Egyptologist guide throughout for context and storytelling.",
]

ABOUT = """\
Discover Egypt’s greatest hits across Cairo, Giza, and Alexandria in a flexible 3-day package (no hotel bundle—choose where you stay).
Day 1 covers the Giza Plateau with a 1-hour ATV ride, time at the Sphinx, and the Grand Egyptian Museum. Day 2 explores the deep
past at Memphis, Saqqara (Step Pyramid), and Dahshur, then caps with a Nile Maxim Dinner Cruise featuring live entertainment.
Day 3 is devoted to Alexandria’s coastal charm and Greco-Roman history—Catacombs, Qaitbay, Roman Theater, and the Bibliotheca.
Lunch is included each day, with private transport and a licensed Egyptologist guide for a smooth, insightful experience.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Giza Wonders & GEM • ATV Ride • Return",
        "steps": [
            ("", "Morning pickup from your location in Cairo/Giza."),
            ("", "Guided visit to the Giza Pyramids & Sphinx."),
            ("", "1-hour ATV ride on the desert plateau by the pyramids."),
            ("", "Egyptian lunch at a local restaurant."),
            ("", "Afternoon visit to the Grand Egyptian Museum (GEM)."),
            ("", "Return to your accommodation in Cairo/Giza."),
        ],
    },
    {
        "day": 2,
        "title": "Memphis • Saqqara • Dahshur • Nile Maxim Dinner Cruise",
        "steps": [
            ("", "Morning pickup."),
            ("", "Explore Memphis and Saqqara (Step Pyramid)."),
            ("", "Head to Dahshur for Bent/Red Pyramids (enter as available)."),
            ("", "Lunch at a local Egyptian restaurant."),
            ("", "Short rest at hotel (optional)."),
            ("", "Evening pickup for the Nile Maxim Dinner Cruise (dinner & live show)."),
            ("", "Drop-off after the cruise."),
        ],
    },
    {
        "day": 3,
        "title": "Alexandria Full-Day • Catacombs • Citadel • Roman Theater • Bibliotheca",
        "steps": [
            ("", "Early pickup and drive to Alexandria."),
            ("", "Catacombs of Kom El Shoqafa."),
            ("", "Qaitbay Citadel on the harbor."),
            ("", "Roman Theater."),
            ("", "Bibliotheca Alexandrina (modern library)."),
            ("", "Lunch at a seafood/local restaurant."),
            ("", "Return to Cairo by evening; drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Professional Egyptologist tour guide",
    "Air-conditioned private transportation",
    "Entry tickets to all listed attractions (standard access)",
    "1-hour ATV ride around the Giza Pyramids",
    "Lunch on all 3 days",
    "Dinner cruise on the Nile (Nile Maxim) with live entertainment",
    "Bottled water throughout the tour",
    "Pickup and drop-off at your chosen location in Cairo or Giza",
]

EXCLUSIONS = [
    "Hotel accommodation",
    "Personal expenses",
    "Tipping (guide, driver, etc.)",
    "Optional activities not mentioned in the itinerary",
    "Entrance to Great Pyramid interior or Mummy Rooms (optional extra)",
    "Drinks during meals (unless specified)",
]

FAQS = [
    ("Is accommodation included?", "No—this package excludes hotels so you can choose freely."),
    ("What should I wear for the ATV ride and pyramid visit?",
     "Comfortable clothes and closed-toe shoes; bring scarf/hat and sunglasses for the sun."),
    ("Is this tour suitable for families or seniors?",
     "Yes—private tour pacing can be customized for families, seniors, or mobility needs."),
    ("Are entrance fees included?",
     "Yes—standard entrance fees listed are included. Optional interior entries are extra."),
    ("Can this tour be customized?",
     "Absolutely—adjust timing, upgrade ATV, or add a night in Alexandria on request."),
    ("Is lunch included every day?", "Yes—lunch is included on all 3 days."),
]


class Command(BaseCommand):
    help = "Seeds the 3-Day Cairo → Alexandria highlights package with destinations, content, and relations."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["cairo", "alexandria", "giza"], default="cairo",
                            help="Choose which destination is primary (default: cairo).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Primary/secondary resolution
        primary_map = {
            "cairo": DestinationName.CAIRO,
            "alexandria": DestinationName.ALEXANDRIA,
            "giza": DestinationName.GIZA,
        }
        primary_name = primary_map[opts["primary"]]

        # Build the “also appears in” set excluding the chosen primary
        addl_names = [d for d in ALSO_APPEARS_IN + [PRIMARY_DEST] if d != primary_name]

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
                .replace("—", "-")
                .replace("–", "-")
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

            if not dry:
                trip.additional_destinations.set(addl_dests)
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

        # Summary (formatted correctly)
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
