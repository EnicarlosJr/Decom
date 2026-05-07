"""Mapa principal de URLs do projeto."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("home.urls", "home"), namespace="home")),
]

if settings.ENABLE_ALLAUTH_LOGIN:
    urlpatterns.insert(1, path("accounts/social/", include("allauth.urls")))
