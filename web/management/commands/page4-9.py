# web/management/commands/seed_trip_cairo_heritage.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# ------------------------------------------------------------
# Trip core (enhanced name format)
# ------------------------------------------------------------
TITLE = "Old Cairo Heritage: Coptic & Islamic Landmarks + Khan Al Khalili"
TEASER = (
    "Discover Coptic churches, historic mosques, and Cairo’s legendary Khan Al Khalili in one curated heritage walk—"
    "sacred sites, stories, and souk culture with a licensed guide."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.GIZA]

DURATION_DAYS = 1                   # ≈6 hours
GROUP_SIZE_MAX = 50                 # per brief
BASE_PRICE = Decimal("95.00")
TOUR_TYPE_LABEL = "Daily Tour — Heritage & Culture"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Heritage",
    "Coptic Cairo",
    "Islamic Cairo",
    "Old Cairo",
    "Culture",
    "Walking Tour",
    "Bazaar",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Visit sacred Coptic landmarks: the Hanging Church and the Cave Church of St. Sergius.",
    "Step inside Ben Ezra Synagogue and trace Cairo’s multi-faith heritage.",
    "Explore Islamic Cairo’s grand mosques and medieval lanes (UNESCO site).",
    "Stroll and shop through Khan Al Khalili Bazaar with your guide.",
    "Enjoy authentic photo ops in courtyards, alleys, and Khedival façades.",
    "Hotel pickup/drop-off, private vehicle, and bottled water included.",
]

ABOUT = """\
Step back in time through Old Cairo’s layered faiths and cultures. Begin in Coptic Cairo at the Hanging Church and
St. Sergius (the Holy Family’s refuge), then visit Ben Ezra Synagogue. Continue into Islamic Cairo’s mosques and
madrasas before ending amid the colors and aromas of Khan Al Khalili. A licensed guide connects the landmarks,
legends, and living traditions that shaped Cairo.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Coptic Cairo → Islamic Cairo → Khan Al Khalili (≈6 hours)",
        "steps": [
            ("", "Hotel pickup in Cairo/Giza; transfer to Old Cairo."),
            ("", "Coptic Cairo: Hanging Church, St. Sergius (Cave Church), and Ben Ezra Synagogue."),
            ("", "Islamic Cairo: explore key mosques and historical sites (route varies by opening times)."),
            ("", "Khan Al Khalili: guided walk with shopping time and optional café stop for tea."),
            ("", "Optional local lunch at a traditional restaurant."),
            ("", "Drop-off at your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Hotel pick-up and drop-off from Cairo or Giza",
    "Private air-conditioned vehicle",
    "Professional Egyptologist or licensed tour guide",
    "Entry fees to featured historical sites (churches, mosques, synagogues)",
    "Guided walking tour of Khan Al Khalili Bazaar",
    "Bottled water during the tour",
]

EXCLUSIONS = [
    "Lunch",
    "Personal expenses and souvenirs",
    "Gratuities for guide and driver (optional but appreciated)",
    "Additional activities or entrance to non-listed attractions",
]

FAQS = [
    ("Is this a private or group tour?", "Private by default; small-group option available upon request."),
    ("How long is the tour?", "About 5–6 hours; we can adjust to your schedule."),
    ("What should I wear?", "Modest clothing recommended for churches/mosques; comfortable walking shoes."),
    ("Is it family-friendly?", "Yes—pace and stops can be tailored for all ages and comfort levels."),
    ("Can I customize stops?", "Absolutely—tell us your interests and we’ll shape the route."),
    ("Is Khan Al Khalili safe?", "Yes—popular with locals and visitors; your guide stays with you."),
]

# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Old Cairo Heritage tour (Coptic & Islamic Landmarks + Khan Al Khalili) with destinations, price, languages, categories, and content."

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
            self.stderr.write(self.style.ERROR("Primary destination 'Cairo' not found. Seed destinations first."))
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

            # Related content
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
