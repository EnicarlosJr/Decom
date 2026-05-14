"""Formularios usados para manter o conteudo da landing page."""

from django import forms

from .models import LandingPageContent, LandingSectionItem


FIELD_INPUT_CLASS = (
    ""
)

FIELD_TEXTAREA_CLASS = (
    ""
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
            "hero_description": forms.Textarea(
                attrs={"class": FIELD_TEXTAREA_CLASS, "rows": 4}
            ),
            "hero_primary_cta_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "hero_secondary_cta_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "services_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "services_title": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "services_description": forms.Textarea(
                attrs={"class": FIELD_TEXTAREA_CLASS, "rows": 4}
            ),
            "contact_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "contact_title": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "contact_description": forms.Textarea(
                attrs={"class": FIELD_TEXTAREA_CLASS, "rows": 4}
            ),
            "contact_panel_badge": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
            "contact_panel_description": forms.Textarea(
                attrs={"class": FIELD_TEXTAREA_CLASS, "rows": 4}
            ),
            "contact_cta_label": forms.TextInput(attrs={"class": FIELD_INPUT_CLASS}),
        }
        labels = {
            "hero_badge": "Selo do topo",
            "hero_title": "Titulo principal",
            "hero_description": "Descricao principal",
            "hero_primary_cta_label": "Texto do botao principal",
            "hero_secondary_cta_label": "Texto do botao secundario",
            "services_badge": "Selo da secao de servicos",
            "services_title": "Titulo da secao de servicos",
            "services_description": "Descricao da secao de servicos",
            "contact_badge": "Selo da secao final",
            "contact_title": "Titulo da secao final",
            "contact_description": "Descricao da secao final",
            "contact_panel_badge": "Selo do painel lateral",
            "contact_panel_description": "Descricao do painel lateral",
            "contact_cta_label": "Texto do botao final",
        }
        help_texts = {
            "hero_badge": "Rotulo curto acima do titulo. Deixe em branco para ocultar.",
            "hero_title": "Mensagem principal exibida na primeira dobra da pagina.",
            "hero_description": "Resumo institucional da pagina. Prefira um paragrafo curto.",
            "hero_primary_cta_label": "Texto do botao principal da capa.",
            "hero_secondary_cta_label": "Texto do botao de apoio exibido ao lado da acao principal.",
            "services_badge": "Rotulo curto para apresentar os cards centrais.",
            "services_title": "Titulo da secao principal de servicos ou destaques.",
            "services_description": "Texto introdutorio curto para contextualizar os cards.",
            "contact_badge": "Rotulo curto da secao final da pagina.",
            "contact_title": "Titulo da chamada final exibida antes do rodape.",
            "contact_description": "Mensagem institucional de encerramento ou orientacao final.",
            "contact_panel_badge": "Selo do painel lateral da secao final.",
            "contact_panel_description": "Texto curto do painel lateral. Deixe vazio para ocultar.",
            "contact_cta_label": "Texto do botao final exibido na secao de contato.",
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
            "description": forms.Textarea(
                attrs={"class": FIELD_TEXTAREA_CLASS, "rows": 4}
            ),
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
        labels = {
            "label": "Rotulo",
            "title": "Titulo",
            "description": "Descricao",
            "action_label": "Texto do link",
            "action_url": "URL do link",
            "order": "Ordem de exibicao",
            "is_active": "Ativo",
        }
        help_texts = {
            "label": "Rotulo curto opcional exibido acima do titulo.",
            "title": "Titulo principal do card ou destaque.",
            "description": "Texto de apoio. Use frases objetivas e evite excesso de informacao.",
            "action_label": "Texto do link ou botao quando houver destino.",
            "action_url": "Use rota interna ou URL completa para a acao do item.",
            "order": "Define a ordem de exibicao. Menores valores aparecem primeiro.",
        }
