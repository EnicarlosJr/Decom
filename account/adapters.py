from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect


ALLOWED_DOMAIN = "ufvjm.edu.br"


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
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
        allowed_email_domain = email.endswith(f"@{ALLOWED_DOMAIN}")
        allowed_google_domain = hd == ALLOWED_DOMAIN

        if email and email in verified_emails and allowed_email_domain:
            return
        if provider_verified and (allowed_email_domain or allowed_google_domain):
            return

        messages.error(
            request,
            "Use uma conta institucional @ufvjm.edu.br para entrar.",
        )
        raise ImmediateHttpResponse(redirect("home"))
