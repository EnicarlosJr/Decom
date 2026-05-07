"""Rotas publicas e autenticadas relacionadas a contas."""

from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path("entrar/", views.request_login_code, name="login_request"),
    path("convites/<str:token>/", views.accept_invitation, name="accept_invitation"),
    path("verificar/", views.verify_login_code, name="verify_login_code"),
    path("painel/", views.dashboard, name="dashboard"),
    path("painel/convites/", views.invitation_panel, name="invitation_panel"),
    path(
        "painel/convites/<int:invitation_id>/reenviar/",
        views.resend_invitation,
        name="resend_invitation",
    ),
    path("sair/", views.logout_view, name="logout"),
]
