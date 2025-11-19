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


TRIP_TITLE = "Sunset at Cairo Tower With Dinner"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/sunset"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 11)]  # 1.webp ... 10.webp


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
    help = "Seed the 'Sunset at Cairo Tower With Dinner' trip with images and content."

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
                        "Watch the sun set over Cairo and the Nile from Cairo Tower, then enjoy dinner "
                        "at the revolving restaurant with unforgettable panoramic views."
                    ),
                    duration_days=1,  # 3 hours mapped to 1 calendar day
                    group_size_max=8,
                    base_price_per_person=Decimal("110.00"),
                    child_price_per_person=Decimal("35.00"),
                    tour_type_label="Private Night Tour — Sunset at Cairo Tower With Dinner",
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
                    "Enjoy a private evening tour to Cairo Tower with Kaya Tours.",
                    "Take in panoramic views of Cairo, Giza, and the Nile at sunset.",
                    "See the Pyramids of Giza from above on a clear day or evening.",
                    "Dine at the revolving restaurant with a 360° view of the city.",
                    "Perfect family-friendly outing with telescopes and kids’ playground available.",
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
                "If you’re looking for the perfect spot to see Cairo and Giza from above, this private sunset tour "
                "to Cairo Tower with Kaya Tours is made for you.\n\n"
                "Your evening begins with pick-up from your hotel at 4:00 PM in a private, air-conditioned vehicle. "
                "You’ll be driven to Cairo Tower, one of the city’s most iconic landmarks, standing at around "
                "187 meters tall on Gezira Island in the Nile.\n\n"
                "After arriving, take the elevator up to the observation deck and watch as the city shifts from day to "
                "golden hour. From the top, you can enjoy sweeping views of the Nile River, downtown Cairo, and, on a "
                "clear day, the Pyramids of Giza in the distance. The late afternoon timing lets you avoid the midday "
                "heat while experiencing the magical transition into dusk.\n\n"
                "To complete the experience, you’ll enjoy dinner (or lunch, depending on timing) at the tower’s "
                "revolving restaurant, which slowly rotates to give you a full 360-degree view of the city as you dine. "
                "Affordable telescopes and a kids’ playground make Cairo Tower an ideal outing for couples, friends, "
                "and families alike.\n\n"
                "After your meal and time enjoying the view, your Kaya Tours tour leader will accompany you back down "
                "and transfer you to your hotel in comfort.\n\n"
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
                    "title": "Sunset at Cairo Tower With Dinner",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "16:00",
                    "title": "Hotel pick-up and transfer to Cairo Tower",
                    "description": (
                        "Your Kaya Tours tour leader will pick you up from your hotel at 4:00 PM in a private, "
                        "air-conditioned vehicle and escort you to Cairo Tower on Gezira Island."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Ascend Cairo Tower and enjoy sunset views",
                    "description": (
                        "Take the elevator up to the observation deck and enjoy panoramic views of Cairo, the Nile, "
                        "and Giza as the sun begins to set. Use available telescopes (optional extra) to spot key "
                        "landmarks across the city."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Dinner at the revolving restaurant",
                    "description": (
                        "Enhance your visit with a included dinner or lunch at Cairo Tower’s revolving restaurant. "
                        "Relax as the restaurant slowly turns, offering a 360-degree city view while you dine."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Free time & hotel drop-off",
                    "description": (
                        "After dinner, enjoy a little free time to take final photos or let children enjoy the "
                        "playground, then meet your tour leader for your transfer back to the hotel."
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
                    "Pick-up services from your hotel and return",
                    "All transfers by private air-conditioned vehicle",
                    "Entrance fees to all mentioned sites (Cairo Tower as per program)",
                    "Bottled water on board the vehicle during the tour",
                    "Dinner or lunch at Cairo Tower",
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
                    "Any extras not mentioned in the itinerary",
                    "Tipping",
                    "Drinks not explicitly included with the meal",
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
                    name="Sunset Cairo Tower Tour With Dinner",
                    price_per_person=Decimal("110.00"),
                    child_price_per_person=Decimal("35.00"),
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
                            caption="Sunset views and Cairo Tower highlights",
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
