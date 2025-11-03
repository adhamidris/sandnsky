# web/management/commands/seed_cafelluca.py
from decimal import Decimal
from typing import List, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from web.models import (
    Destination,
    DestinationName,
    Trip,
    TripAbout,
    TripBookingOption,
    TripCategory,
    TripFAQ,
    TripHighlight,
    TripInclusion,
    TripExclusion,
    TripItineraryDay,
    TripItineraryStep,
    Language,
)

LUXURY_CATEGORY_SLUG = "luxury"
LUXURY_CATEGORY_NAME = "Luxury"

DEFAULT_DURATION_DAYS = 1
DEFAULT_GROUP_SIZE_MAX = 12
DEFAULT_PRICE = Decimal("0.00")  # TODO: set a real price later in Admin

TITLE_RAW = "Cafelluca, private 5 star Felucca, 2 hours nile ride with drinks"
TEASER = (
    "Private 5-star felucca cruise on the Nile with Cairo skyline views. "
    "Choose breakfast, lunch, dinner, or drinks-only. Unlimited soft drinks; on-board entertainment."
)

ABOUT_BODY = (
    "Take a ride along the ancient Nile River aboard a traditional felucca boat. "
    "You'll sit down for breakfast, lunch, or dinner served right on the boat (or enjoy a drinks-only option), "
    "taking in views of Cairo’s skyline along the way. On-board entertainment is provided, including karaoke. "
    "Unlimited soft drinks and juices are included (no alcohol)."
    "\n\n"
    "• Private experience for your group only\n"
    "• Approx. 2 hours on the Nile\n"
    "• Options: Breakfast, Lunch, Dinner, or Drinks-only\n"
    "• Hotel pick-up and drop-off included"
)

HIGHLIGHTS: List[str] = [
    "Private 5-star felucca exclusively for your group",
    "2-hour Nile cruise with Cairo skyline views",
    "Unlimited soft drinks & juices (no alcohol)",
    "Choose breakfast, lunch, dinner, or drinks-only",
    "On-board entertainment (e.g., karaoke)",
]

INCLUSIONS: List[str] = [
    "All taxes, fees and handling charges",
    "Hotel pickup and drop-off",
    "Bottled water",
    "Unlimited soft drinks and juices (no alcohol)",
    "Coffee and/or tea",
    "Private tour/boat crew",
    "Gratuities",
]

# Keep exclusions minimal and only from given info
EXCLUSIONS: List[str] = [
    "Alcoholic beverages",
    "Meals unless a breakfast/lunch/dinner option is selected",
]

FAQS: List[Tuple[str, str]] = [
    ("Is alcohol served on board?", "No. Unlimited soft drinks and juices are included, plus coffee/tea. No alcohol."),
    ("Is this experience private?", "Yes. This is a private tour/activity; only your group will participate."),
    ("Is the boat wheelchair accessible?", "Not wheelchair accessible."),
    ("Are infants allowed and are infant meals included?", "Infants can join; infant meals are not included."),
    ("Do you cater to vegetarians?", "A vegetarian option is available—please advise any dietary requirements when booking."),
    ("When is confirmation provided?", "Confirmation is received at time of booking (or as soon as possible if booked within 1 day of travel)."),
    ("What are the start time options?", "Breakfast, Lunch, Dinner, or Drinks-only departures—confirm with the provider in advance."),
]

ITINERARY_TITLE = "Cairo Felucca Cruise"
ITINERARY_STEPS: List[Tuple[str, str, str]] = [
    ("", "Board your private felucca", "Meet the crew and settle in for your private cruise."),
    ("", "Cairo Tower (pass-by view)", "See Cairo Tower from the Nile as you cruise."),
    ("", "Nile River cruise (approx. 2 hours)", "Enjoy skyline views and unlimited soft drinks/juices."),
    ("", "Return to pier", "Disembark and transfer back to your hotel (if applicable)."),
]

BOOKING_OPTION_LABELS: List[str] = [
    "Felucca ride with drinks only",
    "Cafelluca Dinner/Lunch",
    "Cafelluca Breakfast",
    "Cafelluca Sofitel dinner",
]


class Command(BaseCommand):
    help = "Seeds the Cafelluca Luxury felucca trip in Cairo with content. Safe to re-run."

    def add_arguments(self, parser):
        parser.add_argument("--price", type=str, default=str(DEFAULT_PRICE),
                            help="Base price per adult as a decimal (default: 0.00).")
        parser.add_argument("--group-size", type=int, default=DEFAULT_GROUP_SIZE_MAX,
                            help=f"Max group size (default: {DEFAULT_GROUP_SIZE_MAX}).")
        parser.add_argument("--duration-days", type=int, default=DEFAULT_DURATION_DAYS,
                            help=f"Duration in days (default: {DEFAULT_DURATION_DAYS}).")
        parser.add_argument("--title", type=str, default=TITLE_RAW,
                            help="Override the trip title (minimal tweaks only).")
        parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing data.")

    def _get_or_create_destination(self) -> Destination:
        dest, _ = Destination.objects.get_or_create(
            name=DestinationName.CAIRO.value,
            defaults={"tagline": "", "description": ""},
        )
        return dest

    def _get_or_create_category(self) -> TripCategory:
        cat, _ = TripCategory.objects.get_or_create(
            slug=LUXURY_CATEGORY_SLUG, defaults={"name": LUXURY_CATEGORY_NAME}
        )
        return cat

    def _get_or_create_language_en(self) -> Language:
        lang, _ = Language.objects.get_or_create(name="English", code="en")
        return lang

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        base_price = Decimal(opts["price"])
        group_size = int(opts["group_size"])
        duration_days = int(opts["duration_days"])
        title = opts["title"].strip()

        destination = self._get_or_create_destination()
        category = self._get_or_create_category()
        lang_en = self._get_or_create_language_en()

        tour_type_label = "Luxury — Private Felucca Cruise"

        # Make a stable slug that won’t churn if the title is minimally tweaked
        base_slug = slugify("cafelluca-private-5-star-felucca-2-hour-nile-ride-drinks") or "cafelluca-felucca"

        # Create or update Trip
        trip, created = Trip.objects.get_or_create(
            slug=base_slug,
            defaults={
                "title": title,
                "destination": destination,
                "teaser": TEASER,
                "duration_days": duration_days,
                "group_size_max": group_size,
                "base_price_per_person": base_price,
                "child_price_per_person": None,  # fallback = adult price
                "tour_type_label": tour_type_label,
                "is_service": False,
                "allow_children": True,
                "allow_infants": True,
                "minimum_age": None,
            },
        )

        if not created:
            # Update minimal mutable fields
            trip.title = title
            trip.destination = destination
            trip.teaser = TEASER
            trip.duration_days = duration_days
            trip.group_size_max = group_size
            trip.base_price_per_person = base_price
            trip.tour_type_label = tour_type_label
            # leave images / destination_order untouched
            self.stdout.write(self.style.WARNING(f"Updating existing trip: {trip.title}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Creating trip: {trip.title}"))

        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] Trip would be saved/updated."))
        else:
            trip.save()

        # M2M: category + language
        if not dry_run:
            trip.category_tags.add(category)
            trip.languages.add(lang_en)

        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] Would ensure booking options."))
        else:
            for position, label in enumerate(BOOKING_OPTION_LABELS, start=1):
                TripBookingOption.objects.update_or_create(
                    trip=trip,
                    name=label,
                    defaults={
                        "price_per_person": base_price,
                        "child_price_per_person": None,
                        "position": position,
                    },
                )

        # Replace child content idempotently (delete & recreate)
        def reset_qs(qs):
            count = qs.count()
            if count:
                qs.delete()
            return count

        if dry_run:
            self.stdout.write(self.style.NOTICE("[dry-run] Would replace highlights/about/itinerary/inclusions/exclusions/faqs"))
        else:
            reset_qs(trip.highlights.all())
            reset_qs(trip.itinerary_days.all())
            reset_qs(trip.inclusions.all())
            reset_qs(trip.exclusions.all())
            reset_qs(trip.faqs.all())

            # About
            TripAbout.objects.update_or_create(trip=trip, defaults={"body": ABOUT_BODY})

            # Highlights
            TripHighlight.objects.bulk_create([
                TripHighlight(trip=trip, text=text, position=i + 1)
                for i, text in enumerate(HIGHLIGHTS)
            ])

            # Itinerary
            day = TripItineraryDay.objects.create(trip=trip, day_number=1, title=ITINERARY_TITLE)
            TripItineraryStep.objects.bulk_create([
                TripItineraryStep(day=day, time_label=t, title=ttl, description=desc, position=i + 1)
                for i, (t, ttl, desc) in enumerate(ITINERARY_STEPS)
            ])

            # Inclusions / Exclusions
            TripInclusion.objects.bulk_create([
                TripInclusion(trip=trip, text=text, position=i + 1)
                for i, text in enumerate(INCLUSIONS)
            ])
            TripExclusion.objects.bulk_create([
                TripExclusion(trip=trip, text=text, position=i + 1)
                for i, text in enumerate(EXCLUSIONS)
            ])

            # FAQs
            TripFAQ.objects.bulk_create([
                TripFAQ(trip=trip, question=q, answer=a, position=i + 1)
                for i, (q, a) in enumerate(FAQS)
            ])

        # Summary
        action = "Seeded" if not created else "Created"
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"[dry-run] Would {action.lower()} Cafelluca Luxury trip in Cairo."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{action} Cafelluca Luxury trip in Cairo (slug: {base_slug})."))
            self.stdout.write(self.style.SUCCESS("Gallery intentionally left empty for manual injection."))
            self.stdout.write(self.style.HTTP_INFO("You can adjust price, images, and fine details in Admin anytime."))
