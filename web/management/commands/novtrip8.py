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


TRIP_TITLE = "Cairo Mosques and Khan El Khalili Bazaar Tour"

# Local filesystem path on the machine where you run this command.
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/mosq"

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
    help = "Seed the 'Cairo Mosques and Khan El Khalili Bazaar Tour' trip with images and content."

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
                        "Discover medieval Cairo with Kaya Tours: explore historic mosques, "
                        "walk along Al-Muizz Street, and experience the vibrant Khan El Khalili bazaar."
                    ),
                    duration_days=1,  # ~6 hours mapped to 1 calendar day
                    group_size_max=12,
                    base_price_per_person=Decimal("135.00"),
                    child_price_per_person=Decimal("35.00"),
                    tour_type_label="Private One-Day Tour — Mosques & Khan El Khalili",
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
                    "Discover the medieval heart of Islamic Cairo.",
                    "Visit the Mosque and Madrassa of Sultan Hassan.",
                    "Walk along historic Al-Muizz Street.",
                    "See Bab Zuweila and the Mosque-Mausoleum of Sultan al-Mu’ayyad Shaykh.",
                    "Visit the Mosque of Al-Azhar and the Mosque of El Hussein (where applicable).",
                    "Experience the bustling Khan El Khalili Bazaar.",
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
                "Discover the soul of medieval Cairo on a private full-day tour with Kaya Tours. "
                "Your experience begins with a pick-up from your hotel around 10:00 AM in a modern, "
                "air-conditioned vehicle.\n\n"
                "Your first stop is the remarkable Mosque and Madrasa of Sultan Hassan, an architectural marvel "
                "built in 1356 CE. Constructed during a period marked by the Black Plague, it stands today as a "
                "testament to resilience and faith.\n\n"
                "You will also visit the Mosque of Al-Refai, a stunning example of Mamluk-inspired architecture, "
                "famous for its scale and intricate design. Together, Sultan Hassan and Al-Refai form one of "
                "Cairo’s most impressive historic ensembles.\n\n"
                "The journey continues along Al-Muizz Street towards Bab Zuweila, where you will pass by "
                "Al Khayammeyah and visit the Mosque-Mausoleum of Sultan al-Mu’ayyad Shaykh, named “Al-Mu’ayyad” "
                "or “The Supporter.” Along the way, you will also see the Sabil-Kuttab of Tusun Pasha, a unique "
                "structure with rounded frontage and decoration reminiscent of the Mohammed Ali period.\n\n"
                "Your tour includes visits to the Mosque of Al-Azhar, one of the most important institutions for "
                "Sunni theology and Islamic law, and the Mosque of El Hussein, a historic mosque and mausoleum "
                "with deep spiritual significance.\n\n"
                "Finally, dive into the colorful world of Khan El Khalili, Cairo’s most famous bazaar, where "
                "you can browse stalls filled with spices, leather goods, jewelry, and traditional souvenirs, and "
                "enjoy lunch at a local restaurant.\n\n"
                "After a day filled with unforgettable experiences, you will be comfortably returned to your hotel. "
                "Kaya Tours ensures a smooth, transparent journey with no hidden costs.\n\n"
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
                    "title": "Cairo Mosques and Khan El Khalili Bazaar Tour",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "10:00",
                    "title": "Hotel pick-up and transfer to Sultan Hassan",
                    "description": (
                        "Your Kaya Tours representative will meet you at your hotel around 10:00 AM and escort you "
                        "in a private, air-conditioned vehicle to the Mosque and Madrasa of Sultan Hassan."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit the Mosque and Madrasa of Sultan Hassan",
                    "description": (
                        "Explore the grand Mosque and Madrasa of Sultan Hassan, built in 1356 CE. Learn about its "
                        "remarkable architecture, history, and how it was constructed during the time of the Black Plague."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Visit the Mosque of Al-Refai",
                    "description": (
                        "Continue to the Mosque of Al-Refai, renowned for its monumental scale and elaborate design. "
                        "Discover its role in Cairo’s religious and royal history."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Al-Muizz Street, Bab Zuweila & Al-Mu’ayyad Mosque",
                    "description": (
                        "Walk along Al-Muizz Street towards Bab Zuweila. Visit the Al Khayammeyah area and the "
                        "Mosque-Mausoleum of Sultan al-Mu’ayyad Shaykh, an important Mamluk-era monument named "
                        "after Sultan Al-Mu’ayyad Sayf ad-Din Shaykh."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Sabil-Kuttab of Tusun Pasha",
                    "description": (
                        "See the Sabil-Kuttab of Tusun Pasha, a future museum with a distinctive rounded façade and "
                        "decorative elements reminiscent of the Mohammed Ali period."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Mosque of Al-Azhar and Mosque of El Hussein",
                    "description": (
                        "Visit the Mosque of Al-Azhar, a leading institution of Sunni Islamic learning, and the "
                        "Mosque of El Hussein, a historic mosque and mausoleum with deep religious importance."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Khan El Khalili Bazaar & lunch",
                    "description": (
                        "Finish your walking tour at Khan El Khalili Bazaar. Browse stalls filled with spices, "
                        "leather goods, jewelry, and souvenirs, and enjoy lunch at a local restaurant before "
                        "concluding your day."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to your hotel",
                    "description": (
                        "After immersing yourself in the mosques, streets, and markets of Islamic Cairo, you will be "
                        "transferred back to your hotel in comfort."
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
                    "Pick-up from your hotel in Cairo and return",
                    "Walking tour of Cairo’s most important Islamic sites",
                    "Lunch at a local restaurant",
                    "Entrance fees to the above-mentioned sites",
                    "Shopping tour in Cairo (Khan El Khalili Bazaar)",
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
                    name="Standard Cairo Mosques & Khan El Khalili Tour",
                    price_per_person=Decimal("135.00"),
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
                            caption="Cairo mosques and Khan El Khalili highlights",
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
