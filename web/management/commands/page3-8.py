# web/management/commands/seed_trip_ain_sokhna_yacht.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Ain Sokhna: Luxury Yacht Day Trip on Red Sea"
TEASER = (
    "Luxury yacht day trip from Cairo to Ain Sokhna: Sail Red Sea waters, swim and snorkel in pristine spots, "
    "enjoy onboard seafood lunch, and relax on private yacht with professional crew."
)

PRIMARY_DEST = DestinationName.AIN_EL_SOKHNA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("150.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Yacht Tour",
    "Luxury",
    "Red Sea",
    "Day Trip",
    "Snorkeling",
    "Beach",
]

HIGHLIGHTS = [
    "Sail the Red Sea in style aboard a private luxury yacht along calm, crystal-clear waters of Ain Sokhna.",
    "Perfect day escape from Cairo - just 1.5-2 hours from the city for a relaxing break.",
    "Swim and snorkel in pristine waters with provided snorkeling gear at selected swimming spots.",
    "Enjoy fresh onboard lunch featuring seafood or mixed grill prepared and served on the yacht.",
    "Sunbathe on deck or relax in shaded lounging areas with comfortable seating.",
    "Private and personalized experience ideal for couples, families, or small groups.",
    "Capture Instagram-worthy views of Red Sea, open skies, and golden coastline.",
    "Professional crew service ensuring comfort, safety, and enjoyment throughout the day.",
]

ABOUT = """\
Escape the noise and crowds of Cairo for a day of sun-soaked luxury and sea breeze on this unforgettable private yacht tour to Ain Sokhna, one of Egypt's most pristine Red Sea destinations. This exclusive day trip is designed for those looking to relax, recharge, and enjoy the beauty of the sea in complete comfort and style.

Your journey begins with a comfortable, air-conditioned transfer from Cairo to the Ain Sokhna Marina (approx. 1.5 to 2 hours). Upon arrival, step aboard a luxurious private yacht fully equipped with sun decks, shaded lounges, and onboard amenities. As the yacht sets sail on the calm turquoise waters of the Red Sea, soak in the panoramic sea views, sip on cool drinks, and bask in the warm sun.

The cruise includes several opportunities to swim, snorkel, or just float in the clear waters—perfect for spotting colorful fish and marine life. All snorkeling equipment is provided, making it easy for you to dive right in. Whether you want to sunbathe on deck, relax in the shade, or explore the sea, this tour caters to your perfect day.

A freshly prepared lunch is served onboard by the crew—often featuring grilled seafood, salads, rice, and local delicacies, with soft drinks and juices available throughout the day.

This luxury Red Sea escape is ideal for couples, families, friends, or even small corporate groups. It's the perfect way to spend a relaxing day outside of Cairo, away from the crowds, and immersed in Egypt's natural coastal beauty.

Whether you're celebrating a special occasion or just want a break from sightseeing, this Ain Sokhna yacht tour delivers elegance, tranquility, and unforgettable memories—all in just one day.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Luxury Yacht Day Trip to Ain Sokhna Red Sea",
        "steps": [
            ("Morning", "Pick-up from Cairo hotel in private air-conditioned vehicle"),
            ("Morning", "Scenic drive to Ain Sokhna Marina (approx. 1.5-2 hours)"),
            ("Late Morning", "Board luxury private yacht and safety briefing"),
            ("Late Morning", "Set sail on Red Sea waters, enjoy panoramic views"),
            ("Afternoon", "Swimming and snorkeling stops at selected pristine spots"),
            ("Afternoon", "Fresh onboard buffet lunch served (seafood or mixed options)"),
            ("Afternoon", "Relaxation time: sunbathing, swimming, or shaded lounging"),
            ("Late Afternoon", "Return sail to Ain Sokhna Marina"),
            ("Evening", "Drive back to Cairo and hotel drop-off"),
        ],
    },
]

INCLUSIONS = [
    "Round-trip transfers from Cairo in private air-conditioned vehicle",
    "Full-day private yacht charter from Ain Sokhna Marina",
    "Professional crew and captain services",
    "Snorkeling equipment (masks, fins, snorkels)",
    "Life jackets and safety gear",
    "Onboard buffet lunch (seafood or mixed options)",
    "Soft drinks, juices, and bottled water throughout the day",
    "Swimming stops at selected Red Sea spots",
    "Use of sun deck and shaded seating areas",
    "All marina fees and taxes",
]

EXCLUSIONS = [
    "Alcoholic beverages (available upon request at extra charge)",
    "Towels and swimwear (bring your own)",
    "Gratuities/tips for crew and driver",
    "Optional water sports (banana boat, jet ski, etc. if requested)",
    "Personal expenses",
    "Travel insurance",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Do I need to know how to swim to join the yacht tour?",
     "No, life jackets are provided and you can still enjoy the experience on deck without entering the water."),
    ("What should I bring with me?",
     "Bring swimwear, sunscreen, towel, sunglasses, hat, and a camera. Snorkeling gear is provided."),
    ("Is the lunch onboard suitable for vegetarians?",
     "Yes, vegetarian options are available. Please inform us in advance of any dietary requirements."),
    ("Are children allowed on the yacht?",
     "Yes! The trip is family-friendly and children are welcome."),
    ("Can I request water sports like jet skiing?",
     "Yes, optional water sports can be arranged in advance at an extra cost."),
    ("Is alcohol available onboard?",
     "Alcohol is not included, but can be provided upon request at an additional charge."),
    ("What is the best time of year for this tour?",
     "The tour runs year-round, but the best weather is from October to May when temperatures are milder."),
    ("What happens in case of bad weather?",
     "In case of unfavorable weather conditions, the tour may be rescheduled or cancelled with full refund for safety reasons."),
]


class Command(BaseCommand):
    help = "Seeds the Luxury Yacht Day Trip to Ain Sokhna from Cairo."

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