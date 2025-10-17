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


TITLE = "Overnight Camping Trip from Cairo to El-Fayoum Oasis – Explore Wadi El Rayan & Magic Lake"
TEASER = (
    # Short blurb for listing card (first lines of description)
    "Escape the urban chaos of Cairo and journey into the serene landscapes of El-Fayoum Oasis on this "
    "unforgettable overnight adventure—natural wonders, ancient history, and starry desert skies."
)
DESCRIPTION = (
    # Full “About” body (from the page; trimmed lightly)
    "Escape the urban chaos of Cairo and journey into the serene and surreal landscapes of El-Fayoum Oasis on "
    "this unforgettable overnight adventure. Just a few hours away from Egypt’s bustling capital lies a world "
    "of natural wonders, ancient history, and star-studded skies. You’ll visit Wadi El Rayan waterfalls, ride "
    "a 4×4 desert safari across the dunes, and relax by the shimmering Magic Lake. Camp under the stars with a "
    "traditional Bedouin dinner, then explore Wadi El-Hitan (Valley of the Whales), a UNESCO site famous for "
    "prehistoric fossils that tell the story of an ancient sea."
)

DURATION_DAYS = 2
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("335.00")
TOUR_TYPE_LABEL = "Daily tour — Discovery Safari"

CATEGORIES = ["Daily tour", "Discovery", "Safari"]  # TripCategory
LANGUAGES = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

HIGHLIGHTS = [
    "Explore El-Fayoum Oasis just 2 hours from Cairo.",
    "Visit Wadi El Rayan Waterfalls — Egypt’s desert waterfalls.",
    "Camp under the stars near the Magic Lake.",
    "4x4 desert safari across dunes and valleys.",
    "Relax at the Magic Lake (optional swim/sandboard).",
    "Stargazing in clear desert skies.",
    "Explore Wadi El-Hitan (Valley of the Whales) — UNESCO site.",
    "Authentic Bedouin dinner by campfire.",
    "Great photo opportunities from sunsets to fossil beds.",
    "Perfect 2-day escape blending nature, culture, and relaxation.",
]

ITINERARY = [
    {
        "day_number": 1,
        "title": "Cairo – El-Fayoum – Desert Camping",
        "steps": [
            "Pick up from your Cairo hotel",
            "Arrive in El-Fayoum; visit Wadi El Rayan and the waterfalls",
            "Begin 4x4 desert safari to explore sand dunes and Magic Lake",
            "Free time at Magic Lake (optional swimming or sandboarding)",
            "Set up desert camp; enjoy tea and snacks",
            "Watch the sunset over the dunes",
            "Bedouin dinner by the campfire",
            "Stargazing and overnight stay in tents",
        ],
    },
    {
        "day_number": 2,
        "title": "Wadi El-Hitan – Return to Cairo",
        "steps": [
            "Wake up to desert sunrise, breakfast",
            "Drive to Wadi El-Hitan (Valley of the Whales) and visit the museum",
            "Guided tour of the fossil sites",
            "Begin return journey to Cairo",
            "Drop off at your hotel in Cairo",
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off from your hotel in Cairo",
    "Transportation by air-conditioned vehicle",
    "4x4 desert safari in El-Fayoum",
    "Camping equipment (tent, sleeping bag, mattress)",
    "One-night desert camping near Magic Lake",
    "Bedouin-style dinner and breakfast",
    "Bottled water and soft drinks",
    "Entrance fees to Wadi El Rayan & Wadi El-Hitan",
    "Guided visit to Magic Lake, Wadi El Rayan, and Wadi El-Hitan",
    "Professional English-speaking guide",
]

EXCLUSIONS = [
    "Personal expenses",
    "Tips/gratuities for guide and driver",
    "Travel insurance",
    "Alcoholic beverages",
    "Optional activities not mentioned in itinerary",
]

FAQS = [
    ("Is the camping safe and secure?",
     "Yes. The camping site is in a secure, designated area with professional guides and drivers throughout."),
    ("Do I need prior camping experience?",
     "No. Tents, sleeping gear, and meals are arranged. Beginner-friendly."),
    ("What should I pack?",
     "A small backpack, sunglasses, sunscreen, hat, light jacket, comfortable shoes, and a flashlight/headlamp."),
    ("Are there restroom facilities at the campsite?",
     "Basic facilities are available; expect a rustic experience. Wet wipes and tissues recommended."),
    ("Can vegetarians or those with dietary restrictions be accommodated?",
     "Yes, with advance notice we can arrange suitable meals."),
    ("Is this tour suitable for kids or elderly travelers?",
     "Yes, but the terrain can be slightly challenging; please consult us first."),
    ("Can I extend the trip to two nights?",
     "Yes. We can customize with an extra night or activities such as sandboarding or birdwatching around Lake Qarun."),
]


class Command(BaseCommand):
    help = "Seed/update: Fayoum Overnight Camping Trip (trip + content)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # 1) Destination (predefined choices)
        dest = Destination.objects.get(name=DestinationName.FAYOUM)

        # 2) Categories (M2M)
        cat_objs = []
        for c in CATEGORIES:
            slug = slugify(c) or "category"
            obj, _ = TripCategory.objects.get_or_create(slug=slug, defaults={"name": c})
            # ensure name is up to date if slug existed
            if obj.name != c:
                obj.name = c
                obj.save(update_fields=["name"])
            cat_objs.append(obj)

        # 3) Languages (M2M)
        lang_objs = []
        for name, code in LANGUAGES:
            obj, _ = Language.objects.get_or_create(name=name, code=code)
            lang_objs.append(obj)

        # 4) Trip (upsert) — slug is auto-generated in model.save
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

        # 5) M2M for trip
        trip.category_tags.set(cat_objs)
        trip.languages.set(lang_objs)

        # 6) About (replace)
        TripAbout.objects.update_or_create(trip=trip, defaults={"body": DESCRIPTION})

        # 7) Replace highlights
        TripHighlight.objects.filter(trip=trip).delete()
        for i, text in enumerate(HIGHLIGHTS, start=1):
            TripHighlight.objects.create(trip=trip, text=text, position=i)

        # 8) Replace itinerary (days + steps)
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

        # 9) Replace inclusions & exclusions
        TripInclusion.objects.filter(trip=trip).delete()
        for pos, txt in enumerate(INCLUSIONS, start=1):
            TripInclusion.objects.create(trip=trip, text=txt, position=pos)

        TripExclusion.objects.filter(trip=trip).delete()
        for pos, txt in enumerate(EXCLUSIONS, start=1):
            TripExclusion.objects.create(trip=trip, text=txt, position=pos)

        # 10) Replace FAQs
        TripFAQ.objects.filter(trip=trip).delete()
        for pos, (q, a) in enumerate(FAQS, start=1):
            TripFAQ.objects.create(trip=trip, question=q, answer=a, position=pos)

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} trip: {trip.title} (slug={trip.slug})"
        ))
