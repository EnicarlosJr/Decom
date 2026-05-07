"""Configuracao da aplicacao de contas e autenticacao."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Carrega sinais e metadados da app de contas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Importa os sinais no boot do Django."""
        from . import signals  # noqa: F401
