# web/management/commands/seed_trip_cairo_ain_sokhna.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to El Ain Sokhna: 3-Day City Tour & Beach Escape"
TEASER = (
    "3-day Cairo tour with Giza Pyramids, Egyptian Museum, Nile felucca ride, "
    "and Red Sea beach day at El Ain Sokhna. Perfect blend of ancient history and coastal relaxation."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.AIN_EL_SOKHNA, DestinationName.GIZA]

DURATION_DAYS = 3
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("460.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-City"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "City Tour",
    "Beach Day",
    "Historical",
    "Multi-Day",
    "Pyramids",
]

HIGHLIGHTS = [
    "Explore the legendary Giza Pyramids, Sphinx, and Valley Temple with expert guidance.",
    "Enjoy a 30-minute camel ride with panoramic desert views of the pyramids.",
    "Visit the Grand Egyptian Museum, Egypt's newest archaeological treasure trove.",
    "Discover ancient artifacts and royal mummies at two of Egypt's most important museums.",
    "Relax on a peaceful 1-hour felucca ride on the Nile River at sunset.",
    "Escape the city for a Red Sea beach day at El Ain Sokhna resort.",
    "Delicious lunch included daily with local and seafood options.",
    "Comfortable private transport with professional driver-guide throughout.",
]

ABOUT = """\
Embark on a captivating 3-day journey through Egypt's most iconic historical landmarks and a serene beach getaway with our Cairo & El Ain Sokhna Tour Package. Designed for travelers short on time but eager for an authentic Egyptian experience, this package combines rich culture, ancient history, and coastal relaxation—all in one unforgettable trip.

Day 1 begins with a visit to the majestic Giza Pyramids, one of the Seven Wonders of the Ancient World. Stand in awe of the Pyramids of Khufu, Khafre, and Menkaure, then enjoy a 30-minute camel ride across the desert sands with a perfect backdrop of these architectural marvels. Afterward, explore the much-anticipated Grand Egyptian Museum, home to the most extensive collection of ancient Egyptian artifacts, including treasures from Tutankhamun's tomb.

On Day 2, delve deeper into Egypt's fascinating history. Begin with a guided tour of the Egyptian Museum in Tahrir Square, where ancient artifacts narrate the stories of pharaohs and dynasties. Continue to the National Museum of Egyptian Civilization, a modern space showcasing the royal mummies and diverse aspects of Egypt's heritage. Cap off the day with a 1-hour Felucca ride on the Nile River, soaking in the peaceful breeze and panoramic city views as the sun sets.

Day 3 is a complete change of scenery with a day trip to El Ain Sokhna, a beautiful Red Sea coastal town just two hours from Cairo. Relax on the golden beaches, swim in clear waters, and enjoy your included day-use access at a beach resort. Lunch is included, allowing you to enjoy fresh seafood or Egyptian cuisine with a seaside view before heading back to Cairo.

This tour is ideal for travelers who want to mix history, culture, and leisure, all while benefiting from organized transportation and knowledgeable guides. While accommodation is not included, all transfers, entrance fees, and lunch are covered—making this the perfect, stress-free short getaway.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Giza Pyramids, Camel Ride & Grand Egyptian Museum",
        "steps": [
            ("Morning", "Pickup from your Cairo location"),
            ("Morning", "Visit Giza Plateau: Pyramids, Sphinx, and Valley Temple"),
            ("Morning", "30-minute camel ride around the pyramids"),
            ("Afternoon", "Visit the Grand Egyptian Museum"),
            ("Afternoon", "Lunch at a local restaurant"),
            ("Evening", "Drop-off at your accommodation"),
        ],
    },
    {
        "day": 2,
        "title": "Two Museums & Nile Felucca Ride",
        "steps": [
            ("Morning", "Pickup in the morning"),
            ("Morning", "Visit the Egyptian Museum in Tahrir"),
            ("Afternoon", "Visit the National Museum of Egyptian Civilization (Royal Mummies Hall)"),
            ("Afternoon", "Lunch at a Nile-view restaurant"),
            ("Evening", "1-hour private Felucca ride on the Nile"),
            ("Evening", "Return to accommodation in Cairo"),
        ],
    },
    {
        "day": 3,
        "title": "Day Trip to El Ain Sokhna (Red Sea)",
        "steps": [
            ("Morning", "Early morning pickup from Cairo"),
            ("Morning", "Drive to El Ain Sokhna (approx. 2 hrs)"),
            ("Late Morning", "Enjoy full beach day-use at a resort"),
            ("Afternoon", "Lunch at the resort"),
            ("Afternoon", "Swimming, relaxation, beach walk"),
            ("Evening", "Return to Cairo in the evening"),
        ],
    },
]

INCLUSIONS = [
    "Guided tours with professional Egyptologist guides",
    "Entry tickets to all mentioned sites: Giza Pyramids, Grand Egyptian Museum, Egyptian Museum, Museum of Egyptian Civilization",
    "30-minute camel ride at Giza Pyramids",
    "1-hour private felucca ride on the Nile",
    "Day-use at a beach resort in El Ain Sokhna (with lunch)",
    "Round-trip private transportation from Cairo for all tour days",
    "Lunch included on all 3 days",
    "Bottled water during tours",
    "All service charges and taxes",
]

EXCLUSIONS = [
    "Hotel accommodation",
    "Personal expenses and tips",
    "Drinks during meals",
    "Optional activities not mentioned in the itinerary",
    "Visa fees (if applicable)",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is hotel accommodation included in this tour?",
     "No, this tour package excludes hotel accommodation. However, we can assist you with hotel recommendations upon request."),
    ("Are entrance fees included?",
     "Yes, all entrance tickets to the included sites and museums are covered."),
    ("Can vegetarians or people with dietary restrictions be accommodated?",
     "Absolutely. Please inform us in advance, and we will arrange suitable meals."),
    ("How long is the drive to El Ain Sokhna?",
     "The drive is approximately 2 hours each way from Cairo, depending on traffic."),
    ("Is swimming allowed in El Ain Sokhna during the tour?",
     "Yes! You will have full access to a beach resort with swimming facilities, showers, and changing rooms."),
    ("Is this tour suitable for children or seniors?",
     "Yes, this tour is family-friendly and suitable for all age groups. Moderate walking is involved."),
    ("What should I bring with me?",
     "Sunscreen, hat, comfortable shoes, swimwear (for Day 3), ID/passport, and a camera."),
    ("Are the camel rides and felucca rides private?",
     "Yes, both the camel ride and felucca ride are private experiences included in your tour."),
]


class Command(BaseCommand):
    help = "Seeds the 3-Day Cairo & El Ain Sokhna tour with destinations, content, and relations."

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