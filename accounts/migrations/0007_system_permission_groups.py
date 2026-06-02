from django.db import migrations


PROFILE_ROLE_GROUPS = {
    "is_student": "Alunos",
    "is_professor": "Professores",
    "is_technician": "Tecnicos administrativos",
    "is_department_head": "Chefes de departamento",
    "is_course_coordinator": "Coordenadores de curso",
    "is_internship_coordinator": "Coordenadores de estagio",
    "is_tcc1_coordinator": "Coordenadores de TCC 1",
    "is_tcc2_coordinator": "Coordenadores de TCC 2",
}

LANDING_MANAGER_GROUP = "Editores da landing page"


def create_and_sync_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Profile = apps.get_model("accounts", "Profile")

    groups = {}
    for group_name in [*PROFILE_ROLE_GROUPS.values(), LANDING_MANAGER_GROUP]:
        groups[group_name], _ = Group.objects.get_or_create(name=group_name)

    for profile in Profile.objects.select_related("user"):
        selected_groups = [
            groups[group_name]
            for field_name, group_name in PROFILE_ROLE_GROUPS.items()
            if getattr(profile, field_name)
        ]
        if profile.can_manage_landing_page:
            selected_groups.append(groups[LANDING_MANAGER_GROUP])
        if selected_groups:
            profile.user.groups.add(*selected_groups)


def remove_empty_system_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    group_names = [*PROFILE_ROLE_GROUPS.values(), LANDING_MANAGER_GROUP]
    Group.objects.filter(name__in=group_names, user__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_accessinvitation_roles"),
    ]

    operations = [
        migrations.RunPython(create_and_sync_groups, remove_empty_system_groups),
    ]
