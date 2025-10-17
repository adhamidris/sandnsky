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

# ====== Trip constants (from attached PDF) ======
TITLE = "Overnight Desert Safari from Cairo: Bahariya Oasis, Black & White Desert"

TEASER = (
    "Overnight desert adventure to Bahariya Oasis and the Black & White Desert—"
    "unique landscapes, starry camping, and classic Western Desert highlights."
)

DESCRIPTION = (
    "Escape Cairo for an overnight desert adventure that blends Bahariya Oasis with the Black & White Desert. "
    "Begin with palm groves and natural springs in Bahariya before your 4×4 safari sets off. Explore the Black "
    "Desert’s volcanic hills, the quartz-studded Crystal Mountain, and the dramatic Valley of Agabat. As the day "
    "ends, camp under a star-filled sky in the White Desert among surreal chalk formations. Wake to a peaceful "
    "desert sunrise, enjoy breakfast, then return via Bahariya with lunch before heading back to Cairo."
)

DURATION_DAYS = 2
GROUP_SIZE_MAX = 49
BASE_PRICE = Decimal("330.00")
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

# Highlights (order preserved as on page)
HIGHLIGHTS = [
    "Discover Bahariya Oasis with palm groves and springs",
    "Explore the Black Desert with volcanic peaks and golden sands",
    "Visit Crystal Mountain, a natural ridge of quartz",
    "See the Valley of Agabat’s striking limestone formations",
    "Camp overnight in the White Desert among chalk rock shapes",
    "Enjoy a traditional Bedouin dinner under the stars",
    "Witness a desert sunrise and sunset",
]

# Itinerary (2 days)
ITINERARY = [
    {
        "day_number": 1,
        "title": "Cairo → Bahariya Oasis → Black & White Desert",
        "steps": [
            "Morning pick-up from Cairo and drive to Bahariya Oasis (approx. 4 hours)",
            "Short exploration of Bahariya town and palm groves",
            "Begin 4x4 desert safari",
            "Stop at the Black Desert to see volcanic peaks",
            "Visit Crystal Mountain and Valley of Agabat",
            "Continue to the White Desert, famous for chalk rock formations",
            "Set up camp, Bedouin dinner, and stargazing by the fire",
            "Overnight camping in the White Desert",
        ],
    },
    {
        "day_number": 2,
        "title": "White Desert → Bahariya Oasis → Cairo",
        "steps": [
            "Wake up to a desert sunrise and have breakfast",
            "Free time for photos and exploration",
            "Return to Bahariya Oasis for lunch and relaxation",
            "Drive back to Cairo in the afternoon",
        ],
    },
]

# Included / Excluded (as listed)
INCLUSIONS = [
    "Pick-up & drop-off from Cairo hotel in a private air-conditioned vehicle",
    "4x4 Jeep for the desert safari",
    "Accommodation: 1 night camping in the White Desert",
    "Professional English-speaking desert guide",
    "Meals: 1 Breakfast, 2 Lunches, 1 Dinner",
    "Bottled water and soft drinks",
    "Entrance fees to all mentioned sites",
]

EXCLUSIONS = [
    "Personal expenses",
    "Tips (gratuities)",
    "Travel insurance",
    "Optional activities not listed in the program",
]

# FAQs (short, from page)
FAQS = [
    ("How long is the drive from Cairo to Bahariya Oasis?",
     "Around 4 hours each way, with stops along the route."),
    ("Is camping in the White Desert safe?",
     "Yes, guided by professional desert guides with full equipment."),
    ("Are bathrooms available at the campsite?",
     "Facilities are basic, but essential amenities are provided."),
    ("What should I pack for this tour?",
     "Comfortable clothing, sturdy shoes, sunscreen, hat, light jacket for cool nights, and a camera."),
    ("Can vegetarian or special meals be arranged?",
     "Yes, dietary requests can be accommodated with advance notice."),
]


class Command(BaseCommand):
    help = "Seed/update: Overnight Desert Safari (Bahariya Oasis, Black & White Desert) with multiple destinations."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # ====== Destinations ======
        # Primary: Bahareya Oasis; Additional: White & Black Desert
        primary_dest = Destination.objects.get(name=DestinationName.BAHAREYA)
        extra_dests = [
            Destination.objects.get(name=DestinationName.WHITE_BLACK),
        ]

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
            trip.destination = primary_dest  # enforce primary if changed later
            trip.save()

        # M2M: categories, languages, additional destinations
        trip.category_tags.set(cat_objs)
        trip.languages.set(lang_objs)
        trip.additional_destinations.set(extra_dests)

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
