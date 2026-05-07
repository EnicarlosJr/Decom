from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def default_expires_at():
    return timezone.now() + timedelta(days=7)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_seed_profiles"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("token", models.CharField(editable=False, max_length=80, unique=True)),
                ("notes", models.TextField(blank=True, verbose_name="observacoes")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="enviado em")),
                ("accepted_at", models.DateTimeField(blank=True, null=True, verbose_name="aceito em")),
                ("expires_at", models.DateTimeField(default=default_expires_at, verbose_name="expira em")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "accepted_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="accepted_access_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="issued_access_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "convite de acesso",
                "verbose_name_plural": "convites de acesso",
                "ordering": ["-created_at"],
            },
        ),
    ]
