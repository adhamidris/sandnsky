# web/management/commands/seed_trip_khan_el_khalili.py
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
TITLE = "Cairo: Khan El-Khalili Souk & Local Crafts — Guided Shopping Walk"
TEASER = (
    "Shop Cairo’s most famous bazaar with a pro guide—learn to bargain, discover hidden workshops and cafés, "
    "and soak up the colors and sounds of Old Cairo."
)

# Primary/Additional destinations
PRIMARY_DEST = DestinationName.CAIRO
ALSO_APPEARS_IN = [DestinationName.GIZA]  # hotel pickups often from Giza

# Core trip fields
DURATION_DAYS = 1                 # ~4 hours
GROUP_SIZE_MAX = 15               # per brief (more intimate than 25)
BASE_PRICE = Decimal("0.00")      # free/“from $0.00”
TOUR_TYPE_LABEL = "Daily Tour — Shopping & Culture"

# Languages
LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

# Category tags
CATEGORY_TAGS = [
    "Shopping",
    "Souk",
    "Culture",
    "Walking Tour",
    "Old Cairo",
    "Bargaining",
    "Handicrafts",
    "Bazaar",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Explore Cairo’s oldest and most famous bazaar with a licensed guide.",
    "Shop authentic crafts: lamps, spices, textiles, jewelry, perfumes, leather, and more.",
    "Learn local bargaining tips and discover hidden artisan workshops.",
    "Pause at a classic coffeehouse like El Fishawy for tea or coffee (optional).",
    "Photograph colorful alleys and historic Khedival architecture.",
    "Flexible start times and optional hotel pickup from Cairo/Giza.",
]

ABOUT = """\
Step into the living museum of Khan El-Khalili—Cairo’s legendary souk since the Mamluk era. With a knowledgeable local
guide, navigate labyrinthine alleys, meet artisans, sip tea in storied cafés, and learn the art of bargaining. Perfect for culture
seekers, photographers, and savvy shoppers alike.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Khan El-Khalili Guided Shopping Walk (≈4 hours)",
        "steps": [
            ("", "Optional pickup from your Cairo/Giza hotel and transfer to Khan El-Khalili."),
            ("", "Orientation: history, layout, and safety/bargaining tips for the bazaar."),
            ("", "Guided walk: explore alleys, handicraft stalls, spice and perfume vendors, and metalwork shops."),
            ("", "Shopping time with assistance for pricing, quality checks, and packaging."),
            ("", "Optional café stop (e.g., El Fishawy) for tea/coffee and people-watching."),
            ("", "Photography at colorful spots and Khedival-era façades."),
            ("", "Return or optional drop-off at your hotel/central location."),
        ],
    },
]

INCLUSIONS = [
    "Professional licensed tour guide",
    "Walking tour of Khan El-Khalili Market",
    "Shopping assistance and cultural insights",
    "Complimentary bottled water",
    # note: pickup/drop-off is optional add-on; do not include here
]

EXCLUSIONS = [
    "Hotel pick-up and drop-off (available as optional add-on)",
    "Personal shopping expenses",
    "Meals or drinks at cafés (unless specified in your package)",
    "Gratuities",
]

FAQS = [
    ("Is Khan El-Khalili safe for tourists?", "Yes—very popular with locals and visitors; your guide helps ensure a smooth experience."),
    ("Do I need Arabic to shop?", "No. Many vendors speak basic English; your guide can translate and help bargain."),
    ("How long do we spend there?", "About 2–3 hours inside the market, plus short breaks/transfer time as needed."),
    ("What should I buy?", "Jewelry, brass lamps, spices, textiles, perfumes/oils, leather goods, and handmade crafts are popular."),
    ("Is bargaining acceptable?", "Yes—polite bargaining is expected; your guide will coach you on fair prices."),
]

# ------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Khan El-Khalili shopping tour with destinations, price, languages, categories, and content."

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
