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


TRIP_TITLE = "Tuk Tuk Ride Tour"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/tuk"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 4)]  # 1.webp ... 3.webp


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
    help = "Seed the 'Tuk Tuk Ride Tour' trip with images and content."

    def handle(self, *args, **options):
        try:
            # Nazlet El Samman is by the Pyramids → Giza destination
            destination = Destination.objects.get(name=DestinationName.GIZA)
        except Destination.DoesNotExist:
            raise CommandError(
                "Destination 'Giza' not found. Seed destinations first "
                "or create one with name=DestinationName.GIZA."
            )

        with transaction.atomic():
            trip = Trip.objects.filter(title=TRIP_TITLE).first()
            created = False

            if trip is None:
                trip = Trip(
                    title=TRIP_TITLE,
                    destination=destination,
                    teaser=(
                        "Ride a Tuk Tuk through Nazlet El Samman village near the Pyramids and "
                        "experience authentic local life, markets, and cafés with Kaya Tours."
                    ),
                    duration_days=1,  # ~3 hours mapped to 1 calendar day
                    group_size_max=8,
                    base_price_per_person=Decimal("60.00"),
                    child_price_per_person=Decimal("25.00"),
                    tour_type_label="Private Half-Day Tour — Tuk Tuk Ride in Nazlet El Samman",
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
                    "Visit the quaint Nazlet El Samman Village near the Pyramids of Giza.",
                    "Experience local life on an authentic Tuk Tuk ride.",
                    "Explore local markets and unique neighborhood shops.",
                    "Enjoy a traditional Egyptian café and optional hookah experience.",
                    "Learn about the culture of large, close-knit families in the village.",
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
                "Embark on a cultural journey with Kaya Tours and discover everyday life in Nazlet El Samman Village, "
                "just a short distance from the Pyramids of Giza.\n\n"
                "Pick-up time is flexible and arranged upon request. Your private tour leader will meet you at your "
                "hotel and escort you in a modern, air-conditioned vehicle to the Pyramids area, where the charming "
                "village of Nazlet El Samman is located.\n\n"
                "Upon arrival, hop into a Tuk Tuk and explore narrow streets and local lanes that most visitors never "
                "see. Your guide will take you off the beaten path so you can observe how residents go about their "
                "daily routines—shopping, working, and socializing in a neighborhood right beside one of the world’s "
                "most famous landmarks.\n\n"
                "You’ll wander past local markets and unique shops, and stop at a traditional Egyptian café where you "
                "can enjoy a drink, take memorable photos with locals, and, if you wish, experience the custom of "
                "smoking a shisha (hookah).\n\n"
                "Nazlet El Samman is home to around 20,000 people, many of whom work in tourism as camel drivers, "
                "guides, or owners of papyrus galleries and oriental bazaars. The village is characterized by large, "
                "closely-knit families with well-known local clans. Your guide will share stories and context that "
                "bring the community’s culture and traditions to life.\n\n"
                "After your immersive Tuk Tuk experience and cultural encounters, you’ll be comfortably transferred "
                "back to your hotel.\n\n"
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
                    "title": "Tuk Tuk Ride Tour in Nazlet El Samman",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "Upon request",
                    "title": "Hotel pick-up and transfer to Nazlet El Samman",
                    "description": (
                        "Your Kaya Tours tour leader will pick you up from your hotel at a time arranged in advance "
                        "and transfer you in a private, air-conditioned vehicle to the Pyramids area and Nazlet El "
                        "Samman Village."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Tuk Tuk ride through Nazlet El Samman Village",
                    "description": (
                        "Hop on a Tuk Tuk and ride through the village’s narrow streets and alleys. See how locals live "
                        "day-to-day in the shadow of the Pyramids, passing homes, schools, shops, and small markets."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Local markets, unique shops & village life",
                    "description": (
                        "Explore local markets and unique neighborhood shops. Your guide will take you to places rarely "
                        "visited by tourists, offering authentic glimpses of life in a community closely tied to "
                        "Egypt’s tourism and camel-riding traditions."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Traditional Egyptian café & cultural immersion",
                    "description": (
                        "Stop at a traditional Egyptian café where you can relax, enjoy a drink, take photos with "
                        "locals, and, if you wish, experience the local custom of smoking a hookah (shisha). Learn "
                        "about the culture of large, close-knit families and the main local clans."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel",
                    "description": (
                        "After your Tuk Tuk ride and cultural encounters, you’ll meet your driver again and be "
                        "transferred back to your hotel in comfort."
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
                    name="Standard Tuk Tuk Ride Tour",
                    price_per_person=Decimal("60.00"),
                    child_price_per_person=Decimal("25.00"),
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
                            caption="Tuk Tuk ride and Nazlet El Samman village highlights",
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
