from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import RewardPhase, RewardPhaseTrip


def _invalidate_reward_cache():
    # Import locally to avoid circular dependency during app loading.
    from .rewards import invalidate_reward_phase_cache

    invalidate_reward_phase_cache()


@receiver(post_save, sender=RewardPhase)
def reward_phase_saved(sender, **kwargs):
    _invalidate_reward_cache()


@receiver(post_delete, sender=RewardPhase)
def reward_phase_deleted(sender, **kwargs):
    _invalidate_reward_cache()


@receiver(post_save, sender=RewardPhaseTrip)
def reward_phase_trip_saved(sender, **kwargs):
    _invalidate_reward_cache()


@receiver(post_delete, sender=RewardPhaseTrip)
def reward_phase_trip_deleted(sender, **kwargs):
    _invalidate_reward_cache()
