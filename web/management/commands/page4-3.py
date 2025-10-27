# web/management/commands/seed_trip_africano_park.py
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
TITLE = "Cairo to Alexandria: Africano Park Safari Day Trip (Family-Friendly Wildlife Experience)"
TEASER = (
    "Escape Cairo for a full-day African-themed safari at Africano Park near Alexandria—guided drive-through habitats, "
    "up-close wildlife moments, optional lake boat ride, and plenty of photo time."
)

# Primary/Additional destinations
PRIMARY_DEST = DestinationName.ALEXANDRIA
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.GIZA]

# Core trip fields
DURATION_DAYS = 1                 # 8 hours ≈ 1 day in model terms
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("145.00")
TOUR_TYPE_LABEL = "Daily Tour — Safari"

# Languages
LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

# Categories (tags)
CATEGORY_TAGS = [
    "Safari",
    "Family",
    "Wildlife",
    "Nature",
    "Alexandria",
    "Cairo",
    "Kids",
    "Boat Ride",
    "Photography",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Visit Africano Park, Egypt’s first open-air safari zoo near Alexandria.",
    "Guided safari drive through large habitats with lions, giraffes, zebras, antelopes, monkeys, and more.",
    "Optional boat ride on the park’s mini-lake (available on-site unless included in package).",
    "Shaded walking paths, petting zones, and plenty of time for photos.",
    "Private round-trip transport from Cairo or Giza with an English-speaking guide.",
    "Perfect for families and wildlife lovers looking for a change of pace from historical touring.",
]

ABOUT = """\
Trade Cairo’s bustle for a full-day wildlife escape at Africano Park just outside Alexandria. Egypt’s first open safari-style zoo
lets you experience animals in expansive enclosures by guided drive, with time for gentle strolls, photos, and an optional
boat ride on the park’s lake. This family-friendly day includes private transport, entrance fees, and a guide—so you can
focus on the animals, the greenery, and a different side of Egypt.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Africano Park Safari Experience (8 hours)",
        "steps": [
            ("07:30", "Hotel pickup in Cairo or Giza; depart for Africano Park (approx. 2.5–3 hours)."),
            ("", "Arrive and begin guided safari drive through the park’s habitats (photography stops included)."),
            ("", "Free time to walk shaded paths, visit petting zones, and relax."),
            ("", "Optional boat ride on the mini-lake (available on-site unless pre-included)."),
            ("", "Lunch break at the park restaurant or a nearby local spot (as arranged)."),
            ("15:30", "Begin return drive to Cairo; hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off from your hotel in Cairo or Giza",
    "Private air-conditioned vehicle",
    "Professional English-speaking tour guide",
    "Entrance fees to Africano Park",
    "Guided safari drive through the park",
    "Time for photos and leisure walks",
    "Bottled water and light snacks",
]

EXCLUSIONS = [
    "Personal expenses",
    "Gratuities (optional but appreciated)",
    "Optional activities inside the park (e.g., camel rides)",
    "Boat rides (if not included in the base package)",
]

FAQS = [
    ("How long is the drive from Cairo?", "Typically 2.5–3 hours each way, depending on traffic."),
    ("Is it suitable for children?", "Yes—very family-friendly, with interactive areas and gentle pacing."),
    ("What animals will we see?", "Common sightings include lions, giraffes, zebras, antelopes, monkeys, ostriches, and more."),
    ("Do I need to bring anything special?", "Comfortable clothes and shoes, sunscreen, hat, and a camera are recommended."),
    ("Is the tour private or group-based?", "It can be arranged as a private tour or small group—based on your booking."),
    ("Can I book a boat ride on-site?", "Yes, for a small additional fee unless already included in your package."),
    ("Is the park wheelchair accessible?", "The safari drive is accessible; some walking paths may not be fully paved."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Africano Park Safari day trip with destinations, price, languages, categories, and content."

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
            self.stderr.write(self.style.ERROR("Primary destination 'Alexandria' not found. Seed destinations first."))
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
