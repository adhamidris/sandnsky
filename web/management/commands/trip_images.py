from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Trip, Destination, TripCategory, TripExtra, TripInclusion, TripExclusion, TripFAQ
from web.models import DestinationName


class Command(BaseCommand):
    help = "Seed/update trip images and related models for desert trips."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the changes without saving to the DB",
        )
        parser.add_argument(
            "--overwrite-images",
            action="store_true",
            help="Overwrite existing images if set",
        )

    TRIPS = [
        {
            "title": "3-Day Desert Adventure: White Desert & Bahariya Oasis Exploration",
            "destination": "White & Black Desert",
            "card_image": "trips/cards/785ac5d804.jpg",
            "hero_image": "trips/hero/4bd985d347.jpg",
            "teaser": "Three-day desert safari from Cairo: Bahariya Oasis, Black Desert, Crystal Mountain, Valley of Agabat, and camping under the stars in the White Desert.",
            "duration_days": 3,
            "slug": "3-day-desert-adventure-white-desert-bahariya-oasis-exploration",
        },
        {
            "title": "3-Day Siwa Oasis Tour | Desert Adventure & Natural Springs",
            "destination": "Siwa",
            "card_image": "trips/cards/463c179280.jpg",
            "hero_image": "trips/hero/95025ecdc5.jpg",
            "teaser": "Three-day escape to Siwa: Oracle Temple, Shali Fortress, Cleopatra’s Bath, salt lakes, and a 4×4 safari in the Great Sand Sea with Bedouin dinner under the stars.",
            "duration_days": 3,
            "slug": "3-day-siwa-oasis-tour-desert-adventure-natural-springs",
        },
        {
            "title": "Adventure Tour to Fayoum Oasis & Wadi El-Hitan with Egyptian Lunch",
            "destination": "Fayoum",
            "card_image": "trips/cards/4217eec125.jpg",
            "hero_image": "trips/hero/2017149ceb.jpg",
            "teaser": "Full-day desert adventure: Fayoum Oasis safari, Wadi El-Hitan fossils, Magic Lake and Wadi El-Rayan waterfalls, plus traditional Egyptian lunch.",
            "duration_days": 1,
            "slug": "adventure-tour-to-fayoum-oasis-wadi-el-hitan-with-egyptian-lunch",
        },
        {
            "title": "Overnight Camping Trip from Cairo to El-Fayoum Oasis – Explore Wadi El Rayan & Magic Lake",
            "destination": "Fayoum",
            "card_image": "trips/cards/c03430637b.jpg",
            "hero_image": "trips/hero/3d235ad7c0.jpg",
            "teaser": "Escape the urban chaos of Cairo and journey into the serene landscapes of El-Fayoum Oasis on this unforgettable overnight adventure—natural wonders, ancient history, and starry desert skies.",
            "duration_days": 1,
            "slug": "overnight-camping-trip-from-cairo-to-el-fayoum-oasis-explore-wadi-el-rayan-magic-lake",
        },
        {
            "title": "Overnight Desert Safari from Cairo: Bahariya Oasis, Black & White Desert",
            "destination": "Bahareya Oasis",
            "card_image": "trips/cards/43d277c6b7.jpg",
            "hero_image": "trips/hero/4d9671c82d.jpg",
            "teaser": "Overnight desert adventure to Bahariya Oasis and the Black & White Desert—unique landscapes, starry camping, and classic Western Desert highlights.",
            "duration_days": 1,
            "slug": "overnight-desert-safari-from-cairo-bahariya-oasis-black-white-desert",
        },
    ]

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        overwrite_images = opts["overwrite_images"]

        # Seed the trips with images and related content
        for trip_data in self.TRIPS:
            destination_obj = Destination.objects.get(name=trip_data["destination"])

            self.stdout.write(self.style.MIGRATE_HEADING(f"Seeding images for {trip_data['title']}"))

            try:
                # Create or update the trip object
                trip_obj, created = Trip.objects.get_or_create(
                    title=trip_data["title"],
                    destination=destination_obj,
                    slug=trip_data["slug"],
                    defaults={
                        "teaser": trip_data["teaser"],
                        "duration_days": trip_data["duration_days"],
                    }
                )

                # Update images if missing or if overwriting is requested
                if overwrite_images or not trip_obj.card_image:
                    trip_obj.card_image.name = trip_data["card_image"]

                if overwrite_images or not trip_obj.hero_image:
                    trip_obj.hero_image.name = trip_data["hero_image"]

                if not dry_run:
                    trip_obj.save()

                self.stdout.write(self.style.SUCCESS(f"Updated {trip_data['title']}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error seeding {trip_data['title']}: {e}"))
                if not dry_run:
                    raise

            # Seed additional trip data like inclusions/exclusions or FAQs if needed (optional)
            if not dry_run:
                self._seed_additional_trip_data(trip_obj)

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("Trip images seeding complete."))

    def _seed_additional_trip_data(self, trip_obj):
        # Example of how to seed additional trip data (inclusions, exclusions, etc.)
        inclusions = [
            "Transportation",
            "Guide",
            "Entrance Fees",
        ]
        exclusions = [
            "Personal Expenses",
            "Tips",
        ]
        for inclusion in inclusions:
            TripInclusion.objects.get_or_create(trip=trip_obj, text=inclusion)
        for exclusion in exclusions:
            TripExclusion.objects.get_or_create(trip=trip_obj, text=exclusion)
        
        # Optionally, you can also seed FAQs or other related models
        # Example:
        # trip_faqs = [
        #     {"question": "What is the duration?", "answer": "3 days"},
        # ]
        # for faq in trip_faqs:
        #     TripFAQ.objects.get_or_create(trip=trip_obj, **faq)
