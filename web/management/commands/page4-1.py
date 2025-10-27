# web/management/commands/seed_trip_luxury_cairo_combo.py
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
TITLE = "Giza to Cairo: Luxury Pyramids, Egyptian Museum & Khan el-Khalili (Private Day Tour)"
TEASER = (
    "Premium, fully private day: Giza Pyramids & Sphinx, Egyptian Museum, and Khan el-Khalili Bazaar—"
    "tailored by a personal Egyptologist, luxury vehicle, skip-the-crowds pacing, and VIP photo stops."
)

# Primary/Additional destinations
PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

# Core trip fields
DURATION_DAYS = 1          # 8 hours ≈ 1 day in model terms
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("100.00")
TOUR_TYPE_LABEL = "Daily Tour — Luxury Private"

# Languages
LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

# Categories (tags)
CATEGORY_TAGS = [
    "Luxury",
    "Private Tour",
    "Pyramids",
    "Museum",
    "Bazaar",
    "Cairo",
    "Giza",
    "City Tour",
    "Culture",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "VIP visit to the Giza Pyramids & Sphinx with curated photo stops and flexible timing.",
    "Private luxury vehicle (A/C, Wi-Fi) and personal Egyptologist guide.",
    "Guided exploration of the Egyptian Museum, including Tutankhamun highlights.",
    "Stroll the historic Khan el-Khalili Bazaar with shopping assistance and café options.",
    "Optional add-ons: camel ride on the plateau, Great Pyramid interior, Royal Mummies Room.",
    "Seamless hotel pickup/drop-off and day paced to your preferences.",
]

ABOUT = """\
Experience Cairo in comfort and style with a fully private, customizable day that weaves together the Giza Pyramids & Sphinx,
the Egyptian Museum in Tahrir, and the atmospheric Khan el-Khalili Bazaar. Travel by luxury vehicle with a personal Egyptologist
who tailors depth, pace, and photo stops to your interests—so you enjoy the icons without the hassle. Options for premium lunch
on the Nile, camel ride, or special-entry tickets can be added on request.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Luxury Cairo Icons (8 hours)",
        "steps": [
            ("08:00", "Hotel pickup in a luxury private vehicle (Cairo/Giza)."),
            ("", "Giza Plateau: guided tour of the Pyramids & Sphinx; optional camel ride and panoramic photo stop."),
            ("", "Transfer to Tahrir; guided visit inside the Egyptian Museum (highlights & context)."),
            ("", "Optional lunch at a premium Nile-view restaurant or a curated local eatery."),
            ("", "Khan el-Khalili Bazaar: guided walk, café time, and assisted shopping."),
            ("16:00", "VIP drop-off back at your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Private luxury vehicle with Wi-Fi and air conditioning",
    "Hotel pickup and drop-off (Cairo/Giza)",
    "Professional Egyptologist guide (multilingual on request)",
    "Entry tickets to the Giza Pyramids complex",
    "Entry to the Egyptian Museum",
    "Bottled water and light snacks",
    "Shopping assistance at Khan el-Khalili",
    "All taxes and service charges",
    "Lunch",  # per provided inclusions
]

EXCLUSIONS = [
    "Personal expenses",
    "Tipping for guide and driver (optional)",
    "Entry to paid museum sections (e.g., Royal Mummies Room)",
    "Great Pyramid interior ticket (optional extra)",
]

FAQS = [
    ("Is this a private tour?", "Yes, completely private and fully customizable."),
    ("Can I add or remove stops?", "Absolutely—your guide can tailor timing and depth on the day."),
    ("Are entrance tickets included?", "Standard entry for Giza complex and the Egyptian Museum are included."),
    ("What makes this a luxury tour?", "Private luxury transport, flexible pacing, curated photo stops, and personalized guiding."),
    ("What should I wear?", "Comfortable clothes and walking shoes; sunglasses/hat recommended."),
    ("How long is the tour?", "Around 7–8 hours, adjustable to your schedule."),
    ("Is it suitable for kids or seniors?", "Yes—the pace and logistics can be adapted to all comfort levels."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Luxury Cairo private combo (Giza Pyramids, Egyptian Museum & Khan el-Khalili) with destinations, price, and content."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations
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
                ),
            )

            # Update core fields on re-run
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
