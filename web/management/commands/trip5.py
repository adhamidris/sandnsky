# web/management/commands/seed_trip_nile_cruise_aswan_luxor.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Aswan to Luxor: 4-Day Nile Cruise with Temples & Valley of Kings"
TEASER = (
    "4-day Nile cruise from Aswan to Luxor: Visit Philae Temple, Kom Ombo, Edfu Temple, "
    "Karnak, Luxor Temple, and Valley of Kings. Comfortable standard cruise with expert Egyptologist."
)

PRIMARY_DEST = DestinationName.ASWAN
ALSO_APPEARS_IN = [DestinationName.LUXOR]

DURATION_DAYS = 4
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("800.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-City"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Nile Cruise",
    "Multi-Day",
    "Temple Exploration",
    "Historical",
    "River Journey",
]

HIGHLIGHTS = [
    "Cruise the Nile River in comfort over 4 days from Aswan to Luxor.",
    "Explore iconic temples: Philae, Kom Ombo, Edfu, Karnak, and Luxor.",
    "Discover royal tombs in the Valley of the Kings with expert guidance.",
    "Marvel at the architecture of Queen Hatshepsut's Temple.",
    "Learn from an expert Egyptologist guide at every stop.",
    "Relax with full-board accommodation and stunning river views.",
    "Visit the High Dam and Unfinished Obelisk in Aswan.",
    "Comfortable air-conditioned transport and all entrance fees included.",
]

ABOUT = """\
Discover the timeless beauty of Egypt on a 4-day, 3-night standard Nile Cruise from Aswan to Luxor. This classic journey offers travelers a unique way to experience some of the most legendary sites in ancient Egyptian history—all while relaxing aboard a comfortable cruise ship sailing along the legendary Nile River.

Your journey begins in Aswan, a peaceful and charming city known for its scenic Nile views and Nubian culture. Explore iconic sites such as the High Dam, the Unfinished Obelisk, and the beautiful Philae Temple, dedicated to the goddess Isis. After a relaxing evening onboard, the cruise sets sail toward Kom Ombo, where you'll visit the dual temples dedicated to Sobek and Horus.

Next, continue to Edfu, home to one of Egypt's best-preserved ancient temples—the Temple of Horus. As the cruise drifts north, enjoy peaceful views of traditional villages, lush landscapes, and the golden desert in the background, offering plenty of photo opportunities and time to unwind.

The final destination is the open-air museum city of Luxor, where you'll explore the grandeur of Karnak Temple, the Valley of the Kings, the Mortuary Temple of Hatshepsut, and the Colossi of Memnon. With expertly guided tours and seamless onboard accommodations, this cruise offers the perfect blend of sightseeing, culture, and leisure.

Ideal for history lovers, first-time Egypt visitors, or anyone looking for a relaxing and enriching vacation, the 4-Day Standard Nile Cruise provides an unforgettable way to step back into the past while enjoying modern comforts.

Whether you're traveling solo, as a couple, or with family, this classic Nile journey promises magical moments and deep connections with Egypt's ancient heritage.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Arrival in Aswan – Nile Cruise Embarkation",
        "steps": [
            ("Morning", "Meet & greet service in Aswan"),
            ("Morning", "Visit the High Dam and Unfinished Obelisk"),
            ("Afternoon", "Explore Philae Temple"),
            ("Evening", "Embark the Nile Cruise"),
            ("Night", "Dinner & overnight on board in Aswan"),
        ],
    },
    {
        "day": 2,
        "title": "Kom Ombo & Edfu Temples – Sail to Luxor",
        "steps": [
            ("Morning", "Sail to Kom Ombo and visit the Twin Temple of Sobek & Horus"),
            ("Afternoon", "Continue to Edfu and visit the Temple of Horus (via horse carriage)"),
            ("Evening", "Sail to Luxor via Esna Lock"),
            ("Night", "Overnight on board"),
        ],
    },
    {
        "day": 3,
        "title": "Luxor East Bank – Karnak & Luxor Temples",
        "steps": [
            ("Morning", "Breakfast onboard"),
            ("Morning", "Visit Karnak Temple"),
            ("Afternoon", "Explore Luxor Temple"),
            ("Evening", "Optional sound & light show in Karnak (extra cost)"),
            ("Night", "Overnight on board in Luxor"),
        ],
    },
    {
        "day": 4,
        "title": "Luxor West Bank Tour & Disembarkation",
        "steps": [
            ("Morning", "Breakfast onboard"),
            ("Morning", "Visit Valley of the Kings"),
            ("Afternoon", "Explore Hatshepsut Temple and Colossi of Memnon"),
            ("Afternoon", "Disembarkation in Luxor"),
            ("Evening", "Transfer to airport or onward destination"),
        ],
    },
]

INCLUSIONS = [
    "3 nights aboard a standard Nile Cruise (full board accommodation)",
    "Meet & greet service at airports or train stations",
    "All transfers in air-conditioned vehicles",
    "English-speaking Egyptologist guide",
    "Entrance fees to all mentioned sightseeing",
    "Guided tours in Aswan, Kom Ombo, Edfu, and Luxor",
    "Taxes and service charges",
    "Horse carriage ride in Edfu",
]

EXCLUSIONS = [
    "Any optional tours or personal expenses",
    "Tips and gratuities for guide and crew",
    "Beverages during meals onboard",
    "Domestic flights or train tickets to/from Aswan & Luxor",
    "Entry to the Tomb of Tutankhamun (optional upgrade)",
    "Travel insurance",
    "Sound & Light Show at Karnak Temple",
    "Hot air balloon rides in Luxor",
]

FAQS = [
    ("What is the best time to take this cruise?",
     "The best months are October to April when temperatures are cooler and ideal for sightseeing."),
    ("Are vegetarian meals available on the cruise?",
     "Yes, vegetarian and dietary requests can be accommodated—please notify us in advance."),
    ("Is the cruise suitable for families with children?",
     "Absolutely. The cruise is family-friendly, and children love exploring the temples and stories of ancient Egypt."),
    ("Can I book optional tours during the cruise?",
     "Yes, optional tours like the Abu Simbel excursion or hot air balloon rides can be arranged at an extra cost."),
    ("What kind of Nile Cruise is this?",
     "This is a standard Nile Cruise offering clean, comfortable cabins, buffet meals, and onboard amenities."),
    ("What should I wear for temple visits?",
     "Lightweight, modest clothing is recommended. Bring a hat, sunglasses, and sunscreen for daytime tours."),
    ("Is there Wi-Fi available on the cruise?",
     "Most standard cruises offer limited Wi-Fi access, usually for an additional fee."),
    ("What is the cabin configuration?",
     "Standard twin/double cabins with private bathrooms. Upgrades may be available upon request."),
]


class Command(BaseCommand):
    help = "Seeds the Aswan to Luxor 4-day Nile Cruise trip with destinations, content, and relations."

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