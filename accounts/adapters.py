"""Adaptadores do allauth para aplicar as regras de acesso do portal."""

try:
    from allauth.core.exceptions import ImmediateHttpResponse
    from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
except ImportError:  # pragma: no cover - caminho opcional
    DefaultSocialAccountAdapter = object

    class ImmediateHttpResponse(Exception):
        pass

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from .forms import build_internal_username
from .invitations import clear_pending_invitation, get_pending_invitation, get_valid_pending_invitation
from .models import is_institutional_email


User = get_user_model()


class InstitutionalSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Controla quem pode autenticar e quem pode se cadastrar via Google."""

    def _get_email_data(self, sociallogin):
        """Extrai e normaliza os dados de e-mail retornados pelo provedor."""
        extra_data = sociallogin.account.extra_data or {}
        email = (sociallogin.user.email or extra_data.get("email") or "").strip().lower()
        hd = (extra_data.get("hd") or "").strip().lower()
        verified_emails = {
            email_address.email.strip().lower()
            for email_address in getattr(sociallogin, "email_addresses", [])
            if getattr(email_address, "verified", False) and email_address.email
        }
        provider_verified = bool(
            extra_data.get("email_verified") or extra_data.get("verified_email")
        )
        return email, hd, verified_emails, provider_verified

    def _reject(self, request, message):
        """Interrompe o fluxo social com uma mensagem amigavel ao usuario."""
        messages.error(request, message)
        raise ImmediateHttpResponse(redirect("accounts:login_request"))

    def pre_social_login(self, request, sociallogin):
        """Executa as validacoes antes de conectar ou criar o usuario local."""
        allowed_domain = getattr(
            settings,
            "DEPARTMENT_ALLOWED_EMAIL_DOMAIN",
            "ufvjm.edu.br",
        ).strip().lower()

        email, hd, verified_emails, provider_verified = self._get_email_data(sociallogin)
        allowed_email_domain = is_institutional_email(email)
        allowed_google_domain = hd == allowed_domain

        if not email:
            self._reject(request, "O provedor nao retornou um e-mail valido para autenticacao.")

        if not (
            (email in verified_emails and allowed_email_domain)
            or (provider_verified and (allowed_email_domain or allowed_google_domain))
        ):
            self._reject(
                request,
                f"Use uma conta institucional @{allowed_domain} para entrar.",
            )

        pending_invitation = get_pending_invitation(request)
        if pending_invitation and pending_invitation.email != email:
            self._reject(
                request,
                f"Este convite foi emitido para {pending_invitation.email}. Entre com essa conta institucional.",
            )

        existing_user = User.objects.filter(email__iexact=email, is_active=True).first()
        if existing_user is not None:
            if pending_invitation and pending_invitation.is_usable and pending_invitation.accepted_at is None:
                pending_invitation.mark_as_accepted(existing_user)
                clear_pending_invitation(request)
            return

        if get_valid_pending_invitation(request, email=email) is not None:
            return

        self._reject(
            request,
            "Seu e-mail institucional ainda nao foi autorizado. Solicite um convite a um administrador do sistema.",
        )

    def is_open_for_signup(self, request, sociallogin):
        """Permite cadastro apenas quando existe convite pendente valido."""
        email, _, _, _ = self._get_email_data(sociallogin)
        return get_valid_pending_invitation(request, email=email) is not None

    def save_user(self, request, sociallogin, form=None):
        """Salva o usuario criado no primeiro acesso autorizado por convite."""
        user = sociallogin.user
        email, _, _, _ = self._get_email_data(sociallogin)
        user.email = email
        user.username = build_internal_username(email)
        user.is_active = True
        user.set_unusable_password()
        sociallogin.save(request)

        invitation = get_valid_pending_invitation(request, email=email)
        if invitation is not None:
            invitation.mark_as_accepted(user)
            clear_pending_invitation(request)
        return user
