# web/management/commands/seed_trip_pyramids_light_show.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Giza: Pyramids Sound & Light Show with Dinner Experience"
TEASER = (
    "Evening tour to Giza Pyramids: Enjoy dinner with pyramid views followed by spectacular "
    "Sound and Light Show bringing ancient Egyptian history to life with illuminations and narration."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("55.00")
TOUR_TYPE_LABEL = "Daily Tour — Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
]

CATEGORY_TAGS = [
    "Evening Tour",
    "Cultural",
    "Dinner",
    "Entertainment",
    "Historical",
    "Night Experience",
]

HIGHLIGHTS = [
    "Enjoy a delicious dinner with stunning views of the Pyramids of Giza from restaurant terrace.",
    "Witness the iconic Sound and Light Show - dazzling display of lights, music, and storytelling.",
    "Learn about ancient Egyptian history through captivating narrated experience in multiple languages.",
    "Experience the Pyramids at night, beautifully illuminated against the desert sky.",
    "Hassle-free round-trip transportation from your hotel in Cairo or Giza.",
    "Perfect for couples, families, and solo travelers seeking memorable evening in Egypt.",
    "Comfortable evening atmosphere away from daytime crowds and heat.",
    "Professional hosting and guidance throughout the evening experience.",
]

ABOUT = """\
Imagine an evening where ancient history meets modern enchantment—Dinner with a Light Show Over the Pyramids offers just that. This unique experience takes you to the iconic Giza Plateau, where the majestic Pyramids of Giza and the Sphinx stand tall against the backdrop of a starlit sky. As the sun dips below the horizon, you'll enjoy a delicious dinner with stunning views of one of the world's most iconic landmarks.

The evening begins with a transfer from your hotel in a private or group vehicle, depending on your selection. Upon arrival, you're seated in a specially chosen restaurant or outdoor terrace offering direct or panoramic views of the pyramids. Whether you're indulging in traditional Egyptian cuisine or opting for international fare, the meal is a feast for both the palate and the eyes.

As darkness blankets the desert, the Sound and Light Show begins—an immersive audio-visual experience that brings thousands of years of history to life. Watch as the pyramids and the enigmatic Sphinx are bathed in colorful lights while a captivating narration tells the story of ancient Egypt, its rulers, and the architectural marvels before you.

This tour is ideal for couples, families, or solo travelers looking for a memorable cultural night out in Cairo. It's not just a dinner or a show—it's a journey through time, enhanced by atmospheric lighting, storytelling, and authentic Egyptian hospitality.

Whether you're visiting Egypt for the first time or returning for a deeper connection, this night will be a highlight of your journey—a perfect blend of romance, history, and awe.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Pyramids Sound & Light Show with Dinner Evening",
        "steps": [
            ("Evening", "Pick-up from your hotel in Cairo or Giza"),
            ("Evening", "Transfer to Giza Plateau area"),
            ("Evening", "Dinner at restaurant with panoramic views of the Pyramids"),
            ("Night", "Attend the Sound and Light Show at Giza Pyramids"),
            ("Night", "Watch illuminations and listen to historical narration"),
            ("Late Night", "Return transfer to your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Round-trip transportation from your hotel in Cairo or Giza",
    "Dinner at Pyramids view restaurant (rooftop or terrace)",
    "English-speaking guide or host throughout the evening",
    "Bottled water during the transfer",
    "All service charges and taxes",
    "Sound and Light Show tickets",
    "Comfortable seating arrangements with pyramid views",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Gratuities/tips for guide and driver (optional)",
    "Beverages during dinner (unless specified)",
    "Entry to the Pyramids or Sphinx interior (external show only)",
    "Optional extras not mentioned in the itinerary",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is the Sound and Light Show available every night?",
     "The show runs daily, though times may vary depending on the season. There are also shows in different languages, typically on rotation."),
    ("Is the dinner indoors or outdoors?",
     "The dinner is usually served on a rooftop or terrace with views of the Pyramids. Indoor seating may be arranged in colder months or on request."),
    ("Is this a private or group tour?",
     "You can book this experience as a private tour or join a small group, depending on your preference and budget."),
    ("Is the show suitable for children?",
     "Yes, the show is family-friendly and can be enjoyed by children. They often find the lights and storytelling engaging."),
    ("Can I request vegetarian or vegan options for dinner?",
     "Yes, vegetarian and some vegan options are available. Please mention any dietary requirements during booking."),
    ("Will we enter the Pyramids during this tour?",
     "No, this is an external evening show and does not include entry into the Pyramids or Sphinx interiors."),
    ("What should I wear?",
     "Casual evening wear is recommended. A light jacket may be useful in cooler months."),
    ("How long does the Sound and Light Show last?",
     "The show typically lasts about 1 hour, with the entire evening experience taking approximately 3 hours including transfers and dinner."),
]


class Command(BaseCommand):
    help = "Seeds the Pyramids Sound and Light Show with Dinner evening tour."

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