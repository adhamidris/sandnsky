from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Destination, DestinationGalleryImage, SiteConfiguration
from web.models import DestinationName


class Command(BaseCommand):
    help = "Seed/update destination images and related gallery items."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print changes without saving to the DB",
        )
        parser.add_argument(
            "--overwrite-images",
            action="store_true",
            help="Overwrite existing images if set",
        )

    # Seed each destination with images and gallery items
    DESTINATIONS = {
        "Farafra": {
            "description": (
                "Relaxed oasis near the White Desert with hot springs and local art. "
                "Highlights: Badr Museum, Bir Sitta hot spring, White Desert."
            ),
            "hero_subtitle": (
                "Farafra is a small, unhurried oasis known for hot springs and local art. "
                "It’s the closest community to the White Desert, making it a convenient jump-off "
                "for sunset views and morning walks among the chalk formations. The Badr Museum showcases "
                "desert life through sculpture and painting, while Bir Sitta offers an easy soak."
            ),
            "card_image": "destinations/a6f96e9a87.jpg",
            "hero_image": "destinations/hero/4bd985d347.jpg",
            "gallery_images": [
                ("destinations/gallery/4bd985d347.jpg", 1),
                ("destinations/gallery/4d9671c82d.jpg", 2),
                ("destinations/gallery/5bc2ef7c82.jpg", 3),
                ("destinations/gallery/447eed3c92.jpg", 4),
                ("destinations/gallery/785ac5d804.jpg", 5),
            ],
            "featured_position": 4,
        },
        "Siwa": {
            "description": (
                "Quiet desert oasis with salt lakes and palm groves. Highlights: Shali Fortress, Cleopatra Spring, Great Sand Sea."
            ),
            "hero_subtitle": (
                "Siwa is Egypt’s most remote oasis, known for quiet landscapes and strong Amazigh traditions. "
                "Days revolve around visits to the Oracle Temple of Amun, the mud-brick Shali Fortress, and "
                "soothing dips in Cleopatra’s Spring. The area’s salt lakes are famously buoyant, while nearby hot "
                "springs offer natural relaxation."
            ),
            "card_image": "destinations/95025ecdc5_09O8OLg.jpg",
            "hero_image": "destinations/hero/463c179280_AmQ1Fm0.jpg",
            "gallery_images": [
                ("destinations/gallery/4be6a3b6e4_q2RuZFW.jpg", 1),
                ("destinations/gallery/92d71d0fbc_Jrssf5H.jpg", 2),
                ("destinations/gallery/463c179280_vX0WN9U.jpg", 3),
                ("destinations/gallery/903f27f591_I6YlqUA.jpg", 5),
                ("destinations/gallery/94050b6650_51aHJ9G.jpg", 6),
            ],
            "featured_position": 2,
        },
        "White & Black Desert": {
            "description": (
                "Striking white rock formations and black basalt hills. Highlights: Aqabat Valley, Crystal Mountain, Black Desert."
            ),
            "hero_subtitle": (
                "The White & Black Desert region showcases Egypt’s most distinctive geology in a compact area. "
                "The Black Desert features dark basalt peaks and golden sands, leading toward Crystal Mountain and "
                "the sculpted chalk landscapes of the White Desert. Camping here is a highlight, with wide skies and "
                "clear stars."
            ),
            "card_image": "destinations/785ac5d804.jpg",
            "hero_image": "destinations/hero/43d277c6b7.jpg",
            "gallery_images": [
                ("destinations/gallery/4bd985d347.jpg", 1),
                ("destinations/gallery/4d9671c82d.jpg", 2),
                ("destinations/gallery/5bc2ef7c82.jpg", 3),
                ("destinations/gallery/447eed3c92.jpg", 4),
                ("destinations/gallery/785ac5d804.jpg", 5),
            ],
            "featured_position": 3,
        },
    }

    HERO_BANNER = {
        "hero_image": "site/hero/5926689bcd.jpg",
        "hero_title": "Discover the Magic of Egypt",
        "hero_subtitle": "Embark on an unforgettable journey through ancient wonders and timeless beauty",
        "primary_cta_label": "Explore Tours",
        "primary_cta_href": "/trips",
        "secondary_cta_label": "Learn More",
        "secondary_cta_href": "#about",
    }

    @transaction.atomic
    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        overwrite_images = opts["overwrite_images"]

        # Seed the destinations and hero banner
        for dest_name, dest_data in self.DESTINATIONS.items():
            self.stdout.write(self.style.MIGRATE_HEADING(f"Seeding images for {dest_name}"))

            try:
                dest_obj, created = Destination.objects.get_or_create(name=dest_name)

                # Update destination fields
                dest_obj.description = dest_data["description"]
                dest_obj.hero_subtitle = dest_data["hero_subtitle"]
                dest_obj.card_image.name = dest_data["card_image"] if overwrite_images or not dest_obj.card_image else dest_obj.card_image.name
                dest_obj.hero_image.name = dest_data["hero_image"] if overwrite_images or not dest_obj.hero_image else dest_obj.hero_image.name
                dest_obj.is_featured = True
                dest_obj.featured_position = dest_data["featured_position"]

                if not dry_run:
                    dest_obj.save()

                self.stdout.write(self.style.SUCCESS(f"Updated {dest_name}"))

                # Seed gallery images
                for img_path, position in dest_data["gallery_images"]:
                    gallery_item, created = DestinationGalleryImage.objects.get_or_create(
                        destination=dest_obj,
                        position=position,
                        defaults={"caption": dest_name},
                    )
                    if not dry_run and (overwrite_images or not gallery_item.image):
                        gallery_item.image.name = img_path
                        gallery_item.save()

                    self.stdout.write(self.style.SUCCESS(f"Gallery image for {dest_name} at position {position}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error seeding {dest_name}: {e}"))
                if not dry_run:
                    raise

        # Seed Hero Banner
        try:
            site_config = SiteConfiguration.get_solo()
            site_config.hero_image.name = self.HERO_BANNER["hero_image"] if overwrite_images or not site_config.hero_image else site_config.hero_image.name
            site_config.hero_title = self.HERO_BANNER["hero_title"]
            site_config.hero_subtitle = self.HERO_BANNER["hero_subtitle"]
            site_config.hero_primary_cta_label = self.HERO_BANNER["primary_cta_label"]
            site_config.hero_primary_cta_href = self.HERO_BANNER["primary_cta_href"]
            site_config.hero_secondary_cta_label = self.HERO_BANNER["secondary_cta_label"]
            site_config.hero_secondary_cta_href = self.HERO_BANNER["secondary_cta_href"]

            if not dry_run:
                site_config.save()

            self.stdout.write(self.style.SUCCESS(f"Updated Hero Banner"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error seeding Hero Banner: {e}"))
            if not dry_run:
                raise

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("Image seeding complete."))
