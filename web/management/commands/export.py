from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from web.models import Trip


NOVTRIP_TITLES = [
    "Cairo: Guided Day Tour to Bab al-Futuh & Old Cairo Treasures",
    "Discover Museum of Islamic Art: Half-Day Private Tour",
    "Wadi Degla Tour: Hike, Wildlife, and Scenic Desert Views",
    "Female-Led Cooking & Countryside Farm Tour in Rural Egypt.",
    "El Alamein Day Tour From Cairo",
    "Tour to Cairo Citadel, Khan El-Khalil and Coptic Cairo",
    "Islamic Cairo Full Day Tour",
    "Cairo Mosques and Khan El Khalili Bazaar Tour",
    "Day Trip To Egyptian Museum, Old Cairo",
    "Day Tour To Manial Palace and Cairo Tower",
    "Polar Express Ski Egypt",
    "Coptic Cairo and Cave Church Half Day Tour",
    "Pharaonic Village Tour",
    "Tour To El Moez Street, Bayt Al-Suhaymi and Al Azhar Park With Lunch",
    "Tuk Tuk Ride Tour",
    "Egyptian House Dinner",
    "Half Day Tour to The National Museum of Egyptian Civilization",
    "Tour To the museums of Abdeen Palace In Cairo",
    "Cairo Kayaking Tour on The Nile River",
    'Mall Misr "Mall of Egypt" Shopping Tour',
    "Cairo Photo Session Add On Tour",
    "Sunset at Cairo Tower With Dinner",
    "Al Tannoura Egyptian Heritage Dance Troupe Cairo",
]


class Command(BaseCommand):
    help = (
        "Export image paths (card, hero, gallery) for the 23 November trips "
        "into novtrip_images.json so they can be applied on another DB."
    )

    def handle(self, *args, **options):
        manifest: dict[str, dict] = {}
        missing = []

        for title in NOVTRIP_TITLES:
            trip = Trip.objects.filter(title=title).first()
            if not trip:
                missing.append(title)
                continue

            gallery = []
            for g in trip.gallery_images.order_by("position", "id"):
                gallery.append(
                    {
                        "image": g.image.name,
                        "caption": g.caption,
                        "position": g.position,
                        "image_width": g.image_width,
                        "image_height": g.image_height,
                    }
                )

            manifest[title] = {
                "card_image": trip.card_image.name or "",
                "hero_image": trip.hero_image.name or "",
                "gallery": gallery,
            }

        out_path = Path("novtrip_images.json")
        out_path.write_text(json.dumps(manifest, indent=2))

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {len(manifest)} trips to {out_path} "
                f"(missing: {len(missing)})"
            )
        )
        if missing:
            self.stdout.write(self.style.WARNING("Trips not found locally:"))
            for t in missing:
                self.stdout.write(f"  - {t}")
