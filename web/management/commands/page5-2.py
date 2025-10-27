# web/management/commands/seed_trip_giza_saqqara_memphis.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from django.utils.text import slugify


from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# ------------------------------------------------------------
# Trip core (enhanced name)
# ------------------------------------------------------------
TITLE = "Cairo to Giza, Saqqara & Memphis: Full-Day Pyramids Tour with Lunch"
TEASER = (
    "See the Great Pyramid & Sphinx at Giza, the Step Pyramid at Saqqara, and "
    "ancient Memphis—plus a traditional Egyptian lunch."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("90.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Pyramids",
    "Giza",
    "Saqqara",
    "Memphis",
    "Ancient Egypt",
    "Full Day",
    "Private Tour",
    "Family Friendly",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Visit the Great Pyramid of Khufu, Khafre and Menkaure, plus the Great Sphinx.",
    "Explore Saqqara’s Step Pyramid of Djoser—the earliest large-scale stone pyramid.",
    "Discover the ruins of ancient Memphis: colossal Ramses II and the alabaster sphinx.",
    "Travel in comfort with a private vehicle and Egyptologist guide.",
    "Enjoy a traditional Egyptian lunch at a local restaurant.",
    "Flexible pacing and photo stops at panoramic viewpoints.",
]

ABOUT = """\
Dive deep into Egypt’s pyramid age on a private full-day tour that links Giza’s wonders with
Saqqara’s revolutionary Step Pyramid and the former capital of Memphis. With hotel pickup,
a dedicated Egyptologist, and a relaxed lunch stop, you’ll get context, great viewpoints, and
time to explore without the rush of big groups.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Giza Pyramids • Saqqara Step Pyramid • Ancient Memphis",
        "steps": [
            ("", "Hotel pickup in Cairo or Giza; meet your private Egyptologist guide."),
            ("", "Giza Plateau: Great Pyramid of Khufu, Pyramids of Khafre & Menkaure, and the Great Sphinx."),
            ("", "Drive to Saqqara: explore the Step Pyramid of Djoser and Old Kingdom tombs (time permitting)."),
            ("", "Traditional Egyptian lunch at a local restaurant."),
            ("", "Memphis open-air museum: colossal Ramses II and the alabaster sphinx."),
            ("", "Return transfer to your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Hotel pickup and drop-off (Cairo or Giza)",
    "Private Egyptologist guide",
    "Air-conditioned private transportation",
    "Entrance fees to Giza Pyramids, Saqqara, and Memphis",
    "Traditional Egyptian lunch at a local restaurant",
    "Bottled water during the tour",
    "All service charges and taxes",
]

EXCLUSIONS = [
    "Entrance to the inside of any pyramid (optional & extra cost)",
    "Personal expenses",
    "Gratuities (optional)",
    "Any extras not mentioned in the itinerary",
]

FAQS = [
    ("Is this a private tour or group tour?", "This is a private tour for your party with a dedicated guide and vehicle."),
    ("Are entrance tickets included?", "Yes—standard entries for Giza, Saqqara, and Memphis are included."),
    ("Can I enter the Great Pyramid?", "Yes, with a separate on-site ticket and subject to availability."),
    ("Is lunch included?", "Yes. Vegetarian and other dietary needs can usually be accommodated—please advise in advance."),
    ("How much walking is involved?", "Moderate walking at each site; comfortable shoes and sun protection are recommended."),
    ("Is this tour suitable for children?", "Yes—family friendly and easily paced for kids."),
]

# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Seed the Giza / Saqqara / Memphis full-day trip with destinations, price, languages, categories, and full content."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Destinations
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
            # normalize → stable, URL-safe slug
            slug = slugify(tag.replace("&", " and "))
            # use slug as the natural key to avoid unique collisions
            obj, created = TripCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": tag},
            )
            # if it existed with a different display name, optionally align it
            if not created and obj.name != tag:
                obj.name = tag  # or keep existing; your call
                obj.save(update_fields=["name"])
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

            # Update core fields for repeatable runs
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

        # Summary (fixed join formatting)
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
