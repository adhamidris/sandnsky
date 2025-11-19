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


TRIP_TITLE = "Tour To El Moez Street, Bayt Al-Suhaymi and Al Azhar Park With Lunch"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/moez"

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
    help = (
        "Seed the 'Tour To El Moez Street, Bayt Al-Suhaymi and Al Azhar Park With Lunch' "
        "trip with images and content."
    )

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
                        "Explore El Moez Street, Bayt Al-Suhaymi, traditional crafts streets, "
                        "and enjoy a scenic lunch at Al Azhar Park with panoramic views of Cairo."
                    ),
                    duration_days=1,  # ~6 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("99.00"),
                    child_price_per_person=Decimal("30.00"),
                    tour_type_label="Private Half-Day Tour — El Moez, Bayt Al-Suhaymi & Al Azhar Park",
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
                    "Explore El Moez Le Din Allah Street, one of Egypt’s oldest and most beautiful Islamic streets.",
                    "Visit historic gates and monuments such as Bab El Fetouh and Bab El Nasr.",
                    "Discover architectural gems in El Darb El Asfar, including Barqouq Mosque & School and El Aqmar Mosque.",
                    "Step inside the 350-year-old Bayt Al-Suhaymi, a preserved Ottoman-era house.",
                    "Walk along Al Darb Al Ahmar Street and see traditional trades, crafts, and markets.",
                    "Relax and enjoy lunch with panoramic views of Cairo at Al Azhar Park.",
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
                "Discover the magic of medieval Cairo on this private half-day tour with Kaya Tours, combining historic "
                "Islamic streets, traditional architecture, and one of the city’s most beautiful parks.\n\n"
                "Your expert Kaya Tours guide will meet you at your hotel between 10:00 AM and 01:00 PM to begin your "
                "journey. Start along El Moez Le Din Allah Street, one of Cairo’s oldest and most important historic "
                "streets, lined with mosques, schools, and monuments from different Islamic eras. See landmarks such "
                "as Bab El Fetouh and Bab El Nasr, impressive gates that once guarded the city.\n\n"
                "Continue into El Darb El Asfar, in the heart of Islamic Cairo, where you will discover architectural "
                "gems including Barqouq Mosque & School in Nahassen, El Aqmar Mosque, the Mosque of El Saleh Tala, "
                "and monuments linked to the Qalawoon complex.\n\n"
                "Next, step into the 350-year-old Bayt Al-Suhaymi, a beautifully preserved Ottoman-era house that "
                "offers a glimpse into traditional Cairene domestic life. Then stroll along Al Darb Al Ahmar Street, "
                "a vibrant hub of traditional trades and crafts. Pass through Suq al-Surugiyyiah, the Saddle Makers "
                "Market, known for exquisite leatherwork and handmade goods.\n\n"
                "Your tour continues along Al Moez Street until you arrive at Al Azhar Park, one of Cairo’s highest "
                "and most scenic viewpoints. Nestled in the heart of historic Cairo, the park offers sweeping "
                "panoramic views of the old city skyline. Enjoy a relaxed lunch at a local restaurant in or near the "
                "park, taking in the stunning vistas.\n\n"
                "At the end of your experience, you will be escorted back to your hotel. Kaya Tours ensures transparent "
                "pricing and a hassle-free, memorable day in Islamic Cairo.\n\n"
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
                    "title": "El Moez Street, Bayt Al-Suhaymi & Al Azhar Park Tour",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "10:00–13:00",
                    "title": "Hotel pick-up and transfer to El Moez Street",
                    "description": (
                        "Your Kaya Tours guide will meet you at your hotel between 10:00 AM and 01:00 PM and escort "
                        "you in a private, air-conditioned vehicle to El Moez Le Din Allah Street."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Walk along El Moez Street and historic gates",
                    "description": (
                        "Stroll along El Moez Street, one of Cairo’s most important historic streets, lined with "
                        "monuments from multiple Islamic eras. See landmarks like Bab El Fetouh and Bab El Nasr and "
                        "other notable mosques and complexes along the way."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Explore El Darb El Asfar & key mosques",
                    "description": (
                        "Continue to El Darb El Asfar in the heart of Islamic Cairo. Discover architectural treasures "
                        "including Barqouq Mosque & School, El Aqmar Mosque, the Mosque of El Saleh Tala, and other "
                        "historic buildings associated with the Qalawoon complex."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit Bayt Al-Suhaymi & traditional craft streets",
                    "description": (
                        "Step inside Bayt Al-Suhaymi, a 350-year-old Ottoman-era house, and experience traditional "
                        "Cairene architecture and interior design. Walk along Al Darb Al Ahmar Street and see "
                        "traditional crafts and markets, including Suq al-Surugiyyiah, the Saddle Makers Market."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Al Azhar Park & lunch with panoramic views",
                    "description": (
                        "Head to Al Azhar Park, one of Cairo’s most beautiful green spaces and viewpoints. Enjoy a "
                        "relaxing lunch at a local restaurant in or near the park, taking in panoramic views over "
                        "historic Cairo’s skyline."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return transfer to your hotel",
                    "description": (
                        "After lunch and time to enjoy the park’s atmosphere and views, your guide and driver will "
                        "escort you back to your hotel in Cairo."
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
                    "Private tour leader",
                    "Lunch meal at a local restaurant",
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
                    name="Standard El Moez, Bayt Al-Suhaymi & Al Azhar Park Tour",
                    price_per_person=Decimal("99.00"),
                    child_price_per_person=Decimal("30.00"),
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
                            caption="El Moez Street, Bayt Al-Suhaymi & Al Azhar Park highlights",
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
