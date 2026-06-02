"""Configuracao do admin Django para usuarios, perfis e convites."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .forms import (
    AccessInvitationAdminForm,
    DepartmentUserChangeForm,
    DepartmentUserCreationForm,
)
from .models import AccessInvitation, LoginCode, Profile


User = get_user_model()


class ProfileInline(admin.StackedInline):
    """Permite editar o perfil institucional junto do usuario."""

    model = Profile
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name_plural = "perfil"


@admin.register(AccessInvitation)
class AccessInvitationAdmin(admin.ModelAdmin):
    """Admin operacional para acompanhamento e reenvio de convites."""

    form = AccessInvitationAdminForm
    list_display = (
        "email",
        "roles_summary",
        "status_badge",
        "invited_by",
        "sent_at",
        "expires_at",
        "accepted_at",
        "accepted_user",
    )
    list_filter = ("sent_at", "expires_at", "accepted_at")
    search_fields = ("email", "invited_by__email", "accepted_user__email")
    actions = ("resend_selected_invitations",)
    readonly_fields = (
        "token",
        "acceptance_link",
        "invited_by",
        "sent_at",
        "accepted_at",
        "accepted_user",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "expires_at",
                    "notes",
                    "groups",
                    "acceptance_link",
                    "token",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": (
                    "invited_by",
                    "sent_at",
                    "accepted_at",
                    "accepted_user",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Link de aceite")
    def acceptance_link(self, obj):
        """Exibe um atalho de aceite no detalhe do convite."""
        if not obj.pk:
            return "O link sera gerado apos salvar."
        acceptance_url = obj.build_acceptance_url(request=None)
        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            acceptance_url,
            acceptance_url,
        )

    @admin.display(description="Grupos e permissoes")
    def roles_summary(self, obj):
        """Resume os grupos/permissoes configurados no link."""
        return ", ".join(obj.role_labels) or "-"

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Renderiza o status atual do convite com destaque visual."""
        if obj.accepted_at is not None:
            return format_html(
                '<span style="display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;background:#dcfce7;color:#166534;font-weight:700;">{}</span>',
                "Aceito",
            )
        if obj.is_expired:
            return format_html(
                '<span style="display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;background:#fee2e2;color:#991b1b;font-weight:700;">{}</span>',
                "Expirado",
            )
        if obj.sent_at is not None:
            return format_html(
                '<span style="display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;background:#dbeafe;color:#1d4ed8;font-weight:700;">{}</span>',
                "Enviado",
            )
        return format_html(
            '<span style="display:inline-block;padding:0.25rem 0.75rem;border-radius:999px;background:#f3f4f6;color:#374151;font-weight:700;">{}</span>',
            "Rascunho",
        )

    def save_model(self, request, obj, form, change):
        """Envia automaticamente o convite quando ele nasce ou muda de validade."""
        is_new = obj.pk is None
        if is_new and obj.invited_by_id is None:
            obj.invited_by = request.user
        super().save_model(request, obj, form, change)
        should_send = is_new or {"email", "expires_at"} & set(form.changed_data)
        if should_send and obj.accepted_at is None:
            obj.send_invitation_email(request)
            self.message_user(
                request,
                f"Convite enviado para {obj.email}.",
            )

    @admin.action(description="Reenviar convite por e-mail")
    def resend_selected_invitations(self, request, queryset):
        """Acao em lote para gerar novos links e reenviar convites pendentes."""
        sent = 0
        for invitation in queryset:
            if invitation.accepted_at is not None:
                continue
            invitation.regenerate_link()
            invitation.send_invitation_email(request)
            sent += 1
        self.message_user(request, f"{sent} novo(s) link(s) de convite enviado(s).")


@admin.register(LoginCode)
class LoginCodeAdmin(admin.ModelAdmin):
    """Visualizacao somente leitura dos codigos temporarios emitidos."""

    list_display = ("delivery_email", "created_at", "expires_at", "attempts", "consumed_at")
    list_filter = ("created_at", "expires_at", "consumed_at")
    search_fields = ("delivery_email", "user__email", "user__username")
    readonly_fields = ("delivery_email", "code_hash", "created_at", "expires_at", "consumed_at")

    def has_add_permission(self, request):
        return False


class DepartmentUserAdmin(UserAdmin):
    """Admin de usuarios adaptado ao modelo sem senha local."""

    add_form = DepartmentUserCreationForm
    form = DepartmentUserChangeForm
    inlines = (ProfileInline,)
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name", "username")
    readonly_fields = ("last_login", "date_joined")
    actions = ("disable_local_passwords",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "last_login",
                    "date_joined",
                )
            },
        ),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "is_staff", "is_active"),
            },
        ),
    )

    @admin.action(description="Desabilitar senha local dos usuarios selecionados")
    def disable_local_passwords(self, request, queryset):
        """Remove senhas locais para forcar autenticacao externa quando desejado."""
        updated = 0
        for user in queryset:
            if user.is_superuser:
                continue
            user.set_unusable_password()
            user.save(update_fields=["password"])
            updated += 1
        self.message_user(
            request,
            f"{updated} usuario(s) agora dependem apenas de autenticacao externa.",
        )


admin.site.unregister(User)
admin.site.register(User, DepartmentUserAdmin)
