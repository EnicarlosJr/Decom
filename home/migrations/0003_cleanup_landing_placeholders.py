from django.db import migrations


DEFAULT_TEXT_VALUES = {
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

DEFAULT_ITEMS = [
    {
        "section": "hero_metric",
        "order": 10,
        "label": "Atendimento",
        "title": "Conteudo aberto e area restrita",
        "description": "",
    },
    {
        "section": "hero_metric",
        "order": 20,
        "label": "Acesso institucional",
        "title": "Conta @ufvjm.edu.br",
        "description": "",
    },
    {
        "section": "hero_metric",
        "order": 30,
        "label": "Modulos",
        "title": "Liberados por perfil",
        "description": "",
    },
    {
        "section": "access_step",
        "order": 10,
        "label": "",
        "title": "Convite previo",
        "description": "O primeiro acesso e liberado por convite enviado pela equipe responsavel pelo portal.",
    },
    {
        "section": "access_step",
        "order": 20,
        "label": "",
        "title": "Conta institucional",
        "description": "O usuario conclui a entrada com a propria conta institucional, sem criacao de senha local no sistema.",
    },
    {
        "section": "access_step",
        "order": 30,
        "label": "",
        "title": "Modulos por perfil",
        "description": "Estudantes, docentes, coordenacoes, chefia e equipes administrativas visualizam recursos diferentes conforme a atribuicao institucional.",
    },
    {
        "section": "service",
        "order": 10,
        "label": "Institucional",
        "title": "Departamento",
        "description": "Apresentacao institucional, estrutura academica e informacoes essenciais para a comunidade.",
    },
    {
        "section": "service",
        "order": 20,
        "label": "Academico",
        "title": "Orientacoes",
        "description": "Comunicados, instrucoes gerais e trilhas de atendimento para estudantes e docentes.",
    },
    {
        "section": "service",
        "order": 30,
        "label": "Atendimento",
        "title": "Canais de contato",
        "description": "Encaminhamento para suporte institucional, orientacoes de acesso e demandas administrativas.",
    },
    {
        "section": "service",
        "order": 40,
        "label": "Futuro digital",
        "title": "Servicos autenticados",
        "description": "Modulos internos de estagio, TCC, requerimentos e rotinas de gestao serao incorporados progressivamente.",
    },
    {
        "section": "module_point",
        "order": 10,
        "label": "",
        "title": "Usuarios entram com convite previo e conta institucional autorizada.",
        "description": "",
    },
    {
        "section": "module_point",
        "order": 20,
        "label": "",
        "title": "Cada perfil pode receber permissoes diferentes sem alterar o fluxo principal do portal.",
        "description": "",
    },
    {
        "section": "module_point",
        "order": 30,
        "label": "",
        "title": "Novos modulos podem ser adicionados ao painel do usuario conforme as regras do departamento.",
        "description": "",
    },
    {
        "section": "audience_card",
        "order": 10,
        "label": "Discente",
        "title": "Solicitacoes e acompanhamento",
        "description": "",
    },
    {
        "section": "audience_card",
        "order": 20,
        "label": "Docente",
        "title": "Orientacoes e fluxos academicos",
        "description": "",
    },
    {
        "section": "audience_card",
        "order": 30,
        "label": "Coordenacoes",
        "title": "Gestao e acompanhamento setorial",
        "description": "",
    },
    {
        "section": "audience_card",
        "order": 40,
        "label": "Equipe de gestao",
        "title": "Controle de acesso e operacoes internas",
        "description": "",
    },
]


def clear_seeded_landing_content(apps, schema_editor):
    LandingPageContent = apps.get_model("home", "LandingPageContent")
    LandingSectionItem = apps.get_model("home", "LandingSectionItem")

    for page in LandingPageContent.objects.all():
        changed_fields = []
        for field_name, seeded_value in DEFAULT_TEXT_VALUES.items():
            if getattr(page, field_name) == seeded_value:
                setattr(page, field_name, "")
                changed_fields.append(field_name)
        if changed_fields:
            changed_fields.append("updated_at")
            page.save(update_fields=changed_fields)

        for item_data in DEFAULT_ITEMS:
            LandingSectionItem.objects.filter(
                page=page,
                section=item_data["section"],
                order=item_data["order"],
                label=item_data["label"],
                title=item_data["title"],
                description=item_data["description"],
                action_label="",
                action_url="",
                is_active=True,
            ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0002_alter_landingpagecontent_access_badge_and_more"),
    ]

    operations = [
        migrations.RunPython(
            clear_seeded_landing_content,
            migrations.RunPython.noop,
        ),
    ]
