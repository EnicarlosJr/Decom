"""Configuracao do admin Django para o conteudo da landing page."""

from django.contrib import admin

from .models import LandingPageContent, LandingSectionItem


class LandingSectionItemInline(admin.TabularInline):
    """Edicao inline dos cards e blocos da landing."""

    model = LandingSectionItem
    extra = 0
    fields = (
        "section",
        "order",
        "is_active",
        "label",
        "title",
        "description",
        "action_label",
        "action_url",
    )
    ordering = ("section", "order", "pk")


@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    """Mantem a configuracao unica da landing page no admin."""

    list_display = ("__str__", "updated_at")
    inlines = (LandingSectionItemInline,)

    def has_add_permission(self, request):
        """Impede que o admin crie mais de uma configuracao principal."""
        if LandingPageContent.objects.exists():
            return False
        return super().has_add_permission(request)
