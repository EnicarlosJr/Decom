from types import SimpleNamespace

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from account.adapters import MySocialAccountAdapter


class MySocialAccountAdapterTests(TestCase):
    def setUp(self):
        self.adapter = MySocialAccountAdapter()
        self.factory = RequestFactory()

    def _build_request(self):
        request = self.factory.get("/")
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def _build_sociallogin(self, email, hd="", email_verified=True, address_verified=True):
        extra_data = {"email": email, "email_verified": email_verified}
        if hd:
            extra_data["hd"] = hd

        return SimpleNamespace(
            user=SimpleNamespace(email=email),
            account=SimpleNamespace(extra_data=extra_data),
            email_addresses=[
                EmailAddress(email=email, verified=address_verified, primary=True)
            ],
        )

    def test_allows_verified_ufvjm_email(self):
        request = self._build_request()
        sociallogin = self._build_sociallogin(
            email="aluno@ufvjm.edu.br",
            hd="ufvjm.edu.br",
        )

        self.adapter.pre_social_login(request, sociallogin)

    def test_rejects_email_outside_ufvjm_with_redirect_and_message(self):
        request = self._build_request()
        sociallogin = self._build_sociallogin(
            email="alguem@gmail.com",
            hd="",
        )

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            self.adapter.pre_social_login(request, sociallogin)

        response = ctx.exception.response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
        self.assertEqual(
            [str(message) for message in get_messages(request)],
            ["Use uma conta institucional @ufvjm.edu.br para entrar."],
        )
