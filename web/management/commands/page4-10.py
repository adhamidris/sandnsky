# web/management/commands/seed_trip_mount_sinai.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

TITLE = "Cairo to Sinai: Mount Sunrise & St. Catherine Monastery Overnight Trip"
TEASER = (
    "Overnight trip from Cairo to Mount Sinai: Hike under stars to summit for sunrise, "
    "visit UNESCO World Heritage St. Catherine Monastery with Burning Bush and ancient manuscripts."
)

PRIMARY_DEST = DestinationName.SINAI
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 2
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("500.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery Multi-Tour Safari Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Overnight Tour",
    "Religious",
    "Hiking",
    "UNESCO",
    "Adventure",
    "Historical",
]

HIGHLIGHTS = [
    "Hike under the stars to the sacred summit of Mount Sinai - biblical site of Ten Commandments.",
    "Witness breathtaking sunrise over Sinai Mountains from 2,285-meter summit.",
    "Visit historic St. Catherine Monastery, UNESCO World Heritage Site since 2002.",
    "Explore the site of the Burning Bush and view ancient religious manuscripts.",
    "Experience one of the oldest functioning Christian monasteries in the world (6th century).",
    "Enjoy round-trip transport from Cairo with knowledgeable English-speaking guide.",
    "Optional camel ride available for portions of the ascent.",
    "Spiritual journey combining adventure, history, and religious significance.",
]

ABOUT = """\
Experience the awe-inspiring beauty of Mount Sinai at sunrise and explore the ancient spiritual haven of St. Catherine's Monastery on this full-day guided tour from Cairo. This unforgettable journey offers a blend of adventure, history, and spirituality—all in one breathtaking experience.

Your journey begins with an overnight drive from Cairo to the Sinai Peninsula, a scenic route that takes you through rugged desert landscapes and past historic Bedouin communities. Upon arrival at the foot of Mount Sinai in the early morning hours, you'll begin your ascent, guided by an experienced local who will lead you safely up the revered mountain.

The hike, under a canopy of stars, culminates at the summit of Mount Sinai—believed to be the biblical site where Moses received the Ten Commandments. As dawn breaks, witness a spectacular sunrise over the surrounding mountains—a truly spiritual and unforgettable sight. This moment of tranquility and natural beauty is worth every step of the climb.

After descending the mountain, you'll visit St. Catherine's Monastery, a UNESCO World Heritage Site and one of the oldest functioning Christian monasteries in the world. Built in the 6th century, the monastery houses an impressive collection of religious manuscripts, icons, and ancient architecture, including the legendary Burning Bush.

This tour is ideal for adventure seekers, history enthusiasts, and spiritual travelers alike. With round-trip transport, guided hiking support, and expert commentary, your Mount Sinai & St. Catherine's day trip from Cairo will be a deeply enriching experience you'll never forget.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Evening Departure from Cairo to Sinai",
        "steps": [
            ("Evening", "7:00 PM - Pickup from your Cairo hotel"),
            ("Night", "Overnight drive to Sinai Peninsula (approx. 6-7 hours)"),
            ("Night", "Travel through rugged desert landscapes and Bedouin communities"),
        ],
    },
    {
        "day": 2,
        "title": "Mount Sinai Sunrise & St. Catherine Monastery",
        "steps": [
            ("Early Morning", "1:00 AM - Arrive at Mount Sinai base camp"),
            ("Early Morning", "Begin guided hike to summit under stars"),
            ("Dawn", "Reach summit and witness spectacular sunrise"),
            ("Morning", "Begin descent back to base camp"),
            ("Morning", "Visit St. Catherine Monastery - church, Burning Bush, artifacts"),
            ("Late Morning", "Light breakfast/snack before departure"),
            ("Afternoon", "Depart from St. Catherine for return to Cairo"),
            ("Evening", "Arrive back in Cairo, drop-off at your hotel"),
        ],
    },
]

INCLUSIONS = [
    "Round-trip transportation from Cairo in air-conditioned vehicle",
    "Professional English-speaking tour guide",
    "Mount Sinai entrance fees and hiking permits",
    "St. Catherine Monastery admission ticket",
    "Guided hike up Mount Sinai with local guide",
    "Bottled water during the tour",
    "2 breakfasts and 1 dinner as per itinerary",
    "All taxes and service charges",
]

EXCLUSIONS = [
    "Optional camel ride (available for extra charge)",
    "Gratuities for guides and drivers (optional but appreciated)",
    "Personal expenses and souvenirs",
    "Meals not mentioned in itinerary",
    "Travel insurance",
    "Lunch (optional add-on)",
    "Any other services not mentioned in inclusions",
]

FAQS = [
    ("Is the hike to Mount Sinai difficult?",
     "Yes, the hike involves a steady uphill climb and takes 2.5 to 3 hours. It is moderately challenging and not recommended for people with mobility issues. You may opt for a camel ride for part of the ascent."),
    ("What should I bring with me?",
     "Comfortable hiking shoes, warm clothes (especially for early morning), a flashlight or headlamp, snacks, water, sunscreen, and a small backpack."),
    ("Can I ride a camel instead of hiking?",
     "Yes, camel rides are available for a portion of the hike for an extra fee. Note that the final steps to the summit (750 'Steps of Repentance') must be climbed on foot."),
    ("Are there restrooms on the trail?",
     "There are limited and very basic restroom facilities along the trail. It's recommended to use the restrooms before starting the hike."),
    ("Is food included?",
     "A light breakfast is included after the hike. Other meals are not provided, so it's advisable to bring snacks or purchase food before the tour."),
    ("Is this tour suitable for children?",
     "It depends on the child's stamina and hiking ability. The hike is long and starts at night, so it's better suited for older children or teens."),
    ("What is the altitude of Mount Sinai?",
     "Mount Sinai stands at 2,285 meters (7,497 feet) above sea level. The hike involves significant elevation gain."),
    ("What is the temperature like during the hike?",
     "Temperatures can vary dramatically. It can be quite cold at the summit before sunrise (even below freezing in winter), while daytime temperatures in the valley can be warm. Layered clothing is essential."),
]


class Command(BaseCommand):
    help = "Seeds the Mount Sinai Sunrise & St. Catherine Monastery overnight trip from Cairo."

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