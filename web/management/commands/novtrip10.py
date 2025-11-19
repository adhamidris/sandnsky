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


TRIP_TITLE = "Day Tour To Manial Palace and Cairo Tower"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/manial"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 9)]  # 1.webp ... 8.webp


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
    help = "Seed the 'Day Tour To Manial Palace and Cairo Tower' trip with images and content."

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
                        "Discover Manial Palace, its historic rooms, gardens, and museums, then "
                        "enjoy panoramic views of Cairo from the iconic Cairo Tower."
                    ),
                    duration_days=1,  # 4-hour tour mapped to 1 day
                    group_size_max=12,
                    base_price_per_person=Decimal("164.00"),
                    child_price_per_person=Decimal("37.00"),
                    tour_type_label="Private Half-Day Tour — Manial Palace & Cairo Tower",
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
                    "Explore Manial Palace, home of Prince Mohamed Ali, with its historic rooms and halls.",
                    "Stroll through the unique palace gardens and the so-called ‘Planet’ or botanical garden.",
                    "Visit the Mummified Animal Museum and the palace treasury rooms.",
                    "See the historic Nilometer on Al Roda Island.",
                    "Enjoy a panoramic view of Cairo from the top of Cairo Tower.",
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
                "Discover a different side of Cairo on a half-day private tour with Kaya Tours, combining the "
                "elegant Manial Palace with the iconic Cairo Tower.\n\n"
                "Your experience begins with a pick-up from your hotel at 09:00 AM in a private, air-conditioned "
                "vehicle. Travel to Manial Palace, once the residence of Prince Mohamed Ali, where you will explore "
                "its richly decorated rooms, reception halls, and private quarters. Wander through the distinctive "
                "gardens, often referred to as the ‘Planet’ or botanical garden, and visit the Mummified Animal "
                "Museum, treasury, and meeting rooms.\n\n"
                "You will also stop at the historic Nilometer on Al Roda Island, an ancient structure once used to "
                "measure the Nile’s water levels and forecast the agricultural season.\n\n"
                "Continue to Cairo Tower, one of the most recognizable landmarks in the Egyptian capital. Its partially "
                "open lattice design is inspired by the lotus plant. From the observation deck, enjoy breathtaking "
                "panoramic views over Cairo’s skyline and the Nile.\n\n"
                "After your visit, you will be comfortably transferred back to your hotel. Kaya Tours ensures a "
                "smooth, transparent experience with no hidden costs.\n\n"
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
                    "title": "Day Tour To Manial Palace and Cairo Tower",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "09:00",
                    "title": "Hotel pick-up and transfer to Manial Palace",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel at 09:00 AM in a private, "
                        "air-conditioned vehicle and escort you to Manial Palace."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore Manial Palace & its museums",
                    "description": (
                        "Enjoy an excursion through Manial Palace, where you will visit the home and rooms of "
                        "Mohamed Ali, the unique garden areas, the Mummified Animal Museum, treasury, and meeting "
                        "rooms. Learn about the history of the palace and its royal residents."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit the Nilometer at Al Roda Island",
                    "description": (
                        "Proceed to Al Roda Island to see the historic Nilometer, an ancient structure used to "
                        "measure the Nile’s water level and forecast harvests and taxation in earlier centuries."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Cairo Tower panoramic view",
                    "description": (
                        "Continue to Cairo Tower, one of the most prominent landmarks in Cairo. Its lattice design "
                        "evokes a lotus flower. Take in a beautiful panoramic view of the city and the Nile from the "
                        "observation deck and capture memorable photos."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to your hotel",
                    "description": (
                        "After your visit to Cairo Tower, you will be transferred back to your hotel in comfort, "
                        "concluding your half-day tour."
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
                    "Entrance fees to all mentioned sites",
                    "Lunch meal at a local restaurant",
                    "Bottled water during your trip",
                    "Shopping tours in Cairo (where applicable)",
                    "Private tour leader",
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
                    "Tipping kitty",
                    "Any extras not mentioned in the itinerary",
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
                    name="Standard Manial Palace & Cairo Tower Tour",
                    price_per_person=Decimal("164.00"),
                    child_price_per_person=Decimal("37.00"),
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
                            caption="Manial Palace and Cairo Tower highlights",
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
