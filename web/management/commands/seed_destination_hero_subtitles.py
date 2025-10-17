from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import Destination, DestinationName

SUBTITLES = {
    DestinationName.BAHAREYA: """Bahariya offers an easy desert escape from Cairo with palm groves, warm springs, and a relaxed pace. It’s a practical base for exploring nearby highlights like the Black Desert’s volcanic hills, Crystal Mountain’s quartz ridge, and the dunes around Aqabat Valley. Many visitors pair Bahariya with camping in the White Desert, where chalk formations light up at sunrise and sunset. In town, simple lodges, local meals, and friendly guides make logistics straightforward. If you want a classic Western Desert experience without long transfers, Bahariya is a smart starting point.""",

    DestinationName.SIWA: """Siwa is Egypt’s most remote oasis, known for quiet landscapes and strong Amazigh traditions. Days revolve around visits to the Oracle Temple of Amun, the mud-brick Shali Fortress, and soothing dips in Cleopatra’s Spring. The area’s salt lakes are famously buoyant and photogenic, while nearby hot springs offer natural relaxation. Adventure picks up in the Great Sand Sea, with 4×4 rides, sandboarding, and starry desert dinners. Siwa suits travelers seeking culture, nature, and time to slow down far from the city.""",

    DestinationName.WHITE_BLACK: """The White & Black Desert region showcases Egypt’s most distinctive geology in a compact area. The Black Desert features dark basalt peaks and golden sands, leading toward Crystal Mountain and the sculpted chalk landscapes of the White Desert. Camping here is a highlight: wide skies, clear stars, and sunrise light on strange rock shapes. Short drives connect major viewpoints like Aqabat Valley, making it ideal for one or two nights out. If you want pure desert scenery with simple logistics, this is the go-to circuit.""",

    DestinationName.FARAFRA: """Farafra is a small, unhurried oasis known for hot springs and local art. It’s the closest community to the White Desert, which makes it a convenient jump-off for sunset views and morning walks among the chalk formations. In town, the Badr Museum showcases desert life through sculpture and painting, while Bir Sitta offers an easy soak. Travel services are low-key but welcoming, with guesthouses and guides used to overnighters. Farafra fits travelers who value quiet stops and direct access to the White Desert.""",

    DestinationName.DAKHLA: """Dakhla blends dunes, date farms, and historic villages across a wide, green valley. The standout is Al-Qasr, a preserved medieval settlement of mud-brick alleys and old workshops. Nearby, Deir el-Hagar temple and desert hot springs round out a calm cultural circuit. Accommodation ranges from simple lodges to small eco-stays, and day trips reach viewpoints across the surrounding sands. Dakhla is best for travelers who enjoy heritage walks and steady, scenic drives between sites.""",

    DestinationName.KHARGA: """Kharga is the largest of Egypt’s oases and a crossroads of ancient routes. The Temple of Hibis anchors the area’s archaeology, while the Bagawat Necropolis preserves early Christian chapels and painted tombs. The landscape is open and easy to navigate, with long desert roads linking farms and small communities. Services are practical, and visits pair well with onward travel to Dakhla or the White Desert. Kharga suits travelers interested in clear, well-signed sites and a broad view of desert history.""",
}

class Command(BaseCommand):
    help = "Set or update Destination.hero_subtitle for known destinations (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving."
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        updated = 0
        missing = []

        for dest_choice, subtitle in SUBTITLES.items():
            try:
                dest = Destination.objects.get(name=dest_choice)
            except Destination.DoesNotExist:
                missing.append(dest_choice)
                continue

            subtitle = (subtitle or "").strip()
            before = (dest.hero_subtitle or "").strip()

            if before == subtitle:
                self.stdout.write(f"No change: {dest_choice}")
                continue

            if dry:
                self.stdout.write(
                    f"Would update {dest_choice} hero_subtitle "
                    f"(len {len(before)} -> {len(subtitle)} chars)"
                )
            else:
                dest.hero_subtitle = subtitle
                dest.save(update_fields=["hero_subtitle"])
                self.stdout.write(self.style.SUCCESS(f"Updated: {dest_choice}"))
                updated += 1

        if missing:
            self.stdout.write(self.style.WARNING(
                "Missing Destination rows (not updated): " + ", ".join(missing)
            ))
        if dry:
            self.stdout.write(self.style.WARNING("Dry-run complete. No changes saved."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Done. Updated {updated} destination(s)."))
