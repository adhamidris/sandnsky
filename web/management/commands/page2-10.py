# web/management/commands/seed_trip_grand_egyptian_museum.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Giza: Grand Egyptian Museum Day Tour"
TEASER = (
    "Day tour from Cairo to the Grand Egyptian Museum: Explore Tutankhamun's complete treasures, "
    "royal mummies, and ancient artifacts in the world's largest archaeological museum near Giza Pyramids."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("85.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Tour",
    "Museum",
    "Historical",
    "Cultural",
    "Educational",
]

HIGHLIGHTS = [
    "Discover the iconic Grand Egyptian Museum near the Giza Pyramids with expert guide.",
    "See the complete Tutankhamun treasures on display including the golden mask and artifacts.",
    "Explore the Grand Staircase with massive statues of pharaohs and deities.",
    "Visit the Royal Mummies area and other major galleries spanning ancient Egyptian history.",
    "Enjoy convenient hotel transfers from Cairo in air-conditioned comfort.",
    "Benefit from advanced museum technology including holograms and interactive displays.",
    "Optional visit to nearby Giza Pyramids and Sphinx (available as add-on).",
    "Perfect for history enthusiasts and first-time visitors to Egypt.",
]

ABOUT = """\
Explore Egypt's Timeless Legacy on a Day Tour to the Grand Egyptian Museum from Cairo
Embark on a captivating journey through the rich tapestry of ancient Egypt with a full-day tour from Cairo to the Grand Egyptian Museum (GEM), one of the most anticipated archaeological museums in the world. Located near the Giza Pyramids, this state-of-the-art museum is set to be the largest of its kind globally, housing over 100,000 artifacts, including the complete collection of King Tutankhamun.

Your day begins with a convenient pick-up from your hotel in Cairo by a knowledgeable Egyptologist guide. As you drive towards Giza, you'll get insights into Egypt's ancient and modern history. Upon arrival at the museum, you'll step into a world where the past comes alive through grand architecture, immersive exhibits, and interactive displays.

The tour covers all major halls and galleries, including the Grand Staircase, which showcases massive statues of pharaohs and deities. One of the main highlights is the Tutankhamun Gallery, where visitors can marvel at treasures never before displayed together, such as the iconic golden mask, chariots, jewelry, and ceremonial items. You'll also see artifacts spanning from the Predynastic period to the Greco-Roman era.

What sets this museum apart is not just the collection, but also its advanced technology—holograms, 3D models, and virtual reality bring history to life like never before.

After exploring the museum, enjoy optional shopping or lunch at a local restaurant before returning to your hotel in Cairo. Whether you're a history enthusiast, a casual traveler, or a first-time visitor to Egypt, this day tour offers a deep dive into one of the world's most fascinating civilizations—all in a single, unforgettable day.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Grand Egyptian Museum Exploration",
        "steps": [
            ("Morning", "Pick-up from your Cairo hotel by air-conditioned vehicle"),
            ("Morning", "Arrival at Grand Egyptian Museum (GEM) near Giza Pyramids"),
            ("Late Morning", "Guided tour inside the GEM: Grand Staircase and Tutankhamun Gallery"),
            ("Afternoon", "Explore Royal Mummies area and other major galleries"),
            ("Afternoon", "Optional break for souvenir shopping or café visit"),
            ("Afternoon", "Optional lunch at nearby Egyptian restaurant"),
            ("Late Afternoon", "Optional visit to nearby attractions (Giza Pyramids or local bazaar)"),
            ("Evening", "Drive back to Cairo and drop-off at your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Hotel pick-up and drop-off in Cairo by air-conditioned vehicle",
    "Entrance fees to the Grand Egyptian Museum",
    "Professional Egyptologist tour guide",
    "Bottled water during the tour",
    "All taxes and service charges",
    "Guided tour of major museum sections and galleries",
    "Comprehensive museum exploration with historical context",
]

EXCLUSIONS = [
    "Lunch at local restaurant (optional)",
    "Visit to the Giza Plateau (Pyramids & Sphinx) - available as add-on",
    "Personal guided shopping stop (Papyrus, Perfume, or Bazaar)",
    "Personal expenses and souvenirs",
    "Gratuities for guide and driver",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is the Grand Egyptian Museum fully open?",
     "As of now, selected sections are open for guided tours. Full access may depend on the latest public opening phases. Your guide will ensure you visit all currently accessible highlights."),
    ("Do I need to bring my passport?",
     "It's advisable to bring a copy of your passport, especially for entry and security purposes."),
    ("Can I combine this tour with a visit to the Giza Pyramids?",
     "Yes! Many guests choose to add the Giza Pyramids and the Sphinx to the itinerary. Let us know in advance to customize your experience."),
    ("Is the tour suitable for children?",
     "Absolutely! The museum features interactive exhibits that are engaging for visitors of all ages."),
    ("What should I wear?",
     "Comfortable walking shoes are recommended. Dress modestly, keeping in mind Egypt's cultural norms."),
    ("Are there food or rest areas inside the museum?",
     "Yes, the GEM has cafés, rest areas, and souvenir shops for your convenience."),
    ("How long is the tour duration?",
     "The main museum tour takes approximately 4 hours, but with transfers and optional activities, the entire experience typically lasts 6-8 hours."),
    ("Is photography allowed inside the museum?",
     "Photography policies may vary by exhibit. Generally, non-flash photography is allowed, but some special exhibits may have restrictions."),
]


class Command(BaseCommand):
    help = "Seeds the Grand Egyptian Museum day tour from Cairo."

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