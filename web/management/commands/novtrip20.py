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


TRIP_TITLE = 'Mall Misr "Mall of Egypt" Shopping Tour'

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/moe"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 4)]  # 1.webp ... 3.webp


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
    help = 'Seed the "Mall Misr \"Mall of Egypt\" Shopping Tour" trip with images and content.'

    def handle(self, *args, **options):
        try:
            # If you prefer, switch this to DestinationName.GIZA
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
                        "Shop, dine, and play at Mall of Egypt with Kaya Tours — a private transfer and flexible "
                        "shopping time at one of Egypt’s top malls with fashion, dining, cinema and Ski Egypt."
                    ),
                    duration_days=1,  # ~4 hours mapped to 1 calendar day
                    group_size_max=10,
                    base_price_per_person=Decimal("55.00"),
                    child_price_per_person=Decimal("15.00"),
                    tour_type_label='Private Half-Day Tour — "Mall of Egypt" Shopping Experience',
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
                    "Enjoy private transfers to and from Mall of Egypt.",
                    "Shop top local and international brands in one of Egypt’s premier malls.",
                    "Discover high-end fashion, lifestyle, sports, electronics, and home furnishing outlets.",
                    "Relax at Mall of Egypt’s cafés and dining outlets during your free time.",
                    "Choose optional family leisure such as Ski Egypt, VOX Cinemas, or Magic Planet (extra cost).",
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
                'Enjoy a relaxed half-day of shopping and leisure with Kaya Tours on this private tour to *Mall of '
                'Egypt* (Mall Misr).\n\n'
                "Your tour begins with pick-up from your hotel between 11:00 AM and 06:00 PM in a private, "
                "air-conditioned vehicle. You’ll be driven to Mall of Egypt on Al Wahat Road in 6th of October City, "
                "one of Egypt’s largest and most modern shopping destinations.\n\n"
                "Owned and managed by Majid Al Futtaim, Mall of Egypt features a Gross Leasable Area of about "
                "165,000 square meters and houses the best local and international retailers. Browse an unparalleled "
                "selection of high-end fashion brands, department stores, lifestyle, sports, electronics and home "
                "furnishing outlets.\n\n"
                "In between shopping, you can relax at cafés, enjoy fine or casual dining, and explore the mall’s "
                "family leisure offerings, which include Ski Egypt — Africa’s first indoor ski slope — a 21-screen VOX "
                "Cinemas complex, and the Magic Planet family entertainment center (leisure activities and ski tickets "
                "are available at extra cost).\n\n"
                "With direct access to Wahat Road and large parking capacity, Mall of Egypt is designed as a complete "
                "shopping and entertainment hub for visitors of all ages.\n\n"
                "After your free time at the mall, your Kaya Tours driver will meet you at the agreed meeting point and "
                "transfer you back to your hotel.\n\n"
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
                    "title": 'Mall Misr "Mall of Egypt" Shopping Tour',
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "11:00–18:00 (flexible)",
                    "title": "Hotel pick-up and transfer to Mall of Egypt",
                    "description": (
                        "Your Kaya Tours tour leader will pick you up from your hotel between 11:00 AM and 06:00 PM "
                        "in a private, air-conditioned vehicle and drive you to Mall of Egypt on Al Wahat Road "
                        "in 6th of October City."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Arrival and orientation at the mall",
                    "description": (
                        "On arrival, get a quick orientation about the mall’s main areas: high-end fashion, "
                        "department stores, lifestyle and sports outlets, electronics, home furnishings, dining "
                        "options, and the family entertainment zones."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Free time for shopping and leisure",
                    "description": (
                        "Enjoy free time to shop your favorite brands, relax at cafés and restaurants, or explore "
                        "optional attractions such as Ski Egypt, VOX Cinemas, or Magic Planet (tickets and activities "
                        "are not included in the tour price)."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Meet-up and return transfer to your hotel",
                    "description": (
                        "At the agreed time, meet your Kaya Tours tour leader at the designated meeting point inside "
                        "the mall and relax on your private transfer back to your hotel."
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
                    "Ski Egypt tickets and other paid leisure activities",
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
                    name='"Mall of Egypt" Shopping Tour (Transfers Only)',
                    price_per_person=Decimal("55.00"),
                    child_price_per_person=Decimal("15.00"),
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
                            caption="Mall of Egypt shopping and leisure highlights",
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
