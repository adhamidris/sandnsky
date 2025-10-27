# web/management/commands/seed_trip_cairo_3day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo: 3-Day Guided City Tour with Pyramids & Museums"
TEASER = (
    "3-day comprehensive Cairo tour: Explore Giza Pyramids, Egyptian Museum, Saqqara, Memphis, "
    "Dahshur, Islamic Cairo, Coptic Cairo, and Khan El-Khalili Bazaar. Daily lunch included."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.GIZA]

DURATION_DAYS = 3
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("350.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "Historical",
    "City Tour",
    "Pyramids",
    "Cultural",
]

HIGHLIGHTS = [
    "Stand before the majestic Great Pyramids of Giza and the Sphinx with expert Egyptologist guide.",
    "Discover the treasures of ancient Egypt at the Egyptian Museum including Tutankhamun's artifacts.",
    "Wander through the ancient ruins of Saqqara, Memphis, and Dahshur archaeological sites.",
    "Dive into Cairo's spiritual past in Islamic Cairo with Citadel of Saladin and Muhammad Ali Mosque.",
    "Explore Coptic Cairo's historic churches and Ben Ezra Synagogue in Old Cairo.",
    "Shop and experience local culture at the iconic Khan El Khalili Bazaar.",
    "Enjoy daily lunch at authentic local restaurants with traditional Egyptian cuisine.",
    "Travel comfortably with professional multilingual guide and air-conditioned transportation.",
]

ABOUT = """\
Embark on a captivating 3-day guided journey through the heart of Cairo, Egypt's bustling capital and a city teeming with millennia of history. This expertly crafted tour is designed for travelers who want to experience the essence of ancient, Islamic, and Coptic Cairo — all without the stress of planning. Enjoy daily sightseeing with a professional guide, transportation in air-conditioned vehicles, and delicious local lunches each day. (Please note: hotel accommodation is not included.)

Day 1: Giza Pyramids & Egyptian Museum
Begin your adventure at the iconic Giza Plateau, home to the legendary Pyramids of Giza, the Great Sphinx, and the Valley Temple. Learn about the rich heritage of these World Wonders as your guide brings the ancient pharaohs to life. After lunch at a local restaurant, continue to the Egyptian Museum in Tahrir Square, housing over 120,000 artifacts including the treasures of King Tutankhamun. Walk through centuries of history in one of the world's most important museums.

Day 2: Memphis, Saqqara & Dahshur
On your second day, explore the ancient capital of Memphis, Egypt's first capital and once the most powerful city in the world. Visit the open-air museum and marvel at the colossal statue of Ramses II. Head to Saqqara, the necropolis of Memphis, and home to the famous Step Pyramid of Djoser — the world's oldest large-scale stone structure. Continue to Dahshur, where you'll witness the architectural evolution of pyramids at the Bent Pyramid and the Red Pyramid.

Day 3: Islamic & Coptic Cairo + Khan El-Khalili Bazaar
On your final day, step into the spiritual and cultural depths of Old Cairo. Visit Coptic Cairo, where you'll explore the Hanging Church, Saint Sergius Church, and the Ben Ezra Synagogue. Then, delve into Islamic Cairo, walking through the historic Citadel of Saladin, Mosque of Muhammad Ali, and more. Cap off your journey with a stroll through the vibrant and colorful Khan El-Khalili Bazaar, a marketplace rich in tradition and charm.

This 3-day tour offers a perfect blend of archaeology, history, and culture — ideal for first-time visitors and history enthusiasts alike.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Giza Pyramids & Egyptian Museum",
        "steps": [
            ("Morning", "Hotel pickup in Cairo"),
            ("Morning", "Visit Giza Plateau: Pyramids of Giza, Great Sphinx, and Valley Temple"),
            ("Afternoon", "Lunch at a local restaurant"),
            ("Afternoon", "Explore Egyptian Museum in Tahrir Square with Tutankhamun's treasures"),
            ("Evening", "Drop-off at your hotel"),
        ],
    },
    {
        "day": 2,
        "title": "Memphis, Saqqara & Dahshur Archaeological Sites",
        "steps": [
            ("Morning", "Pickup from your hotel"),
            ("Morning", "Visit Memphis open-air museum and colossal statue of Ramses II"),
            ("Late Morning", "Explore Saqqara necropolis and Step Pyramid of Djoser"),
            ("Afternoon", "Lunch at a traditional restaurant"),
            ("Afternoon", "Visit Dahshur to see Bent Pyramid and Red Pyramid"),
            ("Evening", "Return to your hotel"),
        ],
    },
    {
        "day": 3,
        "title": "Islamic & Coptic Cairo with Khan El-Khalili Bazaar",
        "steps": [
            ("Morning", "Hotel pickup in Cairo"),
            ("Morning", "Explore Coptic Cairo: Hanging Church, Saint Sergius Church, Ben Ezra Synagogue"),
            ("Afternoon", "Lunch at local restaurant"),
            ("Afternoon", "Visit Islamic Cairo: Citadel of Saladin and Mosque of Muhammad Ali"),
            ("Late Afternoon", "Stroll through Khan El-Khalili Bazaar for shopping and cultural experience"),
            ("Evening", "Final drop-off at your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Professional Egyptologist tour guide for all 3 days",
    "Air-conditioned transportation throughout the tour",
    "Entrance fees to all mentioned sites including Giza Plateau",
    "Access to Egyptian Museum, Saqqara, Memphis, and Dahshur",
    "Entrance to Coptic Cairo sites and Islamic Cairo monuments",
    "Lunch at local restaurants on all three days",
    "Bottled water during tours",
    "Pickup and drop-off from Cairo hotels",
    "All service charges and taxes",
]

EXCLUSIONS = [
    "Hotel accommodation in Cairo",
    "Personal expenses and souvenirs",
    "Drinks during lunch meals",
    "Optional activities and tips for guides/drivers",
    "Entrance to the Great Pyramid interior or Mummies Room (available for extra cost)",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is hotel accommodation included?",
     "No, hotel stays are not included in this package. You are free to book your own preferred accommodation."),
    ("Is lunch included each day?",
     "Yes, lunch at a local restaurant is included on all three days."),
    ("What language is the tour conducted in?",
     "The tour is conducted in English, but other languages may be available upon request."),
    ("Can I customize the tour or skip parts?",
     "This is a fixed group tour, but private tours can be arranged on request."),
    ("Are entry tickets included in the price?",
     "Yes, all entry fees to the mentioned sites are included."),
    ("What should I bring?",
     "Comfortable walking shoes, sun protection (hat, sunglasses, sunscreen), a refillable water bottle, and a camera."),
    ("Are tips included?",
     "No, tipping is optional and at your discretion, but it is customary in Egypt."),
    ("How much walking is involved in this tour?",
     "Moderate walking is required at archaeological sites and museums. Comfortable walking shoes are essential."),
]


class Command(BaseCommand):
    help = "Seeds the 3-Day Cairo Guided Tour with pyramids, museums, and cultural sites."

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