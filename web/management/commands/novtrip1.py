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


TRIP_TITLE = "Cairo: Guided Day Tour to Bab al-Futuh & Old Cairo Treasures"


class Command(BaseCommand):
    help = "Seed the 'Bab al-Futuh & Old Cairo Treasures' half-day private tour in Cairo."

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
                        "Explore Cairo’s Islamic legacy with a private tour through "
                        "Bab al-Futuh, Al-Muizz Street, and Khan El Khalili."
                    ),
                    duration_days=1,  # 4-hour tour mapped to 1 calendar day
                    group_size_max=12,  # adjust if you prefer a different cap
                    base_price_per_person=Decimal("116.00"),
                    child_price_per_person=Decimal("29.00"),
                    tour_type_label="Private Half-Day Tour — Old Cairo Treasures",
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
                    "Cairo highlights and Islamic heritage attractions",
                    "Bab al-Futuh city gate (Fatimid-era fortification)",
                    "Al-Muizz Street open-air museum of Islamic architecture",
                    "Khan El Khalili Bazaar shopping experience",
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
                "Explore Cairo’s Islamic legacy with a private guided tour through Bab al-Futuh, "
                "Al-Muizz Street, and Khan El Khalili. Discover ancient gates, mosques, markets, and "
                "untouched mansions from a bygone era in the heart of Islamic Cairo.\n\n"
                "From the comfort of your hotel to the bustling alleys of Old Cairo, your Kaya Tours "
                "tour leader will accompany you in a private air-conditioned vehicle as you uncover "
                "stories of medieval battles, architectural masterpieces, and vibrant local life.\n\n"
                "Kaya Tours ensures a transparent and hassle-free experience. You won’t encounter any "
                "hidden surprises or unexpected costs.\n\n"
                "Note: Pick-up/drop-off from Cairo Airport, Sphinx Airport, New Administrative Capital, "
                "New Cairo, Heliopolis, Badr City, Shorouk, Rehab, Obour, Sheraton Almatar, Sheikh "
                "Zayed City, or Madinty City will incur an additional fee."
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
                    "title": "Guided Day Tour to Bab al-Futuh & Old Cairo Treasures",
                },
            )

            # Clear existing steps to keep this idempotent
            day.steps.all().delete()

            steps = [
                {
                    "time_label": "",
                    "title": "Hotel pick-up & transfer to Islamic Cairo",
                    "description": (
                        "Your Kaya Tours representative will pick you up from your hotel in a private "
                        "air-conditioned vehicle and escort you to the heart of Old Cairo, the center "
                        "of the city’s Islamic heritage."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Discover Bab al-Futuh",
                    "description": (
                        "Begin your exploration at Bab al-Futuh, one of the three surviving gates of "
                        "the ancient Fatimid wall that once encircled Cairo. Built in 1087, this "
                        "impressive structure served as a military gateway and symbol of strength. "
                        "Admire its rounded towers and intricate stone carvings while hearing stories "
                        "of medieval battles and historic defenses."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Stroll along Al-Muizz Street",
                    "description": (
                        "Continue along Al-Muizz Street, often called Cairo’s open-air museum, where "
                        "minarets pierce the sky above centuries-old mosques and mansions. Your guide "
                        "will introduce you to architectural gems such as Al-Hakim Mosque, Bayt "
                        "al-Suhaymi, and traditional sabils (public water fountains)."
                    ),
                },
                {
                    "time_label": "",
                    "title": "Shopping at Khan El Khalili Bazaar",
                    "description": (
                        "End your tour at Khan El Khalili Bazaar, Cairo’s most famous market. Enjoy "
                        "free time to browse for brass lanterns, handmade perfumes, colorful fabrics, "
                        "and unique souvenirs in an atmosphere bursting with history and life."
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
                    "Hotel pick-up and drop-off in Cairo",
                    "Transportation by private air-conditioned vehicle",
                    "Private tour guide",
                    "Bottled water",
                    "Shopping tour of Cairo (Khan El Khalili Bazaar)",
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
                    name="Standard Private Tour",
                    price_per_person=Decimal("116.00"),
                    child_price_per_person=Decimal("29.00"),
                    position=1,
                )
                self.stdout.write(self.style.SUCCESS("Booking option seeded."))

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully."))
