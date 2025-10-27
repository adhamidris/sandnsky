# web/management/commands/seed_trip_cairo_fayoum.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Fayoum: Overnight Desert Camp (Wadi El Rayan & Magic Lake)"
TEASER = (
    "Overnight desert escape from Cairo to Fayoum: Wadi El Rayan waterfalls, 4×4 dunes, "
    "sunset camp at Magic Lake, Bedouin dinner, and next-day Wadi El-Hitan fossils."
)

PRIMARY_DEST = DestinationName.FAYOUM  # Trip “lives under” Fayoum…
ALSO_APPEARS_IN = [DestinationName.CAIRO]  # …and also shows in Cairo via additional_destinations

DURATION_DAYS = 2
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("0.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Safari"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

# (Optional) lightweight tags you can show as chips/filters
CATEGORY_TAGS = [
    "Desert Camping",
    "Overnight",
    "4x4 Safari",
    "Nature & Fossils",
]

HIGHLIGHTS = [
    "Explore El-Fayoum Oasis — one of Egypt’s oldest and most scenic desert oases.",
    "Visit Wadi El Rayan Waterfalls — Egypt’s only desert waterfalls between two lakes.",
    "Camp under the stars near Magic Lake with Bedouin dinner by the fire.",
    "4×4 desert safari across dunes, valleys, and dramatic landscapes.",
    "Optional sandboarding/swim time at Magic Lake’s photogenic shores.",
    "Stargazing in crystal-clear desert skies away from city glow.",
    "Wadi El-Hitan (Valley of the Whales) UNESCO site with ancient whale fossils.",
    "Professional guiding, comfy transport, and authentic local touches.",
]

ABOUT = """\
Escape the urban chaos of Cairo and journey into the serene landscapes of El-Fayoum on an unforgettable overnight adventure.
Visit Wadi El Rayan’s desert waterfalls, ride 4×4 across golden dunes to the shimmering Magic Lake, and spend the night under
a sky full of stars with a Bedouin dinner by the campfire. Next day, walk through deep time at Wadi El-Hitan (Valley of the Whales),
a UNESCO site with fossils from when this desert was once a prehistoric sea. A perfect 2-day blend of nature, adventure, and calm.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo → El-Fayoum • Waterfalls, Magic Lake & Desert Camp",
        "steps": [
            ("", "Hotel pick-up in Cairo and drive to El-Fayoum"),
            ("", "Wadi El Rayan waterfalls visit"),
            ("", "4×4 desert safari across dunes; reach Magic Lake"),
            ("", "Free time (optional swim or sandboarding)"),
            ("", "Set up camp, tea & snacks • Sunset over dunes"),
            ("", "Bedouin dinner by campfire • Stargazing • Overnight in tents"),
        ],
    },
    {
        "day": 2,
        "title": "Wadi El-Hitan (Valley of the Whales) • Return to Cairo",
        "steps": [
            ("", "Sunrise & camp breakfast"),
            ("", "Drive to Wadi El-Hitan, guided tour & museum"),
            ("", "Light lunch/snacks"),
            ("", "Return drive and hotel drop-off in Cairo"),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off from Cairo hotel",
    "Air-conditioned transport",
    "4×4 desert safari in El-Fayoum",
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
     "Yes. The campsite is in a designated area and professional guides/drivers stay with you throughout."),
    ("Do I need prior camping experience?",
     "No—gear, meals, and guidance are provided. It’s beginner-friendly."),
    ("What should I pack?",
     "Backpack, sunglasses, sunscreen, hat, light jacket for night, comfy shoes, flashlight/headlamp, and tissues/wet wipes."),
    ("Are there restroom facilities at the campsite?",
     "Basic facilities are available—expect a rustic experience."),
    ("Can you accommodate vegetarians or dietary needs?",
     "Yes—tell us in advance and we’ll arrange suitable meals."),
    ("Is this tour suitable for kids or elderly travelers?",
     "Generally yes; the terrain can be uneven. Families with young children or seniors should consult us first."),
    ("Can I extend to two nights?",
     "Yes—add nights or extras like sandboarding or birdwatching by request."),
]


class Command(BaseCommand):
    help = "Seeds the Cairo → Fayoum overnight desert camp trip with destinations, content, and relations."

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
