# web/management/commands/seed_trip_giza_halfday.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Giza: Pyramids & Sphinx (Half-Day Tour with Egyptologist)"
TEASER = (
    "Short on time? See the Great Pyramid, Khafre, Menkaure, the Sphinx, and the Valley Temple "
    "with a licensed Egyptologist—hotel pickup and comfy transport included."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1  # Half-day ≈ same day
GROUP_SIZE_MAX = 50
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
    "Half-Day",
    "Egyptologist Guided",
]

HIGHLIGHTS = [
    "Stand before the Great Pyramid of Khufu—the only surviving Ancient Wonder.",
    "Explore the three pyramids of Giza: Khufu, Khafre, and Menkaure.",
    "Admire the Great Sphinx and learn its symbolism and mysteries.",
    "Visit the Valley Temple—site of ancient mummification rituals.",
    "Expert insights from a professional Egyptologist guide.",
    "Convenient half-day format ideal for tight schedules.",
]

ABOUT = """\
Experience the timeless majesty of the Giza Pyramids on a compact half-day tour. Enjoy hotel pickup in Cairo or Giza, then visit
Khufu (Great Pyramid), Khafre, and Menkaure with a licensed Egyptologist who brings ancient engineering and royal history to life.
Continue to the Great Sphinx and the Valley Temple for iconic views and stories. Perfect for travelers short on time who want a
focused, unforgettable introduction to Egypt’s most famous monuments.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Hotel Pickup • Giza Pyramids & Sphinx • Valley Temple • Return",
        "steps": [
            ("", "Pick-up from your Cairo or Giza hotel by private car/van."),
            ("", "Drive to the Giza Plateau, one of the world’s great archaeological sites."),
            ("", "Guided visit: Great Pyramid of Khufu, Pyramid of Khafre, Pyramid of Menkaure."),
            ("", "See the Great Sphinx and explore the Valley Temple."),
            ("", "Free time for photography and optional camel rides (extra)."),
            ("", "Return transfer to your hotel in Cairo or Giza."),
        ],
    },
]

INCLUSIONS = [
    "Pick-up & drop-off at your Cairo or Giza hotel",
    "Private air-conditioned vehicle",
    "Professional English-speaking Egyptologist guide",
    "Entrance fees to the Giza Plateau (pyramids area & Sphinx)",
    "Bottled water during the tour",
]

EXCLUSIONS = [
    "Entrance to the inside of the Great Pyramid or other pyramids (optional, extra ticket)",
    "Camel or horse rides (optional, extra charge)",
    "Tips (gratuities)",
    "Personal expenses",
]

FAQS = [
    ("How long does the half-day tour take?",
     "Usually 4–5 hours depending on traffic and time at the sites."),
    ("Can I enter inside the pyramids?",
     "Yes—entry requires an extra ticket purchased on-site; availability may vary."),
    ("What should I bring?",
     "Comfortable walking shoes, sunscreen, a hat, sunglasses, and a camera."),
    ("Are camel rides included?",
     "No. They’re optional and can be arranged on-site for an additional fee."),
    ("Is this tour suitable for families with children?",
     "Yes. It’s family-friendly and kids often enjoy the experience."),
]


class Command(BaseCommand):
    help = "Seeds the Giza Half-Day Pyramids & Sphinx tour with destinations, content, and relations."

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

        primary_name = DestinationName.GIZA if opts["primary"] == "giza" else DestinationName.CAIRO
        secondary = DestinationName.CAIRO if primary_name == DestinationName.GIZA else DestinationName.GIZA

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

        lang_objs = []
        for lname, code in LANGS:
            obj, _ = Language.objects.get_or_create(name=lname, code=code)
            lang_objs.append(obj)

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

        # Summary (fixed formatting)
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
