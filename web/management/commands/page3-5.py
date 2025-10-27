# web/management/commands/seed_trip_giza_camel.py
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
TITLE = "Giza: Pyramids & Sphinx with Camel Safari — Half-Day Adventure"
TEASER = (
    "Stand before the Great Pyramid, meet the Sphinx, and ride a camel across the Giza sands. "
    "A compact, thrill-filled half-day with iconic photo stops and an Egyptologist guide."
)

PRIMARY_DEFAULT = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]  # dual listing

DURATION_DAYS = 1            # 4h product; keep day count = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("85.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Half-Day",
    "Giza",
    "Pyramids",
    "Camel",
    "Adventure",
    "Photography",
    "Family Friendly",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "See the three Pyramids of Giza: Khufu, Khafre, and Menkaure.",
    "Admire the Great Sphinx and learn its enduring symbolism.",
    "Enjoy a traditional camel ride across the Giza plateau.",
    "Panoramic photo stops with all three pyramids aligned.",
    "Guided by a professional Egyptologist; hotel pickup/drop-off included.",
]

ABOUT = """\
A timeless Giza experience blending world wonders with desert life. Begin at the Great Pyramid of Khufu, explore Khafre and
Menkaure, then approach the Sphinx and Valley Temple. Cap it with a classic camel ride across the plateau for sweeping
pyramid panoramas—perfect for photography, families, and first-time visitors alike.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Giza Pyramids, Sphinx & Camel Safari (approx. 4 hours)",
        "steps": [
            ("", "Pickup from your Cairo or Giza hotel; drive to the Giza Plateau."),
            ("", "Guided visit around the Great Pyramid of Khufu (optional interior ticket available on-site)."),
            ("", "Continue to Khafre and Menkaure with expert commentary."),
            ("", "Camel ride on the sands with skyline and pyramid views (approx. 15–30 minutes)."),
            ("", "Visit the Great Sphinx and Valley Temple; stories and photo time."),
            ("", "Return transfer to your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Professional Egyptologist tour guide",
    "Hotel pickup and drop-off (Cairo or Giza)",
    "Entrance to the Giza Plateau (pyramids & Sphinx area)",
    "Camel ride (approx. 30 minutes)",
    "Bottled water",
]

EXCLUSIONS = [
    "Entrance inside the pyramids (optional, extra ticket)",
    "Meals and additional drinks",
    "Gratuities (optional)",
    "Personal shopping/expenses",
]

FAQS = [
    ("How long is the camel ride?", "Typically 15–30 minutes; longer rides can be arranged on request."),
    ("Is the camel ride safe?", "Yes—handled by experienced cameleers with guidance from your tour team."),
    ("Can I go inside a pyramid?", "Yes—interior entry requires a separate ticket purchased on-site (subject to availability)."),
    ("What should I wear?", "Comfortable shoes, light clothing, hat, and sunscreen for the desert environment."),
    ("Is this suitable for children?", "Yes—families are welcome; young kids may ride with an adult."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Giza Pyramids & Sphinx with Camel Safari trip with price, content, languages, categories, and dual destination listing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace-related", action="store_true",
            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip."
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show changes without writing to DB."
        )
        parser.add_argument(
            "--primary", choices=["giza", "cairo"], default="giza",
            help="Choose the primary destination (default: giza)."
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve primary and additional destinations
        primary_map = {"giza": DestinationName.GIZA, "cairo": DestinationName.CAIRO}
        primary_name = primary_map[opts["primary"]]
        addl_names = [d for d in set(ALSO_APPEARS_IN + [PRIMARY_DEFAULT]) if d != primary_name]

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

            # Update core fields if re-run
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


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
