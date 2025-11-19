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


TRIP_TITLE = "Tour To the museums of Abdeen Palace In Cairo"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/abden"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 6)]  # 1.webp ... 5.webp


def _file_path(filename: str) -> str:
    return os.path.join(IMAGE_BASE_PATH, filename)


def _safe_attach_image(instance, field_name: str, filename: str, stdout=None):
    """
    Attach an image to an ImageField using Django's storage backend
    (e.g., Cloudflare R2) just like the admin upload would.

    If the file does not exist locally, log a warning and skip.
    """
    path = _file_path(filename)
    if not os.path.exists(path):
        message = f"Image not found on disk, skipping {field_name}: {path}"
        if stdout is not None:
            try:
                stdout.write(message + "\n")
            except Exception:
                print(message)
        else:
            print(message)
        return

    field = getattr(instance, field_name)
    if field and getattr(field, "name", None):
        message = f"{field_name} already set for {instance}. Skipping re-upload."
        if stdout is not None:
            try:
                stdout.write(message + "\n")
            except Exception:
                print(message)
        else:
            print(message)
        return

    with open(path, "rb") as f:
        django_file = File(f)
        field.save(os.path.basename(path), django_file, save=False)


class Command(BaseCommand):
    help = "Seed the 'Tour To the museums of Abdeen Palace In Cairo' trip with images and content."

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
                        "Visit Abdeen Palace in the heart of Cairo and explore its museums, "
                        "royal collections, and ornate halls that witnessed key events in modern Egyptian history."
                    ),
                    duration_days=1,  # 3 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("45.00"),
                    child_price_per_person=Decimal("15.00"),
                    tour_type_label="Private Half-Day Tour — Abdeen Palace Museums",
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
                    "Visit Abdeen Palace, one of Cairo’s most remarkable palaces from the Mohamed Ali era.",
                    "Learn how the palace witnessed key events during the late Ottoman and modern periods.",
                    "Explore the lavish interiors designed by Egyptian, Turkish, Italian, and French architects.",
                    "Discover museums displaying royal collections, weapons, decorations, and gifts.",
                    "See ornate halls adorned with paintings, ornaments, and gold-decorated clocks.",
                    "Enjoy a guided tour through the historic Abdeen neighborhood in central Cairo.",
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
                "Visit one of Cairo’s most elegant palaces with Kaya Tours on this private half-day tour to the "
                "museums of Abdeen Palace.\n\n"
                "Your tour begins with pick-up from your hotel at 09:00 AM in a private, air-conditioned vehicle. "
                "Travel to central Cairo, where Abdeen Palace stands above Qasr El-Nil Street in the historic "
                "Abdeen neighborhood.\n\n"
                "Built during the rule of Mohamed Ali’s family and completed under Khedive Ismail, Abdeen Palace is "
                "considered one of the most luxurious and refined palaces in the world in terms of its paintings, "
                "ornaments, and richly decorated halls. Its architecture blends the work of Egyptian, Turkish, "
                "Italian, and French designers.\n\n"
                "Inside, you will visit the palace museums, where collections of weapons, decorations, and diplomatic "
                "gifts are displayed—many of them presented to Egyptian rulers and presidents. The exhibits also "
                "include historical weapons, royal memorabilia, and intricately designed objects that showcase the "
                "palace’s significance as both a royal residence and an administrative center.\n\n"
                "While Abdeen Palace today serves as one of the official residences and workplaces of Egypt’s "
                "president, its ground floor museums remain open to visitors as a window into the country’s royal and "
                "political past.\n\n"
                "After your visit, you will be transferred back to your hotel or another agreed drop-off point. If you "
                "would like to stop for lunch or a snack along the way, your guide can recommend great local spots.\n\n"
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
                    "title": "Half Day Tour to the Museums of Abdeen Palace",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "09:00",
                    "title": "Hotel pick-up and transfer to Abdeen Palace",
                    "description": (
                        "Meet your Kaya Tours guide at your hotel at 09:00 AM. Travel in a private, air-conditioned "
                        "vehicle to the Abdeen neighborhood in central Cairo, where Abdeen Palace is located."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Exterior view and introduction to Abdeen Palace",
                    "description": (
                        "Upon arrival, admire the exterior of Abdeen Palace, built during the reign of Mohamed Ali’s "
                        "dynasty and completed under Khedive Ismail. Hear how the palace became a key stage for "
                        "political events during the late Ottoman and modern periods in Egypt."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Guided visit inside the palace museums",
                    "description": (
                        "Enter the palace museums located on the ground floor. Explore galleries displaying ancient "
                        "and modern weapons, royal decorations, and exquisite diplomatic gifts received by Egypt’s "
                        "leaders and royal family. Learn about the stories behind the collections and the people who "
                        "used or presented them."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore ornate halls, ornaments & details",
                    "description": (
                        "Walk through luxurious halls decorated with paintings, ornaments, and clocks—many trimmed or "
                        "decorated with pure gold. Your guide will highlight key rooms, architectural details, and "
                        "the blend of Egyptian, Turkish, Italian, and French design influences."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel (optional snack stop)",
                    "description": (
                        "After your visit, return to your hotel or preferred drop-off point. If you’d like to stop for "
                        "a snack, coffee, or lunch, your guide can recommend nearby cafés or restaurants along the way."
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
                    "Bottled water during your trip",
                    "All taxes and service charges",
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
                    name="Standard Abdeen Palace Museums Half Day Tour",
                    price_per_person=Decimal("45.00"),
                    child_price_per_person=Decimal("15.00"),
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
                            caption="Abdeen Palace and museum highlights",
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
