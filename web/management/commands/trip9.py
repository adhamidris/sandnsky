# web/management/commands/seed_trip_alex_port_giza_gem.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# --- Trip core (enhanced title) ---------------------------------------------
TITLE = "Alexandria Port to Giza: Pyramids & Grand Egyptian Museum (Shore Excursion)"
TEASER = (
    "Cruise-friendly day trip from Alexandria Port to the Pyramids, Sphinx, and GEM with Egyptologist guide, "
    "private transfers, lunch, and timed schedule to match your ship."
)

# Touring is in Giza/Cairo; default primary = Giza. Also show on Alexandria (origin) and Cairo.
PRIMARY_DEST_DEFAULT = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.ALEXANDRIA, DestinationName.CAIRO]

DURATION_DAYS = 1                 # ~10 hours same-day
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("250.00")    # “from $250,00” → 250.00
TOUR_TYPE_LABEL = "Daily Tour — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Shore Excursion",
    "Pyramids",
    "Grand Egyptian Museum",
    "Cruise-Friendly",
]

# --- Content blocks ----------------------------------------------------------
HIGHLIGHTS = [
    "See the Great Pyramid of Khufu—one of the Seven Wonders of the Ancient World.",
    "Visit the Great Sphinx and the Giza Plateau with a licensed Egyptologist guide.",
    "Explore the Grand Egyptian Museum (GEM), including Tutankhamun treasures.",
    "Private, air-conditioned transfers directly from/to Alexandria Port.",
    "Traditional Egyptian lunch included at a local restaurant.",
    "Itinerary paced and timed for cruise passengers.",
]

ABOUT = """\
Sail into history with a private shore excursion from Alexandria Port to Cairo/Giza. Travel in a comfortable, air-conditioned vehicle
with a licensed Egyptologist, explore the Pyramids & Sphinx, enjoy a local lunch, then tour the Grand Egyptian Museum’s world-class
galleries including Tutankhamun’s collection. Designed around cruise timings for a seamless, worry-free day ashore.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Pickup at Alexandria Port • Giza Pyramids & Sphinx • GEM • Return to Ship",
        "steps": [
            ("", "Pick-up from Alexandria Port and meet your Egyptologist guide."),
            ("", "Scenic private drive to Cairo/Giza (approx. 3 hours; comfort stops en route)."),
            ("", "Guided visit: Giza Pyramids Complex & Sphinx (photo time; optional camel ride if time permits)."),
            ("", "Lunch at a local Egyptian restaurant."),
            ("", "Grand Egyptian Museum guided tour (major galleries, Tutankhamun collection)."),
            ("", "Return drive to Alexandria Port; drop-off at the cruise terminal."),
            ("", "Note: Timing may vary based on traffic and cruise schedule."),
        ],
    },
]

INCLUSIONS = [
    "Pick-up and drop-off at Alexandria Port",
    "Private air-conditioned vehicle with driver",
    "Professional Egyptologist tour guide",
    "Entrance fees to Giza Pyramids Complex",
    "Entrance ticket to the Grand Egyptian Museum",
    "Lunch at a local restaurant",
    "Bottled water during the trip",
    "All taxes and service charges",
]

EXCLUSIONS = [
    "Camel or horse ride at the pyramids (optional, available on-site)",
    "Personal expenses",
    "Gratuities (optional)",
    "Entrance to the inner chambers of the Great Pyramid (optional extra)",
    "Beverages during lunch",
]

FAQS = [
    ("Is this tour suitable for cruise ship passengers?",
     "Yes—pickup/drop-off at Alexandria Port with timing tailored to ship schedules."),
    ("How long is the drive from Alexandria to Cairo?",
     "About 3 hours each way, subject to traffic; comfort stops are included."),
    ("Is there time to go inside a pyramid?",
     "Possibly—interior entry is extra and depends on schedule/time permitting."),
    ("What’s included for lunch?",
     "A selection of local dishes (vegetarian options available). Drinks are extra."),
    ("Can the itinerary be customized?",
     "Yes—this private tour can be adapted within port time constraints."),
    ("Is GEM fully open?",
     "Yes—the main galleries, including the Tutankhamun collection, are open."),
]


# --- Command -----------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the Alexandria Port → Giza (Pyramids & GEM) shore excursion, with price, content, and multi-destination listing."

    def add_arguments(self, parser):
        parser.add_argument("--replace-related", action="store_true",
                            help="Delete & re-create highlights/itinerary/inclusions/exclusions/FAQs for this trip.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Show changes without writing to DB.")
        parser.add_argument("--primary", choices=["giza", "cairo", "alexandria"], default="giza",
                            help="Choose which destination is primary (default: giza).")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        primary_map = {
            "giza": DestinationName.GIZA,
            "cairo": DestinationName.CAIRO,
            "alexandria": DestinationName.ALEXANDRIA,
        }
        primary_name = primary_map.get(opts["primary"], PRIMARY_DEST_DEFAULT)

        # Build additional list excluding the chosen primary
        addl_names = [d for d in ALSO_APPEARS_IN + [PRIMARY_DEST_DEFAULT] if d != primary_name]

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

            # Update core fields if needed
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

            # M2M relations
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


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False
