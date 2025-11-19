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
)


TRIP_TITLE = "Wadi Degla Tour: Hike, Wildlife, and Scenic Desert Views"

# Local filesystem paths on the machine where you run this command.
# These will be read and then saved via Django's storage backend (e.g. Cloudflare R2).
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/wadidg"

CARD_IMAGE_FILENAME = "wadi1.webp"
HERO_IMAGE_FILENAME = "wadi3.webp"
GALLERY_FILENAMES = [f"wadi{i}.webp" for i in range(1, 11)]  # wadi1.webp ... wadi10.webp


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
        # Already has an image, skip unless you want to overwrite.
        stdout.write(
            stdout.style.WARNING(
                f"{field_name} already set for {instance}. Skipping re-upload."
            )
        )
        return

    with open(path, "rb") as f:
        django_file = File(f)
        # Use original filename; storage backend will handle pathing (e.g. trips/cards/, trips/hero/)
        field.save(os.path.basename(path), django_file, save=False)


class Command(BaseCommand):
    help = "Seed the 'Wadi Degla Tour: Hike, Wildlife, and Scenic Desert Views' trip with images."

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
                        "Embark on an adventure in Wadi Degla to discover stunning desert "
                        "landscapes, rare wildlife, and ancient geology with guided hikes "
                        "and a relaxing picnic lunch."
                    ),
                    duration_days=1,  # 5-hour tour mapped to 1 calendar day
                    group_size_max=12,  # tweak if you want
                    base_price_per_person=Decimal("128.00"),
                    child_price_per_person=Decimal("62.00"),
                    tour_type_label="Private Half-Day Tour — Wadi Degla",
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
            # This mimics admin uploads; if images already set, they are left as-is.
            _safe_attach_image(trip, "card_image", CARD_IMAGE_FILENAME, self.stdout)
            _safe_attach_image(trip, "hero_image", HERO_IMAGE_FILENAME, self.stdout)
            # If you want a separate hero_image_mobile later, just add another call here.
            trip.save()
            self.stdout.write(self.style.SUCCESS("Card & hero images processed (if files present)."))

            # --- Highlights ---
            if created or not trip.highlights.exists():
                trip.highlights.all().delete()

                highlights = [
                    "Discover rare wildlife, including gazelles and kestrels.",
                    "Enjoy guided hikes through serene trails of Wadi Degla.",
                    "Learn about ancient geology and fossilized rock formations.",
                    "Relax with a peaceful picnic amid natural surroundings.",
                    "Capture scenic views perfect for nature photography.",
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
                "Embark on a half-day adventure in Wadi Degla, one of Egypt’s most remarkable natural reserves. "
                "Your journey begins with a comfortable pick-up from your hotel in a private, air-conditioned "
                "vehicle, escorted by a professional Kaya Tours representative.\n\n"
                "Upon arrival, you’ll be immersed in the stunning landscapes of Wadi Degla, a breathtaking canyon "
                "that stretches for about 30 kilometers, with limestone cliffs and ancient rock formations that tell "
                "stories from millions of years ago. The reserve is home to rare species of animals and birds, "
                "including gazelles, red foxes, reptiles, and a variety of raptors such as kestrels, owls, and eagles.\n\n"
                "Enjoy guided hikes suitable for different fitness levels, take in the silence and harmony of the "
                "desert, and capture unforgettable nature photography moments. For those seeking extra adventure, "
                "optional activities like mountain biking can be arranged.\n\n"
                "A delicious picnic lunch awaits you amid the serene beauty of Wadi Degla, offering a peaceful break "
                "from the city’s hustle. After a day of exploration, wildlife encounters, and relaxation, you’ll be "
                "comfortably transferred back to your hotel.\n\n"
                "Kaya Tours ensures a hassle-free experience with transparent pricing, professional guides, and "
                "exceptional service for a memorable journey.\n\n"
                "Note: Pick-up/drop-off from Cairo Airport, Sphinx Airport, New Administrative Capital, New Cairo, "
                "Heliopolis, Badr City, Shorouk, Rehab, Obour, Sheraton Almatar, Sheikh Zayed City, or Madinty City "
                "will incur an additional fee."
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
                    "title": "Hike, Wildlife, and Scenic Desert Views",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00–13:30",
                    "title": "Hotel pick-up and transfer to Wadi Degla",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel within the pick-up window "
                        "of 8:00 AM to 1:30 PM in a private, air-conditioned vehicle and escort you to Wadi Degla "
                        "Protected Area."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore Wadi Degla canyon and geology",
                    "description": (
                        "Upon arrival, immerse yourself in the stunning canyon landscapes of Wadi Degla. Marvel at "
                        "limestone cliffs, fossilized rock formations, and the ancient geology that reveals stories "
                        "from millions of years in the past."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Wildlife spotting and guided hikes",
                    "description": (
                        "Enjoy guided hikes along serene trails suitable for different fitness levels. Keep an eye "
                        "out for gazelles, red foxes, reptiles, and a variety of bird species including kestrels, "
                        "owls, and eagles. Your guide will share fascinating insights into the reserve’s unique "
                        "ecosystem and biodiversity."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Picnic lunch and photography time",
                    "description": (
                        "Relax with a picnic lunch amid the quiet desert scenery. Take time to unwind, soak in the "
                        "peaceful surroundings, and capture scenic views and wildlife moments perfect for nature "
                        "photography."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to your hotel",
                    "description": (
                        "After a memorable day of hiking, wildlife encounters, and desert views, you will be "
                        "comfortably transferred back to your hotel in Cairo."
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
                    "Private round-trip transfers from your hotel in a comfortable air-conditioned vehicle",
                    "Professional Kaya Tours representative and local guidance",
                    "Guided hikes inside Wadi Degla Protected Area",
                    "Lunch meal in a Bedouin-style or picnic setting",
                    "Complimentary bottled water during the tour",
                    "Entrance fees to all mentioned sites in the program",
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
                    "Beverages other than bottled water provided",
                ]
                for idx, text in enumerate(exclusions, start=1):
                    TripExclusion.objects.create(
                        trip=trip,
                        text=text,
                        position=idx,
                    )
                self.stdout.write(self.style.SUCCESS("Exclusions seeded."))

            # --- Booking option ---
            if created or not trip.booking_options.exists():
                trip.booking_options.all().delete()
                TripBookingOption.objects.create(
                    trip=trip,
                    name="Standard Wadi Degla Private Tour",
                    price_per_person=Decimal("128.00"),
                    child_price_per_person=Decimal("31.00"),
                    position=1,
                )
                self.stdout.write(self.style.SUCCESS("Booking option seeded."))

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
                            caption="Wadi Degla landscape",
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
