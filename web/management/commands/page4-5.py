# web/management/commands/seed_trip_el_alamein.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# ------------------------------------------------------------
# Trip core (enhanced title per your convention)
# ------------------------------------------------------------
TITLE = "Cairo to El Alamein: War Museum & WWII Cemeteries Day Tour (Private)"
TEASER = (
    "Private full-day journey from Cairo to El Alamein—visit the War Museum, Commonwealth Cemetery, and Axis memorials "
    "with expert commentary, Mediterranean views, and seamless hotel pickup."
)

# Primary/Additional destinations
PRIMARY_DEST = DestinationName.ALEXANDRIA
ALSO_APPEARS_IN = [DestinationName.CAIRO, DestinationName.GIZA]

# Core trip fields
DURATION_DAYS = 1                 # ~8 hours
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("135.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

# Languages
LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

# Category tags
CATEGORY_TAGS = [
    "History",
    "WWII",
    "Museum",
    "Cemeteries",
    "Alexandria",
    "Cairo",
    "Private",
    "Mediterranean",
    "Culture",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Private full-day tour from Cairo to El Alamein with hotel pickup and drop-off.",
    "Explore key WWII sites that shaped the North African campaign.",
    "Visit the El Alamein War Museum—maps, artifacts, uniforms, and dioramas.",
    "Pay tribute at the Commonwealth War Cemetery plus German & Italian memorials.",
    "Expert historical commentary from a professional guide.",
    "Take in serene Mediterranean views that contrast with the battlefield history.",
    "Optional lunch stop at a seaside restaurant (meal not included).",
]

ABOUT = """\
Step back into WWII history on a private day trip from Cairo to El Alamein. Walk the grounds of pivotal battles, visit the
El Alamein War Museum, and pay respects at the Commonwealth, German, and Italian cemeteries—all with expert context
from your guide. Enjoy coastal views, meaningful photo stops, and a smooth round-trip with an optional seaside lunch.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "El Alamein War Museum & Cemeteries (8 hours)",
        "steps": [
            ("07:00", "Hotel pickup in Cairo; drive to El Alamein (approx. 3 hours)."),
            ("", "Guided visit at El Alamein War Museum—comprehensive WWII exhibits."),
            ("", "Commonwealth War Cemetery—pay tribute and learn the stories."),
            ("", "German & Italian Memorials—Axis sites overlooking the Mediterranean."),
            ("", "Lunch break at a local seaside restaurant (meal not included)."),
            ("15:00", "Return drive to Cairo with comfort stops; hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Private round-trip transport from Cairo in an air-conditioned vehicle",
    "Professional English-speaking tour guide",
    "Entrance fees to the El Alamein War Museum",
    "Visits to Commonwealth, German, and Italian War Cemeteries",
    "Bottled water during the trip",
]

EXCLUSIONS = [
    "Personal expenses and souvenirs",
    "Gratuities for guide and driver",
    "Optional additional entrance fees (if applicable)",
    "Travel insurance",
    "Lunch (available at local restaurant)",
]

FAQS = [
    ("How long is the drive from Cairo to El Alamein?", "Approximately 3 hours each way, traffic dependent."),
    ("Is this tour suitable for children?", "Yes—older children and teens interested in history often find it engaging."),
    ("Is there a dress code?", "Modest, respectful attire is recommended when visiting memorials and cemeteries."),
    ("Is the tour wheelchair accessible?", "Some sites are partially accessible; please advise in advance for arrangements."),
    ("Can I customize the tour or add stops?", "Yes—this private tour can be tailored to your interests and timing."),
    ("Are photography and video allowed?", "Generally yes, though some museum sections may restrict flash or filming."),
]

# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the El Alamein day trip with destinations, price, languages, categories, and content."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Resolve destinations
        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Primary destination 'Alexandria' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in ALSO_APPEARS_IN:
            try:
                addl_dests.append(Destination.objects.get(name=d))
            except Destination.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Additional destination '{d}' not found (skipping)."))

        # Languages
        lang_objs = []
        for lname, code in LANGS:
            obj, _ = Language.objects.get_or_create(name=lname, code=code)
            lang_objs.append(obj)

        # Categories
        cat_objs = []
        for tag in CATEGORY_TAGS:
            slug = (
                tag.lower()
                .replace("&", "and")
                .replace("—", "-").replace("–", "-")
                .replace(" ", "-")
            )
            obj, _ = TripCategory.objects.get_or_create(name=tag, defaults={"slug": slug})
            if not obj.slug:
                obj.slug = slug
                obj.save()
            cat_objs.append(obj)

        class _NullCtx:
            def __enter__(self): return self
            def __exit__(self, *a): return False

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
                ),
            )

            # Update core fields on re-run
            changed = []
            def setf(field, value):
                if getattr(trip, field) != value:
                    setattr(trip, field, value)
                    changed.append(field)

            setf("destination", dest_primary)
            setf("teaser", TEASER)
            setf("duration_days", DURATION_DAYS)
            setf("group_size_max", GROUP_SIZE_MAX)
            setf("base_price_per_person", BASE_PRICE)
            setf("tour_type_label", TOUR_TYPE_LABEL)

            if not dry and changed:
                trip.save()

            # M2M
            if not dry:
                trip.additional_destinations.set(addl_dests)
                trip.languages.set(lang_objs)
                trip.category_tags.set(cat_objs)

            # Related content handling
            if replace_related and not dry:
                trip.highlights.all().delete()
                trip.itinerary_days.all().delete()
                trip.inclusions.all().delete()
                trip.exclusions.all().delete()
                trip.faqs.all().delete()
                if hasattr(trip, "about"):
                    trip.about.delete()

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
        self.stdout.write("Languages: " + ", ".join(f"{l.name} ({l.code})" for l in lang_objs))
        self.stdout.write("Categories: " + ", ".join(c.name for c in cat_objs))
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))
