from django.db import migrations, models
import django.db.models.deletion


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


def copy_invitation_flags_to_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    AccessInvitation = apps.get_model("accounts", "AccessInvitation")

    groups = {}
    for group_name in [*PROFILE_ROLE_GROUPS.values(), LANDING_MANAGER_GROUP]:
        groups[group_name], _ = Group.objects.get_or_create(name=group_name)

    for invitation in AccessInvitation.objects.all():
        selected_groups = [
            groups[group_name]
            for field_name, group_name in PROFILE_ROLE_GROUPS.items()
            if getattr(invitation, field_name)
        ]
        if selected_groups:
            invitation.groups.add(*selected_groups)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_system_permission_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="accessinvitation",
            name="groups",
            field=models.ManyToManyField(
                blank=True,
                related_name="access_invitations",
                to="auth.group",
                verbose_name="grupos e permissoes",
            ),
        ),
        migrations.RunPython(copy_invitation_flags_to_groups, migrations.RunPython.noop),
        migrations.RemoveField(model_name="accessinvitation", name="is_student"),
        migrations.RemoveField(model_name="accessinvitation", name="is_professor"),
        migrations.RemoveField(model_name="accessinvitation", name="is_technician"),
        migrations.RemoveField(model_name="accessinvitation", name="is_department_head"),
        migrations.RemoveField(model_name="accessinvitation", name="is_course_coordinator"),
        migrations.RemoveField(model_name="accessinvitation", name="is_internship_coordinator"),
        migrations.RemoveField(model_name="accessinvitation", name="is_tcc1_coordinator"),
        migrations.RemoveField(model_name="accessinvitation", name="is_tcc2_coordinator"),
        migrations.RemoveField(model_name="profile", name="is_student"),
        migrations.RemoveField(model_name="profile", name="is_professor"),
        migrations.RemoveField(model_name="profile", name="is_technician"),
        migrations.RemoveField(model_name="profile", name="is_department_head"),
        migrations.RemoveField(model_name="profile", name="is_course_coordinator"),
        migrations.RemoveField(model_name="profile", name="is_internship_coordinator"),
        migrations.RemoveField(model_name="profile", name="is_tcc1_coordinator"),
        migrations.RemoveField(model_name="profile", name="is_tcc2_coordinator"),
        migrations.RemoveField(model_name="profile", name="can_manage_landing_page"),
    ]
