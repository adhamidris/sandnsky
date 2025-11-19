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


TRIP_TITLE = "Polar Express Ski Egypt"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/ski"

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
    help = "Seed the 'Polar Express Ski Egypt' trip with images and content."

    def handle(self, *args, **options):
        try:
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
                        "Plunge into the frozen tundra at Ski Egypt, Africa’s first indoor ski resort, "
                        "with snow slopes, an interactive snow cavern, and cozy cafés."
                    ),
                    duration_days=1,  # ~3 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("105.00"),
                    child_price_per_person=Decimal("38.00"),
                    tour_type_label="Private Half-Day Tour — Polar Express Ski Egypt",
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
                    "Plunge into the cold of Ski Egypt, Africa’s first indoor ski resort.",
                    "Hit ski and snowboard runs on real snow inside the mall.",
                    "Relax in alpine-style cafés overlooking the snowy slopes.",
                    "Explore the interactive snow cavern and family-friendly snow activities.",
                    "Enjoy private round-trip transfers and a hassle-free experience.",
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
                "Escape Cairo’s desert heat and step into a winter wonderland at Ski Egypt, Africa’s first and only "
                "indoor ski resort. With Kaya Tours, you’ll enjoy a seamless, private half-day experience, complete "
                "with comfortable transfers and curated time inside the park.\n\n"
                "Your tour begins with a pick-up from your hotel at 12:00 PM in a private, air-conditioned vehicle. "
                "Upon arrival at Ski Egypt, located inside the massive Mall of Egypt complex, you will enter a world "
                "of snow-covered slopes and icy adventures.\n\n"
                "Hit the ski or snowboarding runs, relax in one of the cozy cafés overlooking the snow, or strap on "
                "your boots to explore the interactive snow cavern. A dedicated ski school offers lessons for "
                "beginners, while 7,000 tons of real snow shape the pure white hills and slopes that bring the "
                "mountain experience indoors.\n\n"
                "Whether you want to play in the snow, take photos, or simply enjoy the surreal atmosphere of an "
                "indoor winter landscape, this experience offers fun for all ages.\n\n"
                "Kaya Tours ensures all logistics are handled, including your entrance fees and ski tickets, so you "
                "can focus on enjoying your time in the snow.\n\n"
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
                    "title": "Polar Express Ski Egypt Experience",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "12:00",
                    "title": "Hotel pick-up and transfer to Ski Egypt",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel at 12:00 PM in a private, "
                        "air-conditioned vehicle and transfer you to Ski Egypt at Mall of Egypt."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Indoor snow adventure at Ski Egypt",
                    "description": (
                        "Enter Ski Egypt and plunge into the frozen tundra atmosphere. Hit the ski or snowboard runs, "
                        "relax in the alpine-style cafés, or explore the interactive snow cavern with family-friendly "
                        "snow activities. Enjoy the unique feeling of 7,000 tons of real snow forming white hills and "
                        "slopes inside the complex."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Free time for snow play, photos, and shopping",
                    "description": (
                        "Enjoy time at your own pace to play in the snow, take photos, or explore surrounding shopping "
                        "and cafés in the mall as time allows, depending on your ticket and schedule."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel",
                    "description": (
                        "After your indoor snow adventure, your driver will meet you and transfer you back to your "
                        "hotel in Cairo in comfort."
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
                    "All transfers by private air-conditioned vehicle",
                    "Pick-up services from your hotel and return",
                    "Bottled water during your trip",
                    "Shopping tours in Cairo (where time allows)",
                    "Entrance fees and ski tickets for Ski Egypt (as per program)",
                    "All taxes and service charges",
                    "Private tour leader",
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
                    name="Standard Polar Express Ski Egypt",
                    price_per_person=Decimal("105.00"),
                    child_price_per_person=Decimal("38.00"),
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
                            caption="Ski Egypt indoor snow experience",
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
