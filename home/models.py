"""Modelos usados para tornar o conteudo da landing page administravel."""

from django.db import models


class LandingPageContent(models.Model):
    """Configuracao principal dos textos fixos exibidos na home."""
    hero_badge = models.CharField("selo do topo", max_length=120)
    hero_title = models.CharField("titulo principal", max_length=220)
    hero_description = models.TextField("descricao principal")
    hero_primary_cta_label = models.CharField(
        "texto do botao principal",
        max_length=60,
        default="Consultar servicos",
    )
    hero_secondary_cta_label = models.CharField(
        "texto do botao secundario",
        max_length=60,
        default="Area do usuario",
    )
    access_badge = models.CharField("selo do bloco de acesso", max_length=120)
    access_title = models.CharField("titulo do bloco de acesso", max_length=180)
    access_description = models.TextField("descricao do bloco de acesso")
    access_cta_label = models.CharField(
        "texto do botao de acesso",
        max_length=60,
        default="Abrir area do usuario",
    )
    services_badge = models.CharField("selo da secao de servicos", max_length=120)
    services_title = models.CharField("titulo da secao de servicos", max_length=180)
    services_description = models.TextField("descricao da secao de servicos")
    modules_badge = models.CharField("selo da secao autenticada", max_length=120)
    modules_title = models.CharField("titulo da secao autenticada", max_length=180)
    modules_description = models.TextField("descricao da secao autenticada")
    contact_badge = models.CharField("selo da secao final", max_length=120)
    contact_title = models.CharField("titulo da secao final", max_length=180)
    contact_description = models.TextField("descricao da secao final")
    contact_panel_badge = models.CharField("selo do painel lateral final", max_length=120)
    contact_panel_description = models.TextField("descricao do painel lateral final")
    contact_cta_label = models.CharField(
        "texto do botao final",
        max_length=60,
        default="Abrir area do usuario",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "configuracao da landing page"
        verbose_name_plural = "configuracoes da landing page"

    def __str__(self):
        return "Landing page principal"

    @classmethod
    def default_values(cls):
        """Conteudo inicial usado quando a landing ainda nao foi configurada."""
        return {
            "hero_badge": "Portal oficial do Departamento de Computacao",
            "hero_title": (
                "Informacoes publicas, servicos digitais e acesso institucional no mesmo ambiente."
            ),
            "hero_description": (
                "O portal foi estruturado para atender a comunidade academica com conteudo aberto ao publico e, ao mesmo tempo, preparar uma area restrita para fluxos internos do departamento."
            ),
            "hero_primary_cta_label": "Consultar servicos",
            "hero_secondary_cta_label": "Area do usuario",
            "access_badge": "Acesso restrito",
            "access_title": "Entrada institucional controlada",
            "access_description": (
                "O conteudo publico pode ser consultado livremente. As funcionalidades internas sao liberadas somente para usuarios autorizados."
            ),
            "access_cta_label": "Abrir area do usuario",
            "services_badge": "Servicos ao publico",
            "services_title": "Informacoes essenciais e acesso rapido",
            "services_description": (
                "A navegacao foi organizada para diferenciar com clareza o que pode ser consultado livremente do que depende de autenticacao institucional."
            ),
            "modules_badge": "Area autenticada",
            "modules_title": "Estrutura pronta para modulos por nivel de acesso",
            "modules_description": (
                "A autenticacao, os convites e a classificacao de perfis ja estao organizados para receber funcionalidades novas sem misturar rotinas publicas com operacoes internas."
            ),
            "contact_badge": "Atendimento institucional",
            "contact_title": "Orientacoes, acesso e suporte",
            "contact_description": (
                "O portal foi preparado para evoluir sem misturar conteudo publico e operacoes internas. Quando novos modulos forem liberados, eles seguirao a mesma logica de acesso por perfil e autenticacao institucional."
            ),
            "contact_panel_badge": "Precisa entrar no sistema?",
            "contact_panel_description": (
                "Se voce ainda nao possui acesso, procure a equipe responsavel pelo portal para solicitar a liberacao do convite institucional."
            ),
            "contact_cta_label": "Abrir area do usuario",
        }

    @classmethod
    def get_solo(cls):
        """Recupera a unica configuracao de landing, criando o baseline se preciso."""
        page = cls.objects.order_by("pk").first()
        if page is None:
            page = cls.objects.create(**cls.default_values())
            page.seed_default_items()
            return page

        if not page.items.exists():
            page.seed_default_items()
        return page

    def seed_default_items(self):
        """Cria os cards padrao da landing na primeira inicializacao."""
        if self.items.exists():
            return

        self.items.bulk_create(
            [
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.HERO_METRIC,
                    order=10,
                    label="Atendimento",
                    title="Conteudo aberto e area restrita",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.HERO_METRIC,
                    order=20,
                    label="Acesso institucional",
                    title="Conta @ufvjm.edu.br",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.HERO_METRIC,
                    order=30,
                    label="Modulos",
                    title="Liberados por perfil",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.ACCESS_STEP,
                    order=10,
                    title="Convite previo",
                    description="O primeiro acesso e liberado por convite enviado pela equipe responsavel pelo portal.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.ACCESS_STEP,
                    order=20,
                    title="Conta institucional",
                    description="O usuario conclui a entrada com a propria conta institucional, sem criacao de senha local no sistema.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.ACCESS_STEP,
                    order=30,
                    title="Modulos por perfil",
                    description="Estudantes, docentes, coordenacoes, chefia e equipes administrativas visualizam recursos diferentes conforme a atribuicao institucional.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.SERVICE,
                    order=10,
                    label="Institucional",
                    title="Departamento",
                    description="Apresentacao institucional, estrutura academica e informacoes essenciais para a comunidade.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.SERVICE,
                    order=20,
                    label="Academico",
                    title="Orientacoes",
                    description="Comunicados, instrucoes gerais e trilhas de atendimento para estudantes e docentes.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.SERVICE,
                    order=30,
                    label="Atendimento",
                    title="Canais de contato",
                    description="Encaminhamento para suporte institucional, orientacoes de acesso e demandas administrativas.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.SERVICE,
                    order=40,
                    label="Futuro digital",
                    title="Servicos autenticados",
                    description="Modulos internos de estagio, TCC, requerimentos e rotinas de gestao serao incorporados progressivamente.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.MODULE_POINT,
                    order=10,
                    title="Usuarios entram com convite previo e conta institucional autorizada.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.MODULE_POINT,
                    order=20,
                    title="Cada perfil pode receber permissoes diferentes sem alterar o fluxo principal do portal.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.MODULE_POINT,
                    order=30,
                    title="Novos modulos podem ser adicionados ao painel do usuario conforme as regras do departamento.",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.AUDIENCE_CARD,
                    order=10,
                    label="Discente",
                    title="Solicitacoes e acompanhamento",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.AUDIENCE_CARD,
                    order=20,
                    label="Docente",
                    title="Orientacoes e fluxos academicos",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.AUDIENCE_CARD,
                    order=30,
                    label="Coordenacoes",
                    title="Gestao e acompanhamento setorial",
                ),
                LandingSectionItem(
                    page=self,
                    section=LandingSectionItem.Section.AUDIENCE_CARD,
                    order=40,
                    label="Equipe de gestao",
                    title="Controle de acesso e operacoes internas",
                ),
            ]
        )


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
