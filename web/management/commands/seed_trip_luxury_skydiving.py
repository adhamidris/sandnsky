# web/management/commands/seed_trip_luxury_skydiving.py
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import (
    Destination,
    DestinationName,
    Trip,
    TripCategory,
    Language,
    TripHighlight,
    TripAbout,
    TripItineraryDay,
    TripItineraryStep,
    TripInclusion,
    TripExclusion,
    TripFAQ,
    TripExtra,
    Review,
)

# ------------------------------------------------------------
# Trip core configuration
# ------------------------------------------------------------
TITLE = "Sand & Sky Luxury Tandem Skydive Over the Pyramids"
TEASER = (
    "Soar above the Giza Plateau on a Sand & Sky Tandem Skydive—private hosts, premium gear, "
    "and cinematic views of the pyramids in one once-in-a-lifetime jump."
)

PRIMARY_DEST = DestinationName.GIZA
ALSO_APPEARS_IN = [DestinationName.CAIRO]

DURATION_DAYS = 1
GROUP_SIZE_MAX = 12
BASE_PRICE = Decimal("440.00")  # weekday Cessna slot
TOUR_TYPE_LABEL = "Luxury Experience — Tandem Skydive"
MINIMUM_AGE = 21
ALLOW_CHILDREN = False
ALLOW_INFANTS = False

LANGS = [
    ("English", "en"),
    ("Arabic", "ar"),
    ("French", "fr"),
    ("German", "de"),
]

CATEGORY_TAGS = [
    "Luxury",
    "Adventure",
    "Skydiving",
    "Bucket List",
    "Adrenaline",
    "Egypt Exclusives",
]

# ------------------------------------------------------------
# Content blocks
# ------------------------------------------------------------
HIGHLIGHTS = [
    "Jump with Sand & Sky's elite tandem instructors for a 45-second freefall over the Great Pyramids.",
    "Arrive to a private check-in lounge with concierge hosts, safety briefing, and tailored flight plan.",
    "Choose weekday Cessna or upgrade to Hercules C130 lift-offs for panoramic flight paths.",
    "Capture the moment with optional 4K video, on-helmet shots, and post-jump celebration toast.",
    "Door-to-door coordination: pre-jump health checks, weight verification, and luxury transfers on request.",
    "Be part of a limited seasonal skydiving window licensed directly over the UNESCO-listed plateau.",
]

ABOUT = """\
Sand & Sky Tours transforms Egypt's legendary skydive into a luxury adventure reserved for serious thrill-seekers. \
Arrive to our private base beside the Giza Plateau where your personal host handles check-in, equipment fitting, \
and USPA-certified instructor briefing. Moments later you’re climbing above the pyramids—just in time for the door \
to open and Cairo's desert horizon to fill your viewfinder.

This adults-only experience pairs the adrenaline of a 45-second freefall with the calm confidence of world-class \
guides, premium rigs, and meticulous safety checks. Whether you select the weekday Cessna or upgrade to the \
Hercules C130 lift, every jump includes an exclusive landing zone welcome, certificate presentation, and the option \
to continue the celebration with Sand & Sky’s curated brunch overlooking the plateau.

Availability is limited to sanctioned operating windows, and each booking is personally managed by our reservations \
team—from weather monitoring and weight eligibility to arranging private transfers. It’s the most spectacular way to \
tick “Skydive the Pyramids” off your bucket list, elevated with the polish Sand & Sky Tours is known for.
"""

ITINERARY = [
    {
        "day": 1,
        "title": "Luxury Tandem Skydive over the Pyramids",
        "steps": [
            ("06:30", "Door-to-door transfer or self-arrival at Sand & Sky’s private skydive lounge."),
            ("07:00", "Concierge welcome, paperwork, weight/BMI check, and personalized safety briefing."),
            ("07:45", "Gear fitting with premium jumpsuits, harness, altimeter, and dual GoPro mounts if selected."),
            ("08:15", "Board the aircraft (Cessna or Hercules upgrade) for a scenic climb above the Giza plateau."),
            ("08:45", "Leap with your tandem instructor for a 45-second freefall and 5-minute parachute glide."),
            ("08:55", "Soft landing at the dedicated drop zone, certificate ceremony, refreshments, and debrief."),
            ("09:20", "Optional celebration brunch or private transfer back to your hotel."),
        ],
    },
]

INCLUSIONS = [
    "Tandem skydive over the Pyramids of Giza with Sand & Sky Tours’ elite instructor team.",
    "Private welcome lounge access with concierge host and health eligibility screening.",
    "All professional skydiving gear, goggles, jumpsuit, rig, and dual safety checks.",
    "Comprehensive ground training, exit rehearsal, and in-air coaching.",
    "Landing zone refreshments plus commemorative Sand & Sky flight certificate.",
    "Real-time weather monitoring with proactive rescheduling support if conditions shift.",
]

EXCLUSIONS = [
    "Balance payment beyond the initial deposit (settled after booking confirmation).",
    "Premium aircraft upgrade to the Hercules C130 or MI-17 helicopter.",
    "Weekend peak slots (Friday–Sunday) and sunrise priority loads.",
    "HD video and photo packages (add-on available).",
    "Private hotel transfers or celebration brunch (add-ons available).",
    "Personal travel insurance (recommended for extreme sports).",
]

FAQS = [
    (
        "Who can jump?",
        "Participants must be at least 21 on jump day (18–20 with notarised guardian consent) and within the approved weight range."
        " Sand & Sky will verify your BMI, health history, and passport details within 48 hours of booking.",
    ),
    (
        "What are the weight limits?",
        "Maximum 100 kg for men and 91 kg for women, including clothing. Safety harnesses are calibrated to these limits."
        " Our team will confirm your exact stats during pre-jump screening.",
    ),
    (
        "How weather dependent is the skydive?",
        "Skydiving is highly weather sensitive. We watch wind and visibility daily and will reschedule to the next available"
        " slot if needed. Cairo enjoys clear skies most of the year, but breezy mornings can shift timings.",
    ),
    (
        "Can I bring a personal camera?",
        "For safety, only Sand & Sky’s certified instructors and camera flyers may operate equipment in freefall."
        " You can add 4K video and photos as an optional extra.",
    ),
    (
        "Are spectators allowed?",
        "Yes—companions can access the drop zone viewing deck with advance notice. We arrange escorted transfers to ensure security compliance.",
    ),
    (
        "How does payment work?",
        "Secure your slot with a USD $70 deposit. We’ll send wire instructions for the balance and confirm aircraft assignment,"
        " weather updates, and pickup logistics within two business days.",
    ),
]

EXTRAS = [
    ("Upgrade to Hercules C130 or MI-17 lift", Decimal("360.00")),
    ("Weekend premium slot (Fri–Sun)", Decimal("50.00")),
    ("4K video & photo montage", Decimal("50.00")),
    ("Private round-trip luxury transfer", Decimal("80.00")),
    ("Celebration brunch overlooking the pyramids", Decimal("120.00")),
]

REVIEWS = [
    (
        "Amelia G.",
        "Flawless from pickup to landing! The Sand & Sky team handled every detail and the freefall view of the pyramids is indescribable."
        " Video package is a must—we relived the moment all night.",
    ),
    (
        "Luis & Sofia",
        "We booked the Hercules upgrade and it felt like a private air show. Concierge check-in, pro instructors, and the post-jump toast "
        "made it the ultimate anniversary surprise.",
    ),
    (
        "Farah M.",
        "As a first-time jumper I was nervous, but Sand & Sky’s briefing and calm coaching made it pure joy. Worth every dollar for the"
        " safest and most spectacular way to see the pyramids.",
    ),
]


class Command(BaseCommand):
    help = "Seeds the Sand & Sky Luxury Tandem Skydive trip with destinations, content, add-ons, and sample reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--replace-related",
            action="store_true",
            help="Delete & recreate highlights/itinerary/inclusions/exclusions/FAQs/extras/reviews.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without writing to the database.",
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        replace_related = opts["replace_related"]

        try:
            dest_primary = Destination.objects.get(name=PRIMARY_DEST)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR("Primary destination 'Giza' not found. Run seed_destinations first."))
            return

        addl_dests = []
        for name in ALSO_APPEARS_IN:
            try:
                addl_dests.append(Destination.objects.get(name=name))
            except Destination.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Additional destination '{name}' not found (skipping)."))

        lang_objs = []
        for label, code in LANGS:
            lang, _ = Language.objects.get_or_create(name=label, code=code)
            lang_objs.append(lang)

        cat_objs = []
        for tag in CATEGORY_TAGS:
            slug = (
                tag.lower()
                .replace("&", "and")
                .replace("—", "-")
                .replace("–", "-")
                .replace(" ", "-")
            )
            category, created = TripCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": tag},
            )
            if created:
                self.stdout.write(f"Created category '{tag}'")
            if category.name != tag:
                category.name = tag
                category.save(update_fields=["name"])
            cat_objs.append(category)

        class _NullCtx:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

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
                    allow_children=ALLOW_CHILDREN,
                    allow_infants=ALLOW_INFANTS,
                    minimum_age=MINIMUM_AGE,
                ),
            )

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
            setf("allow_children", ALLOW_CHILDREN)
            setf("allow_infants", ALLOW_INFANTS)
            setf("minimum_age", MINIMUM_AGE)

            if changed and not dry:
                trip.save(update_fields=changed)

            if not dry:
                trip.additional_destinations.set(addl_dests)
                trip.languages.set(lang_objs)
                trip.category_tags.set(cat_objs)

            if replace_related and not dry:
                trip.highlights.all().delete()
                trip.itinerary_days.all().delete()
                trip.inclusions.all().delete()
                trip.exclusions.all().delete()
                trip.faqs.all().delete()
                trip.extras.all().delete()
                trip.reviews.all().delete()
                if hasattr(trip, "about"):
                    trip.about.delete()

            if not dry:
                if not TripAbout.objects.filter(trip=trip).exists():
                    TripAbout.objects.create(trip=trip, body=ABOUT)

                if not TripHighlight.objects.filter(trip=trip).exists():
                    for idx, text in enumerate(HIGHLIGHTS, start=1):
                        TripHighlight.objects.create(trip=trip, text=text, position=idx)

                if not TripItineraryDay.objects.filter(trip=trip).exists():
                    for day in ITINERARY:
                        itinerary_day = TripItineraryDay.objects.create(
                            trip=trip,
                            day_number=day["day"],
                            title=day["title"],
                        )
                        for position, (time_label, title) in enumerate(day["steps"], start=1):
                            TripItineraryStep.objects.create(
                                day=itinerary_day,
                                time_label=time_label,
                                title=title,
                                position=position,
                            )

                if not TripInclusion.objects.filter(trip=trip).exists():
                    for idx, text in enumerate(INCLUSIONS, start=1):
                        TripInclusion.objects.create(trip=trip, text=text, position=idx)

                if not TripExclusion.objects.filter(trip=trip).exists():
                    for idx, text in enumerate(EXCLUSIONS, start=1):
                        TripExclusion.objects.create(trip=trip, text=text, position=idx)

                if not TripFAQ.objects.filter(trip=trip).exists():
                    for idx, (question, answer) in enumerate(FAQS, start=1):
                        TripFAQ.objects.create(
                            trip=trip,
                            question=question,
                            answer=answer,
                            position=idx,
                        )

                if not trip.extras.exists():
                    for position, (name, price) in enumerate(EXTRAS, start=1):
                        TripExtra.objects.create(
                            trip=trip,
                            name=name,
                            price=price,
                            position=position,
                        )

                if REVIEWS and not trip.reviews.exists():
                    for author, body in REVIEWS:
                        Review.objects.create(trip=trip, author_name=author, body=body)

        mode = "DRY-RUN" if dry else "APPLY"
        self.stdout.write(self.style.SUCCESS("\n— Trip seeding summary —"))
        self.stdout.write(f"Trip: {TITLE}")
        self.stdout.write(f"Primary destination: {dest_primary.name}")
        if addl_dests:
            self.stdout.write("Also appears in: " + ", ".join(dest.name for dest in addl_dests))
        self.stdout.write("Languages: " + ", ".join(f"{lang.name} ({lang.code})" for lang in lang_objs))
        self.stdout.write("Categories: " + ", ".join(cat.name for cat in cat_objs))
        self.stdout.write(f"Minimum age: {MINIMUM_AGE}+ | Children allowed: {ALLOW_CHILDREN} | Infants allowed: {ALLOW_INFANTS}")
        self.stdout.write(self.style.SUCCESS(f"Mode: {mode} | Created: {created}"))
        self.stdout.write(self.style.SUCCESS("———————————————\n"))
