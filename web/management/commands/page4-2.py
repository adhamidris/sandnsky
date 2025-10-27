# web/management/commands/seed_trip_ain_sokhna_cable_car.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Ain Sokhna: Cable Car Experience & Red Sea Day Trip"
TEASER = (
    "Day trip from Cairo to Ain Sokhna: Ride Egypt's first coastal cable car with panoramic Red Sea views, "
    "enjoy beach time, and experience scenic coastline from above with comfortable round-trip transfers."
)

PRIMARY_DEST = DestinationName.AIN_EL_SOKHNA
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.GIZA]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("110.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Trip",
    "Cable Car",
    "Red Sea",
    "Scenic",
    "Beach",
    "Family Friendly",
]

HIGHLIGHTS = [
    "Ride Egypt's first coastal cable car in Ain Sokhna with modern comfortable cabins.",
    "Soar above the Red Sea with breathtaking panoramic views of coastline and mountains.",
    "Capture stunning photos of the Red Sea coastline and surrounding desert landscape.",
    "Enjoy free time by the beach or explore local resort areas at your leisure.",
    "Includes round-trip private transport from Cairo or Giza hotels.",
    "Family-friendly experience ideal for couples, friends, and solo travelers.",
    "Professional English-speaking guide or tour escort throughout the day.",
    "Perfect escape from Cairo with combination of adventure and relaxation.",
]

ABOUT = """\
Escape the fast pace of Cairo and treat yourself to a day of sea views, mountain landscapes, and unforgettable heights with the Ain Sokhna Cable Car Experience. Located along the Red Sea coastline, just around 90 minutes from Cairo, Ain Sokhna is a favorite destination for city dwellers looking for a quick, scenic retreat — and now, it offers one of the most unique experiences in Egypt: a cable car ride with panoramic views over the Red Sea and surrounding mountains.

Your journey begins with a comfortable, air-conditioned transfer from Cairo to Ain Sokhna. Upon arrival, prepare for a breathtaking cable car experience, gliding smoothly above stunning coastal scenery, crystal-clear waters, and luxurious seaside resorts. This is Egypt like you've never seen before — from above!

The cable car ride offers spectacular photo opportunities, making it perfect for couples, solo travelers, families, and anyone looking to capture a special moment. After your ride, enjoy free time on the beach, grab lunch by the sea, or explore the local resort area at your leisure. The tour is designed for both relaxation and adventure, combining nature, comfort, and modern luxury.

Whether you're looking for a romantic escape, a family outing, or a solo recharge, this day trip delivers something memorable for everyone. With round-trip transport, a professional escort, and curated options to customize your day, the Ain Sokhna Cable Car Experience from Cairo is one of the most refreshing and scenic ways to explore Egypt beyond the capital.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Ain Sokhna Cable Car & Red Sea Day Trip",
        "steps": [
            ("Morning", "Pick-up from your hotel in Cairo or Giza"),
            ("Morning", "Scenic drive to Ain Sokhna (approx. 1.5-2 hours)"),
            ("Late Morning", "Arrive in Ain Sokhna and prepare for cable car experience"),
            ("Late Morning", "Begin the cable car ride over Red Sea and mountains"),
            ("Afternoon", "Free time to relax by beach or explore resort surroundings"),
            ("Afternoon", "Lunch at local restaurant (optional)"),
            ("Late Afternoon", "Depart Ain Sokhna for return journey"),
            ("Evening", "Return and drop-off at your hotel in Cairo"),
        ],
    },
]

INCLUSIONS = [
    "Hotel pick-up and drop-off in Cairo or Giza",
    "Private air-conditioned vehicle for round-trip transportation",
    "English-speaking guide or tour escort",
    "Ain Sokhna cable car ride ticket",
    "Free time at the beach or resort area",
    "Bottled water during transfers",
    "All taxes and service charges",
    "Comfortable and safe cable car experience",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Beach or resort access fees (if applicable)",
    "Gratuities for guide and driver (optional but appreciated)",
    "Extra activities (water sports, spa access, etc.)",
    "Lunch at restaurant (optional)",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("How long is the drive from Cairo to Ain Sokhna?",
     "It usually takes around 1.5 to 2 hours, depending on traffic."),
    ("How long is the cable car ride?",
     "The ride typically lasts about 15-20 minutes one way, offering panoramic views throughout."),
    ("Is this trip suitable for children?",
     "Yes, the cable car and beach areas are very family-friendly."),
    ("What should I bring with me?",
     "Comfortable clothes, sunglasses, sunscreen, a camera, and beachwear if you plan to swim or relax by the sea."),
    ("Can I swim or access resort facilities?",
     "Some beach access may be included depending on your package. Resort facilities like pools, spas, or private beaches may require additional fees."),
    ("Is the cable car safe?",
     "Yes, the cable car is professionally maintained and adheres to safety standards."),
    ("Can I book this as a private tour?",
     "Yes, this tour is typically offered as a private experience for your comfort and flexibility."),
    ("What happens in case of bad weather?",
     "In case of unfavorable weather conditions, the cable car operation may be suspended for safety. Alternative arrangements or rescheduling will be offered."),
]


class Command(BaseCommand):
    help = "Seeds the Ain Sokhna Cable Car Experience day trip from Cairo."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true", help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations (must already exist from your destination seeder)
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Primary destination '{PRIMARY_DEST}' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in ALSO_APPEARS_IN:
            try:
                addl_dests.append(Destination.objects.get(name=d))
            except Destination.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Additional destination '{d}' not found (skipping)."))

        # Languages (get_or_create)
        lang_objs = []
        for lname, code in LANGS:
            obj, _ = Language.objects.get_or_create(name=lname, code=code)
            lang_objs.append(obj)

        # Category tags (as TripCategory rows)
        cat_objs = []
        for tag in CATEGORY_TAGS:
            slug = tag.lower().replace("&", "and").replace("—", "-").replace(" ", "-")
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

            # If exists, update core fields
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

            # M2M: additional_destinations, languages, categories
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

            # Create related if empty (idempotent friendly)
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
        self.stdout.write(f"Languages: " + ", ".join(f"{l.name} ({l.code})" for l in lang_objs))
        self.stdout.write(f"Categories: " + ", ".join(c.name for c in cat_objs))
        self.stdout.write(f"Base Price: ${BASE_PRICE}")
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False