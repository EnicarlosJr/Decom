"""Modelos usados para tornar o conteudo da landing page administravel."""

from django.db import models


class LandingPageContent(models.Model):
    """Configuracao principal dos textos fixos exibidos na home."""
    hero_badge = models.CharField("selo do topo", max_length=120, blank=True, default="")
    hero_title = models.CharField("titulo principal", max_length=220, blank=True, default="")
    hero_description = models.TextField("descricao principal", blank=True, default="")
    hero_primary_cta_label = models.CharField(
        "texto do botao principal",
        max_length=60,
        blank=True,
        default="",
    )
    hero_secondary_cta_label = models.CharField(
        "texto do botao secundario",
        max_length=60,
        blank=True,
        default="",
    )
    access_badge = models.CharField(
        "selo do bloco de acesso", max_length=120, blank=True, default=""
    )
    access_title = models.CharField(
        "titulo do bloco de acesso", max_length=180, blank=True, default=""
    )
    access_description = models.TextField(
        "descricao do bloco de acesso", blank=True, default=""
    )
    access_cta_label = models.CharField(
        "texto do botao de acesso",
        max_length=60,
        blank=True,
        default="",
    )
    services_badge = models.CharField(
        "selo da secao de servicos", max_length=120, blank=True, default=""
    )
    services_title = models.CharField(
        "titulo da secao de servicos", max_length=180, blank=True, default=""
    )
    services_description = models.TextField(
        "descricao da secao de servicos", blank=True, default=""
    )
    modules_badge = models.CharField(
        "selo da secao autenticada", max_length=120, blank=True, default=""
    )
    modules_title = models.CharField(
        "titulo da secao autenticada", max_length=180, blank=True, default=""
    )
    modules_description = models.TextField(
        "descricao da secao autenticada", blank=True, default=""
    )
    contact_badge = models.CharField(
        "selo da secao final", max_length=120, blank=True, default=""
    )
    contact_title = models.CharField(
        "titulo da secao final", max_length=180, blank=True, default=""
    )
    contact_description = models.TextField(
        "descricao da secao final", blank=True, default=""
    )
    contact_panel_badge = models.CharField(
        "selo do painel lateral final", max_length=120, blank=True, default=""
    )
    contact_panel_description = models.TextField(
        "descricao do painel lateral final", blank=True, default=""
    )
    contact_cta_label = models.CharField(
        "texto do botao final",
        max_length=60,
        blank=True,
        default="",
    )
    updated_at = models.DateTimeField(auto_now=True)

    TEXT_FIELD_NAMES = (
        "hero_badge",
        "hero_title",
        "hero_description",
        "hero_primary_cta_label",
        "hero_secondary_cta_label",
        "access_badge",
        "access_title",
        "access_description",
        "access_cta_label",
        "services_badge",
        "services_title",
        "services_description",
        "modules_badge",
        "modules_title",
        "modules_description",
        "contact_badge",
        "contact_title",
        "contact_description",
        "contact_panel_badge",
        "contact_panel_description",
        "contact_cta_label",
    )

    class Meta:
        verbose_name = "configuracao da landing page"
        verbose_name_plural = "configuracoes da landing page"

    def __str__(self):
        return "Landing page principal"

    @classmethod
    def default_values(cls):
        """Conteudo inicial vazio para publicacao posterior pelo admin."""
        return {field_name: "" for field_name in cls.TEXT_FIELD_NAMES}

    @classmethod
    def get_solo(cls):
        """Recupera a unica configuracao de landing, criando o baseline se preciso."""
        page = cls.objects.order_by("pk").first()
        if page is None:
            return cls.objects.create(**cls.default_values())
        return page


class LandingSectionItem(models.Model):
    """Item dinamico de uma secao da landing page."""

    class Section(models.TextChoices):
        HERO_METRIC = "hero_metric", "Metricas do topo"
        ACCESS_STEP = "access_step", "Etapas de acesso"
        SERVICE = "service", "Cartoes de servicos"
        MODULE_POINT = "module_point", "Destaques da area autenticada"
        AUDIENCE_CARD = "audience_card", "Cartoes de perfis"

    page = models.ForeignKey(
        LandingPageContent,
        on_delete=models.CASCADE,
        related_name="items",
    )
    section = models.CharField("secao", max_length=30, choices=Section.choices)
    label = models.CharField("rotulo", max_length=80, blank=True)
    title = models.CharField("titulo", max_length=180)
    description = models.TextField("descricao", blank=True)
    action_label = models.CharField("texto do link", max_length=60, blank=True)
    action_url = models.CharField("URL do link", max_length=255, blank=True)
    order = models.PositiveSmallIntegerField("ordem", default=10)
    is_active = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "item da landing page"
        verbose_name_plural = "itens da landing page"
        ordering = ("section", "order", "pk")

    def __str__(self):
        return f"{self.get_section_display()}: {self.title}"
