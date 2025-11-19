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


TRIP_TITLE = "Tour to Cairo Citadel, Khan El-Khalil and Coptic Cairo"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/cita"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 10)]  # 1.webp ... 9.webp


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
    help = "Seed the 'Tour to Cairo Citadel, Khan El-Khalil and Coptic Cairo' trip with images and content."

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
                        "Visit the Citadel of Salah El Din & the Alabaster Mosque, "
                        "explore Khan El Khalili bazaar, and discover Coptic Cairo’s "
                        "historic churches and synagogue on a private full-day tour."
                    ),
                    duration_days=1,  # 8 hours mapped to 1 day
                    group_size_max=12,
                    base_price_per_person=Decimal("169.00"),
                    child_price_per_person=Decimal("40.00"),
                    tour_type_label="Private One-Day Tour — Citadel, Khan El Khalili & Coptic Cairo",
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
                    "Visit the Saladin Citadel of Cairo and its iconic Alabaster Mosque of Muhammad Ali.",
                    "Stroll through Khan El Khalili Bazaar, Cairo’s historic marketplace.",
                    "Explore Coptic Cairo and its ancient churches and synagogue.",
                    "Marvel at the Hanging Church, one of Egypt’s most famous Coptic churches.",
                    "Visit Ben Ezra Synagogue, St. Barbara Church, and Abu Serga Church.",
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
                "Discover Cairo’s layered history on a private full-day tour that combines the majestic Citadel, "
                "the bustling lanes of Khan El Khalili, and the spiritual heart of Coptic Cairo.\n\n"
                "Your day begins with a pick-up from your hotel in a private air-conditioned vehicle, accompanied "
                "by a professional Kaya Tours representative. Head first to the Citadel of Salah El Din, where you "
                "will visit the stunning Mohamed Ali Alabaster Mosque and enjoy panoramic views over Cairo.\n\n"
                "Afterwards, savor lunch at a local restaurant before continuing to Islamic Cairo and the famous "
                "Khan El Khalili Bazaar. Wander through the historic market, browse for souvenirs, and soak up the "
                "atmosphere of one of the oldest bazaars in the Middle East.\n\n"
                "The tour then moves to Coptic Cairo, where you will explore some of Egypt’s most important Christian "
                "and Jewish heritage sites, including the Hanging Church, Ben Ezra Synagogue, the Church of St. "
                "Barbara, and the Church of Abu Serga.\n\n"
                "Kaya Tours ensures a seamless and comfortable experience throughout the day, with private transfers, "
                "expert guiding, and transparent pricing.\n\n"
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
                    "title": "Citadel, Khan El Khalili & Coptic Cairo Day Tour",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00–10:00",
                    "title": "Hotel pick-up and transfer to the Citadel",
                    "description": (
                        "Your Kaya Tours expert representative will pick you up from your hotel between 8:00 AM and "
                        "10:00 AM in a private air-conditioned vehicle and escort you to the Citadel of Salah El Din."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit the Citadel & Mohamed Ali Alabaster Mosque",
                    "description": (
                        "Explore the majestic Citadel, a medieval Islamic fortification, and visit the impressive "
                        "Mohamed Ali Alabaster Mosque. Enjoy panoramic views over Cairo and learn about the Citadel’s "
                        "role in Egypt’s history."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Lunch at a local restaurant",
                    "description": (
                        "Savor a delicious lunch at a local restaurant, taking a break before continuing your journey "
                        "through the historic quarters of Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Khan El Khalili Bazaar",
                    "description": (
                        "Head to the heart of Islamic Cairo and wander through Khan El Khalili Bazaar. Lose yourself "
                        "in its narrow alleys filled with shops selling spices, perfumes, jewelry, handicrafts, and "
                        "souvenirs in a vibrant, historic setting."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Coptic Cairo: churches and synagogue",
                    "description": (
                        "Continue to Coptic Cairo to explore the Hanging Church, Ben Ezra Synagogue, Church of St. "
                        "Barbara, and Church of Abu Serga. Learn about Egypt’s early Christian and Jewish heritage "
                        "and the stories associated with these sacred sites."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to your hotel",
                    "description": (
                        "At the end of the tour, your guide and driver will transfer you back to your hotel in Cairo "
                        "in comfort."
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
                    "Round-trip transfers from/to your destination in a private air-conditioned vehicle",
                    "Entrance fees to all mentioned sites in the program",
                    "Lunch at a local restaurant",
                    "Shopping tour in Cairo (Khan El Khalili Bazaar)",
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
                    name="Standard Citadel, Khan El Khalili & Coptic Cairo Tour",
                    price_per_person=Decimal("169.00"),
                    child_price_per_person=Decimal("40.00"),
                    position=1,
                )
                self.stdout.write(self.style.SUCCESS("Booking option seeded."))

            # --- Trip extras (add-ons) ---
            if created or not trip.extras.exists():
                trip.extras.all().delete()
                TripExtra.objects.create(
                    trip=trip,
                    name="Sound and Light Show at Pyramids",
                    price=Decimal("70.00"),
                    position=1,
                )
                TripExtra.objects.create(
                    trip=trip,
                    name="One-way transfer from/to Cairo Airport",
                    price=Decimal("25.00"),
                    position=2,
                )
                TripExtra.objects.create(
                    trip=trip,
                    name="Round-trip transfer from/to Cairo Airport",
                    price=Decimal("50.00"),
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
                            caption="Citadel, Khan El Khalili & Coptic Cairo highlights",
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
