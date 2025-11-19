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


TRIP_TITLE = "Egyptian House Dinner"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/dinner"

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
    help = "Seed the 'Egyptian House Dinner' trip with images and content."

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
                        "Share a home-cooked meal with an Egyptian family, learn recipes, and experience "
                        "the warmth and traditions of a real Egyptian house."
                    ),
                    duration_days=1,  # ~4 hours mapped to 1 calendar day
                    group_size_max=8,
                    base_price_per_person=Decimal("100.00"),
                    child_price_per_person=Decimal("30.00"),
                    tour_type_label="Private Half-Day Tour — Egyptian House Dinner Experience",
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
                    "Have dinner in a real Egyptian house with a local family.",
                    "Share in the cooking and learn traditional Egyptian recipes.",
                    "Discover ingredients and spices used in everyday Egyptian cuisine.",
                    "Experience authentic hospitality and the warmth of an Egyptian home.",
                    "Learn about Egyptian customs around serving and sharing meals.",
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
                "Spend an unforgettable evening with an Egyptian family and experience the heart of local life through "
                "food, tradition, and hospitality.\n\n"
                "Your Kaya Tours tour leader will pick you up from your hotel between 12:00 PM and 02:00 PM in a "
                "private, air-conditioned vehicle and take you to a real Egyptian home, where you will be welcomed "
                "as a guest rather than a tourist.\n\n"
                "You’ll join the family in their kitchen to learn about the ingredients, spices, and recipes behind "
                "beloved Egyptian dishes. Depending on the day and season, you may help prepare salads, main dishes, "
                "and sides, discovering how meals are built from freshly ripened fruits and vegetables and seasoned "
                "with aromatic herbs and spices.\n\n"
                "Once the food is ready, you’ll sit down together for a home-cooked meal, getting acquainted with "
                "Egyptian customs of serving and sharing dishes. Your hosts—families connected to Kaya Tours’ guides "
                "and licensed by the Ministry of Tourism—will be happy to explain traditions, answer questions, and "
                "share stories about daily life in Egypt.\n\n"
                "After dinner, enjoy fruit, desserts, and hot or cold beverages while relaxing and chatting with the "
                "family. This is a rare chance to experience Egyptian culture from the inside and feel the warmth and "
                "generosity of an Egyptian home.\n\n"
                "At the end of the experience, you’ll be transferred back to your hotel in comfort.\n\n"
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
                    "title": "Egyptian House Dinner with Local Family",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "12:00–14:00",
                    "title": "Hotel pick-up and transfer to Egyptian home",
                    "description": (
                        "Your Kaya Tours tour leader will pick you up from your hotel between 12:00 PM and 02:00 PM "
                        "and transfer you in a private, air-conditioned vehicle to a local Egyptian family’s home."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Meet the family & learn about the menu",
                    "description": (
                        "Meet your host family, get introduced to the dishes you’ll be preparing and enjoying together, "
                        "and learn about the ingredients and spices used in traditional Egyptian cuisine."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Cooking experience in a real Egyptian kitchen",
                    "description": (
                        "Join the family in the kitchen to help with preparation—washing, chopping, stirring, and "
                        "seasoning. Learn recipes and techniques passed down through generations and ask questions "
                        "about daily life and food traditions."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Shared Egyptian home-cooked dinner",
                    "description": (
                        "Sit down with the family to enjoy a full, home-cooked meal. Discover how dishes are served, "
                        "shared, and enjoyed in an Egyptian household, and experience the warmth and hospitality of "
                        "your hosts."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Dessert, drinks & return to hotel",
                    "description": (
                        "After dinner, enjoy fruit, desserts, and hot or cold beverages while chatting with the "
                        "family. When your visit concludes, your tour leader will escort you back to your hotel."
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
                    "Home-cooked dinner with an Egyptian family",
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
                    name="Standard Egyptian House Dinner Experience",
                    price_per_person=Decimal("100.00"),
                    child_price_per_person=Decimal("30.00"),
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
                            caption="Egyptian home dinner experience highlights",
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
