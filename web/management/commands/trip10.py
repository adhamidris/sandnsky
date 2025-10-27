# web/management/commands/seed_trip_alexandria_cairo_shore.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Alexandria to Cairo: Pyramids & Egyptian Museum Day Tour"
TEASER = (
    "Full-day shore excursion from Alexandria Port to Cairo: Visit Giza Pyramids, Sphinx, "
    "Egyptian Museum, with traditional lunch. Perfect for cruise passengers with guaranteed port return."
)

PRIMARY_DEST = DestinationName.ALEXANDRIA
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.GIZA]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("250.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Shore Excursion",
    "Day Tour",
    "Historical",
    "Pyramids",
    "Cruise Passenger",
]

HIGHLIGHTS = [
    "Visit the Great Pyramids of Giza and the Sphinx - last remaining wonder of the ancient world.",
    "Explore the Egyptian Museum with artifacts over 5,000 years old, including Tutankhamun's treasures.",
    "Enjoy a traditional Egyptian lunch at a local restaurant with authentic cuisine.",
    "Travel in a private, air-conditioned vehicle with expert Egyptologist guide.",
    "Scenic drive between Alexandria and Cairo through Egyptian countryside.",
    "Optional visit to Khan El Khalili Bazaar or Tahrir Square (time permitting).",
    "Guaranteed timely return to Alexandria Port for cruise passengers.",
    "All entrance fees and bottled water included for a hassle-free experience.",
]

ABOUT = """\
Embark on a captivating day tour from Alexandria Port to the heart of Egypt – Cairo – and discover some of the most iconic and awe-inspiring sights the country has to offer. This full-day shore excursion is the perfect way to make the most of your cruise stop in Alexandria, offering a rich blend of history, culture, and local flavors, all in one unforgettable journey.

Your adventure begins as you're picked up directly from Alexandria Port by a comfortable air-conditioned vehicle. As you make your way to Cairo, enjoy scenic views of the Egyptian countryside while your professional guide shares insights about the history and culture of the region. The first major stop is at the world-famous Giza Pyramids, where you'll witness the last remaining wonder of the ancient world – the Great Pyramid of Khufu – along with the pyramids of Khafre and Menkaure. Don't miss the chance to snap a photo with the iconic Sphinx, the guardian of the plateau.

Next, you'll head to the Egyptian Museum, home to a vast collection of artifacts that date back thousands of years, including the priceless treasures of Tutankhamun. After immersing yourself in the rich history of ancient Egypt, you'll enjoy a delicious lunch at a local restaurant, where you can taste authentic Egyptian cuisine.

Depending on time, you may also have the opportunity to shop for souvenirs or stroll through the vibrant streets of Khan El Khalili Bazaar or visit Tahrir Square, depending on the itinerary and traffic conditions.

This tour is designed to ensure a timely return to Alexandria Port, giving you peace of mind and a full day of exploration without the stress. It's a perfect blend of ancient history, cultural experiences, and comfortable travel – all in one day!
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Alexandria Port to Cairo: Pyramids, Museum & City Tour",
        "steps": [
            ("Early Morning", "Pick-up from Alexandria Port by air-conditioned vehicle"),
            ("Morning", "Scenic drive to Cairo (approx. 2.5-3 hours) with guide commentary"),
            ("Late Morning", "Visit Giza Plateau: Great Pyramid, Pyramids of Khafre & Menkaure, Sphinx"),
            ("Afternoon", "Explore the Egyptian Museum with Tutankhamun's treasures"),
            ("Afternoon", "Traditional Egyptian lunch at local restaurant"),
            ("Late Afternoon", "Optional: Khan El Khalili Bazaar or Tahrir Square (time permitting)"),
            ("Evening", "Return drive to Alexandria Port"),
            ("Night", "Drop-off at Alexandria Port for cruise departure"),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off at Alexandria Port",
    "Professional English-speaking Egyptologist guide",
    "All transfers in a private air-conditioned vehicle",
    "Entrance fees to Giza Pyramids and Egyptian Museum",
    "Lunch at a local restaurant in Cairo",
    "Bottled water during the tour",
    "All service charges and taxes",
    "Port security coordination and assistance",
]

EXCLUSIONS = [
    "Any optional activities not mentioned in the itinerary",
    "Personal expenses and souvenirs",
    "Gratuities (tips) for guide and driver",
    "Camel ride at the pyramids (available at extra cost)",
    "Drinks during lunch",
    "Entry to the Great Pyramid interior (available at extra cost)",
    "Travel insurance",
]

FAQS = [
    ("How long is the drive from Alexandria Port to Cairo?",
     "The drive takes approximately 2.5 to 3 hours each way, depending on traffic."),
    ("Is this tour suitable for cruise passengers with limited time?",
     "Yes, the tour is specifically designed for cruise passengers and ensures timely return to the port."),
    ("What type of lunch is included?",
     "A set-menu lunch at a local Egyptian restaurant is included, with options for vegetarians upon request."),
    ("Are entrance fees included in the tour price?",
     "Yes, all main entrance fees, including the Pyramids and the Egyptian Museum, are included."),
    ("Will I have time to enter the Great Pyramid?",
     "Entering the Great Pyramid requires a separate ticket and is subject to time availability. Let your guide know in advance."),
    ("Can the tour be done as a private tour?",
     "Absolutely. Private tours are available for individuals, couples, families, or small groups."),
    ("What should I bring with me?",
     "Comfortable walking shoes, sun protection (hat, sunscreen), camera, passport (for port security), and some cash for optional expenses."),
    ("Is there a guarantee we'll return to the port on time?",
     "Yes, we guarantee timely return to Alexandria Port. Our tours are specifically scheduled with cruise departure times in mind."),
]


class Command(BaseCommand):
    help = "Seeds the Alexandria to Cairo shore excursion trip with destinations, content, and relations."

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