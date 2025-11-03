from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import Trip


@receiver(m2m_changed, sender=Trip.additional_destinations.through)
def handle_additional_destinations_change(sender, instance, action, **kwargs):
    if action not in {"post_add", "post_remove", "post_clear"}:
        return
    if not isinstance(instance, Trip):
        return
    instance.sync_package_trip_category()
