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


TRIP_TITLE = "Half Day Tour to The National Museum of Egyptian Civilization"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/national"

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
    help = "Seed the 'Half Day Tour to The National Museum of Egyptian Civilization' trip with images and content."

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
                        "Discover Egypt’s story at the National Museum of Egyptian Civilization, "
                        "from early history to royal mummies and everyday life."
                    ),
                    duration_days=1,  # 4 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("79.00"),
                    child_price_per_person=Decimal("25.00"),
                    tour_type_label="Private Half-Day Tour — National Museum of Egyptian Civilization",
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
                    "Explore the National Museum of Egyptian Civilization (NMEC) with a private guide.",
                    "Get an overview of Egypt’s history, culture, and civilization in one place.",
                    "See artifacts from different eras: statues, jewelry, pottery, tools, and more.",
                    "Visit the Royal Mummies Hall and learn about ancient beliefs in the afterlife.",
                    "Discover Egyptian mythology, gods, temples, and religious practices.",
                    "Gain insight into daily life in ancient Egypt through household artifacts and clothing.",
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
                "Unravel the story of Egypt across thousands of years on this private half-day tour to the National "
                "Museum of Egyptian Civilization (NMEC) with Kaya Tours.\n\n"
                "Your tour begins with pick-up from your hotel at 08:00 AM in a private, air-conditioned vehicle. "
                "Upon arrival at NMEC, your guide will introduce you to the museum’s unique concept—tracing Egyptian "
                "civilization from prehistoric times through pharaonic, Greco-Roman, Coptic, Islamic, and modern eras.\n\n"
                "Start with an overview of Egyptian history, culture, and civilization, then explore galleries that "
                "showcase statues, jewelry, pottery, tools, and everyday objects from different periods. Admire the "
                "craftsmanship and learn how these artifacts reflect religion, art, power, and daily life.\n\n"
                "A key highlight is the Royal Mummies Hall, where carefully preserved mummies of ancient Egyptian "
                "rulers are displayed in a dedicated, atmospheric setting. Here you’ll learn about burial practices, "
                "beliefs in the afterlife, and the rituals that protected the king’s journey beyond death.\n\n"
                "Your visit also covers exhibits dedicated to mythology and religion, featuring Egyptian gods, temples, "
                "and sacred rituals, as well as sections that illustrate the daily lives of ancient Egyptians—family "
                "structures, clothing, household items, and economic activities.\n\n"
                "Before leaving, you can stop by the museum shop to pick up books, replicas, and souvenirs to remember "
                "your visit. After the tour, you’ll be transferred back to your hotel in comfort.\n\n"
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
                    "title": "Half Day Tour to the National Museum of Egyptian Civilization",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00",
                    "title": "Hotel pick-up and transfer to NMEC",
                    "description": (
                        "Your Kaya Tours guide will pick you up from your hotel at 08:00 AM in a private, "
                        "air-conditioned vehicle and escort you to the National Museum of Egyptian Civilization."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Introduction to Egyptian history & civilization",
                    "description": (
                        "Begin your tour with an overview of Egypt’s long history, culture, and civilization. "
                        "Understand how NMEC is organized to present Egypt’s story across multiple eras."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Galleries of artifacts from different eras",
                    "description": (
                        "Visit galleries displaying statues, jewelry, pottery, tools, and other artifacts from "
                        "different periods of Egyptian history. Learn about their craftsmanship and cultural "
                        "significance with your private guide."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Royal mummies and beliefs in the afterlife",
                    "description": (
                        "Explore exhibits featuring mummies, sarcophagi, and tomb artifacts. Learn about the "
                        "pharaohs, burial practices, funerary rituals, and ancient Egyptian beliefs surrounding "
                        "death and the afterlife."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Mythology, religion, and daily life",
                    "description": (
                        "Discover exhibits dedicated to Egyptian deities, temples, and religious rituals. Gain insight "
                        "into daily life in ancient Egypt—family structure, clothing, household objects, and the "
                        "economy—through curated displays."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Museum shop and return to your hotel",
                    "description": (
                        "Before leaving, you may visit the museum gift shop to purchase books, replicas, and "
                        "souvenirs. After your visit, your guide will escort you back to your hotel in Cairo."
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
                    "Shopping tours in Cairo (where time allows)",
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
                    name="Standard Half Day NMEC Tour",
                    price_per_person=Decimal("79.00"),
                    child_price_per_person=Decimal("25.00"),
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
                            caption="National Museum of Egyptian Civilization highlights",
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
