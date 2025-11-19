from __future__ import annotations

from decimal import Decimal

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
)


TRIP_TITLE = "Discover Museum of Islamic Art: Half-Day Private Tour"


class Command(BaseCommand):
    help = "Seed the 'Discover Museum of Islamic Art: Half-Day Private Tour' in Cairo."

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
                        "A half-day private tour of the Museum of Islamic Art with "
                        "hotel pick-up, expert guide, and seamless return for a rich "
                        "and hassle-free cultural experience."
                    ),
                    duration_days=1,  # 4-hour tour mapped to 1 calendar day
                    group_size_max=12,  # adjust as you like
                    base_price_per_person=Decimal("92.00"),
                    child_price_per_person=Decimal("24.00"),
                    tour_type_label="Private Half-Day Tour — Museum of Islamic Art",
                    is_service=False,
                    allow_children=True,
                    allow_infants=True,
                )
                trip.save()
                created = True
                self.stdout.write(self.style.SUCCESS(f"Created trip: {trip.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Trip already exists: {trip.title}"))

            # --- Highlights ---
            if created or not trip.highlights.exists():
                trip.highlights.all().delete()

                highlights = [
                    "Rare manuscripts – ancient Islamic scripts and texts",
                    "Astrolabes collection – medieval astronomical instruments",
                    "Intricate jewelry – finely crafted ornaments and pieces",
                    "Architectural fragments – historical building remnants",
                    "Islamic ceramics – stunning pottery and decorative art",
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
                "Experience a half-day private tour dedicated to the Museum of Islamic Art in Cairo. "
                "Your journey begins with a comfortable pick-up from your hotel in a private, "
                "air-conditioned vehicle, guided by a professional Kaya Tours representative.\n\n"
                "Upon arrival, you’ll explore one of the world’s most important collections of Islamic art, "
                "featuring rare manuscripts, astrolabes, intricate jewelry, architectural fragments, and "
                "beautiful Islamic ceramics. Your private tour guide will share the history and stories "
                "behind each collection, offering deep cultural context and insight.\n\n"
                "After taking in the museum’s treasures, you’ll be comfortably transferred back to your hotel, "
                "ensuring a seamless and enriching cultural experience from start to finish.\n\n"
                "Kaya Tours ensures a transparent and hassle-free experience by including all attraction "
                "entry fees upfront in our itineraries. You won’t encounter any hidden surprises or "
                "unexpected costs.\n\n"
                "Note: Pick-up/drop-off from Cairo Airport, Sphinx Airport, New Administrative Capital, "
                "New Cairo, Heliopolis, Badr City, Shorouk, Rehab, Obour, Sheraton Almatar, Sheikh Zayed City, "
                "or Madinty City will incur an additional fee."
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
                    "title": "Half-Day Private Tour to the Museum of Islamic Art",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "08:00",
                    "title": "Hotel pick-up and transfer",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel at around 8:00 AM "
                        "in a private, deluxe air-conditioned vehicle and escort you to the Museum of Islamic Art."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Guided tour inside the Museum of Islamic Art",
                    "description": (
                        "Upon arrival, immerse yourself in the museum’s vast collection, ranging from rare "
                        "manuscripts and astrolabes to intricate jewelry, architectural fragments, and Islamic "
                        "ceramics. Your private tour guide will explain the historical and cultural significance "
                        "behind the exhibits and highlight the most important pieces."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Cultural insights and return transfer",
                    "description": (
                        "After exploring the museum’s collections and gaining deep insights into Islamic art and "
                        "heritage, you will be transferred back to your hotel in comfort, completing a smooth and "
                        "enriching half-day experience."
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
                    "Private tour guide",
                    "Entrance fees and tickets to the Museum of Islamic Art",
                    "Bottled water on board the vehicle during the tour",
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
                    "Any additional expenses that are not listed in the itinerary",
                    "Tipping",
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
                    name="Standard Private Museum Tour",
                    price_per_person=Decimal("92.00"),
                    child_price_per_person=Decimal("24.00"),
                    position=1,
                )
                self.stdout.write(self.style.SUCCESS("Booking option seeded."))

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully."))
