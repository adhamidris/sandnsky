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


TRIP_TITLE = "Pharaonic Village Tour"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/pharonicv"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 7)]  # 1.webp ... 6.webp


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
    help = "Seed the 'Pharaonic Village Tour' trip with images and content."

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
                        "Visit the Pharaonic Village in Cairo and experience daily life in ancient Egypt "
                        "through live reenactments, replicas, and immersive exhibits."
                    ),
                    duration_days=1,  # ~3 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("95.00"),
                    child_price_per_person=Decimal("30.00"),
                    tour_type_label="Private Half-Day Tour — Pharaonic Village",
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
                    "Visit the Pharaonic Village in Cairo, a living museum of ancient Egypt.",
                    "See reenactments of daily life in the time of the Pharaohs.",
                    "Sail along canals that recreate the sights and sounds of ancient Egypt.",
                    "Learn about ancient Egyptian crafts, agriculture, religion, and daily routines.",
                    "Enjoy private transfers and guiding with Kaya Tours.",
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
                "Step back in time and experience ancient Egypt brought to life at the Pharaonic Village on this "
                "private half-day tour with Kaya Tours.\n\n"
                "Your tour begins with pick-up from your hotel between 08:00 AM and 01:00 PM in a private, "
                "air-conditioned vehicle. Travel to the Pharaonic Village, an immersive open-air museum where "
                "carefully reconstructed scenes and live actors recreate the daily life of the Pharaohs.\n\n"
                "As you sail along the canals that circuit the island, you are surrounded by scenes from the Egypt of "
                "history and legend: farmers working the fields, craftsmen at their trades, priests performing rituals, "
                "and more. The sounds, costumes, and settings give you the feeling of having traveled through time to "
                "a distant and glorious past.\n\n"
                "Inside the village, you can explore exhibits, replicas, and educational displays that explain ancient "
                "Egyptian customs, beliefs, and daily routines in an engaging and accessible way — ideal for families, "
                "students of history, and anyone with a passion for Egyptology.\n\n"
                "After you complete your visit, you will be transferred back to your hotel in Cairo. Kaya Tours ensures "
                "a smooth and hassle-free experience with transparent inclusions.\n\n"
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
                    "title": "Pharaonic Village Half Day Tour",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00–13:00",
                    "title": "Hotel pick-up and transfer to the Pharaonic Village",
                    "description": (
                        "Your Kaya Tours guide will pick you up from your hotel between 08:00 AM and 01:00 PM in a "
                        "private, air-conditioned vehicle and escort you to the Pharaonic Village in Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Canal cruise and introduction to ancient Egypt",
                    "description": (
                        "Begin your visit by sailing along the canals that circuit the island. As you glide through "
                        "the water, live reenactments and detailed sets immerse you in the sights and sounds of "
                        "ancient Egypt, from daily village life to royal ceremonies."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore exhibits and reconstructions of pharaonic life",
                    "description": (
                        "Walk through the village’s exhibits to learn more about ancient Egyptian agriculture, "
                        "crafts, religion, and daily routines. See how people lived, worked, and worshipped, and "
                        "gain a deeper understanding of the civilization behind the monuments."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Free time and return to your hotel",
                    "description": (
                        "Enjoy some free time to explore additional areas or shops on-site, then meet your guide and "
                        "driver for the return transfer back to your hotel in Cairo."
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
                    "Lunch at a local restaurant or on-site (as per program)",
                    "Entrance fees to the Pharaonic Village",
                    "Private tour guide",
                    "All taxes and service charges",
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
                    name="Standard Pharaonic Village Half Day Tour",
                    price_per_person=Decimal("95.00"),
                    child_price_per_person=Decimal("30.00"),
                    position=1,
                )
                self.stdout.write(self.style.SUCCESS("Booking option seeded."))

            # --- Trip extras (add-ons) ---
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
                TripExtra.objects.create(
                    trip=trip,
                    name="Sound and Light Show at Pyramids",
                    price=Decimal("70.00"),
                    position=3,
                )
                self.stdout.write(self.style.SUCCESS("Extras (add-ons) seeded."))

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
                            caption="Pharaonic Village Cairo highlights",
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
