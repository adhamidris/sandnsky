# web/management/commands/seed_trip_dahshur_saqqara_memphis.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Giza: Dahshur, Saqqara & Memphis Pyramid Tour"
TEASER = (
    "Day tour from Cairo to ancient pyramid sites: Explore Dahshur's Bent and Red Pyramids, "
    "Saqqara's Step Pyramid, and Memphis' open-air museum with colossal statues."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("95.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Tour",
    "Historical",
    "Pyramids",
    "Archaeological",
    "Ancient Sites",
]

HIGHLIGHTS = [
    "Explore the Bent Pyramid and Red Pyramid at Dahshur - key examples of pyramid evolution.",
    "Visit Memphis, the first capital of Ancient Egypt with 5,000 years of history.",
    "See the colossal statue of Ramses II and the Alabaster Sphinx at Memphis open-air museum.",
    "Discover Saqqara's Step Pyramid of Djoser, the world's earliest large-scale stone structure.",
    "Learn from an expert Egyptologist guide about Egypt's Old Kingdom history and architecture.",
    "Experience less crowded archaeological sites compared to Giza Plateau.",
    "Optional entry inside the Red Pyramid and Bent Pyramid (additional cost).",
    "Comfortable private transportation with hotel pickup and drop-off.",
]

ABOUT = """\
Step beyond the famous Giza Plateau and discover the ancient roots of Egyptian civilization with a day tour to Dahshur, Memphis, and Saqqara—three of Egypt's most historically rich sites. This journey is perfect for travelers who want to explore Egypt's early pyramids, royal tombs, and the remains of the very first capital of Ancient Egypt.

Your tour begins at Dahshur, home to two remarkable pyramids that showcase the evolution of pyramid-building techniques. The Bent Pyramid, with its unique angular design, marks an important architectural transition, while the Red Pyramid, often considered the world's first true smooth-sided pyramid, stands as a magnificent example of ancient engineering. These lesser-visited sites also offer a peaceful atmosphere away from the crowds.

Next, you'll head to Memphis, the first capital of unified Egypt and once the cultural heart of the kingdom. Founded around 3100 BC by King Narmer, Memphis was a political, religious, and commercial hub for centuries. Today, the open-air museum of Memphis allows you to admire impressive statues and artifacts, including the colossal limestone statue of Ramses II and the alabaster sphinx.

The journey continues to Saqqara, the vast necropolis of the ancient city. Saqqara is most famous for the Step Pyramid of Djoser, designed by the legendary architect Imhotep, which represents the earliest large-scale stone structure ever built. As you explore the site, you'll encounter tombs decorated with hieroglyphics, intricate carvings, and fascinating burial chambers that reveal insights into ancient Egyptian beliefs about the afterlife.

With the guidance of a professional Egyptologist, this day tour provides a comprehensive look at Egypt's Old Kingdom, highlighting the architectural, cultural, and historical developments that paved the way for the grandeur of the Giza Pyramids. Perfect for history enthusiasts and curious travelers, this trip is an unforgettable journey into Egypt's ancient legacy.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Dahshur, Memphis & Saqqara Ancient Sites Tour",
        "steps": [
            ("Morning", "Pick-up from your hotel in Cairo or Giza"),
            ("Morning", "Drive to Dahshur (about 40 km south of Cairo)"),
            ("Morning", "Visit the Bent Pyramid and the Red Pyramid at Dahshur"),
            ("Late Morning", "Continue to Memphis open-air museum"),
            ("Afternoon", "Explore Memphis: colossal statue of Ramses II and Alabaster Sphinx"),
            ("Afternoon", "Head to Saqqara archaeological site"),
            ("Afternoon", "Visit the Step Pyramid of Djoser and surrounding tombs"),
            ("Afternoon", "Learn about ancient burial traditions and early pyramid designs"),
            ("Late Afternoon", "Optional lunch stop at local restaurant"),
            ("Evening", "Return transfer to your hotel in Cairo or Giza"),
        ],
    },
]

INCLUSIONS = [
    "Hotel pick-up and drop-off from Cairo or Giza",
    "Professional Egyptologist tour guide",
    "Private air-conditioned transportation throughout the tour",
    "Entrance fees to Dahshur, Memphis, and Saqqara sites",
    "Bottled water during the tour",
    "All taxes and service charges",
    "Comprehensive guided tour of all three archaeological sites",
]

EXCLUSIONS = [
    "Entrance inside pyramids or special tombs (optional, extra tickets)",
    "Meals and drinks (unless specified)",
    "Gratuities for guide and driver",
    "Personal expenses and souvenirs",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("How long is the tour?",
     "The full tour takes around 6 hours, including travel time between sites."),
    ("Can I enter the pyramids at Dahshur?",
     "Yes, both the Red Pyramid and Bent Pyramid can be entered with an additional ticket. Your guide can assist if you wish to go inside."),
    ("Is this tour suitable for children?",
     "Yes, families often enjoy this tour. However, entering pyramids involves narrow passages, which may not be suitable for very young children."),
    ("What should I wear?",
     "Comfortable walking shoes, light clothing, a hat, and sunscreen are recommended for the desert environment."),
    ("Why visit Dahshur and Saqqara if I've already seen the Giza Pyramids?",
     "These sites are essential to understanding the evolution of pyramid construction and provide a more peaceful, less crowded experience compared to Giza."),
    ("How much walking is involved?",
     "Moderate walking is required between sites and around the archaeological areas. The terrain can be uneven in places."),
    ("Are there restroom facilities at the sites?",
     "Yes, there are basic restroom facilities available at the main entrances of Dahshur, Memphis, and Saqqara."),
    ("Is photography allowed?",
     "Yes, photography is allowed at all outdoor sites. Some interior tomb areas may have restrictions."),
]


class Command(BaseCommand):
    help = "Seeds the Dahshur, Saqqara & Memphis day tour exploring ancient pyramid sites."

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