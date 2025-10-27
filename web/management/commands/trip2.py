# web/management/commands/seed_trip_cairo_giza_gem.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# --- Trip core ---------------------------------------------------------------

TITLE = "Cairo to Giza: Pyramids & Grand Egyptian Museum (Full-Day Tour)"
TEASER = (
    "See the Pyramids, Sphinx, and the Grand Egyptian Museum in one seamless day—"
    "hotel pickup, Egyptologist guide, and comfortable transport included."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1           # 6 hours ≈ same-day tour
GROUP_SIZE_MAX = 25         # “Over 25” → cap 25 as a sensible default
BASE_PRICE = Decimal("0.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Pyramids",
    "Grand Egyptian Museum",
    "Full-Day",
    "Egyptologist Guided",
]

# --- Content blocks ----------------------------------------------------------

HIGHLIGHTS = [
    "Visit the world-famous Pyramids of Giza: Khufu, Khafre, and Menkaure.",
    "Stand before the legendary Great Sphinx and explore the Valley Temple.",
    "Explore the Grand Egyptian Museum (GEM), the world’s largest archaeological museum.",
    "See the complete Tutankhamun collection and monumental masterpieces.",
    "Guided commentary by a licensed Egyptologist throughout.",
    "Capture breathtaking photos on the Giza Plateau.",
    "Optional camel ride experience near the pyramids (on-site, extra).",
    "Comfortable, air-conditioned round-trip transportation and hotel pickup/drop-off.",
]

ABOUT = """\
Discover two of Egypt’s icons in one day: the Pyramids & Sphinx on the Giza Plateau and the state-of-the-art Grand Egyptian Museum.
Begin with hotel pickup in Cairo or Giza and meet your licensed Egyptologist guide. Walk in the footsteps of pharaohs at Khufu, Khafre,
and Menkaure, then see the timeless Sphinx and Valley Temple. Continue to GEM to explore world-class galleries featuring the full
Tutankhamun collection and monumental statues. A seamless, comfortable experience designed for history lovers and first-timers alike.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Hotel Pickup • Pyramids & Sphinx • Grand Egyptian Museum • Return",
        "steps": [
            ("", "Hotel pickup in Cairo or Giza; meet your Egyptologist guide."),
            ("", "Giza Plateau: visit Khufu (Great Pyramid), Khafre, Menkaure; optional pyramid interior (ticketed)."),
            ("", "Great Sphinx & Valley Temple visit with guided commentary."),
            ("", "Transfer to the Grand Egyptian Museum (GEM)."),
            ("", "Guided tour: Tutankhamun collection, monumental statues, immersive galleries; free time and gift shop."),
            ("", "Return transfer and hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Entry to the Giza Plateau (Pyramids & Sphinx)",
    "Licensed Egyptologist tour guide",
    "Hotel pickup and drop-off (Cairo/Giza)",
    "Air-conditioned private or group transport",
    "Bottled water",
    "Entry to the Grand Egyptian Museum (GEM)",
    "Lunch at local restaurant (vegan/vegetarian available)",
]

EXCLUSIONS = [
    "Entry to the interior of the Great Pyramid (optional, additional fee)",
    "Camel or horse rides (available on-site)",
    "Gratuities (optional)",
    "Personal purchases or expenses",
]

FAQS = [
    ("Is the Grand Egyptian Museum fully open?",
     "As of 2025, most of GEM is open to visitors, including major galleries and the Tutankhamun collection. This tour includes access to open sections."),
    ("Can I enter inside the pyramids?",
     "Yes. You can purchase a separate ticket at the site for the Great Pyramid or smaller ones. Entry is limited and involves narrow passages."),
    ("Are camel rides included?",
     "No. Camel rides are available on the Giza Plateau and can be arranged on-site for an additional fee."),
    ("Is this tour suitable for kids or seniors?",
     "Yes. It’s family-friendly with a comfortable pace. Tell us if mobility assistance is needed."),
    ("What should I bring?",
     "Comfortable shoes, sunglasses, sunscreen, a hat, and a camera. The sun can be strong around midday."),
    ("Can this tour be customized?",
     "Absolutely. Private tours can adjust timings, add stops (e.g., Egyptian Museum in Tahrir, Nile boat ride), and tailor the pace."),
]


# --- Command -----------------------------------------------------------------

class Command(BaseCommand):
    help = "Seeds the Cairo → Giza: Pyramids & GEM day tour with destinations, content, and relations."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["giza", "cairo"], default="giza",
                            help="Choose which destination is primary (default: giza).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Allow switching primary via flag
        primary_name = DestinationName.GIZA if opts["primary"] == "giza" else DestinationName.CAIRO
        secondary = DestinationName.CAIRO if primary_name == DestinationName.GIZA else DestinationName.GIZA

        # Resolve destinations (should exist already)
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
                .replace("—", "-")
                .replace("–", "-")
                .replace(" ", "-")
            )
            obj, _ = TripCategory.objects.get_or_create(name=tag, defaults={"slug": slug})
            if not obj.slug:
                obj.slug = slug
                obj.save()
            cat_objs.append(obj)

        # Upsert trip
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

class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
