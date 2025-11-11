# yourapp/management/commands/seed_nile_pharaoh_cruise.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from web.models import (
    Destination, DestinationName,
    Trip, TripHighlight, TripAbout,
    TripItineraryDay, TripItineraryStep,
    TripInclusion, TripExclusion,
)

TRIP_TITLE = "Nile Pharaoh Dinner Cruise on the Nile"

TEASER = (
    "Enjoy a romantic evening on the Nile with a buffet dinner, live belly dancing and Tanoura, "
    "Cairo skyline views from the upper deck, and convenient hotel pickup and drop-off."
)

ABOUT_BODY = (
    "After a convenient pickup, board the cruise to sail along the Nile and take in night views of Cairo. "
    "Feast on an open buffet dinner and enjoy live belly dancing and Tanoura performances. "
    "Capture photos from the upper deck before returning to your hotel."
)

# If you prefer to set a concrete discounted child price later in admin, keep it None.
ADULT_PRICE = Decimal("50.00")
CHILD_PRICE = None  # set to e.g., Decimal("40.00") if you want an explicit discounted rate now

HIGHLIGHTS = [
    "Nile night cruise with buffet dinner",
    "Live belly dancing and Tanoura show",
    "Cairo skyline views from the upper deck",
    "Hotel pickup and drop-off included",
]

INCLUSIONS = [
    "Local guide",
    "Pickup & drop-off transfers",
    "Open buffet dinner",
    "Belly dancing and Tanoura show",
    "All taxes & services",
]

EXCLUSIONS = [
    "Water and drinks (unless specified)",
    "Personal items",
    "Tipping",
]

# Simple, single-evening outline mapped to the provided times
ITINERARY_STEPS = [
    ("18:00", "Hotel Pickup", "Representative meets you and transfers to the cruise pier."),
    ("18:30", "Boarding & Sail", "Board the vessel and begin a ~2-hour sail on the Nile."),
    ("19:00", "Dinner Buffet", "Open buffet dinner served on board."),
    ("19:30", "Live Shows", "Belly dancing and traditional Tanoura performances."),
    ("20:30", "Upper Deck Photos", "Capture skyline views from the upper deck."),
    ("21:30", "Disembark & Transfer", "Return to pier and transfer back to your hotel (ETA ~22:30)."),
]


class Command(BaseCommand):
    help = "Seed the 'Nile Pharaoh Dinner Cruise on the Nile' trip with minimal curated content (incl. exclusions)."

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Ensure Cairo destination exists ---
        cairo, _ = Destination.objects.get_or_create(
            name=DestinationName.CAIRO.value,
            defaults={"tagline": "Cairo by day and by night"},
        )

        # --- Create or update the Trip (minimal required fields only) ---
        trip, created = Trip.objects.get_or_create(
            title=TRIP_TITLE,
            defaults={
                "destination": cairo,
                "teaser": TEASER,
                "duration_days": 1,         # evening experience
                "group_size_max": 20,       # sensible default; adjust as needed
                "base_price_per_person": ADULT_PRICE,
                "child_price_per_person": CHILD_PRICE,
                "tour_type_label": "Evening Tour — Dinner Cruise",
            },
        )

        if not created:
            trip.destination = cairo
            trip.teaser = TEASER
            trip.duration_days = trip.duration_days or 1
            trip.group_size_max = trip.group_size_max or 20
            trip.base_price_per_person = ADULT_PRICE
            trip.child_price_per_person = CHILD_PRICE
            trip.tour_type_label = trip.tour_type_label or "Evening Tour — Dinner Cruise"
            trip.save()

        # --- About (OneToOne) ---
        TripAbout.objects.update_or_create(trip=trip, defaults={"body": ABOUT_BODY})

        # --- Highlights (reset) ---
        TripHighlight.objects.filter(trip=trip).delete()
        for pos, text in enumerate(HIGHLIGHTS, start=1):
            TripHighlight.objects.create(trip=trip, text=text, position=pos)

        # --- Inclusions (reset) ---
        TripInclusion.objects.filter(trip=trip).delete()
        for pos, text in enumerate(INCLUSIONS, start=1):
            TripInclusion.objects.create(trip=trip, text=text, position=pos)

        # --- Exclusions (reset) ---
        TripExclusion.objects.filter(trip=trip).delete()
        for pos, text in enumerate(EXCLUSIONS, start=1):
            TripExclusion.objects.create(trip=trip, text=text, position=pos)

        # --- Itinerary (reset to one evening) ---
        TripItineraryDay.objects.filter(trip=trip).delete()
        day = TripItineraryDay.objects.create(
            trip=trip,
            day_number=1,
            title="Evening Nile Dinner Cruise (Cairo)",
        )
        for pos, (time_label, title, desc) in enumerate(ITINERARY_STEPS, start=1):
            TripItineraryStep.objects.create(
                day=day,
                time_label=time_label,
                title=title,
                description=desc,
                position=pos,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded trip: '{trip.title}' (slug: {trip.slug}) · Destination: {cairo.name}"
            )
        )
