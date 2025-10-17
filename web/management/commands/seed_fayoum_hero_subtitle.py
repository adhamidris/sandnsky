from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import Destination, DestinationName

FAYOUM_HERO_SUBTITLE = (
    "Fayoum is an easy escape from Cairo—an oasis of lakes, dunes, and quiet villages. "
    "Spend time by Lake Qarun, see the Wadi El-Rayan Waterfalls and shimmering Magic Lake, "
    "then head to Wadi El-Hitan (Valley of the Whales) for a UNESCO-listed fossil trail. "
    "Birdlife, desert picnics, and soft sunsets set the pace, while Tunis Village adds pottery "
    "studios and slow travel charm. Short drives connect highlights, making Fayoum ideal for "
    "nature, light adventure, and a reset from city life."
)

class Command(BaseCommand):
    help = "Set or update Destination.hero_subtitle for Fayoum (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show the planned change without saving."
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        try:
            dest = Destination.objects.get(name=DestinationName.FAYOUM)
        except Destination.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                "Destination 'Fayoum' not found. Create it first, then re-run."
            ))
            return

        new_text = FAYOUM_HERO_SUBTITLE.strip()
        before = (dest.hero_subtitle or "").strip()

        if before == new_text:
            self.stdout.write("No change: hero_subtitle already up to date for Fayoum.")
            return

        if dry:
            self.stdout.write(
                f"[DRY-RUN] Would update Fayoum hero_subtitle "
                f"(len {len(before)} -> {len(new_text)} chars)."
            )
        else:
            dest.hero_subtitle = new_text
            dest.save(update_fields=["hero_subtitle"])
            self.stdout.write(self.style.SUCCESS("Updated Fayoum hero_subtitle."))
