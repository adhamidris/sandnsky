# web/management/commands/seed_trip_alexandria_day_from_cairo.py
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
TITLE = "Cairo to Alexandria: Full-Day Private City Highlights with Lunch"
TEASER = (
    "Escape Cairo for a private day in Egypt’s Mediterranean gem—Alexandria. "
    "Catacombs, Pompey’s Pillar, Qaitbay Citadel, and Bibliotheca Alexandrina, "
    "with an Egyptologist guide, lunch, and private A/C transport."
)

PRIMARY_DEST_DEFAULT = DestinationName.ALEXANDRIA
ALSO_APPEARS_IN = [DestinationName.CAIRO]   # dual listing

DURATION_DAYS = 1              # ~10 hours day trip
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("180.00")
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Day Trip",
    "Alexandria",
    "Cairo",
    "History",
    "Coast",
    "Museums",
]

# -------------------------------------------------------------------
# Content blocks
# -------------------------------------------------------------------
HIGHLIGHTS = [
    "Explore the Catacombs of Kom El Shoqafa with an Egyptologist guide.",
    "See Pompey’s Pillar and traces of Roman Alexandria.",
    "Discover Qaitbay Citadel, built where the ancient Lighthouse once stood.",
    "Visit the modern Bibliotheca Alexandrina (interior subject to opening hours).",
    "Private A/C transport from Cairo/Giza hotels with hotel pickup and drop-off.",
    "Lunch at a local restaurant included; bottled water provided.",
]

ABOUT = """\
Trade Cairo’s bustle for sea breezes and layered history on a private day trip to Alexandria. Travel in a comfortable, air-conditioned
vehicle with your Egyptologist guide and explore Kom El Shoqafa’s catacombs, Pompey’s Pillar, Qaitbay Citadel, and the striking
Bibliotheca Alexandrina. Enjoy an included lunch and flexible pacing while you uncover Greco-Roman, Islamic, and Egyptian
heritage along the Mediterranean coast.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Alexandria in a Day — Private Tour from Cairo",
        "steps": [
            ("", "Early pickup from your Cairo/Giza hotel; drive ~3 hours to Alexandria."),
            ("", "Guided visit: Catacombs of Kom El Shoqafa."),
            ("", "Photo stop and walk around Pompey’s Pillar."),
            ("", "Explore Qaitbay Citadel on the site of the ancient Lighthouse."),
            ("", "Lunch at a local restaurant (drinks extra)."),
            ("", "Visit the Bibliotheca Alexandrina (exterior/interior per opening hours)."),
            ("", "Return drive to Cairo; hotel drop-off."),
        ],
    },
]

INCLUSIONS = [
    "Private air-conditioned vehicle",
    "Professional Egyptologist guide",
    "Hotel pickup and drop-off in Cairo/Giza",
    "Entrance fees to all listed sites",
    "Lunch at a local restaurant (drinks extra)",
    "Bottled water during the tour",
]

EXCLUSIONS = [
    "Personal items",
    "Tipping (gratuities)",
    "Any optional tours or add-ons",
]

FAQS = [
    ("How long is the drive from Cairo to Alexandria?",
     "About 3 hours each way, depending on traffic."),
    ("Is lunch included?",
     "Yes—lunch is included; beverages are extra."),
    ("Can the itinerary be customized?",
     "Yes—this is a private tour; pacing and stops can be adjusted within opening hours."),
    ("How much walking is involved?",
     "Moderate walking; wear comfortable shoes."),
    ("Are entrance fees included?",
     "Yes—all listed site entries are included."),
    ("Is this tour suitable for children?",
     "Absolutely—families are welcome and pacing can be adapted."),
    ("What time do we start?",
     "Typically between 6:00–7:00 AM to maximize Alexandria time."),
]

# -------------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Full-Day Alexandria Private Tour (from Cairo Hotels) with price, content, languages, categories, and dual destination listing."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["alexandria", "cairo"], default="alexandria",
                            help="Choose the primary destination (default: alexandria).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        # Primary destination choice
        primary_map = {
            "alexandria": DestinationName.ALEXANDRIA,
            "cairo": DestinationName.CAIRO,
        }
        primary_name = primary_map[opts["primary"]]
        addl_names = [d for d in (set(ALSO_APPEARS_IN + [PRIMARY_DEST_DEFAULT])) if d != primary_name]

        # Resolve destinations
        try:
            dest_primary = Destination.objects.get(name=primary_name)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Primary destination '{primary_name}' not found. Seed destinations first."))
            return

        addl_dests = []
        for d in addl_names:
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

            # Update core fields if re-run
            changed = []
            def setf(field, value):
                old = getattr(trip, field)
                if old != value:
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

            # Related content (optional rebuild)
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


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
