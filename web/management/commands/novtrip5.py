from __future__ import annotations

import os
from decimal import Decimal

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from web.models import (
    Destination,
    DestinationName,
    Trip,
    TripHighlight,
    TripAbout,
    TripItineraryDay,
    TripItineraryStep,
    TripInclusion,
    TripExclusion,
    TripBookingOption,
    TripGalleryImage,
    TripExtra,
)


TRIP_TITLE = "El Alamein Day Tour From Cairo"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/alamin"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 6)]  # 1.webp ... 5.webp


def _file_path(filename: str) -> str:
    return os.path.join(IMAGE_BASE_PATH, filename)


def _safe_attach_image(instance, field_name: str, filename: str, stdout):
    """
    Attach an image to an ImageField using Django's storage backend
    (e.g., Cloudflare R2) just like the admin upload would.

    If the file does not exist locally, log a warning and skip.
    """
    path = _file_path(filename)
    if not os.path.exists(path):
        stdout.write(
            stdout.style.WARNING(
                f"Image not found on disk, skipping {field_name}: {path}"
            )
        )
        return

    field = getattr(instance, field_name)
    if field and getattr(field, "name", None):
        stdout.write(
            stdout.style.WARNING(
                f"{field_name} already set for {instance}. Skipping re-upload."
            )
        )
        return

    with open(path, "rb") as f:
        django_file = File(f)
        field.save(os.path.basename(path), django_file, save=False)


class Command(BaseCommand):
    help = "Seed the 'El Alamein Day Tour From Cairo' trip with images and content."

    def handle(self, *args, **options):
        try:
            # Anchoring under Cairo (departure city)
            destination = Destination.objects.get(name=DestinationName.CAIRO)
        except Destination.DoesNotExist:
            raise CommandError(
                "Destination 'Cairo' not found. Seed destinations first "
                "or create one with name=DestinationName.CAIRO."
            )

        with transaction.atomic():
            trip = Trip.objects.filter(title=TRIP_TITLE).first()
            created = False

            if trip is None:
                trip = Trip(
                    title=TRIP_TITLE,
                    destination=destination,
                    teaser=(
                        "Travel from Cairo to El Alamein to visit World War II sites, "
                        "including the Military Museum and Commonwealth cemeteries, on "
                        "a private full-day tour with Kaya Tours."
                    ),
                    duration_days=1,  # 12-hour tour mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("234.00"),
                    child_price_per_person=Decimal("49.00"),
                    tour_type_label="Private One-Day Tour — El Alamein from Cairo",
                    is_service=False,
                    allow_children=True,
                    allow_infants=True,
                )
                trip.save()
                created = True
                self.stdout.write(self.style.SUCCESS(f"Created trip: {trip.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Trip already exists: {trip.title}"))

            # --- Attach card & hero images via storage (Cloudflare R2) ---
            _safe_attach_image(trip, "card_image", CARD_IMAGE_FILENAME, self.stdout)
            _safe_attach_image(trip, "hero_image", HERO_IMAGE_FILENAME, self.stdout)
            # hero_image_mobile left blank for now.
            trip.save()
            self.stdout.write(self.style.SUCCESS("Card & hero images processed (if files present)."))

            # --- Highlights ---
            if created or not trip.highlights.exists():
                trip.highlights.all().delete()

                highlights = [
                    "Travel from Cairo along Egypt’s Mediterranean coast to El Alamein.",
                    "Visit the El Alamein Military Museum with World War II exhibits.",
                    "Learn about key WWII battles and the roles of Montgomery and Rommel.",
                    "Pay respects at the Commonwealth and Axis cemeteries overlooking the sea.",
                    "Enjoy a private full-day tour with lunch and comfortable transfers.",
                ]
                for idx, text in enumerate(highlights, start=1):
                    TripHighlight.objects.create(
                        trip=trip,
                        text=text,
                        position=idx,
                    )
                self.stdout.write(self.style.SUCCESS("Highlights seeded."))

            # --- About ---
            about_body = (
                "Travel west from Cairo along Egypt’s Mediterranean coast to El Alamein, the site of one of the "
                "most significant battles of World War II. This private full-day tour with Kaya Tours takes you to "
                "historic battlefields, memorials, and museums that honor soldiers of many nationalities.\n\n"
                "Your journey begins with a pick-up from your hotel in Cairo at around 07:00 AM in a private, "
                "modern air-conditioned vehicle. On arrival in El Alamein, you will visit the El Alamein Military "
                "Museum, where displays of weapons, tanks, uniforms, and archival materials bring the North African "
                "campaign to life. Exhibits describe the actions of key figures like Montgomery and Rommel and the "
                "events that shaped this crucial turning point in the war.\n\n"
                "You will then continue to the World War II cemeteries, located on a small peninsula overlooking the "
                "sea. These serene, citadel-like cemeteries are the final resting place for Commonwealth, Greek, "
                "Italian, and German soldiers, providing a powerful place for remembrance and reflection.\n\n"
                "After a day of exploring the history and landscapes of El Alamein, you will enjoy a lunch at a local "
                "restaurant before returning comfortably to your hotel in Cairo.\n\n"
                "Kaya Tours ensures a transparent and hassle-free experience, with no hidden surprises or unexpected "
                "costs.\n\n"
                "Note: Pick-up/drop-off from Cairo Airport, Sphinx Airport, New Administrative Capital, New Cairo, "
                "Heliopolis, Badr City, Shorouk, Rehab, Obour, Sheraton Almatar, Sheikh Zayed City, or Madinty City "
                "will be for an additional cost."
            )

            TripAbout.objects.update_or_create(
                trip=trip,
                defaults={"body": about_body},
            )
            self.stdout.write(self.style.SUCCESS("About section seeded."))

            # --- Itinerary (Day 1 with steps) ---
            day, _ = TripItineraryDay.objects.update_or_create(
                trip=trip,
                day_number=1,
                defaults={
                    "title": "El Alamein Day Tour From Cairo",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "07:00",
                    "title": "Hotel pick-up and drive to El Alamein",
                    "description": (
                        "Your Kaya Tours guide will pick you up from your hotel in Cairo at around 07:00 AM in a "
                        "private, modern air-conditioned vehicle. Enjoy a scenic drive west along the Mediterranean "
                        "coast towards El Alamein."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit El Alamein Military Museum",
                    "description": (
                        "Begin your tour at the El Alamein Military Museum, where exhibits showcase weapons, tanks, "
                        "military uniforms, and archival materials from World War II. Learn about the North African "
                        "campaign and the roles of commanders like Montgomery and Rommel through detailed displays and "
                        "narratives."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore World War II cemeteries",
                    "description": (
                        "Continue to the World War II cemeteries located west of the town on a small peninsula "
                        "overlooking the sea. These solemn, citadel-like cemeteries are the final resting place for "
                        "Commonwealth, Greek, Italian, and German soldiers. Spend time reflecting and paying your "
                        "respects in this peaceful setting."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Lunch at a local restaurant",
                    "description": (
                        "Enjoy a lunch meal at a local restaurant in El Alamein, where you can relax and take in the "
                        "coastal atmosphere before the return journey to Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return drive to Cairo",
                    "description": (
                        "After completing your visits and lunch, you will travel back to Cairo in comfort. Your guide "
                        "and driver will drop you off at your hotel, concluding a memorable day exploring El Alamein’s "
                        "World War II heritage."
                    ),
                },
            ]

            for idx, s in enumerate(steps, start=1):
                TripItineraryStep.objects.create(
                    day=day,
                    position=idx,
                    time_label=s["time_label"],
                    title=s["title"],
                    description=s["description"],
                )
            self.stdout.write(self.style.SUCCESS("Itinerary seeded."))

            # --- Inclusions ---
            if created or not trip.inclusions.exists():
                trip.inclusions.all().delete()
                inclusions = [
                    "Pick-up services from and to your hotel in Cairo",
                    "All transfers and tours by private modern air-conditioned vehicle",
                    "Assistance of Kaya Tours representatives during the day tour",
                    "Entrance fees to the mentioned sights in El Alamein",
                    "Bottled water during your trip",
                    "Lunch meal at a local restaurant",
                    "Private tour guide",
                ]
                for idx, text in enumerate(inclusions, start=1):
                    TripInclusion.objects.create(
                        trip=trip,
                        text=text,
                        position=idx,
                    )
                self.stdout.write(self.style.SUCCESS("Inclusions seeded."))

            # --- Exclusions ---
            if created or not trip.exclusions.exists():
                trip.exclusions.all().delete()
                exclusions = [
                    "Any extras not mentioned in the itinerary",
                    "Tipping",
                ]
                for idx, text in enumerate(exclusions, start=1):
                    TripExclusion.objects.create(
                        trip=trip,
                        text=text,
                        position=idx,
                    )
                self.stdout.write(self.style.SUCCESS("Exclusions seeded."))

            # --- Booking option (main tour) ---
            if created or not trip.booking_options.exists():
                trip.booking_options.all().delete()
                TripBookingOption.objects.create(
                    trip=trip,
                    name="Standard El Alamein Day Tour from Cairo",
                    price_per_person=Decimal("234.00"),
                    child_price_per_person=Decimal("49.00"),
                    position=1,
                )
                self.stdout.write(self.style.SUCCESS("Booking option seeded."))

            # --- Trip extras (airport transfer add-ons) ---
            if created or not trip.extras.exists():
                trip.extras.all().delete()
                TripExtra.objects.create(
                    trip=trip,
                    name="One-way transfer from/to Cairo Airport",
                    price=Decimal("25.00"),
                    position=1,
                )
                TripExtra.objects.create(
                    trip=trip,
                    name="Round-trip transfer from/to Cairo Airport",
                    price=Decimal("50.00"),
                    position=2,
                )
                self.stdout.write(self.style.SUCCESS("Extras (airport transfers) seeded."))

            # --- Gallery images ---
            if created or not trip.gallery_images.exists():
                trip.gallery_images.all().delete()

                position = 1
                for filename in GALLERY_FILENAMES:
                    path = _file_path(filename)
                    if not os.path.exists(path):
                        self.stdout.write(
                            self.style.WARNING(
                                f"Gallery image not found on disk, skipping: {path}"
                            )
                        )
                        continue

                    with open(path, "rb") as f:
                        django_file = File(f)
                        gallery_image = TripGalleryImage(
                            trip=trip,
                            caption="El Alamein tour highlights",
                            position=position,
                        )
                        gallery_image.image.save(
                            os.path.basename(path),
                            django_file,
                            save=True,
                        )
                        position += 1

                self.stdout.write(self.style.SUCCESS("Gallery images processed (if files present)."))

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully."))
