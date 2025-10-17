from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from web.models import (
    Destination, DestinationName,
    Trip, TripAbout, TripHighlight,
    TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
    TripCategory, Language,
)

# ====== Trip constants (from the attached PDF) ======
TITLE = "3-Day Siwa Oasis Tour | Desert Adventure & Natural Springs"

# Short teaser for listing cards
TEASER = (
    "Three-day escape to Siwa: Oracle Temple, Shali Fortress, Cleopatra’s Bath, salt lakes, "
    "and a 4×4 safari in the Great Sand Sea with Bedouin dinner under the stars."
)

# Full About body (concise and clean)
DESCRIPTION = (
    "Journey from Cairo to the remote Siwa Oasis for three days of culture, nature, and desert adventure. "
    "Explore the Oracle Temple of Amun and the mud-brick Shali Fortress, float in sparkling salt lakes, and "
    "soak in Cleopatra’s Bath. Ride a 4×4 into the Great Sand Sea for dune bashing, sandboarding, and a Bedouin "
    "dinner under the stars—then unwind in hot springs before heading back to Cairo."
)

DURATION_DAYS = 3
# Page shows “Group Size 50 people”; elsewhere "Over 25" — we’ll use 50.
GROUP_SIZE_MAX = 50
# Page shows “from $590,00”
BASE_PRICE = Decimal("590.00")
TOUR_TYPE_LABEL = "Daily tour — Discovery Safari"

# Categories (M2M)
CATEGORIES = ["Daily tour", "Discovery", "Safari"]

# Languages (M2M)
LANGUAGES = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

# Highlights (order preserved from PDF)
HIGHLIGHTS = [
    "Discover the hidden paradise of Siwa Oasis",
    "Visit the Oracle Temple of Amun (linked to Alexander the Great)",
    "Explore the ancient Shali Fortress",
    "Float in Siwa’s salt lakes and relax at Cleopatra’s Bath",
    "4x4 safari in the Great Sand Sea with dune bashing and sandboarding",
    "Bedouin dinner under the stars in the desert",
    "Immerse in palm groves and Siwa’s unique Berber culture",
]

# Itinerary — 3 days
ITINERARY = [
    {
        "day_number": 1,
        "title": "Cairo → Siwa Oasis",
        "steps": [
            "Early morning departure from Cairo to Siwa (approx. 8–9 hours, with scenic stops)",
            "Arrival in Siwa and hotel/eco-lodge check-in",
            "Leisure evening to explore the oasis town",
            "Overnight in Siwa",
        ],
    },
    {
        "day_number": 2,
        "title": "Siwa Cultural & Desert Exploration",
        "steps": [
            "Breakfast at the lodge",
            "Visit the Oracle Temple of Amun, Shali Fortress, and Cleopatra’s Bath",
            "Float in Siwa’s famous salt lakes",
            "Afternoon 4x4 safari in the Great Sand Sea: dune bashing, sandboarding, sunset views",
            "Bedouin dinner in the desert under the stars",
            "Overnight in Siwa",
        ],
    },
    {
        "day_number": 3,
        "title": "Siwa Oasis → Cairo",
        "steps": [
            "Morning free time (optional hot springs/last strolls)",
            "Depart Siwa and drive back to Cairo",
            "Evening drop-off at your hotel",
        ],
    },
]

# Included / Excluded (as listed)
INCLUSIONS = [
    "Pick-up & drop-off in Cairo by private air-conditioned vehicle",
    "Accommodation in Siwa: 2 nights hotel (half-board)",
    "Lunch at a local restaurant or picnic lunch (drinks excluded)",
    "4x4 desert safari in the Great Sand Sea",
    "English-speaking guide",
    "Entrance fees to mentioned sites",
    "Bedouin dinner in the desert",
    "Bottled water during the trip",
]

EXCLUSIONS = [
    "Personal expenses",
    "Tips for guides and drivers",
    "Travel insurance",
    "Optional activities not mentioned in the itinerary",
]

# FAQs (from page, simplified)
FAQS = [
    ("How long is the drive from Cairo to Siwa Oasis?",
     "Approximately 8–9 hours, with scenic stops along the way."),
    ("What type of accommodation is provided?",
     "Traditional eco-lodge or comfortable hotel blending modern amenities with local charm."),
    ("Is the desert safari safe?",
     "Yes, operated by professional drivers and guides experienced in desert terrain."),
    ("What should I pack?",
     "Light clothes, hat, sunscreen, sturdy shoes, swimwear for springs/lakes, and a jacket for cool evenings."),
    ("Can vegetarian or special meals be arranged?",
     "Yes—please inform us in advance and suitable meals will be arranged."),
]


class Command(BaseCommand):
    help = "Seed/update: 3-Day Siwa Oasis Tour (with optional multiple destinations support)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # ====== Destinations ======
        # Primary: Siwa. Add related destinations here if needed (e.g., Bahareya or White & Black Desert).
        primary_dest = Destination.objects.get(name=DestinationName.SIWA)
        additional_dests = []  # e.g., [Destination.objects.get(name=DestinationName.BAHAREYA)]

        # ====== Categories ======
        cat_objs = []
        for c in CATEGORIES:
            slug = slugify(c) or "category"
            obj, _ = TripCategory.objects.get_or_create(slug=slug, defaults={"name": c})
            if obj.name != c:
                obj.name = c
                obj.save(update_fields=["name"])
            cat_objs.append(obj)

        # ====== Languages ======
        lang_objs = []
        for name, code in LANGUAGES:
            obj, _ = Language.objects.get_or_create(name=name, code=code)
            lang_objs.append(obj)

        # ====== Trip (upsert) ======
        trip, created = Trip.objects.get_or_create(
            title=TITLE,
            destination=primary_dest,
            defaults=dict(
                teaser=TEASER,
                duration_days=DURATION_DAYS,
                group_size_max=GROUP_SIZE_MAX,
                base_price_per_person=BASE_PRICE,
                tour_type_label=TOUR_TYPE_LABEL,
            ),
        )
        if not created:
            trip.teaser = TEASER
            trip.duration_days = DURATION_DAYS
            trip.group_size_max = GROUP_SIZE_MAX
            trip.base_price_per_person = BASE_PRICE
            trip.tour_type_label = TOUR_TYPE_LABEL
            trip.destination = primary_dest  # enforce primary
            trip.save()

        # M2M: categories, languages, additional destinations (if any)
        trip.category_tags.set(cat_objs)
        trip.languages.set(lang_objs)
        trip.additional_destinations.set(additional_dests)

        # ====== About ======
        TripAbout.objects.update_or_create(trip=trip, defaults={"body": DESCRIPTION})

        # ====== Highlights (replace) ======
        TripHighlight.objects.filter(trip=trip).delete()
        for pos, text in enumerate(HIGHLIGHTS, start=1):
            TripHighlight.objects.create(trip=trip, text=text, position=pos)

        # ====== Itinerary (replace) ======
        TripItineraryStep.objects.filter(day__trip=trip).delete()
        TripItineraryDay.objects.filter(trip=trip).delete()
        for d in ITINERARY:
            day = TripItineraryDay.objects.create(
                trip=trip, day_number=d["day_number"], title=d["title"]
            )
            for pos, title in enumerate(d["steps"], start=1):
                TripItineraryStep.objects.create(
                    day=day, time_label="", title=title, description="", position=pos
                )

        # ====== Inclusions / Exclusions (replace) ======
        TripInclusion.objects.filter(trip=trip).delete()
        for pos, txt in enumerate(INCLUSIONS, start=1):
            TripInclusion.objects.create(trip=trip, text=txt, position=pos)

        TripExclusion.objects.filter(trip=trip).delete()
        for pos, txt in enumerate(EXCLUSIONS, start=1):
            TripExclusion.objects.create(trip=trip, text=txt, position=pos)

        # ====== FAQs (replace) ======
        TripFAQ.objects.filter(trip=trip).delete()
        for pos, (q, a) in enumerate(FAQS, start=1):
            TripFAQ.objects.create(trip=trip, question=q, answer=a, position=pos)

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} trip: {trip.title} (slug={trip.slug})"
        ))
