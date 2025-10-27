# web/management/commands/seed_trip_old_cairo_halfday.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# -------------------------------------------------------------------
# Trip core (enhanced title per your convention)
# -------------------------------------------------------------------
TITLE = "Cairo: Half-Day Old Cairo — Coptic Churches & Ben Ezra Synagogue"
TEASER = (
    "Walk through the spiritual heart of Old Cairo: the Hanging Church, St. Sergius & Bacchus, St. Barbara, and the "
    "historic Ben Ezra Synagogue. A concise, insight-rich journey into Coptic and Jewish heritage with hotel transfers."
)

PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = []  # keep listing under Cairo only

# Your Trip model stores integer days (min 1). For half-day, we set to 1.
DURATION_DAYS = 1
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("80.00")
TOUR_TYPE_LABEL = "Daily Tour — Single Tour"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Half-Day",
    "Cairo",
    "Old Cairo",
    "Religious Heritage",
    "Coptic Cairo",
    "Jewish Heritage",
    "City Tour",
    "Culture",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Visit the iconic Hanging Church overlooking the ancient Babylon Fortress.",
    "Explore St. Sergius & Bacchus (Abu Serga), built over the Holy Family cave.",
    "Discover St. Barbara’s Church and its early Christian relics and architecture.",
    "Step inside the historic Ben Ezra Synagogue, linked to the Cairo Geniza.",
    "Gain context from a knowledgeable Egyptologist guide throughout.",
    "Comfortable round-trip transfers from your hotel.",
]

ABOUT = """\
Step back into the spiritual heart of Old Cairo where Coptic Christian and Jewish landmarks sit within the walls of ancient
Babylon. Visit the Hanging Church, St. Sergius & Bacchus (Abu Serga), St. Barbara, and the Ben Ezra Synagogue while
your Egyptologist guide connects these monuments to Cairo’s layered past. A concise half-day immersion that’s big on
meaning, minimal on logistics—perfect for culture lovers with limited time.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Old Cairo Spiritual Sites (Half-Day)",
        "steps": [
            ("", "Hotel pickup in Cairo or Giza; transfer to Old Cairo."),
            ("", "Hanging Church (Saint Virgin Mary’s Church) guided visit."),
            ("", "Church of St. Sergius & Bacchus (Abu Serga) and the Holy Family cave."),
            ("", "Church of St. Barbara—architecture, relics, and early Christian history."),
            ("", "Ben Ezra Synagogue—history and the Cairo Geniza story."),
            ("", "Return transfer to your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Professional licensed Egyptologist tour guide",
    "Private air-conditioned vehicle for transfers",
    "Hotel pickup and drop-off in Cairo/Giza",
    "Entrance fees to all listed sites",
    "Bottled water",
    "Private tour",
]

EXCLUSIONS = [
    "Personal items/expenses",
    "Tipping/gratuities",
    "Optional tours or add-ons",
    "Meals and drinks unless specified",
]

FAQS = [
    ("How long is the tour?", "Around 3–4 hours including transfers, depending on traffic and site pace."),
    ("Do I need to dress modestly?", "Yes—shoulders and knees covered is recommended for religious sites."),
    ("Is the tour suitable for children?", "Absolutely. Guides adapt explanations for younger visitors."),
    ("Are meals included?", "No meals are included; an optional snack or café stop can be added on request."),
    ("Can this tour be customized?", "Yes. Private tours can add stops or adjust pace and timing."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Half-Day Old Cairo tour (Coptic Churches & Ben Ezra Synagogue) with price, content, languages, and categories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace-related", action="store_true",
            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip."
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show changes without writing to DB."
        )

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
                )
            )

            # Update core fields if rerun
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
