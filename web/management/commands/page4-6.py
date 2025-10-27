# web/management/commands/seed_trip_nile_dinner_cruise.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo: Nile Maxim Luxury Dinner Cruise with Entertainment"
TEASER = (
    "Evening Nile River cruise aboard luxury Nile Maxim: Enjoy gourmet buffet dinner, "
    "belly dancing show, Tanoura performance, and live Arabic music with Cairo skyline views."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.GIZA]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("80.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Dinner Cruise",
    "Evening Tour",
    "Entertainment",
    "Luxury",
    "Cultural",
    "Nile River",
]

HIGHLIGHTS = [
    "Sail the Nile in style aboard the 5-star Nile Maxim luxury cruise boat.",
    "Enjoy lavish buffet dinner with Egyptian and international cuisine selections.",
    "Experience live cultural entertainment: belly dancing and Tanoura whirling dervish show.",
    "Listen to live Arabic music performances throughout the cruise.",
    "Admire scenic Nile views at night with Cairo's illuminated skyline and bridges.",
    "Atmospheric dining experience perfect for couples and special occasions.",
    "Family-friendly entertainment suitable for all ages.",
    "Convenient hotel transfers included from Cairo or Giza.",
    "Choose between indoor air-conditioned seating or open-air deck.",
]

ABOUT = """\
Spend a magical evening gliding along the historic Nile River aboard the elegant Nile Maxim—Cairo's most prestigious dinner cruise. This luxury Nile dinner cruise offers an unforgettable combination of gourmet dining, lively entertainment, and breathtaking views of Cairo's illuminated skyline.

Your night begins with a convenient pickup from your hotel and a short drive to the dock where the Nile Maxim—a floating restaurant operated by the renowned Marriott Hotel—awaits. Step aboard the 5-star vessel, known for its luxurious ambiance, spacious deck, and impeccable service.

Once onboard, you'll be treated to a lavish open buffet dinner featuring a wide selection of Egyptian and international dishes—perfectly prepared to please every palate. Enjoy everything from grilled meats, fresh salads, hot appetizers, and rich desserts as you cruise gently down the Nile.

As you dine, the entertainment begins. You'll experience a dynamic live show featuring an authentic belly dancing performance, a mesmerizing Tanoura (whirling dervish) dance, and traditional Arabic music. The energetic performances, combined with the elegant river backdrop, create a uniquely immersive Egyptian night.

The cruise offers both indoor air-conditioned seating and outdoor open-air deck space, allowing you to enjoy the fresh evening breeze and the shimmering lights of Cairo's cityscape, iconic bridges, and riverside landmarks.

Whether you're celebrating a special occasion, enjoying a romantic evening, or simply looking to experience Egyptian culture in style, the Nile Maxim dinner cruise delivers a perfect blend of fine dining and unforgettable entertainment—all on the timeless waters of the Nile.

After approximately 2 hours of cruising, you'll disembark and be transferred back to your hotel, full of great food, beautiful sights, and lively memories.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Nile Maxim Luxury Dinner Cruise Evening",
        "steps": [
            ("Evening", "Pick-up from your hotel in Cairo or Giza"),
            ("Evening", "Arrive at dock and board the luxurious Nile Maxim cruise boat"),
            ("Evening", "Begin 2-hour Nile River cruise with buffet dinner service"),
            ("Night", "Enjoy live entertainment: belly dancing and Tanoura shows"),
            ("Night", "Listen to live Arabic music performances"),
            ("Night", "Admire illuminated Cairo skyline and bridges from the river"),
            ("Late Night", "Disembark and return transfer to your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Round-trip hotel transfers in private air-conditioned vehicle",
    "2-hour dinner cruise on the Nile Maxim luxury boat",
    "Open buffet dinner with Egyptian and international cuisine",
    "Live entertainment: belly dancer, Tanoura show, live band",
    "All taxes and service charges",
    "Comfortable seating with indoor and outdoor options",
    "Professional service throughout the evening",
]

EXCLUSIONS = [
    "Alcoholic beverages (available for purchase onboard)",
    "Personal expenses and souvenirs",
    "Gratuities/tips for crew or driver",
    "Photography services onboard (optional)",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("How long is the Nile Maxim dinner cruise?",
     "The cruise lasts approximately 2 hours, including dinner and live entertainment."),
    ("Is the cruise suitable for children?",
     "Yes, children are welcome. The show is family-friendly, and kids often enjoy the dancing and music."),
    ("Is the dinner served buffet-style?",
     "Yes, the dinner is an open buffet with a variety of Egyptian and international options."),
    ("Are drinks included in the price?",
     "Soft drinks may be included depending on the package. Alcoholic beverages are available for purchase onboard."),
    ("What kind of entertainment is provided?",
     "The cruise features a belly dancing show, Tanoura (whirling dervish), and live Arabic music."),
    ("Is there a dress code?",
     "Smart casual is recommended. No formal wear is required, but guests often dress nicely for the occasion."),
    ("Is the boat air-conditioned?",
     "Yes, the indoor dining area is fully air-conditioned, and there's also an open-air deck."),
    ("Can I request vegetarian or special meals?",
     "Yes, vegetarian options are available. Please mention any dietary restrictions when booking."),
]


class Command(BaseCommand):
    help = "Seeds the Nile Maxim Luxury Dinner Cruise evening experience."

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