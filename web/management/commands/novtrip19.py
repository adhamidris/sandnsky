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


TRIP_TITLE = "Cairo Kayaking Tour on The Nile River"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/kayaking"

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
    help = "Seed the 'Cairo Kayaking Tour on The Nile River' trip with images and content."

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
                        "Kayak along the Nile in Cairo on a guided adventure, with flexible start times "
                        "from morning to afternoon — perfect for beginners and experienced paddlers alike."
                    ),
                    duration_days=1,  # ~4 hours mapped to 1 calendar day
                    group_size_max=10,
                    base_price_per_person=Decimal("60.00"),
                    child_price_per_person=Decimal("20.00"),
                    tour_type_label="Private Adventure Tour — Kayaking on the Nile in Cairo",
                    is_service=False,
                    allow_children=True,
                    allow_infants=False,
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
                    "Enjoy a guided kayaking experience on the Nile in Cairo.",
                    "Flexible start times from 07:00 AM to 03:00 PM.",
                    "Suitable for beginners and experienced kayakers — briefing and support included.",
                    "Take in unique riverside views of Cairo away from the city’s traffic.",
                    "Join a Nile-side kayak club and paddle with professional supervision.",
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
                "Experience Cairo from a completely different angle on this private kayaking tour on the Nile with "
                "Kaya Tours.\n\n"
                "Your adventure begins with pick-up from your hotel anywhere in Cairo or Giza between 07:00 AM and "
                "03:00 PM in a private, air-conditioned vehicle. You’ll be transferred to a dedicated kayak club "
                "on the Nile.\n\n"
                "Upon arrival, your instructor will give you a safety and technique briefing of about 15 minutes, "
                "covering paddling basics, balance, and how to handle the kayak on the water. Even if you’ve never "
                "kayaked before, you’re welcome to join — beginners receive extra guidance and are escorted by one of "
                "the club’s trainers in their own kayak.\n\n"
                "Once you’re ready, head out onto the Nile for an unforgettable paddling session of around 3 hours. "
                "Glide along the river, enjoy the calm water, and take in unique views of Cairo’s skyline, bridges, "
                "and riverside landmarks far from the city’s usual noise and traffic.\n\n"
                "Your guide and kayak trainers will stay close, ensuring a safe and enjoyable experience while you "
                "soak up the scenery, take photos, and enjoy the cool breeze on the water.\n\n"
                "After your session, you’ll return to the club, then be transferred back to your hotel in comfort.\n\n"
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
                    "title": "Cairo Kayaking Tour on the Nile River",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "07:00–15:00 (flexible)",
                    "title": "Hotel pick-up from Cairo or Giza",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel anywhere in Cairo or Giza "
                        "between 07:00 AM and 03:00 PM and transfer you in a private, air-conditioned vehicle to "
                        "the Nile-side kayak club."
                    ),
                },
                {
                    "time_label": "15 minutes",
                    "title": "Briefing session at the kayak club",
                    "description": (
                        "Upon arrival, you’ll receive a safety and technique briefing of about 15 minutes. Instructors "
                        "will explain paddling basics, how to balance the kayak, and what to expect on the water. "
                        "Beginners are especially supported and can paddle under close supervision."
                    ),
                },
                {
                    "time_label": "Up to 3 hours",
                    "title": "Kayaking tour on the Nile River",
                    "description": (
                        "Start your kayaking tour on the Nile and enjoy a unique perspective of Cairo from the water. "
                        "Paddle along the river, take in the skyline, bridges, and riverside life, and enjoy the calm "
                        "away from the city traffic. Trainers accompany beginners in separate kayaks for extra safety."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to the club and hotel drop-off",
                    "description": (
                        "After your kayaking session, return to the club to rest and freshen up. Then meet your driver "
                        "again for a comfortable transfer back to your hotel."
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
                    "Entrance/usage fees for the kayak club or facilities as per program",
                    "Bottled water during your trip",
                    "Approximately 3-hour kayaking tour on the Nile",
                    "Private tour leader / escort",
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
                    name="Standard Nile Kayaking Tour (3 Hours)",
                    price_per_person=Decimal("60.00"),
                    child_price_per_person=Decimal("20.00"),
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
                            caption="Kayaking on the Nile in Cairo — tour highlights",
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
