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


TRIP_TITLE = "Islamic Cairo Full Day Tour"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/islamic"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 7)]  # 1.webp ... 6.webp


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
    help = "Seed the 'Islamic Cairo Full Day Tour' trip with images and content."

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
                        "Discover Islamic Cairo with Kaya Tours: visit the historic Citadel, "
                        "marvel at the Mosque of Muhammad Ali, and explore the magnificent "
                        "Sultan Hassan and Al-Refai mosques."
                    ),
                    duration_days=1,  # 6 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("163.00"),
                    child_price_per_person=Decimal("38.00"),
                    tour_type_label="Private One-Day Tour — Islamic Cairo Highlights",
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
                    "Discover the historic heart of Islamic Cairo.",
                    "Visit the Saladin Citadel of Cairo, a medieval Islamic fortification.",
                    "Marvel at the Mosque of Muhammad Ali (Alabaster Mosque).",
                    "Explore the Mosque and Madrassa of Sultan Hassan.",
                    "Experience the grandeur of the Al-Refai Mosque.",
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
                "Discover the essence of Islamic Cairo on a private full-day tour with Kaya Tours. "
                "Your journey begins with a comfortable pick-up from your hotel around 08:00 AM or 11:00 AM "
                "in a modern air-conditioned vehicle.\n\n"
                "Travel to the historic Citadel of Cairo, a medieval Islamic fortress constructed by Salah "
                "ad-Din (Saladin) and enhanced by successive Egyptian rulers. Within its walls stands the "
                "renowned Mosque of Muhammad Ali, also known as the Alabaster Mosque, one of Cairo’s most "
                "iconic landmarks. Take in the spiritual atmosphere and admire the mosque’s intricate interior "
                "and commanding views of the city.\n\n"
                "Your tour continues to the Mosque and Madrassa of Sultan Hassan, an architectural masterpiece "
                "whose construction began in 1356 CE, during a period marked by the Black Plague. Today it "
                "remains a symbol of resilience and one of Cairo’s most impressive historic mosques.\n\n"
                "Next, visit the Mosque of Al-Refai, celebrated for its grandeur and innovative design. Together, "
                "Sultan Hassan and Al-Refai form a striking architectural pairing that showcases centuries of "
                "Islamic art and craftsmanship.\n\n"
                "Throughout the tour, you’ll walk through some of Cairo’s most important Islamic sites, guided by "
                "an expert who brings the city’s history and stories to life. At the end of the experience, you "
                "will be comfortably transferred back to your hotel.\n\n"
                "Kaya Tours ensures a transparent and hassle-free experience with no hidden surprises or "
                "unexpected costs.\n\n"
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
                    "title": "Islamic Cairo Full Day Tour",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00–11:00",
                    "title": "Hotel pick-up and transfer to the Citadel",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel around 08:00 AM or 11:00 AM "
                        "in a modern air-conditioned vehicle and escort you to the historic Citadel of Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore the Citadel of Cairo & Mosque of Muhammad Ali",
                    "description": (
                        "Visit the Citadel of Cairo, a medieval Islamic fortification founded by Salah ad-Din "
                        "(Saladin). Explore its courtyards and enjoy panoramic views over the city before visiting "
                        "the Mosque of Muhammad Ali, also known as the Alabaster Mosque, one of Cairo’s most "
                        "beautiful and iconic mosques."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit the Mosque and Madrassa of Sultan Hassan",
                    "description": (
                        "Continue to the Mosque and Madrassa of Sultan Hassan, an architectural masterpiece from "
                        "the 14th century. Learn about its history, design, and how it was constructed during a "
                        "challenging period marked by the Black Plague."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit the Mosque of Al-Refai",
                    "description": (
                        "Next, visit the Mosque of Al-Refai, noted for its grandeur and distinctive architecture. "
                        "Located opposite Sultan Hassan, it forms part of one of Cairo’s most impressive historic "
                        "ensembles."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to your hotel",
                    "description": (
                        "After exploring the main Islamic landmarks of Cairo, you will be transferred back to your "
                        "hotel in comfort, concluding your full-day Islamic Cairo experience."
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
                    "Walking tour of Cairo’s most important Islamic sites",
                    "Lunch at a local restaurant",
                    "Entrance fees to the above-mentioned sites",
                    "Pick-up from your hotel in Cairo and return",
                    "Private tour guide",
                    "Shopping tour in Cairo (where applicable)",
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
                    name="Standard Islamic Cairo Full Day Tour",
                    price_per_person=Decimal("163.00"),
                    child_price_per_person=Decimal("38.00"),
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
                            caption="Islamic Cairo landmarks",
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
