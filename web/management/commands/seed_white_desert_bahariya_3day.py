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

# ====== Trip constants (from uploaded page/PDF) ======
TITLE = "3-Day Desert Adventure: White Desert & Bahariya Oasis Exploration"

# Short blurb for listing cards
TEASER = (
    "Three-day desert safari from Cairo: Bahariya Oasis, Black Desert, Crystal Mountain, "
    "Valley of Agabat, and camping under the stars in the White Desert."
)

# Full About body (concise, stitched from the page)
DESCRIPTION = (
    "Embark on a three-day journey into Egypt’s Western Desert, combining Bahariya Oasis, the Black Desert, "
    "Crystal Mountain, the Valley of Agabat, and the surreal White Desert. Begin with palm groves and springs "
    "around Bahariya, then cross volcanic hills and golden sands in the Black Desert. Continue to quartz-studded "
    "Crystal Mountain and dramatic Agabat formations before camping under a sky full of stars in the White Desert. "
    "Enjoy Bedouin dinners by the campfire, a magical desert sunrise, and expert guidance throughout."
)

DURATION_DAYS = 3
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("550.00")
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

# Highlights (order preserved)
HIGHLIGHTS = [
    "Discover Bahariya Oasis with palm groves and hot springs",
    "Explore the Black Desert with unique volcanic hills and golden sands",
    "Visit Crystal Mountain, a natural ridge sparkling with quartz",
    "See the Valley of Agabat with dramatic limestone formations",
    "Camp overnight in the White Desert among chalk rock sculptures",
    "Enjoy a traditional Bedouin dinner under the stars",
    "Witness stunning desert sunrise and sunset moments",
]

# Itinerary: 3 days with ordered steps
ITINERARY = [
    {
        "day_number": 1,
        "title": "Cairo → Bahariya Oasis → Black Desert",
        "steps": [
            "Pick up from Cairo and drive to Bahariya Oasis (approx. 4 hours)",
            "Explore Bahariya town and palm groves",
            "Visit the Black Desert with its volcanic hills",
            "Overnight stay in Bahariya Oasis (hotel/lodge)",
        ],
    },
    {
        "day_number": 2,
        "title": "Bahariya Oasis → Crystal Mountain → White Desert",
        "steps": [
            "Breakfast and departure with 4x4 safari",
            "Visit Crystal Mountain and the Valley of Agabat",
            "Continue to the White Desert to see unique rock formations",
            "Set up desert camp and enjoy Bedouin dinner under the stars",
            "Overnight camping in the White Desert",
        ],
    },
    {
        "day_number": 3,
        "title": "White Desert → Bahariya Oasis → Cairo",
        "steps": [
            "Sunrise breakfast in the desert",
            "Free time for photos and exploration",
            "Return to Bahariya Oasis for lunch",
            "Drive back to Cairo in the afternoon",
        ],
    },
]

# Included / Excluded
INCLUSIONS = [
    "Pick-up and drop-off from Cairo",
    "Transportation by private air-conditioned vehicle",
    "4x4 jeep for desert safari",
    "English-speaking desert guide",
    "Accommodation (1 night in Bahariya Oasis, 1 night camping in White Desert)",
    "Meals as per itinerary (Breakfast, Lunch, Dinner)",
    "Bedouin camping equipment (tents, blankets, sleeping bags)",
    "All entrance fees to mentioned sites",
    "Bottled water",
]

EXCLUSIONS = [
    "Personal expenses",
    "Gratuities (tips for guides and drivers)",
    "Travel insurance",
    "Optional activities not mentioned in the program",
]

# FAQs (short and practical)
FAQS = [
    ("How difficult is the tour?",
     "Moderate and suitable for most travelers; no prior desert experience required."),
    ("What should I pack?",
     "Comfortable clothes, sturdy shoes, hat, sunscreen, a jacket for cool nights, and a camera."),
    ("Are bathrooms available during camping?",
     "Basic facilities are provided, but amenities are limited."),
    ("Can vegetarian meals be arranged?",
     "Yes, vegetarian and special dietary meals can be prepared upon request."),
    ("Is the tour safe for families with kids?",
     "Yes, families are welcome and children enjoy the camping and desert landscapes."),
]


class Command(BaseCommand):
    help = "Seed/update: 3-Day White Desert & Bahariya Oasis Adventure (trip + content)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # 1) Destination (predefined choices) — no Bahariya in enum, so use White & Black Desert
        dest = Destination.objects.get(name=DestinationName.WHITE_BLACK)

        # 2) Categories (ensure slugs & names)
        cat_objs = []
        for c in CATEGORIES:
            slug = slugify(c) or "category"
            obj, _ = TripCategory.objects.get_or_create(slug=slug, defaults={"name": c})
            if obj.name != c:
                obj.name = c
                obj.save(update_fields=["name"])
            cat_objs.append(obj)

        # 3) Languages
        lang_objs = []
        for name, code in LANGUAGES:
            obj, _ = Language.objects.get_or_create(name=name, code=code)
            lang_objs.append(obj)

        # 4) Trip (upsert) — slug generated by model.save()
        trip, created = Trip.objects.get_or_create(
            title=TITLE,
            destination=dest,
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
            trip.save()

        # 5) M2M
        trip.category_tags.set(cat_objs)
        trip.languages.set(lang_objs)

        # 6) About
        TripAbout.objects.update_or_create(trip=trip, defaults={"body": DESCRIPTION})

        # 7) Highlights (replace)
        TripHighlight.objects.filter(trip=trip).delete()
        for i, text in enumerate(HIGHLIGHTS, start=1):
            TripHighlight.objects.create(trip=trip, text=text, position=i)

        # 8) Itinerary (replace)
        TripItineraryStep.objects.filter(day__trip=trip).delete()
        TripItineraryDay.objects.filter(trip=trip).delete()
        for day_def in ITINERARY:
            day = TripItineraryDay.objects.create(
                trip=trip,
                day_number=day_def["day_number"],
                title=day_def["title"],
            )
            for pos, title in enumerate(day_def["steps"], start=1):
                TripItineraryStep.objects.create(
                    day=day, time_label="", title=title, description="", position=pos
                )

        # 9) Inclusions / Exclusions (replace)
        TripInclusion.objects.filter(trip=trip).delete()
        for pos, txt in enumerate(INCLUSIONS, start=1):
            TripInclusion.objects.create(trip=trip, text=txt, position=pos)

        TripExclusion.objects.filter(trip=trip).delete()
        for pos, txt in enumerate(EXCLUSIONS, start=1):
            TripExclusion.objects.create(trip=trip, text=txt, position=pos)

        # 10) FAQs (replace)
        TripFAQ.objects.filter(trip=trip).delete()
        for pos, (q, a) in enumerate(FAQS, start=1):
            TripFAQ.objects.create(trip=trip, question=q, answer=a, position=pos)

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} trip: {trip.title} (slug={trip.slug})"
        ))
