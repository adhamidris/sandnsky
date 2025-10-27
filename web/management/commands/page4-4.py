# web/management/commands/seed_trip_ain_sokhna_private.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to El Ain Sokhna: Private Red Sea Beach Day Trip"
TEASER = (
    "Private day trip from Cairo to El Ain Sokhna: Enjoy Red Sea beach escape with resort access, "
    "swimming, sunbathing, and optional water activities. Flexible itinerary with private driver."
)

PRIMARY_DEST = DestinationName.AIN_EL_SOKHNA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 15
BASE_PRICE = Decimal("190.00")
TOUR_TYPE_LABEL = "Daily Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Private Tour",
    "Beach Day",
    "Red Sea",
    "Day Trip",
    "Relaxation",
    "Flexible",
]

HIGHLIGHTS = [
    "Private round-trip transfer from Cairo in air-conditioned vehicle with personal driver.",
    "Red Sea beach day at El Ain Sokhna - closest Red Sea destination to Cairo.",
    "Flexible beach options: choose between luxury resort or natural public beach access.",
    "Total relaxation day - unplug from city noise with peaceful seaside escape.",
    "Optional activities available: snorkeling, jet skiing, or private yacht cruise.",
    "Seaside dining options with fresh seafood at local restaurants (optional).",
    "Perfect for families, couples, or solo travelers seeking quick relaxing getaway.",
    "Incredible photo opportunities with Red Sea, golden sands, and mountain backdrop.",
    "Self-guided experience with complete freedom and flexible schedule.",
]

ABOUT = """\
Escape the hustle and noise of Cairo with a serene and refreshing private full-day getaway to El Ain Sokhna, a peaceful Red Sea resort town just under two hours from the capital. Perfect for those seeking sun, sea, and a stress-free escape, this tour offers you a day of total relaxation at the nearest Red Sea beach from Cairo.

Your day begins with a comfortable private transfer in an air-conditioned vehicle directly from your hotel in Cairo. As you journey eastward, the busy streets give way to open desert and mountain landscapes until you reach the calm turquoise waters of El Ain Sokhna.

Upon arrival, you'll have several options depending on your preferences: spend your day at a luxurious beachfront resort with pool and beach access, or choose a more secluded public beach area to enjoy natural beauty without the crowds. Swim in the warm waters of the Red Sea, lounge under the sun, or take a walk along the coastline—this experience is designed to let you unwind at your own pace.

For those looking to upgrade the day, optional activities like yacht cruises, snorkeling, jet skiing, or a seafood lunch by the sea can be arranged in advance.

Whether you're a solo traveler, a couple, or a family, this private full-day tour to Ain Sokhna offers the perfect balance of privacy, freedom, and comfort. No guides, no rigid schedule—just a vehicle, a driver, and your own itinerary to relax by the sea and reset before returning to the city.

This day trip is an ideal choice for those with limited time in Egypt who still want to experience the magic of the Red Sea without an overnight stay.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Private El Ain Sokhna Red Sea Beach Escape",
        "steps": [
            ("Morning", "Pickup from your hotel in Cairo by private air-conditioned vehicle"),
            ("Morning", "Scenic transfer to El Ain Sokhna (approx. 1.5-2 hours)"),
            ("Late Morning", "Arrive in Ain Sokhna and check-in at selected beach resort or public beach"),
            ("Daytime", "Free leisure time: swim, relax by sea, sunbathe, enjoy resort amenities"),
            ("Daytime", "Optional activities: boat trip, jet ski session, or lunch at seafood restaurant"),
            ("Late Afternoon", "Departure from Ain Sokhna for return journey"),
            ("Evening", "Drop-off at your hotel in Cairo"),
        ],
    },
]

INCLUSIONS = [
    "Private round-trip transportation from your hotel in Cairo",
    "Air-conditioned vehicle with professional driver",
    "Full-day access to private beach or resort (based on option chosen)",
    "Bottled water during transport",
    "Day-use facilities including changing rooms",
    "All taxes and service charges",
    "Flexibility to customize your day with free time",
    "Complete privacy with no other travelers",
]

EXCLUSIONS = [
    "Optional activities (yacht cruise, jet ski, snorkeling, etc.)",
    "Towels and swimwear (bring your own)",
    "Personal expenses and souvenirs",
    "Gratuities for driver (optional)",
    "Travel insurance",
    "Lunch and meals (available as optional add-on)",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is this tour private?",
     "Yes, the tour includes a private car and driver. You won't be grouped with other travelers."),
    ("Can I swim in Ain Sokhna?",
     "Absolutely! The Red Sea waters at Ain Sokhna are warm and swimmable year-round."),
    ("Are there options for food?",
     "You can dine at beachside restaurants, resort cafes, or arrange lunch as an optional add-on. You're also welcome to bring your own snacks."),
    ("Do I need to bring towels or beachwear?",
     "Yes, please bring your own towel, swimsuit, sunscreen, and any beach essentials."),
    ("Is this a guided tour?",
     "No, this is a self-guided day escape with a private driver. You'll have total freedom to relax and explore."),
    ("Can I book water activities like jet skis or a yacht?",
     "Yes, we can arrange optional water activities in advance at an additional cost."),
    ("What is the best time to visit Ain Sokhna?",
     "The best months are October through May, when the weather is mild and ideal for beach relaxation."),
    ("How much time do we actually spend at the beach?",
     "Typically 5-6 hours of beach time, depending on travel time and your preferences."),
]


class Command(BaseCommand):
    help = "Seeds the El Ain Sokhna Private Day Trip from Cairo."

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