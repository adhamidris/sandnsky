# web/management/commands/seed_trip_alexandria_elalamein_2day.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName, Trip, TripCategory, Language,
    TripHighlight, TripAbout, TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion, TripFAQ,
)

# --- Trip core (enhanced title per your convention) --------------------------
TITLE = "Alexandria to El Alamein: 2-Day City & WWII History (War Museum & Cemeteries)"
TEASER = (
    "Two-day combo: Alexandria’s ancient/modern icons plus El Alamein’s WWII War Museum and cemeteries. "
    "Includes lunches, entries, Egyptologist guide, and private A/C transport."
)

# Touring centers on Alexandria/El Alamein; default primary = Alexandria.
# Also show on Cairo (pickup possible from Cairo).
PRIMARY_DEST_DEFAULT = DestinationName.ALEXANDRIA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 2
GROUP_SIZE_MAX = 50
BASE_PRICE = Decimal("325.00")  # “$325,00” → 325.00
TOUR_TYPE_LABEL = "Multi-Day — Discovery"

LANGS = [
    ("English", "en"),
    ("Espanol", "es"),
    ("Italian", "it"),
    ("Russian", "ru"),
]

CATEGORY_TAGS = [
    "Multi-Day",
    "Alexandria",
    "El Alamein",
    "WWII History",
    "Museums",
    "Coastal",
]

# --- Content blocks ----------------------------------------------------------
HIGHLIGHTS = [
    "Guided exploration of Alexandria’s landmarks: Kom El Shoqafa, Pompey’s Pillar, Qaitbay Citadel, and Bibliotheca Alexandrina.",
    "Full WWII history day at El Alamein: War Museum, Commonwealth War Cemetery, Italian & German memorials.",
    "Coastal Mediterranean views and seated lunches both days at local restaurants.",
    "Private, air-conditioned transport and licensed Egyptologist guide.",
    "Entrance fees to listed sites included; bottled water provided.",
    "Flexible pickup/drop-off in Alexandria or Cairo.",
]

ABOUT = """\
Blend antiquity with modern history on this two-day guided tour. Day 1 showcases Alexandria’s Greco-Roman remains, Islamic
heritage, and modern icons along the Mediterranean. Day 2 heads west to El Alamein to trace the North Africa campaign at the War
Museum and international cemeteries. Lunch is included on both days; accommodation is not included so you can choose where to
stay in Alexandria. Private A/C transport, entries, and Egyptologist guide keep the experience seamless.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Alexandria City Highlights",
        "steps": [
            ("", "Pickup from your location (Cairo or Alexandria). Drive to Alexandria (A/C vehicle)."),
            ("", "Visit the Catacombs of Kom El Shoqafa."),
            ("", "Photo stop at Pompey’s Pillar."),
            ("", "Explore the Citadel of Qaitbay."),
            ("", "Tour the Bibliotheca Alexandrina (exterior/interior per operating hours)."),
            ("", "Lunch at a seaside restaurant."),
            ("", "Free time along the Corniche or for shopping."),
            ("", "Evening drop-off at your hotel in Alexandria (hotel not included)."),
        ],
    },
    {
        "day": 2,
        "title": "El Alamein WWII Heritage",
        "steps": [
            ("", "Morning pickup from your Alexandria hotel."),
            ("", "Drive to El Alamein (~1.5 hours)."),
            ("", "Visit the El Alamein War Museum (artifacts, vehicles, and campaign exhibits)."),
            ("", "Explore the Commonwealth War Cemetery."),
            ("", "Visit the Italian and German War Cemeteries/Memorials."),
            ("", "Lunch at a local restaurant."),
            ("", "Return transfer to Alexandria or Cairo per your preference. End of services."),
        ],
    },
]

INCLUSIONS = [
    "Professional English-speaking Egyptologist guide (both days)",
    "Air-conditioned private transportation (round-trip)",
    "Entrance fees to all mentioned sites",
    "Lunch on both days at local restaurants",
    "Bottled water during the tour",
    "All applicable taxes and service charges",
]

EXCLUSIONS = [
    "Hotel accommodation (not provided)",
    "Any extra meals or drinks not mentioned",
    "Personal expenses and gratuities",
    "Optional activities or additional entrance tickets",
    "Travel insurance (optional)",
]

FAQS = [
    ("Is hotel accommodation included?",
     "No—please arrange your own hotel stay in Alexandria between Day 1 and Day 2."),
    ("Is the tour suitable for children?",
     "Yes—content is presented respectfully; families are welcome."),
    ("Are meals included?",
     "Yes—lunch is included on both days; drinks are extra unless specified."),
    ("What should I bring?",
     "Comfortable walking shoes, sun protection, camera, passport/ID; a light jacket in winter."),
    ("Is the tour private or group-based?",
     "It can be arranged as a private or small-group tour depending on booking."),
]

# --- Command -----------------------------------------------------------------
class Command(BaseCommand):
    help = "Seeds the 2-Day Alexandria & El Alamein tour with price, content, languages, categories, and multi-destination listing."

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

        primary_map = {
            "alexandria": DestinationName.ALEXANDRIA,
            "cairo": DestinationName.CAIRO,
        }
        primary_name = primary_map[opts["primary"]]
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
