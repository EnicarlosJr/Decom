# Arquitetura do Portal DECOM

## Visao geral

O sistema foi desenhado para separar claramente duas camadas:

1. conteudo publico do portal
2. area autenticada com acesso controlado

Ele usa Django server-rendered, com regras de acesso centralizadas na app `accounts`.

## Componentes principais

### Camada publica

- `home.views.index`
- `templates/home/index.html`
- `LandingPageContent`
- `LandingSectionItem`

Essa camada entrega a landing page e permite que o conteudo seja alterado sem mudar o layout.

### Camada autenticada

- `accounts.views.request_login_code`
- `accounts.views.verify_login_code`
- `accounts.views.dashboard`
- `accounts.views.invitation_panel`

Essa camada concentra login, painel do usuario e gestao operacional de convites.

## Regras de autenticacao

### Regra de negocio

- novos usuarios nao entram livremente
- o primeiro acesso depende de convite
- usuarios ja criados podem voltar pela tela normal de login

### Implementacao

- `InstitutionalSocialAccountAdapter.pre_social_login()` valida dominio, verificacao do e-mail e convite pendente
- se o usuario ja existir e estiver ativo, a entrada e permitida sem novo convite
- se o usuario nao existir, o cadastro so abre quando houver convite valido

## Convites

`AccessInvitation` guarda:

- e-mail autorizado
- status de envio
- aceite
- validade
- token de acesso

### Decisao importante

O metodo `renew()` nao troca mais o token do convite.

Motivo:

- evitar quebra de links antigos em reenvios
- tornar o fluxo mais robusto quando o usuario volta a abrir um e-mail antigo

Tambem existe compatibilidade defensiva em `AccessInvitation.find_by_token()` para lidar com:

- links copiados com padding removido
- pequenas truncagens de token feitas por clientes de e-mail

## Perfis e permisses

O perfil complementar do usuario fica em `Profile`.

Ele concentra:

- papeis institucionais
- `can_manage_landing_page`

Uso atual:

- `staff` opera convites
- `staff` ou `can_manage_landing_page` edita a landing

## Frontend

O frontend atual segue uma direcao unica:

- tipografia `Fraunces` para titulos
- tipografia `Manrope` para leitura geral
- fundo em camadas claras com contraste suave
- componentes compartilhados em `templates/base.html`

Classes utilitarias principais:

- `.surface-panel`
- `.surface-soft`
- `.section-label`
- `.btn-primary`
- `.btn-secondary`
- `.btn-light`

### Cabecalho e dropdown da conta

- o cabecalho atual reaproveita o estilo do DSGov, mas nao usa o markup completo exigido por `BRHeader`
- por isso a inicializacao do header em `templates/base.html` e defensiva
- o dropdown da conta autenticada usa estrutura em `templates/navbar.html` com controle local de abrir, fechar, clique fora, `Esc` e `resize`
- a classe `header-account` existe para manter o menu do usuario fechado por padrao em desktop e mobile

### Painel de convites

- `templates/accounts/invitation_panel.html` segue um fluxo enxuto
- a tela foi reduzida para formulario de criacao, filtros e tabela de convites
- metricas, modais extras e acoes sem fluxo implementado foram removidos para manter consistencia operacional

## Pontos de extensao

### Novos modulos internos

Adicionar em:

- regras de visibilidade em `accounts.views._build_access_modules`
- nova rota e template autenticado

### Novas secoes da landing

Adicionar em:

- `LandingSectionItem.Section`
- `home.views.LANDING_SECTION_CONFIGS`
- `templates/home/index.html`
- `templates/home/landing_editor.html`

### Nova regra de acesso

Adicionar em:

- `accounts.adapters.InstitutionalSocialAccountAdapter`
- testes em `accounts/tests.py`

## Testes

A cobertura atual valida principalmente:

- fluxo de codigo temporario
- convite de primeiro acesso
- painel de convites
- compatibilidade do token de convite
- acesso ao admin de convites
- permissao do editor de landing

Comando:

```powershell
.\.venv\Scripts\python.exe manage.py test home accounts
```
