from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent



SECRET_KEY = 'django-insecure-r6-8f%kr$-yoekkj20p!$qji8me!=eidcjy2dbz*&p+1de5ze+'

DEBUG = True 

ALLOWED_HOSTS = []  


#  APLICAÇÕES
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Necessário para allauth (multi-sites)
    'django.contrib.sites',

    # Allauth (autenticação)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Provider Google
    'allauth.socialaccount.providers.google',

    # Seu app
    'account',
]

SITE_ID = 1  # Deve existir no admin (/admin/sites/site/)


# 🧠 MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',

    # Proteção CSRF (formulários)
    'django.middleware.csrf.CsrfViewMiddleware',

    # Autenticação padrão Django
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    # Middleware do allauth (controle de sessão social)
    'allauth.account.middleware.AccountMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


#  AUTENTICAÇÃO
AUTHENTICATION_BACKENDS = [
    # Login padrão Django (admin, etc.)
    'django.contrib.auth.backends.ModelBackend',

    # Login social (Google)
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Configuração geral do Allauth
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True

# Redirecionamento após login
LOGIN_REDIRECT_URL = '/'


#  TEMPLATES
ROOT_URLCONF = 'decom.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Pode adicionar templates globais depois
        'DIRS': [],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                # Obrigatório para allauth funcionar
                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'decom.wsgi.application'


# BANCO DE DADOS (DEV)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# SENHAS
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# INTERNACIONALIZAÇÃO
LANGUAGE_CODE = 'pt-br'  

TIME_ZONE = 'America/Sao_Paulo' 

USE_I18N = True
USE_TZ = True



# ARQUIVOS ESTÁTICOS
STATIC_URL = 'static/'



# GOOGLE LOGIN (ALLAUTH)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # Segurança moderna (recomendado)
        'OAUTH_PKCE_ENABLED': True,

        # Permissões solicitadas ao Google
        'SCOPE': [
            'profile',
            'email',
        ],

        # Tipo de acesso
        'AUTH_PARAMS': {
            'access_type': 'online',  # usar 'offline' se quiser refresh token
            'hd': 'ufvjm.edu.br',
        },

        #Opcional: pegar foto do usuário que tem no document do allauth
        #'FETCH_USERINFO': True,
    }
}



# RESTRIÇÃO DE DOMÍNIO (UFVJM)
# Adapter customizado para permitir apenas emails institucionais
SOCIALACCOUNT_ADAPTER = 'account.adapters.MySocialAccountAdapter'
