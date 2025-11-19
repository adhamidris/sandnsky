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


TRIP_TITLE = "Coptic Cairo and Cave Church Half Day Tour"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/coptic"

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
    help = "Seed the 'Coptic Cairo and Cave Church Half Day Tour' trip with images and content."

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
                        "Visit Coptic Cairo’s historic churches, the Hanging Church and Abu Serga, "
                        "then continue to the Cave Church of Saint Simon in Moqattam."
                    ),
                    duration_days=1,  # ~4 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("94.00"),
                    child_price_per_person=Decimal("27.00"),
                    tour_type_label="Private Half-Day Tour — Coptic Cairo & Cave Church",
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
                    "Discover Coptic Cairo, one of the most important Christian areas in Egypt.",
                    "Visit the Church of Abu Serga (St. Sergius) and the Holy Family cave.",
                    "See the Hanging Church, one of Egypt’s most famous Coptic churches.",
                    "Visit the Church of St. Barbara and the old Jewish Ben Ezra Synagogue.",
                    "Explore the Cave Church of Saint Simon in the Moqattam Hills.",
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
                "Explore the spiritual heart of Christian Cairo and discover one of the city’s most unique landmarks "
                "on this private half-day tour with Kaya Tours.\n\n"
                "Your guide will pick you up from your hotel between 08:00 AM and 11:00 AM in a private, "
                "air-conditioned vehicle and take you to Old Cairo, also known as Christian Coptic Cairo. This area "
                "is among the most important locations traditionally associated with the Holy Family’s journey in "
                "Egypt, where the spiritual impact of their presence is still felt today.\n\n"
                "Visit the Church of Abu Serga (St. Sergius), built above the cave where the Holy Family is believed "
                "to have taken shelter. Explore the surrounding Fort of Babylon area, a pilgrimage destination for "
                "Christians from around the world. You will also visit the Hanging Church, one of Egypt’s most famous "
                "Coptic churches, and the Church of St. Barbara, as well as the old Jewish Ben Ezra Synagogue.\n\n"
                "Your tour continues to the Cave Church of Saint Simon in the Moqattam Hills. Carved into the rock, "
                "this impressive complex includes several cave churches, with the Monastery of St. Simon the Tanner "
                "being the largest. Its amphitheater can accommodate thousands of worshippers and is a striking sight "
                "for visitors interested in seeing something very different in Cairo.\n\n"
                "After your visit, you will be transferred back to your hotel in comfort. Kaya Tours ensures a "
                "seamless, transparent experience with no hidden costs.\n\n"
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
                    "title": "Coptic Cairo and Cave Church Half Day Tour",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00–11:00",
                    "title": "Hotel pick-up and transfer to Coptic Cairo",
                    "description": (
                        "Your Kaya Tours guide will pick you up from your hotel between 08:00 AM and 11:00 AM in a "
                        "private, air-conditioned vehicle and escort you to Old Cairo, also known as Christian Coptic Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit Abu Serga Church and the Holy Family cave",
                    "description": (
                        "Visit the Church of Abu Serga (St. Sergius), built above the cave where the Holy Family is "
                        "believed to have taken refuge during their stay in Egypt. Explore the surrounding Fort of "
                        "Babylon area, an important pilgrimage site for Christians from around the world."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Hanging Church, St. Barbara & Ben Ezra Synagogue",
                    "description": (
                        "Continue to visit the Hanging Church, one of Egypt’s most famous Coptic churches, then see "
                        "the Church of St. Barbara and the historic Ben Ezra Synagogue, each reflecting centuries of "
                        "religious heritage in Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Cave Church of Saint Simon in Moqattam",
                    "description": (
                        "Head to the Moqattam Hills to visit the Cave Church of Saint Simon and the surrounding cave "
                        "church complex. See the impressive amphitheater and rock-carved worship spaces that make this "
                        "site truly unique."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel",
                    "description": (
                        "After completing your visits in Coptic Cairo and the Cave Church, you will be transferred "
                        "back to your hotel in Cairo in comfort."
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
                    name="Standard Coptic Cairo & Cave Church Half Day Tour",
                    price_per_person=Decimal("94.00"),
                    child_price_per_person=Decimal("27.00"),
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
                            caption="Coptic Cairo and Cave Church highlights",
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
