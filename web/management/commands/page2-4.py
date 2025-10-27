# web/management/commands/seed_trip_egypt_highlights.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Alexandria: 4-Day Egypt Highlights with Fayoum Oasis"
TEASER = (
    "4-day Egypt highlights tour: Explore Cairo's museums and bazaars, Fayoum Oasis waterfalls, "
    "Giza Pyramids, Saqqara, Memphis, and Alexandria's Mediterranean treasures. Daily lunch included."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.FAYOUM, DestinationName.ALEXANDRIA, DestinationName.GIZA]

DURATION_DAYS = 4
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("600.00")
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
    "City Tour",
    "Oasis Visit",
    "Coastal Tour",
]

HIGHLIGHTS = [
    "Marvel at the legendary Great Pyramids of Giza and Sphinx with expert guided tour.",
    "Explore ancient relics and Tutankhamun's treasures at the Egyptian Museum.",
    "Discover the serene beauty of El-Fayoum's natural oasis with waterfalls and lakes.",
    "Step into ancient tombs at Saqqara (Step Pyramid) and Dahshur (Bent and Red Pyramids).",
    "Shop for local crafts and experience vibrant culture at Khan El-Khalili Bazaar.",
    "Visit the Citadel of Saladin and majestic Mosque of Muhammad Ali in Islamic Cairo.",
    "Day trip to the Mediterranean city of Alexandria with catacombs and Qaitbay Citadel.",
    "Daily authentic Egyptian lunch included at local restaurants throughout the tour.",
]

ABOUT = """\
Embark on an unforgettable journey through Egypt's rich history and natural wonders with this 4-day guided tour from Cairo, covering the essential highlights of Cairo, El-Fayoum, Giza, and Alexandria. This well-curated tour offers an immersive experience without accommodation, making it ideal for travelers with their own lodging arrangements.

Day 1 kicks off with a deep dive into Cairo's ancient past at the Egyptian Museum, home to the world's most extensive collection of Pharaonic antiquities including the treasures of Tutankhamun. Continue your exploration at the Saladin Citadel, a medieval Islamic fortification featuring the stunning Mosque of Muhammad Ali. Wrap up your day in the vibrant Khan El-Khalili Bazaar, a historic market alive with traditional crafts, spices, and street food.

On Day 2, take a scenic road trip to El-Fayoum Oasis, an off-the-beaten-path gem boasting natural and archaeological wonders. Visit the water wheels of Fayoum, explore the Wadi El-Rayan waterfalls, and discover the ancient city of Medinet Madi or Qasr Qarun, depending on seasonal access. A perfect day for nature lovers and history buffs alike.

Day 3 is devoted to the timeless wonders of the Giza Plateau. Marvel at the Great Pyramids of Giza, the Sphinx, and then delve into the lesser-known, yet equally fascinating sites of Memphis (the ancient capital), Saqqara (home of the Step Pyramid), and Dahshur where the Bent and Red Pyramids reside.

Finally, Day 4 whisks you away to the coastal city of Alexandria. Discover the Catacombs of Kom El Shoqafa, the majestic Qaitbay Citadel, and the site of the ancient Lighthouse of Alexandria. End your tour with a visit to the Alexandria Library and enjoy a fresh Mediterranean lunch.

This guided tour includes all transfers, entrance fees, and lunch each day — just bring your curiosity and camera! Hotels are not included, making it a flexible choice for personalized stays.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Cairo City Tour – Museums & Islamic Cairo",
        "steps": [
            ("Morning", "Pick-up from hotel in Cairo"),
            ("Morning", "Visit the Egyptian Museum – 120,000+ artifacts including Tutankhamun's treasures"),
            ("Afternoon", "Explore the Citadel of Saladin & Mosque of Muhammad Ali"),
            ("Afternoon", "Stroll and shop at Khan El-Khalili Bazaar"),
            ("Afternoon", "Lunch at a local restaurant"),
            ("Evening", "Drop-off at your hotel"),
        ],
    },
    {
        "day": 2,
        "title": "El-Fayoum Oasis – Natural Wonders & Waterfalls",
        "steps": [
            ("Morning", "Pick-up from your hotel in Cairo"),
            ("Morning", "Travel to El-Fayoum Oasis"),
            ("Late Morning", "Visit Wadi El-Rayan waterfalls"),
            ("Afternoon", "Stop at Mudawara Mountain, Magic Lake, and Qarun Lake"),
            ("Afternoon", "Explore Qasr Qarun or Medinet Madi"),
            ("Afternoon", "Lunch in a local restaurant in El-Fayoum"),
            ("Evening", "Return to Cairo and drop-off at your hotel"),
        ],
    },
    {
        "day": 3,
        "title": "Giza Pyramids & Ancient Memphis Sites",
        "steps": [
            ("Morning", "Pick-up from hotel in Cairo"),
            ("Morning", "Visit Giza Pyramids and the Sphinx"),
            ("Afternoon", "Explore Memphis – Egypt's first capital"),
            ("Afternoon", "Visit Saqqara – Step Pyramid of Djoser"),
            ("Afternoon", "See Dahshur's Bent and Red Pyramids"),
            ("Afternoon", "Enjoy lunch in a traditional Egyptian restaurant"),
            ("Evening", "Return to your hotel in Cairo"),
        ],
    },
    {
        "day": 4,
        "title": "Alexandria Day Tour – Mediterranean Coast",
        "steps": [
            ("Early Morning", "Pick-up early morning from Cairo"),
            ("Morning", "Travel to Alexandria (~2.5 hours)"),
            ("Late Morning", "Visit Catacombs of Kom El-Shoqafa"),
            ("Afternoon", "Explore the Qaitbay Citadel on the Mediterranean"),
            ("Afternoon", "Photo stop at the site of the ancient Lighthouse"),
            ("Afternoon", "Visit the modern Bibliotheca Alexandrina"),
            ("Afternoon", "Lunch by the sea"),
            ("Evening", "Return to Cairo and hotel drop-off"),
        ],
    },
]

INCLUSIONS = [
    "Professional Egyptologist guide throughout the tour",
    "Air-conditioned private transportation for all transfers",
    "Entrance fees to all listed attractions and sites",
    "Lunch each day at local restaurants",
    "Bottled water during tours",
    "All taxes and service charges",
    "Pick-up and drop-off from your accommodation in Cairo",
    "All transportation between cities and sites",
]

EXCLUSIONS = [
    "Hotel accommodation (not included)",
    "Personal expenses and souvenirs",
    "Drinks during meals",
    "Gratuities for guides and drivers (optional but recommended)",
    "Any optional activities not listed in the itinerary",
    "Entry to the Mummy Room or Royal Hall in Egyptian Museum (optional upgrade)",
    "Entry inside Pyramids (available at extra cost)",
    "Travel insurance",
]

FAQS = [
    ("Does this tour include hotel accommodation?",
     "No, this package is designed without hotel stays. You can book your own accommodation in Cairo as per your preference."),
    ("Is this a private or group tour?",
     "This is typically a private tour, but shared/group options can be arranged upon request."),
    ("Are meals included?",
     "Yes, lunch is included each day at a local restaurant. Drinks and dinner are not included."),
    ("What should I bring for the El-Fayoum trip?",
     "Comfortable shoes, sunblock, hat, and a camera. A light jacket in winter is recommended."),
    ("Can I customize the tour or skip a day?",
     "Yes, the tour is customizable. Please contact us in advance to adjust your itinerary."),
    ("Are all entrance tickets included?",
     "Yes, all main site entrance tickets are included. Optional sites like entering inside pyramids or the Mummy Room at the museum are extra."),
    ("How much walking is involved in this tour?",
     "Moderate walking is required at archaeological sites and museums. Comfortable walking shoes are recommended."),
    ("Is there a lot of driving between sites?",
     "There are drives of 2-3 hours to Fayoum and Alexandria, but these are broken up with stops and scenic views."),
]


class Command(BaseCommand):
    help = "Seeds the 4-Day Egypt Highlights tour covering Cairo, Fayoum, and Alexandria."

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