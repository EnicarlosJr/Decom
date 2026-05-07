"""Formularios usados para manter o conteudo da landing page."""

from django import forms

from .models import LandingPageContent, LandingSectionItem


FIELD_INPUT_CLASS = (
    "field-input block w-full rounded-2xl border border-slate-300 "
    "bg-white px-4 py-4 text-slate-900 placeholder-slate-400 shadow-sm "
    "outline-none transition focus:border-gov.blue focus:ring-4 "
    "focus:ring-[rgba(53,91,136,0.12)]"
)

FIELD_TEXTAREA_CLASS = (
    "field-input block min-h-28 w-full rounded-2xl border border-slate-300 "
    "bg-white px-4 py-4 text-slate-900 placeholder-slate-400 shadow-sm "
    "outline-none transition focus:border-gov.blue focus:ring-4 "
    "focus:ring-[rgba(53,91,136,0.12)]"
)


class LandingPageContentForm(forms.ModelForm):
    """Edicao dos campos textuais principais da landing page."""

    class Meta:
        model = LandingPageContent
        fields = (
            "hero_badge",
            "hero_title",
            "hero_description",
            "hero_primary_cta_label",
            "hero_secondary_cta_label",
            "services_badge",
            "services_title",
            "services_description",
            "contact_badge",
            "contact_title",
            "contact_description",
            "contact_panel_badge",
            "contact_panel_description",
            "contact_cta_label",
        )
        widgets = {
            "hero_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "hero_title": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "hero_description": forms.Textarea(attrs={"class": FIELD_TEXTAREA_CLASS}),
            "hero_primary_cta_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "hero_secondary_cta_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "services_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "services_title": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "services_description": forms.Textarea(attrs={"class": FIELD_TEXTAREA_CLASS}),
            "contact_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "contact_title": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "contact_description": forms.Textarea(attrs={"class": FIELD_TEXTAREA_CLASS}),
            "contact_panel_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "contact_panel_description": forms.Textarea(attrs={"class": FIELD_TEXTAREA_CLASS}),
            "contact_cta_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
        }


class LandingSectionItemForm(forms.ModelForm):
    """Edicao de cards e blocos dinamicos da landing page."""

    class Meta:
        model = LandingSectionItem
        fields = (
            "label",
            "title",
            "description",
            "action_label",
            "action_url",
            "order",
            "is_active",
        )
        widgets = {
            "label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "title": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": FIELD_TEXTAREA_CLASS}),
            "action_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "action_url": forms.TextInput(
                attrs={
                    "class": FIELD_INPUT_CLASS,
                    "placeholder": "/pagina-interna/ ou https://exemplo.com",
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": FIELD_INPUT_CLASS,
                    "min": 0,
                    "step": 10,
                }
            ),
        }
