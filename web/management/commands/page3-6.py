# web/management/commands/seed_trip_white_desert_3day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to White Desert: 3-Day Bahariya Oasis & Desert Safari"
TEASER = (
    "3-day desert adventure from Cairo to Bahariya Oasis and White Desert: Explore Black Desert, "
    "Crystal Mountain, camp under stars, and experience Bedouin culture in surreal landscapes."
)

PRIMARY_DEST = DestinationName.BAHAREYA
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.WHITE_BLACK]

DURATION_DAYS = 3
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("550.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-Tour Safari"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Desert Safari",
    "Camping",
    "Adventure",
    "Multi-Day",
    "4x4 Safari",
    "Natural Wonders",
]

HIGHLIGHTS = [
    "Discover the Bahariya Oasis, a lush desert haven surrounded by palm groves and hot springs.",
    "Explore the mysterious Black Desert with its unique volcanic hills and golden sands.",
    "Marvel at the glittering Crystal Mountain, a natural wonder made of sparkling quartz crystals.",
    "Experience the breathtaking Valley of Agabat, framed by dramatic limestone cliffs.",
    "Camp overnight in the surreal White Desert, famous for chalk rock formations shaped by wind.",
    "Enjoy a traditional Bedouin dinner under the stars around a desert campfire.",
    "Witness magical desert sunrise and sunset, perfect for photography and reflection.",
    "Travel in comfortable 4x4 vehicles with experienced desert guides.",
]

ABOUT = """\
Embark on a once-in-a-lifetime journey deep into Egypt's desert landscapes with our 3-Day Desert Adventure to the White Desert and Bahariya Oasis. This unforgettable experience combines breathtaking natural wonders, ancient heritage, and the thrill of desert camping under the stars.

Your adventure begins with a drive from Cairo to the Bahariya Oasis, an enchanting haven in the Western Desert, surrounded by palm groves and natural springs. The oasis offers a glimpse into traditional desert life, where history, culture, and nature blend seamlessly. From there, your exploration continues into the Black Desert, known for its unique volcanic hills and golden sand dunes.

As the journey unfolds, you'll venture into the world-famous White Desert, a surreal landscape filled with chalk-white rock formations sculpted by centuries of wind and sand. Here, the desert transforms into a natural art gallery, with formations shaped like animals, mushrooms, and abstract sculptures. Spending the night camping in the White Desert is truly magical—imagine sitting around a campfire, enjoying a traditional Bedouin meal, and gazing at a sky full of stars far away from city lights.

Throughout the tour, you'll also visit Crystal Mountain, a sparkling ridge made of quartz crystals, and the Valley of Agabat, where towering limestone cliffs rise dramatically above golden sands. Experienced guides and drivers ensure your comfort and safety while sharing insights into the desert's geology, history, and cultural significance.

Whether you're seeking adventure, tranquility, or inspiration, this 3-day safari offers the perfect escape. It's not just a tour—it's an immersion into the heart of Egypt's natural beauty, where silence, stars, and landscapes create memories that last forever.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo → Bahariya Oasis → Black Desert",
        "steps": [
            ("Morning", "Pick up from Cairo and drive to Bahariya Oasis (approx. 4 hrs)"),
            ("Afternoon", "Explore Bahariya town and palm groves"),
            ("Afternoon", "Visit the Black Desert with its volcanic hills"),
            ("Evening", "Overnight stay in Bahariya Oasis (hotel/lodge)"),
        ],
    },
    {
        "day": 2,
        "title": "Bahariya Oasis → Crystal Mountain → White Desert",
        "steps": [
            ("Morning", "Breakfast and departure with 4x4 safari vehicles"),
            ("Morning", "Visit Crystal Mountain and the Valley of Agabat"),
            ("Afternoon", "Continue to the White Desert to witness unique rock formations"),
            ("Evening", "Set up desert camp and enjoy Bedouin dinner under the stars"),
            ("Night", "Overnight camping in the White Desert"),
        ],
    },
    {
        "day": 3,
        "title": "White Desert → Bahariya Oasis → Cairo",
        "steps": [
            ("Morning", "Sunrise breakfast in the desert"),
            ("Morning", "Free time for photos and exploration of White Desert"),
            ("Afternoon", "Return to Bahariya Oasis for lunch"),
            ("Afternoon", "Drive back to Cairo"),
            ("Evening", "Drop-off in Cairo"),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off from Cairo in private air-conditioned vehicle",
    "Transportation by private air-conditioned vehicle to/from desert",
    "4x4 jeep for desert safari in White Desert and surrounding areas",
    "English-speaking desert guide throughout the tour",
    "Accommodation (1 night at Bahariya Oasis hotel/lodge, 1 night camping in White Desert)",
    "All meals as per itinerary (breakfast, lunch, dinner)",
    "Bedouin camping equipment (tents, blankets, sleeping bags)",
    "All entrance fees to mentioned sites and protected areas",
    "Bottled water during the tour",
    "All taxes and service charges",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Gratuities for guides and drivers",
    "Travel insurance",
    "Optional activities not mentioned in the program",
    "Alcoholic beverages",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("How difficult is the tour?",
     "This tour is moderate and suitable for most travelers. No prior desert experience is required."),
    ("What should I pack?",
     "Comfortable clothes, sturdy shoes, hat, sunscreen, a jacket for cool nights, and a camera are recommended."),
    ("Are bathrooms available during camping?",
     "Basic facilities are provided during desert camping, but expect limited amenities."),
    ("Can vegetarian meals be arranged?",
     "Yes, vegetarian and special dietary meals can be prepared upon request."),
    ("Is the tour safe for families with kids?",
     "Yes, families are welcome. Children will enjoy the desert landscapes and camping experience."),
    ("What is the temperature like in the desert?",
     "Days can be warm to hot, while nights can be quite cool, especially in winter months. Layered clothing is recommended."),
    ("Is there mobile phone reception in the desert?",
     "Reception is limited in remote desert areas. The White Desert has very spotty coverage."),
    ("What type of vehicles are used for the desert safari?",
     "We use 4x4 vehicles specifically designed for desert terrain, driven by experienced desert drivers."),
]


class Command(BaseCommand):
    help = "Seeds the 3-Day White Desert & Bahariya Oasis desert adventure tour."

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