# yourapp/management/commands/seed_camel_giza.py
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from yourapp.models import (
    Destination, DestinationName,
    Trip, TripHighlight, TripAbout,
    TripItineraryDay, TripItineraryStep,
    TripInclusion,
)

TRIP_TITLE = "Ride a Camel at The Pyramids of Giza Including BBQ Dinner"

OVERVIEW = (
    "This safari tour combines an adventurous camel ride around the massive Pyramids "
    "with a relaxing evening of food and entertainment."
)

ABOUT_BODY = (
    "Your private guide meets you at your hotel lobby before sunset. Choose your camel, ride along "
    "the Sahara near the Giza Plateau, and enjoy panoramic pyramid views while your guide helps with "
    "photos. After the ride, unwind with a BBQ dinner (beef, chicken kofta, and more). "
    "Private transportation is included. After the tour, you’ll be transferred back to your hotel."
)

HIGHLIGHTS = [
    "Sunset camel ride by the Pyramids of Giza",
    "Private hotel pickup and drop-off in an air-conditioned vehicle",
    "BBQ dinner with grilled options",
    "Expert local tour guide and photo stops",
    "All fees and taxes included",
]

INCLUSIONS = [
    "Pickup & drop-off service from hotel",
    "Air-conditioned private transportation",
    "Expert tour guide",
    "All fees and taxes",
    "Dinner (BBQ)",
    "Tipping (optional)",
]

ITINERARY_STEPS = [
    ("16:30", "Hotel Pickup", "Guide meets you in the lobby (holds a sign), transfer to Giza area."),
    ("17:15", "Camel Selection & Briefing", "Choose your camel and get basic riding instructions."),
    ("17:30", "Sunset Camel Ride", "Ride near the Giza Plateau and stop for photos in the desert."),
    ("18:30", "BBQ Dinner", "Relax with a BBQ dinner: beef, chicken kofta and sides."),
    ("19:30", "Return Transfer", "Drive back to your hotel and drop-off."),
]


class Command(BaseCommand):
    help = "Seed the 'Ride a Camel at The Pyramids of Giza Including BBQ Dinner' trip."

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Ensure destinations exist (primary: Giza; additional: Cairo) ---
        giza, _ = Destination.objects.get_or_create(
            name=DestinationName.GIZA.value,
            defaults={"tagline": "See the Pyramids up close"},
        )
        cairo, _ = Destination.objects.get_or_create(
            name=DestinationName.CAIRO.value,
            defaults={"tagline": "The sprawling capital of Egypt"},
        )

        # --- Create/Update Trip (minimal required fields only) ---
        trip, created = Trip.objects.get_or_create(
            title=TRIP_TITLE,
            defaults={
                "destination": giza,
                "teaser": OVERVIEW,
                "duration_days": 1,                  # daily experience
                "group_size_max": 12,                # sensible default; tweak later if needed
                "base_price_per_person": Decimal("95.00"),
                "child_price_per_person": Decimal("50.00"),
                "tour_type_label": "Daily Tour — Sunset Camel Ride",
            },
        )

        # If it already exists, keep it fresh/minimal without overwriting images, etc.
        if not created:
            trip.destination = giza
            trip.teaser = OVERVIEW
            trip.duration_days = trip.duration_days or 1
            trip.group_size_max = trip.group_size_max or 12
            trip.base_price_per_person = Decimal("95.00")
            trip.child_price_per_person = Decimal("50.00")
            trip.tour_type_label = trip.tour_type_label or "Daily Tour — Sunset Camel Ride"
            trip.save()

        # --- Additional destination (Cairo) ---
        trip.additional_destinations.add(cairo)

        # --- About (OneToOne) ---
        TripAbout.objects.update_or_create(
            trip=trip,
            defaults={"body": ABOUT_BODY},
        )

        # --- Highlights (reset to our minimal curated set) ---
        TripHighlight.objects.filter(trip=trip).delete()
        for pos, text in enumerate(HIGHLIGHTS, start=1):
            TripHighlight.objects.create(trip=trip, text=text, position=pos)

        # --- Inclusions (reset to our minimal curated set) ---
        TripInclusion.objects.filter(trip=trip).delete()
        for pos, text in enumerate(INCLUSIONS, start=1):
            TripInclusion.objects.create(trip=trip, text=text, position=pos)

        # --- Itinerary (simple single-day outline) ---
        # Wipe and recreate a clean single-day itinerary
        TripItineraryDay.objects.filter(trip=trip).delete()
        day = TripItineraryDay.objects.create(
            trip=trip,
            day_number=1,
            title="Sunset Camel Ride & BBQ Dinner (Giza)",
        )
        for pos, (time_label, title, desc) in enumerate(ITINERARY_STEPS, start=1):
            TripItineraryStep.objects.create(
                day=day,
                time_label=time_label,
                title=title,
                description=desc,
                position=pos,
            )

        # (Optional) You can add FAQs or Extras here in the future if needed.

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded trip: '{trip.title}' (slug: {trip.slug}) · Destination: {giza.name} [+{cairo.name}]"
            )
        )
