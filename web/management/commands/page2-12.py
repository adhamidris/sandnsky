# web/management/commands/seed_trip_siwa_oasis.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Siwa: 4-Day Oasis Tour with Desert Safari & Salt Lakes"
TEASER = (
    "4-day Siwa Oasis tour from Cairo: Explore Temple of the Oracle, swim in salt lakes, "
    "4x4 desert safari in Great Sand Sea, Cleopatra's Spring, and experience authentic Berber culture."
)

PRIMARY_DEST = DestinationName.SIWA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 4
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("840.00")
TOUR_TYPE_LABEL = "Daily Tour — Multi-Tour Safari"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Oasis Tour",
    "Desert Safari",
    "Multi-Day",
    "Cultural",
    "Adventure",
    "4x4 Safari",
]

HIGHLIGHTS = [
    "Explore the remote and mystical Siwa Oasis, Egypt's hidden gem in the western desert.",
    "Swim in the crystal-clear Salt Lakes and rejuvenate in natural hot springs.",
    "Visit the legendary Temple of the Oracle, once visited by Alexander the Great.",
    "Float in Cleopatra's Pool, a natural spring surrounded by date palms.",
    "Witness a golden desert sunset over the Great Sand Sea during 4x4 safari.",
    "Enjoy an exhilarating desert safari with sandboarding and Bedouin dinner under stars.",
    "Wander the ancient ruins of the Shali Fortress and Mountain of the Dead.",
    "Experience authentic Berber culture, traditional food, and local hospitality.",
]

ABOUT = """\
Escape the city noise and dive into the serene and mystical beauty of Egypt's western desert with our 4-Day, 3-Night Siwa Oasis Tour – an unforgettable journey into one of the most untouched and magical regions of the country. Starting from Cairo, this carefully curated tour takes you across breathtaking landscapes, ancient ruins, salt lakes, natural hot and cold springs, and the heart of Berber culture.

Siwa, known for its isolation, has retained its unique traditions, language, and way of life. Over these four days, you'll explore the majestic Temple of the Oracle (visited by Alexander the Great), swim in the stunning Cleopatra Spring, and float effortlessly in the surreal Salt Lakes – famed for their healing properties and Instagram-worthy vistas.

Your desert adventure continues with a thrilling 4×4 sand dune safari, where you'll witness the stunning beauty of the Great Sand Sea, visit Bir Wahid hot spring for a warm desert soak, and enjoy traditional Bedouin meals under the stars. With knowledgeable local guides, comfortable accommodations, and air-conditioned transport, this journey strikes the perfect balance between adventure, relaxation, and cultural immersion.

Whether you're a nature lover, a history buff, or simply looking for an off-the-beaten-path experience, Siwa Oasis will capture your soul. Join us and uncover one of Egypt's best-kept secrets in just four days – memories that will last a lifetime.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo to Siwa Oasis – Journey to the Desert",
        "steps": [
            ("Early Morning", "Pickup from your Cairo hotel"),
            ("Morning", "Drive to Siwa Oasis (approx. 8-9 hours with breaks)"),
            ("Afternoon", "Arrival and check-in at eco-lodge or hotel"),
            ("Evening", "Free time to relax or explore the local market"),
            ("Night", "Dinner and overnight in Siwa"),
        ],
    },
    {
        "day": 2,
        "title": "Siwa Historical Exploration – Ancient Sites & Springs",
        "steps": [
            ("Morning", "Breakfast at the hotel"),
            ("Morning", "Visit to the Temple of the Oracle of Amun"),
            ("Late Morning", "Explore Shali Fortress, the ancient mud-brick citadel"),
            ("Afternoon", "Walk through the old town and local markets"),
            ("Afternoon", "Swim in Cleopatra's Spring"),
            ("Evening", "Sunset at Fatnas Island"),
            ("Night", "Dinner and overnight stay"),
        ],
    },
    {
        "day": 3,
        "title": "Salt Lakes & Desert Safari Adventure",
        "steps": [
            ("Morning", "Breakfast at accommodation"),
            ("Morning", "Visit to Siwa's Salt Lakes – swim and float"),
            ("Afternoon", "Lunch (optional)"),
            ("Afternoon", "4x4 desert safari to the Great Sand Sea"),
            ("Late Afternoon", "Sandboarding on the dunes"),
            ("Evening", "Visit Bir Wahid Hot Spring"),
            ("Evening", "Sunset view in the dunes"),
            ("Night", "Bedouin-style dinner under the stars"),
        ],
    },
    {
        "day": 4,
        "title": "Siwa to Cairo – Return Journey",
        "steps": [
            ("Morning", "Early breakfast at accommodation"),
            ("Morning", "Optional visit to Mountain of the Dead"),
            ("Late Morning", "Start drive back to Cairo"),
            ("Evening", "Drop-off at your hotel in Cairo"),
        ],
    },
]

INCLUSIONS = [
    "Round-trip transportation from Cairo in air-conditioned vehicle",
    "3 nights' accommodation in Siwa (eco-lodge or hotel)",
    "Daily breakfast and dinner during the stay",
    "Guided visits to historical and natural sites",
    "4x4 desert safari to the Great Sand Sea with sandboarding",
    "Visit to Salt Lakes and Bir Wahid hot spring",
    "Local English-speaking tour guide in Siwa",
    "Bottled water during excursions",
    "All entrance fees mentioned in the itinerary",
    "Bedouin-style dinner under the stars",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Gratuities for guides and drivers (optional but appreciated)",
    "Travel insurance",
    "Lunch meals (available as optional addition)",
    "Any services not mentioned in the itinerary",
    "Alcoholic beverages",
    "Optional activities not specified",
]

FAQS = [
    ("How far is Siwa from Cairo?",
     "Siwa Oasis is approximately 750 km from Cairo. The drive takes around 8-9 hours with rest stops."),
    ("Is the road to Siwa safe?",
     "Yes, the road is generally safe and frequently traveled by tour operators. We travel during daylight and include rest stops for comfort."),
    ("What type of accommodation is included?",
     "We offer stays in eco-lodges or 3-star hotels depending on your preference and availability. All options provide clean, comfortable rooms with local charm."),
    ("What should I pack for this trip?",
     "Light clothing for daytime, warmer layers for evening desert temperatures, swimsuit (for springs and lakes), comfortable walking shoes, sunscreen, sunglasses, hat, and personal toiletries."),
    ("Can vegetarians or special diets be accommodated?",
     "Yes, please inform us in advance about dietary preferences or restrictions."),
    ("Is this tour suitable for children or older travelers?",
     "Yes, though the desert safari may be bumpy. We can adjust the program based on your group's needs."),
    ("Are there bathroom facilities during the desert safari?",
     "Basic facilities are available at designated stops. The desert itself has no facilities, so we plan accordingly."),
    ("What is the best time of year to visit Siwa?",
     "October to April is ideal with pleasant temperatures. Summer months can be extremely hot."),
]


class Command(BaseCommand):
    help = "Seeds the 4-Day Siwa Oasis tour from Cairo with desert safari and cultural experiences."

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