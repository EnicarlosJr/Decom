"""Views da landing page publica e do editor de conteudo do front."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory
from django.shortcuts import redirect, render

from accounts.models import user_can_manage_landing_content

from .forms import LandingPageContentForm, LandingSectionItemForm
from .models import LandingPageContent, LandingSectionItem


LandingSectionItemFormSet = inlineformset_factory(
    LandingPageContent,
    LandingSectionItem,
    form=LandingSectionItemForm,
    extra=1,
    can_delete=True,
)

LANDING_SECTION_CONFIGS = [
    {
        "section": LandingSectionItem.Section.HERO_METRIC,
        "title": "Destaques do topo",
        "description": "Cards curtos logo abaixo da capa. Use para chamadas objetivas, prazos, cursos ou pontos de destaque.",
    },
    {
        "section": LandingSectionItem.Section.SERVICE,
        "title": "Cards principais",
        "description": "Cards da area central da landing. Aqui entram os conteudos que realmente precisam aparecer para o publico.",
    },
]


def _has_any_value(*values):
    """Indica se ao menos um valor textual foi preenchido."""
    return any(bool(value) for value in values)


def _build_landing_groups(page):
    """Agrupa os itens dinamicos da landing por secao renderizada."""
    grouped_items = {
        section: list(
            page.items.filter(section=section, is_active=True).order_by("order", "pk")
        )
        for section, _ in LandingSectionItem.Section.choices
    }
    return grouped_items


def _build_editor_sections(page, data=None):
    """Monta os formsets por secao usados no editor da landing."""
    sections = []
    for config in LANDING_SECTION_CONFIGS:
        section = config["section"]
        sections.append(
            {
                **config,
                "formset": LandingSectionItemFormSet(
                    data=data,
                    instance=page,
                    queryset=page.items.filter(section=section).order_by("order", "pk"),
                    prefix=section,
                ),
            }
        )
    return sections


def _save_editor_section(section_formset, page, section):
    """Persiste insercoes, edicoes e exclusoes de uma secao do editor."""
    for deleted_obj in section_formset.deleted_objects:
        deleted_obj.delete()

    for obj in section_formset.save(commit=False):
        obj.page = page
        obj.section = section
        obj.save()


def index(request):
    """Renderiza a landing page publica do portal."""
    page = LandingPageContent.get_solo()
    grouped_items = _build_landing_groups(page)
    hero_metrics = grouped_items[LandingSectionItem.Section.HERO_METRIC]
    service_cards = grouped_items[LandingSectionItem.Section.SERVICE]
    has_contact_panel = _has_any_value(
        page.contact_panel_badge,
        page.contact_panel_description,
        page.contact_cta_label,
    )
    has_services_section = _has_any_value(
        page.services_badge,
        page.services_title,
        page.services_description,
    ) or bool(service_cards)
    has_contact_section = _has_any_value(
        page.contact_badge,
        page.contact_title,
        page.contact_description,
        page.contact_cta_label,
    )
    has_hero_actions = bool(page.hero_secondary_cta_label) or (
        bool(page.hero_primary_cta_label) and has_services_section
    )
    has_hero_content = _has_any_value(
        page.hero_badge,
        page.hero_title,
        page.hero_description,
    ) or has_hero_actions
    return render(
        request,
        "home/index.html",
        {
            "landing_page": page,
            "hero_metrics": hero_metrics,
            "service_cards": service_cards,
            "has_contact_panel": has_contact_panel,
            "has_services_section": has_services_section,
            "has_contact_section": has_contact_section,
            "show_hero_section": has_hero_content or has_contact_panel or bool(hero_metrics),
            "can_manage_landing_content": user_can_manage_landing_content(request.user),
        },
    )


@login_required
def landing_editor(request):
    """Tela autenticada para gestao do conteudo da landing page."""
    if not user_can_manage_landing_content(request.user):
        raise PermissionDenied

    page = LandingPageContent.get_solo()

    if request.method == "POST":
        content_form = LandingPageContentForm(request.POST, instance=page)
        editor_sections = _build_editor_sections(page, data=request.POST)
        all_valid = content_form.is_valid() and all(
            section["formset"].is_valid() for section in editor_sections
        )

        if all_valid:
            content_form.save()
            for section in editor_sections:
                _save_editor_section(section["formset"], page, section["section"])
            messages.success(
                request,
                "O conteudo publico da landing page foi atualizado.",
            )
            return redirect("home:landing_editor")
        messages.error(
            request,
            "Revise os campos destacados antes de salvar a landing page.",
        )
    else:
        content_form = LandingPageContentForm(instance=page)
        editor_sections = _build_editor_sections(page)

    return render(
        request,
        "home/landing_editor.html",
        {
            "content_form": content_form,
            "editor_sections": editor_sections,
            "landing_page": page,
        },
    )
