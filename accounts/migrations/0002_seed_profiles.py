from django.conf import settings
from django.db import migrations


def seed_profiles(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    user_model = apps.get_model(app_label, model_name)
    profile_model = apps.get_model("accounts", "Profile")

    for user in user_model.objects.all():
        full_name = f"{user.first_name} {user.last_name}".strip()
        profile_model.objects.get_or_create(
            user=user,
            defaults={"display_name": full_name},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_profiles, migrations.RunPython.noop),
    ]
