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


TRIP_TITLE = "Day Trip To Egyptian Museum, Old Cairo"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/oldcair"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 9)]  # 1.webp ... 8.webp


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
    help = "Seed the 'Day Trip To Egyptian Museum, Old Cairo' trip with images and content."

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
                        "Spend the day exploring the Egyptian Museum and Old Cairo with Kaya Tours, "
                        "including Coptic landmarks like the Hanging Church and Abu Serga."
                    ),
                    duration_days=1,  # ~6 hours mapped to 1 day
                    group_size_max=12,
                    base_price_per_person=Decimal("162.00"),
                    child_price_per_person=Decimal("38.00"),
                    tour_type_label="Private One-Day Tour — Egyptian Museum & Old Cairo",
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
            # hero_image_mobile left blank.
            trip.save()
            self.stdout.write(self.style.SUCCESS("Card & hero images processed (if files present)."))

            # --- Highlights ---
            if created or not trip.highlights.exists():
                trip.highlights.all().delete()

                highlights = [
                    "Visit the Egyptian Museum with its vast collection of Pharaonic antiquities.",
                    "Discover over 5,000 years of ancient Egyptian art and history.",
                    "Explore Coptic Cairo and its historic churches.",
                    "See the Hanging Church, one of Egypt’s most famous Coptic churches.",
                    "Visit Abu Serga Church and the Holy Family cave.",
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
                "Spend an unforgettable day exploring the treasures of ancient and Coptic Cairo on a private tour with "
                "Kaya Tours. Your experience begins with a pick-up from your hotel between 08:00 AM and 10:00 AM in a "
                "private, air-conditioned vehicle.\n\n"
                "Start with a visit to the Egyptian Museum, home to one of the world’s largest and most precious "
                "collections of Egyptian antiquities. Discover artifacts spanning over 5,000 years of history, with "
                "more than 250,000 genuine pieces on display, showcasing the rich legacy of the Pharaohs.\n\n"
                "After immersing yourself in ancient Egypt, continue to Old Cairo and Coptic Cairo. Visit the famous "
                "Hanging Church, one of the oldest and most significant Coptic churches in Egypt, built above the "
                "gatehouse of a Roman fortress.\n\n"
                "You will also visit Abu Serga (Saints Sergius and Bacchus Church), where you can see the Holy Cave "
                "believed to have sheltered the Holy Family during their journey through Egypt.\n\n"
                "Your day includes lunch at a local restaurant, bottled water, and time for a brief shopping stop in "
                "Cairo before you are comfortably transferred back to your hotel.\n\n"
                "Kaya Tours ensures a transparent and hassle-free experience, with no hidden surprises or unexpected "
                "costs.\n\n"
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
                    "title": "Day Trip To Egyptian Museum & Old Cairo",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00–10:00",
                    "title": "Hotel pick-up and transfer to Egyptian Museum",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel between 08:00 AM and "
                        "10:00 AM in a private, air-conditioned vehicle and escort you to the Egyptian Museum."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Guided visit of the Egyptian Museum",
                    "description": (
                        "Explore the Egyptian Museum, which houses an unparalleled collection of artifacts from the "
                        "Pharaonic period. See a rare collection representing over 5,000 years of art and history, "
                        "with more than 250,000 genuine antiquities on display."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit Old Cairo & the Hanging Church",
                    "description": (
                        "Proceed to Old Cairo and Coptic Cairo to visit the Hanging Church, one of Egypt’s most famous "
                        "Coptic churches, built above the remains of a Roman fortress gatehouse."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Abu Serga Church & Holy Family Cave",
                    "description": (
                        "Visit Abu Serga Church (Saints Sergius and Bacchus), where you will see the Holy Cave believed "
                        "to have sheltered the Holy Family during their journey in Egypt."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Lunch and brief shopping stop",
                    "description": (
                        "Enjoy a lunch meal at a local restaurant and take some time for a brief shopping tour in Cairo "
                        "before concluding your visit."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel",
                    "description": (
                        "After completing your tour of the Egyptian Museum and Old Cairo, you will be transferred back "
                        "to your hotel in comfort."
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
                    "Shopping tour in Cairo",
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
                    name="Standard Day Trip to Egyptian Museum & Old Cairo",
                    price_per_person=Decimal("162.00"),
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
                            caption="Egyptian Museum and Old Cairo highlights",
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
