# Portal DECOM

Portal institucional em Django com:

- landing page publica editavel
- autenticacao por conta institucional
- controle de primeiro acesso por convite
- painel autenticado para usuarios e administradores

## O que o sistema faz

- Usuarios novos entram no portal apenas quando recebem um convite.
- O convite serve para o primeiro cadastro e validacao da conta correta.
- Depois que o usuario ja existe no sistema, ele pode voltar pela tela normal de login em `/accounts/entrar/`.
- Administradores podem criar e reenviar convites pelo painel web ou pelo admin do Django.
- O conteudo da landing pode ser mantido por `staff` ou por usuarios com a permissao de perfil `can_manage_landing_page`.

## Estrutura do projeto

- `decom/`: configuracoes do projeto Django.
- `accounts/`: autenticacao, convites, perfis e painel autenticado.
- `home/`: landing page publica e editor de conteudo da home.
- `templates/`: interface server-rendered do sistema.

## Apps principais

### `accounts`

Responsabilidades:

- login por codigo temporario
- integracao com login social via allauth
- regra de acesso por convite no primeiro login
- criacao automatica de usuario local no primeiro acesso autorizado
- painel autenticado
- operacao de convites

Modelos principais:

- `Profile`: papeis institucionais e permissoes extras do usuario
- `AccessInvitation`: convite de primeiro acesso
- `LoginCode`: codigo temporario do fluxo alternativo por e-mail

### `home`

Responsabilidades:

- renderizar a pagina inicial publica
- armazenar textos e cards dinamicos da landing
- permitir edicao controlada da landing page

Modelos principais:

- `LandingPageContent`: textos principais da home
- `LandingSectionItem`: cards e blocos dinamicos da home

## Fluxos do sistema

### 1. Primeiro acesso por convite

1. Um admin cria um convite em `/accounts/painel/convites/`.
2. O sistema envia um link unico para o e-mail institucional.
3. O usuario abre o link do convite.
4. O sistema guarda o convite na sessao e redireciona para o login social.
5. Se a conta autenticada bater com o convite, o usuario e criado ou vinculado.
6. O convite e marcado como aceito.

### 2. Reentrada normal do usuario

1. O usuario acessa `/accounts/entrar/`.
2. Clica em login com a conta institucional.
3. Se o usuario ja existe e esta ativo, entra normalmente mesmo sem convite pendente.

Esse ponto e importante:

- o convite e obrigatorio apenas para criar ou liberar o primeiro acesso
- ele nao e necessario para logins posteriores

### 3. Fluxo alternativo por codigo

Quando o login social nao estiver disponivel no ambiente:

1. o usuario informa o e-mail institucional
2. recebe um codigo temporario
3. valida o codigo em `/accounts/verificar/`

## Permissoes

- `is_staff`: pode operar o painel de convites
- `profile.can_manage_landing_page=True`: pode editar o conteudo da landing page

## Rotas principais

- `/`: home publica
- `/accounts/entrar/`: area de login
- `/accounts/painel/`: painel autenticado
- `/accounts/painel/convites/`: gestao de convites
- `/conteudo/landing/`: editor da landing
- `/admin/`: admin nativo do Django

## Interface atual

- O cabecalho usa componentes do DSGov com dropdown local para o menu da conta.
- O menu do usuario autenticado fica em `templates/navbar.html`.
- A inicializacao compartilhada de componentes e comportamentos de dropdown fica em `templates/base.html`.
- O painel de convites foi reduzido para um fluxo direto: criar, filtrar, listar e reenviar.

## Configuracao

### E-mail

```env
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.seu-servidor.com
EMAIL_PORT=587
EMAIL_HOST_USER=usuario
EMAIL_HOST_PASSWORD=senha
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=nao-responda@decom.ufvjm.edu.br
SITE_BASE_URL=http://localhost:8000
```

### Login social

O projeto habilita allauth automaticamente quando a biblioteca estiver instalada.
Nesse modo:

- o provider Google fica disponivel em `accounts/social/`
- o dominio institucional esperado e `ufvjm.edu.br`

## Execucao local

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

## Validacao

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test home accounts
```

## Documentacao adicional

- [Arquitetura](docs/ARQUITETURA.md)
