# web/management/commands/seed_trip_nile_cruise_luxor_aswan.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Luxor to Aswan: 5-Day Nile Cruise with Temples & Valley of Kings"
TEASER = (
    "5-day Nile cruise from Luxor to Aswan: Explore Karnak, Valley of Kings, Edfu & Kom Ombo temples, "
    "Philae Temple, with optional Abu Simbel visit. Comfortable 5-star cruise with expert Egyptologist."
)

PRIMARY_DEST = DestinationName.LUXOR
ALSO_APPEARS_IN = [DestinationName.ASWAN]

DURATION_DAYS = 5
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
    "Explore ancient temples and tombs with a certified Egyptologist guide.",
    "Cruise the majestic Nile River aboard a comfortable 5-star standard ship.",
    "Discover the wonders of Luxor, including the Valley of the Kings and Karnak Temple.",
    "Visit the famous Edfu Temple of Horus and Kom Ombo's unique double temple.",
    "Enjoy Aswan's major sights including Philae Temple and the High Dam.",
    "Optional visit to Abu Simbel – one of Egypt's most awe-inspiring monuments.",
    "Full board accommodation with daily meals and onboard entertainment.",
    "Comfortable air-conditioned transport and all entrance fees included.",
]

ABOUT = """\
Embark on an unforgettable journey through the heart of Ancient Egypt with this Standard 5-Day, 4-Night Nile Cruise from Luxor to Aswan. This carefully curated Egypt tour offers the perfect balance of comfort, culture, and discovery as you sail along the legendary Nile River, one of the world's most iconic waterways.

Your journey begins in Luxor, often referred to as the world's greatest open-air museum. Here, you'll explore some of Egypt's most revered ancient sites, including the Karnak Temple, the Luxor Temple, the Valley of the Kings, and the Temple of Queen Hatshepsut. With expert guides, you'll dive deep into the fascinating stories of pharaohs, gods, and dynasties that shaped human history.

As you cruise south, enjoy the tranquility of the Nile's lush landscapes and small riverside villages. Onboard your comfortable standard-class cruise ship, you'll be treated to cozy accommodations, daily meals, and occasional entertainment, providing a relaxed base for your adventures.

In Edfu and Kom Ombo, you'll visit two beautifully preserved temples dedicated to Horus and the crocodile god Sobek, respectively. The journey concludes in the stunning city of Aswan, where you'll explore the Philae Temple, the Unfinished Obelisk, and the impressive High Dam.

Whether you're a history lover, a cultural explorer, or simply looking for a unique travel experience, this Nile Cruise offers an extraordinary glimpse into the past combined with modern-day comfort. Join us for a once-in-a-lifetime adventure through Egypt's timeless wonders – a journey that's as enriching as it is relaxing.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Luxor – Embarkation & East Bank Tour",
        "steps": [
            ("Morning", "Meet & assist upon arrival in Luxor"),
            ("Morning", "Visit Karnak Temple and Luxor Temple"),
            ("Afternoon", "Embark on the Nile Cruise"),
            ("Evening", "Dinner onboard"),
            ("Night", "Overnight in Luxor"),
        ],
    },
    {
        "day": 2,
        "title": "Luxor – West Bank Tour & Cruise to Edfu",
        "steps": [
            ("Morning", "Visit the Valley of the Kings"),
            ("Morning", "Explore Hatshepsut Temple and Colossi of Memnon"),
            ("Afternoon", "Lunch onboard while sailing to Edfu"),
            ("Evening", "Overnight onboard in Edfu"),
        ],
    },
    {
        "day": 3,
        "title": "Edfu & Kom Ombo Temple Visits",
        "steps": [
            ("Morning", "Visit Temple of Horus in Edfu"),
            ("Afternoon", "Sail to Kom Ombo"),
            ("Afternoon", "Visit Temple of Sobek and Haroeris"),
            ("Evening", "Overnight onboard near Aswan"),
        ],
    },
    {
        "day": 4,
        "title": "Aswan Sightseeing & Optional Activities",
        "steps": [
            ("Morning", "Visit the High Dam"),
            ("Morning", "Tour the Unfinished Obelisk"),
            ("Afternoon", "Explore Philae Temple"),
            ("Evening", "Optional: Sound & Light Show at Philae Temple"),
            ("Night", "Overnight in Aswan"),
        ],
    },
    {
        "day": 5,
        "title": "Aswan – Disembarkation & Optional Abu Simbel",
        "steps": [
            ("Morning", "Breakfast onboard"),
            ("Morning", "Optional excursion to Abu Simbel (additional cost)"),
            ("Afternoon", "Disembark & transfer to airport/train station for departure"),
        ],
    },
]

INCLUSIONS = [
    "4 nights onboard a standard-class Nile cruise (shared double/twin cabin)",
    "Full board meals (breakfast, lunch, and dinner)",
    "Sightseeing tours in Luxor, Edfu, Kom Ombo, and Aswan with licensed Egyptologist guide",
    "All ground transfers in air-conditioned vehicles",
    "Entrance fees to all listed sites in the itinerary",
    "English-speaking tour guide during excursions",
    "Onboard entertainment (subject to availability)",
    "Meet and assist service upon arrival in Luxor",
]

EXCLUSIONS = [
    "International & domestic flights",
    "Entry visa to Egypt",
    "Tipping for guide, drivers, and cruise staff",
    "Optional tours or personal expenses",
    "Drinks and beverages not included in meals",
    "Travel insurance (highly recommended)",
    "Abu Simbel excursion (available at additional cost)",
    "Sound & Light Show at Philae Temple (optional extra)",
]

FAQS = [
    ("Is this tour suitable for children or elderly travelers?",
     "Yes, the cruise is suitable for all age groups. However, some walking and climbing at temples may be required."),
    ("What is the best time to take this Nile Cruise?",
     "October to April is the best season due to cooler weather, but cruises operate year-round."),
    ("Are vegetarian or special meals available onboard?",
     "Yes, please inform us of dietary requirements in advance."),
    ("Is Wi-Fi available on the cruise ship?",
     "Most standard cruises offer limited Wi-Fi access, usually for an additional fee."),
    ("Can I add Abu Simbel to the itinerary?",
     "Absolutely! Abu Simbel can be added as an optional excursion on the final day."),
    ("What type of rooms are included?",
     "Standard cabins with private bathrooms. Upgrades to deluxe or suite cabins may be available upon request."),
    ("Are flights included in this package?",
     "No, international and domestic flights are not included but can be arranged at an additional cost."),
    ("What is the group size for this tour?",
     "Maximum group size is 50 people, ensuring personalized attention from our guides."),
]


class Command(BaseCommand):
    help = "Seeds the Luxor to Aswan 5-day Nile Cruise trip with destinations, content, and relations."

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
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False