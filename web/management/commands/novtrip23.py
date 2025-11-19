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


TRIP_TITLE = "Al Tannoura Egyptian Heritage Dance Troupe Cairo"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/tannora"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "2.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 8)]  # 1.webp ... 7.webp


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
    help = "Seed the 'Al Tannoura Egyptian Heritage Dance Troupe Cairo' trip with images and content."

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
                        "Witness the famous Al Tannoura Egyptian Heritage Dance at Wekalet El Ghoury with Kaya Tours, "
                        "including transfers, show tickets, and a private tour leader."
                    ),
                    duration_days=1,  # ~3 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("60.00"),
                    child_price_per_person=Decimal("15.00"),
                    tour_type_label="Private Night Tour — Al Tannoura Heritage Dance, Cairo",
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
                    "Enjoy an evening at Wekalet El Ghoury, a stunning Mamluk-era arts center in El Azhar area.",
                    "Watch the famous Al Tannoura Egyptian Heritage Dance Troupe perform their whirling dervish show.",
                    "Experience live folkloric music that showcases Egypt’s musical heritage.",
                    "Witness the colorful Tanoura Dance followed by a spiritual whirling dervish performance.",
                    "Relax with hassle-free private transfers and a Kaya Tours tour leader throughout the evening.",
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
                "Spend an unforgettable evening in the heart of Old Cairo with Kaya Tours on this private night tour "
                "to see the Al Tannoura Egyptian Heritage Dance Troupe.\n\n"
                "Your experience begins with pick-up from your hotel at 06:00 PM in a private, air-conditioned "
                "vehicle. You’ll be transferred to Wekalet El Ghoury, an architecturally stunning arts center built "
                "in 1504 A.D. during the Mamluk era, located near El Azhar in Central Cairo.\n\n"
                "Here you’ll attend the famous Tannoura show, one of Egypt’s most remarkable folk musical evenings. "
                "The performance is presented by El Tanoura Troupe for Cultural Heritage, a group that has performed "
                "in more than 30 countries.\n\n"
                "The evening usually begins with a selection of folkloric music performed by local Egyptian musicians, "
                "highlighting the richness of Egypt’s musical traditions. This is followed by the Tanoura Dance show, "
                "featuring colorful spinning skirts and rhythmic movements. The performance culminates in a special "
                "spiritual whirling dervish segment that creates a powerful, immersive atmosphere.\n\n"
                "After the show ends, your Kaya Tours tour leader will escort you back to your vehicle for a comfortable "
                "transfer to your hotel.\n\n"
                "Please ensure you are at the pickup point on time to avoid delays, as your presence is required for "
                "ticket handling and coordination with the tour leader.\n\n"
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
                    "title": "Al Tannoura Egyptian Heritage Dance Troupe Cairo",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "18:00",
                    "title": "Hotel pick-up and transfer to Wekalet El Ghoury",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel at 06:00 PM in a private, "
                        "air-conditioned vehicle. Travel to Wekalet El Ghoury in the El Azhar area of Central Cairo."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Arrival and introduction to the venue",
                    "description": (
                        "Arrive at Wekalet El Ghoury, a beautifully preserved Mamluk-era caravanserai built in 1504 A.D. "
                        "Your tour leader will provide background on the venue and guide you to your seats."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Folkloric music performance",
                    "description": (
                        "Enjoy a live performance of Egyptian folkloric music by local musicians, showcasing Egypt’s "
                        "musical heritage and traditional instruments."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Tanoura Dance and whirling dervish show",
                    "description": (
                        "Watch the Al Tannoura Dance show performed by the Egyptian Heritage Troupe, followed by a "
                        "special spiritual whirling dervish segment that creates a powerful and memorable finale."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel",
                    "description": (
                        "After the show ends, meet your tour leader and return comfortably to your hotel in your "
                        "private, air-conditioned vehicle."
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
                    "Entrance fees and Tannoura show tickets",
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
                    name="Al Tannoura Heritage Dance Show at Wekalet El Ghoury",
                    price_per_person=Decimal("60.00"),
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
                            caption="Al Tannoura Egyptian Heritage Dance at Wekalet El Ghoury",
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
