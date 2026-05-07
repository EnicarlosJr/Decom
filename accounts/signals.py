"""Sinais que mantem perfis de usuario sincronizados com o auth Django."""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    """Cria automaticamente um perfil para cada novo usuario autenticado."""
    if created:
        Profile.objects.create(user=instance, display_name=instance.get_full_name())
