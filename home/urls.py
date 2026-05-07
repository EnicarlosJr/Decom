"""Rotas publicas da landing e do editor de conteudo."""

from django.urls import path

from . import views


app_name = "home"


urlpatterns = [
    path("", views.index, name="index"),
    path("conteudo/landing/", views.landing_editor, name="landing_editor"),
]
