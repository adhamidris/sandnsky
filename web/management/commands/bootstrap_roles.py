from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

# Default role-to-permission mapping. Each tuple is (app_label, model, permission_codename_prefixes).
# Adjust the lists below to fit your org needs.
ALL = ["add", "change", "delete", "view"]
READ = ["view"]

ROLE_CONFIG = {
    "Booking Manager": [
        ("web", "booking", ALL),
        ("web", "bookingextra", ALL),
        ("web", "bookingreward", ALL),
    ],
    "Content Editor": [
        ("web", "trip", ALL),
        ("web", "tripabout", ALL),
        ("web", "triphighlight", ALL),
        ("web", "tripgalleryimage", ALL),
        ("web", "tripitineraryday", ALL),
        ("web", "tripitinerarystep", ALL),
        ("web", "tripinclusion", ALL),
        ("web", "tripexclusion", ALL),
        ("web", "tripfaq", ALL),
        ("web", "tripbookingoption", ALL),
        ("web", "tripextra", ALL),
        ("web", "triprelation", ALL),
        ("web", "blogpost", ALL),
        ("web", "blogsection", ALL),
        ("web", "destination", ALL),
        ("web", "destinationgalleryimage", ALL),
        ("web", "review", ALL),
        ("web", "rewardphase", ALL),
        ("web", "rewardphasetrip", ALL),
    ],
    "SEO Manager": [
        ("seo", "seoentry", ALL),
        ("seo", "seofaq", ALL),
        ("seo", "seosnippet", ALL),
        ("seo", "seoredirect", ALL),
    ],
    "Site Manager": [
        ("web", "siteconfiguration", ALL),
        ("web", "siteheropair", ALL),
    ],
    "Read Only": [
        ("web", "booking", READ),
        ("web", "trip", READ),
        ("web", "tripabout", READ),
        ("web", "triphighlight", READ),
        ("web", "tripgalleryimage", READ),
        ("web", "tripitineraryday", READ),
        ("web", "tripitinerarystep", READ),
        ("web", "tripinclusion", READ),
        ("web", "tripexclusion", READ),
        ("web", "tripfaq", READ),
        ("web", "tripbookingoption", READ),
        ("web", "tripextra", READ),
        ("web", "triprelation", READ),
        ("web", "blogpost", READ),
        ("web", "blogsection", READ),
        ("web", "destination", READ),
        ("web", "destinationgalleryimage", READ),
        ("web", "review", READ),
        ("web", "siteconfiguration", READ),
        ("web", "siteheropair", READ),
        ("web", "rewardphase", READ),
        ("seo", "seoentry", READ),
    ],
}

RETIRED_ROLES = {
    "Review Moderator",
    "Rewards Manager",
}


class Command(BaseCommand):
    help = "Create/update default staff role groups with recommended permissions."

    def handle(self, *args, **options):
        for role_name, model_perms in ROLE_CONFIG.items():
            group, created = Group.objects.get_or_create(name=role_name)
            added = 0

            for app_label, model, codes in model_perms:
                for perm in self._get_perms(app_label, model, codes):
                    if not group.permissions.filter(id=perm.id).exists():
                        group.permissions.add(perm)
                        added += 1

            status = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{status.capitalize()} group '{role_name}' (added {added} permissions)"
                )
            )

        # Remove retired roles explicitly so they stop appearing in the UI.
        for retired in RETIRED_ROLES:
            deleted, _ = Group.objects.filter(name=retired).delete()
            if deleted:
                self.stdout.write(
                    self.style.WARNING(f"Deleted retired role group '{retired}'")
                )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "Done. Assign staff users to the appropriate groups; superusers already bypass this."
            )
        )

    def _get_perms(self, app_label, model, codes):
        """
        Resolve Permission objects for the given model and permission code prefixes.
        """
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f"Skipping missing content type {app_label}.{model}")
            )
            return []

        codenames = [f"{code}_{model}" for code in codes]
        perms = Permission.objects.filter(
            content_type=content_type, codename__in=codenames
        )
        missing = set(codenames) - set(perms.values_list("codename", flat=True))
        for codename in missing:
            self.stdout.write(
                self.style.WARNING(
                    f"Permission '{app_label}.{codename}' not found; ensure the model has that default permission."
                )
            )
        return list(perms)
