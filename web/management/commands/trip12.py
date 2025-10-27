# web/management/commands/seed_trip_cairo_white_desert.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to White Desert: 5-Day City Tour & Desert Safari"
TEASER = (
    "5-day adventure from Cairo to White Desert and Bahariya Oasis: Explore Giza Pyramids, Egyptian Museum, "
    "camp under stars in White Desert, visit Crystal Mountain and Black Desert with Bedouin hospitality."
)

PRIMARY_DEST = DestinationName.BAHAREYA
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.WHITE_BLACK]

DURATION_DAYS = 5
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("850.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-Tour Safari"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Desert Safari",
    "Multi-Day",
    "Camping",
    "Adventure",
    "Historical",
    "4x4 Safari",
]

HIGHLIGHTS = [
    "Stand in awe before the Great Pyramids of Giza and the Sphinx with expert guided tours.",
    "Explore the treasure-packed Egyptian Museum with Tutankhamun's artifacts.",
    "Discover Islamic and Coptic landmarks in Old Cairo and Khan El Khalili Bazaar.",
    "Travel deep into the surreal landscapes of the White Desert National Park.",
    "Visit the otherworldly Crystal Mountain and Black Desert volcanic formations.",
    "Camp under the stars in the Sahara with authentic Bedouin hospitality and traditional meals.",
    "Relax in Bahariya Oasis with natural hot springs and palm groves.",
    "Experience both ancient civilization and natural wonders in one comprehensive tour.",
]

ABOUT = """\
Embark on an unforgettable 5-day Egyptian adventure that blends the bustling energy of Cairo with the mystical beauty of the White Desert and Bahariya Oasis. This tour offers a unique combination of city exploration and desert escape—perfect for travelers seeking both culture and nature in one seamless itinerary.

Spend your first two days exploring Cairo, the vibrant capital steeped in thousands of years of history. With expert-guided tours (hotel accommodation not included), you'll visit world-famous landmarks such as the Giza Pyramids, Sphinx, and the Egyptian Museum, home to artifacts that bring ancient pharaohs to life. Stroll through local markets, marvel at Islamic architecture, and experience authentic Egyptian flavors during your included lunch breaks.

Next, trade the cityscape for an awe-inspiring desert journey. Over the next three days, travel deep into the Western Desert to discover the stunning Bahariya Oasis and the surreal White Desert National Park. Witness natural wonders such as black volcanic hills, sparkling salt lakes, and the dramatic limestone formations that give the White Desert its name. Spend nights under the stars in Bedouin-style camps, enjoying traditional meals, desert silence, and breathtaking sunrises.

This package includes lunch, transportation, local guides, and desert accommodation, ensuring a worry-free experience. It's ideal for adventurous souls, photographers, and those curious to discover both Egypt's ancient and natural marvels in a short span.

Please note: Hotel stay in Cairo is not included, allowing you the freedom to choose your preferred accommodation. This gives you flexibility and customization while keeping the desert portion fully guided and arranged.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Arrival in Cairo – Giza Pyramids & Sphinx Tour",
        "steps": [
            ("Morning", "Meet your guide at your Cairo hotel (accommodation not included)"),
            ("Morning", "Guided visit to Giza Pyramids and Sphinx"),
            ("Morning", "Visit the Valley Temple"),
            ("Afternoon", "Enjoy an included local lunch"),
            ("Afternoon", "Optional stop at Papyrus Institute or Perfume Shop"),
            ("Evening", "Return to hotel (evening at leisure)"),
        ],
    },
    {
        "day": 2,
        "title": "Egyptian Museum & Old Cairo Exploration",
        "steps": [
            ("Morning", "Visit the Egyptian Museum (Tutankhamun's treasures)"),
            ("Afternoon", "Explore Old Cairo (Coptic Cairo, Hanging Church)"),
            ("Afternoon", "Visit Khan El Khalili Bazaar for shopping"),
            ("Afternoon", "Enjoy lunch at a local restaurant"),
            ("Evening", "Transfer to your hotel or spend evening exploring"),
        ],
    },
    {
        "day": 3,
        "title": "Transfer to Bahariya Oasis – Black Desert & Crystal Mountain",
        "steps": [
            ("Early Morning", "Pick-up from Cairo hotel"),
            ("Morning", "Drive to Bahariya Oasis (approx. 4-5 hours)"),
            ("Afternoon", "Explore Black Desert and Crystal Mountain"),
            ("Afternoon", "Stop at Agabat Valley for photo opportunities"),
            ("Evening", "Set up desert camp in the White Desert"),
            ("Night", "Dinner under the stars, overnight camping"),
        ],
    },
    {
        "day": 4,
        "title": "White Desert Exploration – Return to Bahariya Oasis",
        "steps": [
            ("Morning", "Watch sunrise over the surreal landscape"),
            ("Morning", "Breakfast at the camp"),
            ("Morning", "Explore rock formations (Mushroom, Chicken, etc.)"),
            ("Afternoon", "Return to Bahariya Oasis"),
            ("Evening", "Free time to relax or take optional hot spring bath"),
            ("Night", "Overnight in eco-lodge or basic hotel"),
        ],
    },
    {
        "day": 5,
        "title": "Bahariya Oasis Tour & Return to Cairo",
        "steps": [
            ("Morning", "Breakfast at lodge"),
            ("Morning", "Optional local tour of Bahariya (Golden Mummies or Oasis village)"),
            ("Afternoon", "Return drive to Cairo"),
            ("Evening", "Drop-off at hotel or Cairo airport"),
        ],
    },
]

INCLUSIONS = [
    "Professional English-speaking tour guides in Cairo and desert",
    "Transportation in air-conditioned vehicles for city tours",
    "All transfers between sites and to/from desert",
    "White Desert safari with 4x4 transport",
    "Overnight camping in the White Desert (1 night) with all equipment",
    "Overnight in Bahariya Oasis (1 night in basic hotel or eco-lodge)",
    "All meals during desert portion (lunch, dinner, breakfast)",
    "Lunch included on Cairo days at local restaurants",
    "Bottled water during the desert trip",
    "All entrance fees to included sites",
    "Camping equipment and sleeping bags",
    "All applicable taxes and service charges",
]

EXCLUSIONS = [
    "Hotel accommodation in Cairo",
    "Personal expenses and souvenirs",
    "Tipping for guides and drivers",
    "Optional activities not listed in the itinerary",
    "Beverages during meals",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is hotel accommodation in Cairo included?",
     "No, this package excludes hotel stays in Cairo, allowing you to choose based on your preference and budget."),
    ("What type of vehicle is used for the desert trip?",
     "A 4x4 vehicle is used for all off-road desert travel to ensure a safe and smooth experience."),
    ("Do I need to bring my own camping gear?",
     "No, all camping equipment including tents and sleeping bags is provided."),
    ("Is this tour suitable for children or older travelers?",
     "Yes, but the desert camping and long drives may not be suitable for very young children or those with mobility issues."),
    ("Are vegetarian or special meals available?",
     "Yes, please inform us in advance of any dietary requirements."),
    ("Will I have cell signal in the desert?",
     "Coverage is limited in the White Desert; we recommend informing family in advance."),
    ("Can I add extra nights in Cairo before or after the tour?",
     "Absolutely. We can help with add-ons or hotel recommendations upon request."),
    ("What should I pack for the desert portion?",
     "Warm clothing for cold nights, comfortable walking shoes, sunscreen, hat, flashlight, and personal toiletries."),
]


class Command(BaseCommand):
    help = "Seeds the 5-Day Cairo & White Desert Safari trip with destinations, content, and relations."

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