# web/management/commands/seed_trip_fayoum_adventure.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Fayoum: Oasis Safari & Valley of Whales Day Tour"
TEASER = (
    "Day tour from Cairo to Fayoum Oasis: Desert safari, Wadi El-Hitan UNESCO fossil site, "
    "Magic Lake, Wadi El-Rayan waterfalls, and traditional Egyptian lunch included."
)

PRIMARY_DEST = DestinationName.FAYOUM
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.GIZA]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("220.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Safari"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Desert Safari",
    "Day Tour",
    "UNESCO Site",
    "Adventure",
    "Oasis Tour",
    "Fossils",
]

HIGHLIGHTS = [
    "Explore the Fayoum Oasis and its natural beauty with desert landscapes and lakes.",
    "Visit Wadi El-Hitan (Valley of Whales), UNESCO World Heritage Site with 40-million-year-old fossils.",
    "See fossilized whale skeletons dating back millions of years in open-air museum.",
    "Enjoy thrilling 4x4 desert safari across golden dunes of Fayoum.",
    "Stop at Magic Lake and Wadi El-Rayan Waterfalls for photography and relaxation.",
    "Experience traditional Egyptian lunch in desert or local eco-lodge setting.",
    "Optional visit to Tunis Village for pottery and cultural exploration.",
    "Professional Egyptologist guide providing insights into geology and natural history.",
]

ABOUT = """\
Embark on an unforgettable desert adventure with a Fayoum Oasis Safari & Valley of Whales (Wadi El-Hitan) Tour, a perfect blend of nature, history, and traditional culture. Just two hours from Cairo, the Fayoum Oasis is one of Egypt's most picturesque and historically rich destinations, offering unique landscapes, wildlife, and ancient wonders.

Your journey begins with a desert safari in Fayoum, where golden dunes and breathtaking natural sights await. The oasis is home to stunning attractions like Magic Lake and Wadi El-Rayan Waterfalls, which provide incredible opportunities for photography and relaxation. You'll also pass by Tunis Village, a charming artistic community known for its pottery and authentic countryside charm.

The highlight of the tour is a visit to Wadi El-Hitan (Valley of Whales), a UNESCO World Heritage Site. This extraordinary open-air museum showcases fossilized remains of whales that lived over 40 million years ago, providing rare insights into the evolution of marine life. Walking among these ancient fossils in the middle of the desert is a once-in-a-lifetime experience that connects natural history with breathtaking scenery.

To complete your adventure, you'll enjoy a traditional Egyptian lunch served in a local style, giving you a taste of authentic flavors while surrounded by the desert's tranquility. With the guidance of an expert tour leader, you'll gain a deep understanding of the area's geology, archaeology, and ecology.

This tour is perfect for those seeking a balance of adventure, history, and culture—whether you're a nature lover, history enthusiast, or simply looking for an off-the-beaten-path experience. The Fayoum Oasis and Valley of Whales promise not only incredible landscapes but also a deeper appreciation of Egypt's natural and prehistoric heritage.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Fayoum Oasis Adventure - Desert Safari & Whale Fossils",
        "steps": [
            ("Morning", "Pick-up from Cairo or Giza hotel"),
            ("Morning", "Drive towards Fayoum Oasis (around 2 hours)"),
            ("Late Morning", "Desert Safari with 4x4 vehicle across dunes"),
            ("Late Morning", "Visit Wadi El-Rayan Waterfalls and Magic Lake"),
            ("Afternoon", "Continue to Wadi El-Hitan (Valley of Whales)"),
            ("Afternoon", "Explore fossilized whale remains and open-air museum"),
            ("Afternoon", "Traditional Egyptian lunch at eco-lodge or Bedouin-style camp"),
            ("Late Afternoon", "Optional visit to Tunis Village for pottery and culture"),
            ("Evening", "Relaxing desert drive back to Cairo"),
            ("Evening", "Drop-off at your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off from Cairo or Giza hotels",
    "Professional Egyptologist guide and desert safari driver",
    "4x4 Jeep safari through Fayoum Desert",
    "Entrance fees to Wadi El-Hitan and Wadi El-Rayan",
    "Traditional Egyptian lunch at local establishment",
    "Bottled water throughout the tour",
    "All taxes and service charges",
    "Comprehensive guided tour of all sites",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Gratuities for guide and driver",
    "Optional activities (sandboarding, pottery workshop in Tunis Village)",
    "Drinks not mentioned in inclusions",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("How far is Fayoum from Cairo?",
     "It's about 90 km southwest of Cairo (around 2 hours by car)."),
    ("What makes Wadi El-Hitan special?",
     "It's a UNESCO World Heritage Site famous for fossilized whale skeletons that prove the transition of whales from land to sea creatures."),
    ("Is the desert safari safe?",
     "Yes, the safari is led by experienced drivers using 4x4 vehicles, ensuring both safety and adventure."),
    ("What should I wear for this tour?",
     "Comfortable clothes, sturdy shoes, a hat, sunglasses, and sunscreen are highly recommended."),
    ("Can children join this tour?",
     "Yes, families are welcome. Kids especially enjoy the fossils and the desert safari experience."),
    ("Is sandboarding available?",
     "Yes, sandboarding can be arranged at Fayoum's dunes for an additional cost."),
    ("What type of lunch is served?",
     "Traditional Egyptian lunch featuring local dishes, typically served in an eco-lodge or Bedouin-style setting."),
    ("Are there restroom facilities at the sites?",
     "Basic restroom facilities are available at main stops. It's recommended to use facilities before leaving Cairo."),
]


class Command(BaseCommand):
    help = "Seeds the Fayoum Oasis & Wadi El-Hitan adventure day tour."

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