"""Configuracao da aplicacao responsavel pela home do portal."""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """Metadados da app de home e landing page."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "home"
