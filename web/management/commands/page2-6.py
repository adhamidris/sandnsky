# web/management/commands/seed_trip_cairo_fayoum_2day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to El-Fayoum: 2-Day Pyramids & Oasis Tour"
TEASER = (
    "2-day guided tour from Cairo: Explore Giza Pyramids, Saqqara, Memphis, and Dahshur on day one, "
    "then discover El-Fayoum's waterfalls and Valley of Whales UNESCO site on day two. Daily lunch included."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.FAYOUM, DestinationName.GIZA]

DURATION_DAYS = 2
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("350.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "Historical",
    "Oasis Tour",
    "Pyramids",
    "UNESCO Site",
]

HIGHLIGHTS = [
    "Explore the Great Pyramids of Giza and the iconic Sphinx with expert Egyptologist guide.",
    "Discover the ancient ruins of Memphis, the first capital of unified Egypt.",
    "Visit Saqqara to see the Step Pyramid of Djoser, world's earliest stone monument.",
    "Explore the lesser-known pyramids of Dahshur including Bent and Red Pyramids.",
    "Experience El-Fayoum's natural beauty with waterfalls at Wadi El Rayan.",
    "Tour Wadi Al-Hitan (Valley of the Whales), a UNESCO World Heritage fossil site.",
    "Enjoy traditional Egyptian lunches in authentic local settings both days.",
    "Travel in comfort with private air-conditioned transport and professional guide.",
]

ABOUT = """\
Embark on a fascinating 2-day journey through the heart of ancient and natural Egypt with this expertly guided tour from Cairo. Combining the iconic historical treasures of Giza, Memphis, Saqqara, and Dahshur with the scenic beauty of El-Fayoum Oasis, this immersive experience offers a deep dive into Egypt's rich heritage and diverse landscapes. Perfect for travelers who want to make the most of a short stay, this tour balances archaeological marvels and natural wonders—all with the convenience of private transport and lunch included.

Day 1: Ancient Egyptian Marvels
Your tour begins with a visit to the legendary Giza Plateau, home to the Great Pyramids of Giza and the enigmatic Sphinx. Explore one of the last remaining Wonders of the Ancient World and delve into stories of pharaohs and pyramids with your expert Egyptologist guide. Continue to Memphis, the ancient capital of Egypt, where you'll witness the impressive statue of Ramses II and other artifacts that speak of a glorious past.

Next, head to Saqqara, the vast necropolis that houses the Step Pyramid of Djoser—the world's earliest stone monument. Learn about early pyramid construction and the evolution of royal tombs. The final stop of the day is Dahshur, home to the Bent Pyramid and the Red Pyramid, offering a quieter, less touristy perspective on pyramid architecture.

Day 2: The Hidden Gem of El-Fayoum
On day two, escape the city and journey southwest to El-Fayoum, a lush desert oasis known for its lakes, waterfalls, and archaeological ruins. Visit the beautiful Wadi El Rayan, famed for its waterfalls and tranquil setting, and explore Wadi Al-Hitan (Valley of the Whales), a UNESCO World Heritage Site that showcases fossilized remains of ancient whales dating back 40 million years.

This enriching tour brings together culture, history, and nature, making it an ideal choice for those who want to experience Egypt beyond the usual tourist routes—all while enjoying included lunches and hassle-free transportation.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Ancient Egypt Exploration – Pyramids & Historic Sites",
        "steps": [
            ("Morning", "Hotel pickup in Cairo or Giza"),
            ("Morning", "Guided tour of the Giza Pyramids and Sphinx"),
            ("Late Morning", "Transfer to Memphis; visit the open-air museum"),
            ("Afternoon", "Lunch at a local restaurant"),
            ("Afternoon", "Tour of Saqqara (Step Pyramid and tombs)"),
            ("Late Afternoon", "Visit Dahshur (Bent Pyramid and Red Pyramid)"),
            ("Evening", "Return to your hotel"),
        ],
    },
    {
        "day": 2,
        "title": "El-Fayoum Oasis Adventure – Waterfalls & Fossils",
        "steps": [
            ("Morning", "Pickup from your hotel in Cairo"),
            ("Morning", "Arrival at Wadi El Rayan; enjoy the waterfalls"),
            ("Late Morning", "Visit Wadi Al-Hitan (Valley of the Whales) UNESCO site"),
            ("Afternoon", "Lunch at a local restaurant in El-Fayoum"),
            ("Afternoon", "Optional visit to Tunis Village (known for pottery)"),
            ("Evening", "Return to Cairo"),
            ("Evening", "Drop-off at your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Professional Egyptologist tour guide for both days",
    "Private air-conditioned transportation throughout the tour",
    "Admission tickets to all mentioned sites including Giza Plateau",
    "Entrance to Saqqara, Memphis, and Dahshur archaeological sites",
    "Access to Wadi El Rayan and Wadi Al-Hitan (Valley of Whales)",
    "Lunch on both days at local restaurants",
    "Bottled water during tours",
    "Pickup and drop-off from Cairo or Giza hotels",
    "All taxes and service charges",
]

EXCLUSIONS = [
    "Hotel accommodation in Cairo",
    "Gratuities for guide and driver (optional)",
    "Any additional meals or drinks not specified",
    "Entrance to the Great Pyramid interior or Solar Boat Museum (optional tickets)",
    "Personal expenses and souvenirs",
    "Optional activities such as camel rides",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is hotel accommodation included in the tour?",
     "No, this tour excludes hotel accommodation. You can book your own stay in Cairo or Giza."),
    ("Can I go inside the Great Pyramid?",
     "Entrance to the Great Pyramid is not included but can be added on-site for an additional fee."),
    ("Are children allowed on this tour?",
     "Yes, this tour is family-friendly. Children must be accompanied by an adult."),
    ("What type of vehicle is used for transport?",
     "Private, air-conditioned vehicles are used throughout the tour for comfort and convenience."),
    ("What should I wear?",
     "Comfortable walking shoes, sunglasses, and lightweight clothing are recommended. Bring a hat and sunscreen for sun protection."),
    ("Is the tour wheelchair accessible?",
     "Some sites may be challenging due to uneven terrain. Contact us in advance for special arrangements."),
    ("Are vegetarian meal options available?",
     "Yes, please inform us of any dietary restrictions when booking."),
    ("How strenuous is the walking at the archaeological sites?",
     "Moderate walking is required. The sites involve some uneven terrain and steps. Comfortable walking shoes are essential."),
]


class Command(BaseCommand):
    help = "Seeds the 2-Day Cairo & El-Fayoum tour with pyramids and oasis exploration."

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