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


TRIP_TITLE = "Female-Led Cooking & Countryside Farm Tour in Rural Egypt."

# Local filesystem paths on the machine where you run this command.
# These will be read and then saved via Django's storage backend (e.g. Cloudflare R2).
IMAGE_BASE_PATH = "/Users/adham/Desktop/latest-sand/rulareg"

CARD_IMAGE_FILENAME = "1.webp"
HERO_IMAGE_FILENAME = "7.webp"
GALLERY_FILENAMES = [f"{i}.webp" for i in range(1, 12)]  # 1.webp ... 11.webp


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
        field.save(os.path.basename(path), django_file, save=False)


class Command(BaseCommand):
    help = "Seed the 'Female-Led Cooking & Countryside Farm Tour in Rural Egypt.' trip with images."

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
                        "Explore Egypt’s rural charm with women-led farming and cooking experiences. "
                        "Harvest seasonal fruits, learn ancestral recipes, and support sustainable "
                        "local communities."
                    ),
                    duration_days=1,  # ~6-hour experience mapped to 1 calendar day
                    group_size_max=12,  # adjust as you like
                    base_price_per_person=Decimal("300.00"),
                    child_price_per_person=Decimal("73.00"),
                    tour_type_label=(
                        "Private Half-Day Tour — Female-Led Cooking & Countryside Farm Experience"
                    ),
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
            # hero_image_mobile left blank for now; you can add another image if desired.
            trip.save()
            self.stdout.write(self.style.SUCCESS("Card & hero images processed (if files present)."))

            # --- Highlights ---
            if created or not trip.highlights.exists():
                trip.highlights.all().delete()

                highlights = [
                    "Explore sustainable farming methods passed down for generations.",
                    "Harvest seasonal fruits like mangoes and dates with local farmers.",
                    "Join hands-on cooking classes led by rural Egyptian women.",
                    "Enjoy a farm-to-table meal using fresh ingredients you picked.",
                    "Support sustainable tourism and women’s empowerment in Egypt.",
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
                "Experience the warmth and authenticity of rural Egypt with a female-led cooking and countryside "
                "farm tour. This immersive experience connects you directly with local communities, traditional "
                "farming practices, and ancestral recipes.\n\n"
                "Your journey begins with a private transfer from your hotel to the countryside, where you’ll meet "
                "rural Egyptian women who lead sustainable farming and cooking activities. Explore traditional "
                "cultivation techniques and learn how families have farmed the land for generations.\n\n"
                "Enjoy a farm-to-table lunch prepared by local women using fresh ingredients harvested from the "
                "fields around you. Depending on the season, you may take part in agricultural experiences like "
                "Mango Harvest (July–August) or Date Harvest & Agwa Making (August–September), where you can pick "
                "fruits and learn traditional food preservation methods.\n\n"
                "Deepen your culinary skills with cooking classes lasting 3–5 hours, guided by rural women who share "
                "their ancestral recipes, stories, and techniques. Beyond food, this experience directly supports "
                "rural Egyptian women, creates local employment, and preserves Egypt’s traditional foodways through "
                "sustainable gastro tourism.\n\n"
                "Kaya Tours ensures a transparent and hassle-free experience, so you won’t encounter any hidden "
                "surprises or unexpected costs.\n\n"
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
                    "title": "Female-Led Cooking & Countryside Farm Experience",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "",
                    "title": "Hotel pick-up and countryside transfer",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel at a time slot that suits "
                        "your schedule and escort you in a private, modern air-conditioned vehicle to the rural "
                        "countryside, where your women-led farm experience begins."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Introduction to sustainable farming practices",
                    "description": (
                        "Start with a countryside tour guided by local women and farmers who will introduce you to "
                        "traditional and sustainable farming techniques passed down through generations. Learn how "
                        "families cultivate the land and preserve agricultural heritage."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Seasonal harvest activities",
                    "description": (
                        "Depending on the season, join agricultural activities such as Mango Harvest (July–August) or "
                        "Date Harvest & Agwa Making (August–September). Experience fruit picking, learn about "
                        "harvest cycles, and discover traditional methods of food preservation."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Women-led cooking class",
                    "description": (
                        "Take part in a hands-on cooking class lasting 3–5 hours, led by rural Egyptian women who "
                        "share ancestral recipes, techniques, and personal stories. Prepare authentic dishes using "
                        "fresh ingredients sourced directly from the farm."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Farm-to-table meal and cultural connection",
                    "description": (
                        "Enjoy a farm-to-table meal featuring the dishes you helped prepare, served in a relaxed "
                        "countryside setting. Take time to connect with your hosts, ask questions, and gain a deeper "
                        "understanding of rural life and food traditions in Egypt."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Return to your hotel",
                    "description": (
                        "After a fulfilling day of cooking, learning, and cultural exchange, you will be comfortably "
                        "transferred back to your hotel, carrying with you memorable flavors and stories from rural "
                        "Egypt."
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
                    "Private tour leader available in your preferred language for a personalized experience",
                    "Pick-up services from your hotel and return",
                    "All transfers by a modern private air-conditioned vehicle",
                    "Entrance fees to all mentioned sites and activities in the program",
                    "Bottled water during your trip",
                    "Farm-to-table meal included in the itinerary",
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
                    "Personal expenses and tipping",
                    "Any additional beverages not included in the itinerary",
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
                    name="Standard Female-Led Cooking & Farm Tour",
                    price_per_person=Decimal("300.00"),
                    child_price_per_person=Decimal("73.00"),
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
                            caption="Female-led rural cooking & countryside experience",
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
