# web/management/commands/seed_trip_cairo_palaces.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo: Royal Palaces Day Tour - Abdeen, Baron & Manial Palace"
TEASER = (
    "Day tour exploring Cairo's royal heritage: Visit Baron Palace's Indian-inspired architecture, "
    "Abdeen Palace's presidential museum, and Manial Palace's Ottoman-Persian blend with gardens."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = []

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("100.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Tour",
    "Cultural",
    "Historical",
    "Architecture",
    "Royal Heritage",
    "City Tour",
]

HIGHLIGHTS = [
    "Explore Baron Palace, Cairo's most unique landmark inspired by Indian and Cambodian architecture.",
    "Visit the lavish Abdeen Palace, former residence of Egypt's royal family, now a museum of royal treasures.",
    "Discover the enchanting Manial Palace, blending Ottoman, Moorish, and Persian styles with beautiful gardens.",
    "Learn fascinating stories of Egypt's modern royal history and architectural heritage.",
    "See royal collections including weapons, gifts from world leaders, and priceless artifacts.",
    "Enjoy comfortable transfers between palaces with professional English-speaking guide.",
    "Lunch included at a local restaurant featuring authentic Egyptian cuisine.",
    "Experience Cairo beyond ancient monuments with its rich 19th-20th century royal history.",
]

ABOUT = """\
Step into Cairo's royal past with a captivating day tour to three of its most iconic palaces: Baron Palace, Abdeen Palace, and Manial Palace. This immersive cultural journey takes you through different eras of Egyptian history, showcasing architectural beauty, royal collections, and hidden stories behind Cairo's most impressive residences.

Your first stop will be the Baron Palace, one of Cairo's most unusual landmarks. Built in the early 20th century by Belgian industrialist Édouard Empain, this Hindu-inspired palace is surrounded by myth and legend. Its striking design, inspired by Indian temples and Cambodian architecture, sets it apart as one of the most fascinating structures in the city. Inside, you'll explore ornately decorated halls and learn about the mysterious history surrounding this unique monument.

The tour continues with a visit to the Abdeen Palace, the official residence of Egypt's former royal family and one of the most luxurious palaces in the world. Today, it serves as a presidential palace and a museum, housing collections of weapons, gifts from world leaders, and priceless artifacts. The palace reflects Egypt's modern royal history and its connections with global powers.

Next, you'll head to the beautiful Manial Palace, built by Prince Mohamed Ali in the early 20th century. This palace blends Ottoman, Moorish, and Persian styles, offering a glimpse into the luxurious lifestyle of Egyptian royalty. Surrounded by lush gardens and housing rare antiques, manuscripts, and artwork, the palace is an enchanting stop that combines culture and tranquility.

This full-day tour offers not only a glimpse into Egypt's regal past but also a deeper understanding of its cultural influences, from European to Islamic art and architecture. Whether you're fascinated by history, architecture, or royal heritage, this experience is a perfect way to explore Cairo's treasures beyond its ancient monuments.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo Royal Palaces Exploration - Three Iconic Residences",
        "steps": [
            ("Morning", "Pick-up from your Cairo or Giza hotel"),
            ("Morning", "Visit Baron Palace - Hindu-inspired architecture with unique design"),
            ("Late Morning", "Explore Abdeen Palace - Former royal residence and presidential museum"),
            ("Afternoon", "Lunch at local restaurant with Egyptian cuisine"),
            ("Afternoon", "Discover Manial Palace - Ottoman, Moorish, and Persian styles with gardens"),
            ("Late Afternoon", "Return transfer to your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off at your Cairo or Giza hotel",
    "Transportation in private air-conditioned vehicle",
    "Professional English-speaking tour guide",
    "Entrance fees to Baron, Abdeen, and Manial Palaces",
    "Bottled water during the tour",
    "Lunch at a local restaurant",
    "All taxes and service charges",
    "Comprehensive guided tour of all three palaces",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Gratuities for guide and driver (optional)",
    "Any optional activities not mentioned in the program",
    "Travel insurance",
    "Additional photography fees in restricted areas",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("How long does this palace tour last?",
     "The tour lasts approximately 5-6 hours, including transfers, visits, and lunch."),
    ("Are photography and video allowed inside the palaces?",
     "Photography is generally permitted in most areas, but some sections may require additional fees."),
    ("What should I wear for the tour?",
     "Comfortable clothing and shoes are recommended. Since this is a cultural tour, modest attire is preferable."),
    ("Are the palaces accessible for children?",
     "Yes, children are welcome and may enjoy the palaces, especially the gardens of Manial Palace."),
    ("Is lunch included?",
     "Yes, lunch at a local restaurant is included in the tour package."),
    ("Which palace is the most impressive?",
     "Each palace has its unique charm: Baron for architecture, Abdeen for royal collections, and Manial for gardens and blend of styles."),
    ("Is there a lot of walking involved?",
     "Moderate walking is required between palace rooms and gardens. Comfortable walking shoes are recommended."),
    ("Can this tour be customized to include other sites?",
     "Yes, private tours can be customized to include other attractions upon request."),
]


class Command(BaseCommand):
    help = "Seeds the Cairo Royal Palaces Day Tour visiting Abdeen, Baron, and Manial Palaces."

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